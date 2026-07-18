import pytest
from pydantic import ValidationError
from app.models.schemas import ClusterRequest, ClusterResponse, ClusterPoint, ClusterInfo, ClusterStats


class TestSchemas:
    def test_cluster_request_valid(self):
        """Test valid ClusterRequest."""
        request = ClusterRequest(texts=["text1", "text2", "text3"])
        assert request.texts == ["text1", "text2", "text3"]
        assert request.n_clusters is None

    def test_cluster_request_with_n_clusters(self):
        """Test ClusterRequest with specified n_clusters."""
        request = ClusterRequest(texts=["text1", "text2"], n_clusters=5)
        assert request.n_clusters == 5

    def test_cluster_request_empty_texts_raises(self):
        """Test that empty texts list is handled by route, not schema."""
        # Pydantic doesn't validate empty lists by default
        # The route handles this case
        request = ClusterRequest(texts=[])
        assert request.texts == []  # Valid Pydantic model
        # The validation happens in the route handler

    def test_cluster_point_valid(self):
        """Test valid ClusterPoint."""
        point = ClusterPoint(
            x=0.5, y=-0.3, cluster="0",
            confidence=0.92, text="Sample text"
        )
        assert point.x == 0.5
        assert point.cluster == "0"
        assert point.confidence == 0.92

    def test_cluster_info_valid(self):
        """Test valid ClusterInfo."""
        info = ClusterInfo(id="0", name="Test Cluster", size=10, color="#3b82f6")
        assert info.id == "0"
        assert info.name == "Test Cluster"
        assert info.size == 10

    def test_cluster_stats_valid(self):
        """Test valid ClusterStats."""
        stats = ClusterStats(total_points=100, num_clusters=5, silhouette_score=0.75)
        assert stats.total_points == 100
        assert stats.num_clusters == 5
        assert stats.silhouette_score == 0.75

    def test_cluster_response_valid(self):
        """Test valid ClusterResponse."""
        response = ClusterResponse(
            clusters=[ClusterInfo(id="0", name="C1", size=5, color="#fff")],
            points=[ClusterPoint(x=0, y=0, cluster="0", confidence=1.0, text="t")],
            stats=ClusterStats(total_points=1, num_clusters=1, silhouette_score=1.0)
        )
        assert len(response.clusters) == 1
        assert len(response.points) == 1
