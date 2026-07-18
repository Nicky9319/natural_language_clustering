import pytest
import numpy as np
from app.services.clusterer import Clusterer


class TestClusterer:
    def setup_method(self):
        self.clusterer = Clusterer(k_min=2, k_max=5)

    def test_choose_optimal_k_returns_within_range(self):
        """Test that choose_optimal_k returns K within the specified range."""
        # Create synthetic data with 3 obvious clusters
        np.random.seed(42)
        embeddings = np.vstack([
            np.random.randn(20, 10) + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            np.random.randn(20, 10) + [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            np.random.randn(20, 10) + [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        ])

        k, score = self.clusterer.choose_optimal_k(embeddings)

        assert self.clusterer.k_min <= k <= self.clusterer.k_max
        assert -1.0 <= score <= 1.0

    def test_cluster_returns_expected_keys(self):
        """Test that cluster returns all expected keys."""
        embeddings = np.random.randn(30, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=3)

        expected_keys = ['labels', 'points_2d', 'confidence', 'n_clusters', 'silhouette', 'cluster_sizes']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_cluster_labels_count_matches_input(self):
        """Test that number of labels matches number of input embeddings."""
        embeddings = np.random.randn(50, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=3)

        assert len(result['labels']) == 50
        assert len(result['points_2d']) == 50
        assert len(result['confidence']) == 50

    def test_cluster_points_2d_shape(self):
        """Test that UMAP produces 2D points."""
        embeddings = np.random.randn(20, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=2)

        assert result['points_2d'].shape == (20, 2)

    def test_cluster_confidence_in_01(self):
        """Test that confidence values are in [0, 1] range."""
        embeddings = np.random.randn(20, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=2)

        assert np.all(result['confidence'] >= 0)
        assert np.all(result['confidence'] <= 1)

    def test_cluster_sizes_sum_to_n(self):
        """Test that cluster sizes sum to total number of points."""
        embeddings = np.random.randn(40, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=4)

        total = sum(result['cluster_sizes'].values())
        assert total == 40

    def test_cluster_with_single_text(self):
        """Test that clustering handles single text gracefully."""
        embeddings = np.random.randn(1, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=1)

        assert result['n_clusters'] == 1
        assert len(result['labels']) == 1

    def test_points_2d_normalized(self):
        """Test that points_2d are normalized to [0, 1] range."""
        embeddings = np.random.randn(30, 10)
        result = self.clusterer.cluster(embeddings, n_clusters=3)

        points = result['points_2d']
        assert np.all(points >= 0)
        assert np.all(points <= 1)
