import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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


# ─────────────────────────────────────────────────────────────────────────────
# Helper to build a mock Cerebras chat completions response with given texts
# ─────────────────────────────────────────────────────────────────────────────
def _make_cerebras_response(texts: list[str]):
    """Return a ready-to-use mock chat completions response with valid JSON."""
    import json
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps({"texts": texts})
    mock_resp.choices[0].message.reasoning = None
    return mock_resp


class TestSampleEndpoint:
    """Tests for GET /api/sample endpoint."""

    def test_sample_default_count(self, client):
        """Test that default count=100 returns exactly 100 texts."""
        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_client = MagicMock()
            mock_cerebras_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = _make_cerebras_response(
                ["Sample text"] * 100
            )
            response = client.get("/api/sample")
        assert response.status_code == 200
        data = response.json()
        assert len(data["texts"]) == 100
        assert data["count"] == 100

    def test_sample_custom_count_500(self, client):
        """Test that count=500 returns 500 texts across multiple chunks."""
        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_client = MagicMock()
            mock_cerebras_cls.return_value = mock_client
            # Each chunk returns 100 texts; 500 texts = 5 chunks
            mock_client.chat.completions.create.side_effect = [
                _make_cerebras_response(["text"] * 100)
                for _ in range(5)
            ]
            response = client.get("/api/sample?count=500")
        assert response.status_code == 200
        data = response.json()
        assert len(data["texts"]) == 500
        assert data["count"] == 500

    def test_sample_max_count_10000(self, client):
        """Test that count=10000 is accepted and returns 10000 texts."""
        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_client = MagicMock()
            mock_cerebras_cls.return_value = mock_client
            # 100 chunks × 100 texts each = 10000
            mock_client.chat.completions.create.side_effect = [
                _make_cerebras_response(["text"] * 100)
                for _ in range(100)
            ]
            response = client.get("/api/sample?count=10000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["texts"]) == 10000
        assert data["count"] == 10000

    def test_sample_invalid_count_zero(self, client):
        """Test that count=0 returns 422."""
        response = client.get("/api/sample?count=0")
        assert response.status_code == 422

    def test_sample_invalid_count_too_large(self, client):
        """Test that count=10001 returns 422."""
        response = client.get("/api/sample?count=10001")
        assert response.status_code == 422

    def test_sample_api_error_returns_500(self, client):
        """Test that Cerebras failure returns 500."""
        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_cerebras_cls.return_value.chat.completions.create.side_effect = Exception("Network error")
            response = client.get("/api/sample")
        assert response.status_code == 500

    def test_sample_rate_limit_exhausted_returns_500(self, client):
        """Test that after 3 failed retries on RateLimitError, endpoint returns 500."""
        from cerebras.cloud.sdk import RateLimitError as CerebrasRateLimitError
        # Create a real subclass that only needs a message (not full httpx response)
        class MockRateLimitError(CerebrasRateLimitError):
            def __init__(self, message):
                self._message = message
                super().__init__(message=message, response=MagicMock(), body=None)
            def __str__(self):
                return self._message

        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_client = MagicMock()
            mock_cerebras_cls.return_value = mock_client
            # All 3 attempts fail with MockRateLimitError
            mock_client.chat.completions.create.side_effect = MockRateLimitError("rate limited")
            response = client.get("/api/sample?count=100")
        assert response.status_code == 500
        assert "Failed to generate texts" in response.json()["detail"]

    def test_sample_uses_reasoning_field_when_content_none(self, client):
        """Test JSON extraction from reasoning field when content is None."""
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = None
        mock_resp.choices[0].message.reasoning = '{"texts": ["From reasoning 1", "From reasoning 2", "From reasoning 3"]}'
        with patch('app.routes.cluster.Cerebras') as mock_cerebras_cls:
            mock_client = MagicMock()
            mock_cerebras_cls.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_resp
            response = client.get("/api/sample?count=3")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "From reasoning" in data["texts"][0]
