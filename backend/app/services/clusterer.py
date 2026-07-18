import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler
import umap.umap_ as umap
from collections import Counter
import logging
import hdbscan


logger = logging.getLogger("clusterer")


class Clusterer:
    def __init__(self, k_min: int = 5, k_max: int = 15):
        self.k_min = k_min
        self.k_max = k_max

    def choose_optimal_k(self, embeddings: np.ndarray) -> tuple[int, float]:
        """Find optimal K using silhouette score."""
        logger.info(f"Finding optimal K between {self.k_min} and {self.k_max}...")
        best_k = self.k_min
        best_score = -1.0

        for k in range(self.k_min, self.k_max + 1):
            km = KMeans(n_clusters=k, random_state=42, n_init="auto")
            labels = km.fit_predict(embeddings)

            if len(set(labels)) == 1:
                continue

            score = silhouette_score(embeddings, labels, metric="euclidean")
            if score > best_score:
                best_score = score
                best_k = k

        logger.info(f"Optimal K={best_k} with silhouette score={best_score:.4f}")
        return best_k, best_score

    def cluster_with_hdbscan(self, embeddings: np.ndarray, min_cluster_size: int = None):
        """Perform HDBSCAN clustering for automatic cluster detection and UMAP projection.

        HDBSCAN automatically detects outliers (label -1) which are treated as noise.
        """
        min_cs = min_cluster_size if min_cluster_size is not None else 5
        logger.info(f"Running HDBSCAN with min_cluster_size={min_cs}...")

        # Embeddings are normalized before clustering, so Euclidean distance preserves
        # cosine similarity ordering while staying compatible with this HDBSCAN build.
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cs, metric="euclidean")
        labels = clusterer.fit_predict(embeddings)

        # Count valid clusters (excluding noise label -1)
        unique_labels = set(labels)
        n_clusters = len([l for l in unique_labels if l != -1])

        # Count noise points
        n_noise = sum(1 for l in labels if l == -1)
        logger.info(f"HDBSCAN found {n_clusters} clusters and {n_noise} noise points")

        # Compute silhouette score only on non-noise points
        valid_mask = labels != -1
        n_valid = valid_mask.sum()

        if n_valid < 2 or n_clusters < 2:
            # Not enough valid clusters for silhouette score
            silhouette = None
            logger.warning("HDBSCAN produced fewer than 2 valid clusters, cannot compute silhouette score")
        else:
            valid_embeddings = embeddings[valid_mask]
            valid_labels = labels[valid_mask]
            try:
                silhouette = silhouette_score(valid_embeddings, valid_labels, metric='cosine')
                logger.info(f"HDBSCAN silhouette score (non-noise points): {silhouette:.4f}")
            except Exception as e:
                logger.warning(f"Could not compute silhouette score: {e}")
                silhouette = None

        # Calculate confidence based on cluster membership probability (hdbscan.probabilities_)
        # Higher probability = more confident assignment to cluster
        # Noise points get 0 confidence
        confidence = clusterer.probabilities_

        # For noise points (label -1), set confidence to 0
        confidence = np.array([c if l != -1 else 0.0 for l, c in zip(labels, confidence)])

        logger.info("Running UMAP for 2D projection...")
        # UMAP for 2D projection
        reducer = umap.UMAP(n_components=2, metric="cosine", random_state=42)
        points_2d = reducer.fit_transform(embeddings)
        logger.info("UMAP projection complete")

        # Normalize points to [0, 1] for better visualization
        scaler = MinMaxScaler()
        points_2d = scaler.fit_transform(points_2d)

        # Count cluster sizes (excluding noise)
        cluster_sizes = Counter([l for l in labels if l != -1])
        logger.info(f"HDBSCAN clustering complete: {n_clusters} clusters with sizes {dict(cluster_sizes)}")

        return {
            "labels": labels,
            "points_2d": points_2d,
            "confidence": confidence,
            "n_clusters": n_clusters,
            "silhouette": silhouette,
            "cluster_sizes": cluster_sizes
        }

    def cluster(self, embeddings: np.ndarray, n_clusters: int = None, method: str = "kmeans", min_cluster_size: int = None):
        """Perform clustering and UMAP projection.

        Args:
            embeddings: Input embedding vectors
            n_clusters: Number of clusters for K-Means (ignored for HDBSCAN)
            method: "kmeans" for manual K selection or "hdbscan" for automatic detection
            min_cluster_size: Minimum cluster size for HDBSCAN (only used when method="hdbscan")
        """
        if method == "hdbscan":
            logger.info("Using HDBSCAN auto-detect clustering method")
            return self.cluster_with_hdbscan(embeddings, min_cluster_size)

        # K-Means path
        if n_clusters is None:
            n_clusters, silhouette = self.choose_optimal_k(embeddings)
        else:
            silhouette = None
            logger.info(f"Using specified K={n_clusters}")

        logger.info(f"Running K-Means with K={n_clusters}...")
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(embeddings)
        centers = kmeans.cluster_centers_
        logger.info("K-Means clustering complete")

        # Calculate confidence (inverse distance to center)
        distances = np.linalg.norm(embeddings - centers[labels], axis=1)
        # Normalize to [0, 1]
        if distances.max() - distances.min() > 1e-12:
            confidence = 1.0 - (distances - distances.min()) / (distances.max() - distances.min())
        else:
            confidence = np.ones_like(distances)

        logger.info("Running UMAP for 2D projection...")
        # UMAP for 2D projection
        reducer = umap.UMAP(n_components=2, metric="cosine", random_state=42)
        points_2d = reducer.fit_transform(embeddings)
        logger.info("UMAP projection complete")

        # Normalize points to [0, 1] for better visualization
        scaler = MinMaxScaler()
        points_2d = scaler.fit_transform(points_2d)

        cluster_sizes = Counter(labels)
        logger.info(f"Clustering complete: {n_clusters} clusters with sizes {dict(cluster_sizes)}")

        return {
            "labels": labels,
            "points_2d": points_2d,
            "confidence": confidence,
            "n_clusters": n_clusters,
            "silhouette": silhouette,
            "cluster_sizes": cluster_sizes
        }
