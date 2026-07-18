from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import os


logger = logging.getLogger("embedder")


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
            model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
            logger.info("=" * 50)
            logger.info(f"LOADING EMBEDDING MODEL ({model_name})...")
            logger.info("=" * 50)

            # Check for cached model
            cache_dir = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
            logger.info(f"HuggingFace cache dir: {cache_dir}")
            if os.path.exists(cache_dir):
                logger.info(f"Cache contents: {os.listdir(cache_dir)[:10]}...")

            try:
                logger.info("Creating SentenceTransformer instance...")
                self._model = SentenceTransformer(model_name, device="cpu")
                logger.info("SentenceTransformer created, now loading model...")
                logger.info("Calling model.to() if needed...")
                self._model.to("cpu")
                logger.info("=" * 50)
                logger.info("EMBEDDING MODEL LOADED SUCCESSFULLY!")
                logger.info("=" * 50)
            except Exception as e:
                logger.error(f"FAILED to load embedding model: {type(e).__name__}: {e}")
                logger.error(f"Model load error traceback:", exc_info=True)
                raise
        return self._model

    def encode(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        logger.info(f"[ENCODE] Starting to encode {len(texts)} texts...")
        logger.info(f"[ENCODE] Calling load_model()...")
        model = self.load_model()
        logger.info(f"[ENCODE] Model loaded, calling model.encode()...")
        embeddings = model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=True  # Enable progress bar to see encoding progress
        )
        logger.info(f"[ENCODE] Encoded {len(texts)} texts, embedding shape: {embeddings.shape}")
        return embeddings


# Singleton instance
embedder = Embedder()
