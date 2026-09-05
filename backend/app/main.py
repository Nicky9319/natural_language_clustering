from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
logger.info(f"GOOGLE_API_KEY configured: {os.getenv('GOOGLE_API_KEY') is not None}")
logger.info(f"CEREBRAS_API_KEY configured: {os.getenv('CEREBRAS_API_KEY') is not None}")

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

# Serve frontend static files from the app directory (built React app)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# CORS middleware for frontend
# In production, set FRONTEND_URL environment variable to restrict origins
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since frontend is served from same origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cluster_router)


@app.get("/health")
async def health():
    llm_available = os.getenv("GOOGLE_API_KEY") is not None or os.getenv("CEREBRAS_API_KEY") is not None
    return {"status": "healthy", "llm_available": llm_available}


# Serve static files (React build) and handle SPA routing
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """
    Serve static files from the React build, falling back to index.html for SPA routing.
    Only serves non-API paths to avoid conflicts with API routes.
    """
    # Skip API routes
    if path.startswith("api"):
        return

    file_path = os.path.join(STATIC_DIR, path)

    # If path is a file, serve it
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # For non-file paths (e.g., /cluster), serve index.html for SPA routing
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    # No frontend built yet
    return {"error": "Frontend not built. See README for build instructions."}


@app.get("/")
async def root():
    """Serve the React app index.html."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "Natural Language Clustering API - visit /docs for API docs"}
