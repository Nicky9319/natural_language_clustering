import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestClusterEndpoint:
    def test_cluster_empty_texts(self, client):
        """Test clustering with empty texts list."""
        response = client.post("/api/cluster", json={"texts": []})
        assert response.status_code == 400
        assert "No texts provided" in response.json()["detail"]

    def test_cluster_single_text(self, client):
        """Test clustering with single text (needs at least 4)."""
        response = client.post("/api/cluster", json={"texts": ["single text"]})
        assert response.status_code == 400
        assert "at least 4 texts" in response.json()["detail"]

    def test_cluster_valid_texts(self, client):
        """Test clustering with enough texts for valid UMAP (min 4)."""
        response = client.post(
            "/api/cluster",
            json={"texts": ["error connecting to server", "database timeout issue", "login problem here", "payment failed"], "n_clusters": 2}
        )
        assert response.status_code == 200
        data = response.json()

        # With 4 texts and K=2, should create 2 clusters
        assert "clusters" in data
        assert "points" in data
        assert "stats" in data

    def test_cluster_response_structure(self, client):
        """Test that cluster response has correct structure."""
        response = client.post(
            "/api/cluster",
            json={"texts": ["text a", "text b", "text c", "text d", "text e", "text f"], "n_clusters": 2}
        )
        assert response.status_code == 200
        data = response.json()

        # Check stats structure
        stats = data["stats"]
        assert stats["total_points"] == 6
        assert "num_clusters" in stats
        assert "silhouette_score" in stats

        # Check points structure
        assert len(data["points"]) == 6
        point = data["points"][0]
        assert all(k in point for k in ["x", "y", "cluster", "confidence", "text"])

        # Check clusters structure
        assert len(data["clusters"]) == 2
        cluster = data["clusters"][0]
        assert all(k in cluster for k in ["id", "name", "size", "color"])

    def test_cluster_with_explicit_k(self, client):
        """Test clustering with explicit number of clusters."""
        response = client.post(
            "/api/cluster",
            json={"texts": ["a", "b", "c", "d", "e", "f"], "n_clusters": 2}
        )
        assert response.status_code == 200
        data = response.json()
        # With 6 points and K=2, should get 2 clusters
        assert data["stats"]["num_clusters"] == 2

    def test_cluster_texts_not_list(self, client):
        """Test that texts must be a list."""
        response = client.post(
            "/api/cluster",
            json={"texts": "single string instead of list"}
        )
        assert response.status_code == 422  # Validation error
