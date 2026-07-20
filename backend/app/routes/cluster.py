from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import ClusterRequest, ClusterResponse, ClusterPoint, ClusterInfo, ClusterStats, SampleTextsResponse
from app.services.embedder import embedder
from app.services.clusterer import Clusterer
from app.services.namer import namer
from collections import defaultdict
import asyncio
import concurrent.futures
import logging
import time
from cerebras.cloud.sdk import Cerebras
from cerebras.cloud.sdk import RateLimitError as CerebrasRateLimitError
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cluster_api")


def _extract_json_from_text(text: str) -> str | None:
    """Extract JSON object from text by finding {"texts": or last {...} block."""
    import re
    # Try to find ```json ... ``` code block first (greedy to capture outermost braces)
    json_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', text)
    if json_match:
        return json_match.group(1)
    # Try to find {"texts": ...} pattern - look for the opening brace after "texts": or """
    texts_marker = re.search(r'["\']texts["\']\s*:\s*\[', text)
    if texts_marker:
        # Find the opening { before "texts"
        search_start = max(0, texts_marker.start() - 200)
        search_region = text[search_start:texts_marker.end()]
        brace_pos = -1
        for i, c in enumerate(search_region):
            if c == '{':
                brace_pos = i
        if brace_pos >= 0:
            start = search_start + brace_pos
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
    # Last resort: find the FIRST { that eventually closes at depth 0.
    # This captures the outermost JSON object even when inner objects share the same line.
    for i, c in enumerate(text):
        if c == '{':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        return text[i:j+1]
    return None


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

    # Name clusters using Cerebras (if available) - this is fast, runs in-thread
    logger.info(f"POST /api/cluster - Calling Cerebras for cluster naming...")
    step_time = log_step("Starting Cerebras cluster naming", step_time)
    try:
        names = namer.name_clusters(cluster_texts)
        step_time = log_step(f"Cerebras naming complete: {names}", step_time)
    except Exception as e:
        logger.error(f"POST /api/cluster - Naming FAILED: {type(e).__name__}: {e}")
        names = {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}
        step_time = log_step("Using fallback cluster names due to naming error", step_time)

    # Build response
    clusters = []
    cluster_idx = 0
    for label in sorted(cluster_texts.keys()):
        name_info = names.get(label, {"name": f"Cluster {cluster_idx+1}", "description": None})
        clusters.append(ClusterInfo(
            id=str(label),
            name=name_info.get("name", f"Cluster {cluster_idx+1}"),
            description=name_info.get("description"),
            size=cluster_sizes[label],
            color=CLUSTER_COLORS[cluster_idx % len(CLUSTER_COLORS)]
        ))
        cluster_idx += 1

    # Add "Unclustered" pseudo-cluster for HDBSCAN noise points
    if noise_count > 0:
        clusters.append(ClusterInfo(
            id="unclustered",
            name="Unclustered",
            description="Points that could not be assigned to any cluster",
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


CHUNK_SIZE = 100  # texts per Cerebras API call


def _is_retryable_error(e: Exception) -> bool:
    """Return True for transient errors worth retrying."""
    if isinstance(e, CerebrasRateLimitError):
        return True
    # Timeout / connection errors
    err_name = type(e).__name__
    err_msg = str(e).lower()
    if 'timeout' in err_msg or 'timed out' in err_msg:
        return True
    if 'connection' in err_msg or 'network' in err_msg:
        return True
    return False


def _fetch_chunk(client: Cerebras, chunk_idx: int, chunk_size: int) -> list[str]:
    """Fetch one chunk of sample texts from Cerebras, with retry."""
    import json

    prompt = f"""Generate EXACTLY {chunk_size} diverse, short text snippets (each 10-20 words) for a text clustering demo.
These MUST cover various topics like technology, business, health, science, entertainment, sports, politics, education, finance, etc.
You MUST provide exactly {chunk_size} items in the array, no more and no less.

Return them as a JSON object with a "texts" key containing an array of EXACTLY {chunk_size} strings:

{{"texts": ["Text 1...", "Text 2...", "Text 3...", ...up to "Text {chunk_size}..."]}}

Respond ONLY with valid JSON containing exactly {chunk_size} texts:"""

    response = client.chat.completions.create(
        model="gpt-oss-120b",
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
        timeout=180.0
    )

    raw_content = response.choices[0].message.content
    if raw_content is None:
        reasoning = response.choices[0].message.reasoning
        if reasoning:
            raw_content = _extract_json_from_text(reasoning)

    if raw_content is None:
        raise ValueError("Cerebras returned empty response")

    result_text = raw_content.strip()
    data = json.loads(result_text)
    texts = data.get("texts", [])
    return texts


@router.get("/sample", response_model=SampleTextsResponse)
async def get_sample_texts(
    count: int = Query(default=100, ge=1, le=10000, description="Number of sample texts to generate (1-10000)")
):
    """Generate up to 10,000 diverse sample texts using Cerebras API, with batching and retry."""
    start_time = time.time()
    logger.info(f"GET /api/sample - count={count}")

    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        logger.warning("GET /api/sample - CEREBRAS_API_KEY not set")
        raise HTTPException(status_code=500, detail="CEREBRAS_API_KEY not configured")

    cerebras_client = Cerebras(api_key=api_key)

    num_chunks = (count + CHUNK_SIZE - 1) // CHUNK_SIZE
    all_texts: list[str] = []
    failed_chunks: list[int] = []

    for chunk_idx in range(num_chunks):
        chunk_start = time.time()
        texts_in_chunk = min(CHUNK_SIZE, count - len(all_texts))

        try:
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=2, max=30),
                retry=retry_if_exception_type(Exception),
                reraise=True,
                before_sleep=lambda retry_state: logger.warning(
                    f"GET /api/sample - chunk {chunk_idx+1}/{num_chunks} retry {retry_state.attempt_number}/3 "
                    f"after error: {type(retry_state.outcome.exception()).__name__}: {retry_state.outcome.exception()}"
                )
            )
            def fetch_with_retry():
                return _fetch_chunk(cerebras_client, chunk_idx, texts_in_chunk)

            chunk_texts = fetch_with_retry()
            all_texts.extend(chunk_texts)
            chunk_elapsed = time.time() - chunk_start
            logger.info(
                f"GET /api/sample - chunk {chunk_idx+1}/{num_chunks} OK "
                f"(+{len(chunk_texts)} texts, {chunk_elapsed:.1f}s, total so far: {len(all_texts)})"
            )

        except Exception as e:
            if not _is_retryable_error(e):
                # Non-retryable error (e.g., JSON parse, validation) — fail immediately
                logger.error(f"GET /api/sample - chunk {chunk_idx+1}/{num_chunks} non-retryable error: {type(e).__name__}: {e}")
                raise HTTPException(status_code=500, detail=f"Cerebras API error: {type(e).__name__}: {str(e)}")
            # Retry exhausted — record failure
            logger.error(f"GET /api/sample - chunk {chunk_idx+1}/{num_chunks} failed after 3 retries: {type(e).__name__}: {e}")
            failed_chunks.append(chunk_idx + 1)

        # Early exit if we already have enough texts
        if len(all_texts) >= count:
            break

    if failed_chunks:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate texts for chunks {failed_chunks} after retries. Try again or reduce count."
        )

    result_texts = all_texts[:count]
    elapsed = time.time() - start_time
    logger.info(f"GET /api/sample - Returning {len(result_texts)} texts in {elapsed:.1f}s via {num_chunks} chunks")

    return SampleTextsResponse(texts=result_texts, count=len(result_texts))
