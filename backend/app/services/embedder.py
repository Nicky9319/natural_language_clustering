import numpy as np
import logging
import os
import json

logger = logging.getLogger("embedder")

# Default config
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"  # Google AI embedding model


def _load_config() -> dict:
    """Load config from config.json if present."""
    # embedder.py is at /app/app/services/embedder.py
    # config.json is at /app/config.json (three levels up from services/)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    logger.info(f"[CONFIG] Looking for config at: {config_path}")
    logger.info(f"[CONFIG] Base dir: {base_dir}")
    logger.info(f"[CONFIG] File exists: {os.path.exists(config_path)}")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                logger.info(f"[CONFIG] Loaded config: {config}")
                return config
        except Exception as e:
            logger.error(f"[CONFIG] Failed to load config: {e}")
    return {}


class Embedder:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Embedder singleton created")
        return cls._instance

    def load_model(self):
        if self._model is None:
            config = _load_config()
            embed_config = config.get("embedding_model", {})
            provider = embed_config.get("provider", "local")
            model_name = embed_config.get("name", DEFAULT_EMBEDDING_MODEL)

            logger.info("=" * 50)
            logger.info(f"Embedding provider: {provider}")
            logger.info(f"Embedding model: {model_name}")
            logger.info("=" * 50)

            self._provider = provider
            self._model = model_name

        return self._model

    def encode(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        logger.info(f"[ENCODE] Encoding {len(texts)} texts...")

        if self._model is None:
            self.load_model()

        if self._provider == "google":
            return self._encode_google(texts, normalize)
        elif self._provider == "local":
            return self._encode_local(texts, normalize)
        else:
            # Default to local
            return self._encode_local(texts, normalize)

    def _encode_google(self, texts: list[str], normalize: bool) -> np.ndarray:
        """Encode texts using Google AI API. Falls back to local on quota errors."""
        import google.generativeai as genai

        model_name = self._model  # e.g., "gemini-embedding-001"
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        genai.configure(api_key=api_key)

        # Google AI embeddings API - model name must be "models/xxx"
        model_for_api = f"models/{model_name}" if not model_name.startswith("models/") else model_name

        logger.info(f"[GOOGLE AI] Using model: {model_for_api}")

        try:
            result = genai.embed_content(
                model=model_for_api,
                content=texts,
                task_type="SEMANTIC_SIMILARITY"
            )

            embeddings = np.array(result["embedding"], dtype=np.float32)
            logger.info(f"[GOOGLE AI] Encoded {len(texts)} texts, shape: {embeddings.shape}")

            if normalize:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            return embeddings

        except Exception as e:
            err_str = str(e).lower()
            if "resourcerestricted" in err_str or "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                logger.warning(f"[GOOGLE AI] Quota exceeded ({e}), falling back to local BGE-m3")
                return self._encode_local(texts, normalize)
            raise

    def _encode_local(self, texts: list[str], normalize: bool) -> np.ndarray:
        """Encode texts using local BGE-m3 model."""
        if not hasattr(self, '_local_model'):
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local BGE-m3 model...")
            self._local_model = SentenceTransformer("BAAI/bge-m3", device="cpu")
            self._local_model.to("cpu")
            logger.info("Local model loaded!")

        embeddings = self._local_model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        logger.info(f"[LOCAL] Encoded {len(texts)} texts, shape: {embeddings.shape}")
        return embeddings


# Singleton instance
embedder = Embedder()
