import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.namer import ClusterNamer


class TestClusterNamer:
    def setup_method(self):
        """Reset environment before each test."""
        self.env_backup = os.environ.get("CEREBRAS_API_KEY")

    def teardown_method(self):
        """Restore environment after each test."""
        if self.env_backup:
            os.environ["CEREBRAS_API_KEY"] = self.env_backup
        else:
            os.environ.pop("CEREBRAS_API_KEY", None)

    def test_namer_without_cerebras_key(self):
        """Test that namer uses fallback names when no CEREBRAS_API_KEY."""
        os.environ.pop("CEREBRAS_API_KEY", None)
        namer = ClusterNamer()

        assert not namer.is_available()

        cluster_texts = {0: ["text1", "text2"], 1: ["text3", "text4"]}
        names = namer.name_clusters(cluster_texts)

        assert names == {0: {"name": "Cluster 1", "description": None}, 1: {"name": "Cluster 2", "description": None}}

    def test_namer_with_cerebras_key(self):
        """Test that namer attempts to use Cerebras when key is present."""
        os.environ["CEREBRAS_API_KEY"] = "test-key"

        with patch('cerebras.cloud.sdk.Cerebras') as mock_cerebras:
            mock_client = MagicMock()
            mock_cerebras.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"1": {"name": "Database Issues", "description": "DB problems"}, "2": {"name": "Network Errors", "description": "Network issues"}}'
            mock_client.chat.completions.create.return_value = mock_response

            namer = ClusterNamer()
            assert namer.is_available()

    def test_name_clusters_fallback_on_parse_error(self):
        """Test fallback names when Cerebras response can't be parsed."""
        os.environ["CEREBRAS_API_KEY"] = "test-key"

        with patch('cerebras.cloud.sdk.Cerebras') as mock_cerebras:
            mock_client = MagicMock()
            mock_cerebras.return_value = mock_client

            # Return invalid JSON
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Not valid JSON"
            mock_client.chat.completions.create.return_value = mock_response

            namer = ClusterNamer()
            cluster_texts = {0: ["text1"], 1: ["text2"]}
            names = namer.name_clusters(cluster_texts)

            # Should fallback to generic names
            assert names == {0: {"name": "Cluster 1", "description": None}, 1: {"name": "Cluster 2", "description": None}}

    def test_name_clusters_fallback_on_exception(self):
        """Test fallback names when Cerebras API throws exception."""
        os.environ["CEREBRAS_API_KEY"] = "test-key"

        with patch('cerebras.cloud.sdk.Cerebras') as mock_cerebras:
            mock_cerebras.return_value.chat.completions.create.side_effect = Exception("API Error")

            namer = ClusterNamer()
            cluster_texts = {0: ["text1"]}
            names = namer.name_clusters(cluster_texts)

            # Should fallback to generic names
            assert names == {0: {"name": "Cluster 1", "description": None}}

    def test_name_clusters_reasoning_field_used_when_content_none(self):
        """Test that _extract_json_from_text handles nested JSON from Cerebras reasoning field."""
        from app.services.namer import _extract_json_from_text
        import json

        # Simulate what Cerebras returns when content is None — the reasoning field
        # contains nested JSON like: {"1": {"name": "...", "description": "..."}}
        reasoning_text = '{"1": {"name": "From Reasoning", "description": "Extracted from reasoning"}}'
        result = _extract_json_from_text(reasoning_text)
        assert result is not None, "Should extract JSON from reasoning text"
        data = json.loads(result)
        assert data["1"]["name"] == "From Reasoning"
        assert data["1"]["description"] == "Extracted from reasoning"
