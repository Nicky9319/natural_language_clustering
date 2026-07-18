import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.namer import ClusterNamer


class TestClusterNamer:
    def setup_method(self):
        """Reset environment before each test."""
        self.env_backup = os.environ.get("GROQ_API_KEY")

    def teardown_method(self):
        """Restore environment after each test."""
        if self.env_backup:
            os.environ["GROQ_API_KEY"] = self.env_backup
        else:
            os.environ.pop("GROQ_API_KEY", None)

    def test_namer_without_groq_key(self):
        """Test that namer uses fallback names when no GROQ_API_KEY."""
        os.environ.pop("GROQ_API_KEY", None)
        namer = ClusterNamer()

        assert not namer.is_available()

        cluster_texts = {0: ["text1", "text2"], 1: ["text3", "text4"]}
        names = namer.name_clusters(cluster_texts)

        assert names == {0: "Cluster 1", 1: "Cluster 2"}

    def test_namer_with_groq_key(self):
        """Test that namer attempts to use GROQ when key is present."""
        os.environ["GROQ_API_KEY"] = "test-key"

        with patch('groq.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"1": "Database Issues", "2": "Network Errors"}'
            mock_client.chat.completions.create.return_value = mock_response

            namer = ClusterNamer()
            assert namer.is_available()

    def test_name_clusters_fallback_on_parse_error(self):
        """Test fallback names when GROQ response can't be parsed."""
        os.environ["GROQ_API_KEY"] = "test-key"

        with patch('groq.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_groq.return_value = mock_client

            # Return invalid JSON
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Not valid JSON"
            mock_client.chat.completions.create.return_value = mock_response

            namer = ClusterNamer()
            cluster_texts = {0: ["text1"], 1: ["text2"]}
            names = namer.name_clusters(cluster_texts)

            # Should fallback to generic names
            assert names == {0: "Cluster 1", 1: "Cluster 2"}

    def test_name_clusters_fallback_on_exception(self):
        """Test fallback names when GROQ API throws exception."""
        os.environ["GROQ_API_KEY"] = "test-key"

        with patch('groq.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.side_effect = Exception("API Error")

            namer = ClusterNamer()
            cluster_texts = {0: ["text1"]}
            names = namer.name_clusters(cluster_texts)

            # Should fallback to generic names
            assert names == {0: "Cluster 1"}
