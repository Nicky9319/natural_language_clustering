from fastapi import APIRouter, HTTPException
from app.models.schemas import ClusterRequest, ClusterResponse, ClusterPoint, ClusterInfo, ClusterStats, SampleTextsResponse
from app.services.embedder import embedder
from app.services.clusterer import Clusterer
from app.services.namer import namer
from collections import defaultdict
import asyncio
import concurrent.futures
import logging
import time
import groq
import os


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cluster_api")


router = APIRouter(prefix="/api", tags=["cluster"])


# Predefined cluster colors
CLUSTER_COLORS = [
    "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#d946ef", "#a855f7", "#64748b", "#e11d48"
]


def _run_embedder(texts: list[str]):
    """Synchronous embedding function for thread pool."""
    return embedder.encode(texts)


def _run_clustering(embeddings, n_clusters: int | None, method: str, min_cluster_size: int | None):
    """Synchronous clustering function for thread pool."""
    clusterer = Clusterer()
    return clusterer.cluster(embeddings, n_clusters, method, min_cluster_size)


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_texts(request: ClusterRequest):
    """Cluster texts using embeddings and K-Means."""
    start_time = time.time()
    step_time = start_time
    logger.info(f"POST /api/cluster ========== START ==========")
    logger.info(f"POST /api/cluster - Received request with {len(request.texts)} texts")

    def log_step(step_name, prev_time):
        """Log progress with elapsed time from start and since last step."""
        now = time.time()
        elapsed_total = now - start_time
        elapsed_step = now - prev_time
        logger.info(f"POST /api/cluster - [STEP] {step_name} - +{elapsed_step:.1f}s total, {elapsed_total:.1f}s elapsed")
        return now

    if not request.texts:
        logger.warning("POST /api/cluster - No texts provided")
        raise HTTPException(status_code=400, detail="No texts provided")

    if len(request.texts) < 4:
        logger.warning(f"POST /api/cluster - Insufficient texts: {len(request.texts)}")
        raise HTTPException(status_code=400, detail="Need at least 4 texts to cluster (UMAP requires minimum points)")

    # Validate method
    if request.method not in ("kmeans", "hdbscan"):
        logger.warning(f"POST /api/cluster - Invalid method: {request.method}")
        raise HTTPException(status_code=400, detail="method must be 'kmeans' or 'hdbscan'")

    # Validate n_clusters for kmeans method
    if request.method == "kmeans" and request.n_clusters is not None:
        if request.n_clusters < 1:
            logger.warning(f"POST /api/cluster - Invalid n_clusters: {request.n_clusters}")
            raise HTTPException(status_code=400, detail="n_clusters must be at least 1")
        if request.n_clusters > len(request.texts):
            logger.warning(f"POST /api/cluster - n_clusters {request.n_clusters} > texts {len(request.texts)}")
            raise HTTPException(status_code=400, detail="n_clusters must be <= number of texts")
    # For hdbscan, n_clusters is ignored (auto-detected)

    step_time = log_step(f"Validating input for {len(request.texts)} texts, method={request.method}", step_time)

    # Run blocking operations in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        try:
            logger.info(f"POST /api/cluster - Starting embedding model load...")
            step_time = log_step("Starting embedding encoding", step_time)
            embeddings = await loop.run_in_executor(pool, _run_embedder, request.texts)
            step_time = log_step(f"Embedding complete, shape: {embeddings.shape}", step_time)
        except Exception as e:
            logger.error(f"POST /api/cluster - Embedding FAILED: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding failed: {type(e).__name__}: {str(e)}")

        try:
            method_name = "K-Means" if request.method == "kmeans" else "HDBSCAN"
            logger.info(f"POST /api/cluster - Starting {method_name} + UMAP clustering...")
            step_time = log_step(f"Starting {method_name} clustering", step_time)
            result = await loop.run_in_executor(pool, _run_clustering, embeddings, request.n_clusters, request.method, request.min_cluster_size)
            step_time = log_step(f"Clustering complete, {result['n_clusters']} clusters found", step_time)
        except Exception as e:
            logger.error(f"POST /api/cluster - Clustering FAILED: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Clustering failed: {type(e).__name__}: {str(e)}")

    labels = result["labels"]
    points_2d = result["points_2d"]
    confidence = result["confidence"]
    n_clusters = result["n_clusters"]
    silhouette = result["silhouette"]
    cluster_sizes = result["cluster_sizes"]

    # Group texts by cluster for naming (skip noise label -1 for HDBSCAN)
    cluster_texts = defaultdict(list)
    for i, label in enumerate(labels):
        if label != -1:  # Skip noise points for naming
            cluster_texts[label].append(request.texts[i])

    noise_count = sum(1 for l in labels if l == -1)
    logger.info(f"POST /api/cluster - Grouped texts into {n_clusters} clusters ({noise_count} noise points excluded from naming)")
    step_time = log_step(f"Grouped texts into {n_clusters} clusters", step_time)

    # Name clusters using GROQ (if available) - this is fast, runs in-thread
    logger.info(f"POST /api/cluster - Calling Groq for cluster naming...")
    step_time = log_step("Starting Groq cluster naming", step_time)
    try:
        names = namer.name_clusters(cluster_texts)
        step_time = log_step(f"Groq naming complete: {names}", step_time)
    except Exception as e:
        logger.error(f"POST /api/cluster - Naming FAILED: {type(e).__name__}: {e}")
        names = {i: f"Cluster {i+1}" for i in cluster_texts.keys()}
        step_time = log_step("Using fallback cluster names due to naming error", step_time)

    # Build response
    clusters = []
    cluster_idx = 0
    for label in sorted(cluster_texts.keys()):
        clusters.append(ClusterInfo(
            id=str(label),
            name=names.get(label, f"Cluster {cluster_idx+1}"),
            size=cluster_sizes[label],
            color=CLUSTER_COLORS[cluster_idx % len(CLUSTER_COLORS)]
        ))
        cluster_idx += 1

    # Add "Unclustered" pseudo-cluster for HDBSCAN noise points
    if noise_count > 0:
        clusters.append(ClusterInfo(
            id="unclustered",
            name="Unclustered",
            size=noise_count,
            color="#e5e7eb"  # Gray for noise
        ))

    points = []
    for i, (x, y) in enumerate(points_2d):
        label = labels[i]
        # For noise points (label -1), use "unclustered" as the cluster identifier
        cluster_id = "unclustered" if label == -1 else str(label)
        points.append(ClusterPoint(
            x=float(x),
            y=float(y),
            cluster=cluster_id,
            confidence=float(confidence[i]),
            text=request.texts[i]
        ))

    stats = ClusterStats(
        total_points=len(request.texts),
        num_clusters=n_clusters,
        silhouette_score=float(silhouette) if silhouette is not None else 0.0
    )

    step_time = log_step(f"Building response with {len(clusters)} clusters, {len(points)} points", step_time)

    total_elapsed = time.time() - start_time
    logger.info(f"POST /api/cluster ========== COMPLETE ==========")
    logger.info(f"POST /api/cluster - Total time: {total_elapsed:.2f}s")
    logger.info(f"POST /api/cluster - Returning {len(clusters)} clusters with {len(points)} points")

    return ClusterResponse(
        clusters=clusters,
        points=points,
        stats=stats
    )


@router.get("/sample", response_model=SampleTextsResponse)
async def get_sample_texts():
    """Fetch 100 sample texts from Groq for clustering demo."""
    start_time = time.time()
    logger.info("GET /api/sample - Fetching sample texts from Groq")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GET /api/sample - GROQ_API_KEY not set")
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    try:
        groq_client = groq.Groq(api_key=api_key)

        prompt = """Generate EXACTLY 100 diverse, short text snippets (each 10-20 words) for a text clustering demo.
These MUST cover various topics like technology, business, health, science, entertainment, sports, politics, education, finance, etc.
You MUST provide exactly 100 items in the array, no more and no less.

Return them as a JSON object with a "texts" key containing an array of EXACTLY 100 strings:

{"texts": ["Text 1...", "Text 2...", "Text 3...", ...up to "Text 100..."]}

Respond ONLY with valid JSON containing exactly 100 texts:"""

        logger.info("GET /api/sample - Calling Groq API...")
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates sample text data. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=8192,
                timeout=120.0  # 120 second timeout for Groq API
            )
            logger.info(f"GET /api/sample - Groq API response received, status OK")
        except groq.RateLimitError as e:
            logger.error(f"GET /api/sample - Groq API rate limit exceeded: {e}")
            raise HTTPException(status_code=429, detail=f"Groq API rate limit exceeded - please wait a moment and try again: {str(e)}")
        except groq.APITimeoutError as e:
            logger.error(f"GET /api/sample - Groq API timeout: {e}")
            raise HTTPException(status_code=504, detail=f"Groq API timeout - please try again: {str(e)}")
        except groq.APIStatusError as e:
            logger.error(f"GET /api/sample - Groq API status error: {e.status_code} - {e.response}")
            raise HTTPException(status_code=e.status_code, detail=f"Groq API error ({e.status_code}): {str(e)}")
        except Exception as e:
            logger.error(f"GET /api/sample - Unexpected Groq API error: {type(e).__name__} - {e}")
            raise HTTPException(status_code=500, detail=f"Groq API failed: {type(e).__name__}: {str(e)}")

        result_text = response.choices[0].message.content.strip()
        logger.info(f"GET /api/sample - Received response from Groq, parsing JSON...")

        import json
        try:
            data = json.loads(result_text)
            texts = data.get("texts", [])

            if len(texts) < 100:
                logger.warning(f"GET /api/sample - Only received {len(texts)} texts, padding to 100...")
                # Pad with diverse meaningful texts if needed
                padding_templates = [
                    "Machine learning algorithms are transforming industries worldwide",
                    "Climate change affects ecosystems across every continent",
                    "Healthcare innovation leads to better patient outcomes",
                    "Space exploration opens new frontiers for humanity",
                    "Education technology reaches remote learners everywhere",
                    "Renewable energy powers sustainable development",
                    "Financial markets respond to global economic trends",
                    "Sports analytics revolutionize team performance strategies",
                    "Music streaming connects artists with global audiences",
                    "Social media shapes modern communication patterns",
                    "Artificial intelligence assists in scientific discoveries",
                    "Urban planning creates smarter cities for tomorrow",
                    "Food security addresses challenges in agriculture",
                    "Cybersecurity protects critical digital infrastructure",
                    "Transportation advances improve logistics efficiency",
                    "Entertainment content engages diverse audiences globally",
                    "Fashion industry adapts to changing consumer preferences",
                    "Environmental conservation efforts gain momentum everywhere",
                    "Scientific research unlocks new possibilities for future",
                    "Digital transformation reshapes business operations"
                ]
                idx = 0
                while len(texts) < 100:
                    texts.append(f"{padding_templates[idx % len(padding_templates)]} ({len(texts) + 1})")
                    idx += 1

            elapsed = time.time() - start_time
            logger.info(f"GET /api/sample - Returning {len(texts)} sample texts in {elapsed:.2f}s")

            return SampleTextsResponse(texts=texts[:100])

        except json.JSONDecodeError as e:
            logger.error(f"GET /api/sample - JSON parse error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse Groq response: {str(e)}")

    except Exception as e:
        logger.error(f"GET /api/sample - Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sample texts: {str(e)}")
