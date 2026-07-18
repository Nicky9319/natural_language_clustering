from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.cluster import router as cluster_router
import os
from dotenv import load_dotenv
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

# Load .env file if present
load_dotenv()

logger.info("=" * 60)
logger.info("Starting Natural Language Clustering API...")
logger.info("=" * 60)
logger.info(f"GROQ_API_KEY configured: {os.getenv('GROQ_API_KEY') is not None}")

# Keep startup responsive by default. The embedding model is loaded on the first
# clustering request unless PRELOAD_EMBEDDING_MODEL=true is set.
if os.getenv("PRELOAD_EMBEDDING_MODEL", "").lower() == "true":
    from app.services.embedder import embedder
    logger.info("Pre-loading embedding model at startup...")
    try:
        embedder.load_model()
        logger.info("Embedding model ready!")
    except Exception as e:
        logger.error(f"Failed to load embedding model at startup: {e}")


app = FastAPI(
    title="Natural Language Clustering API",
    description="API for clustering text data using embeddings and K-Means",
    version="1.0.0"
)

# CORS middleware for frontend
# In production, set FRONTEND_URL environment variable to restrict origins
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000"],  # Allow localhost for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cluster_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "groq_available": os.getenv("GROQ_API_KEY") is not None}
