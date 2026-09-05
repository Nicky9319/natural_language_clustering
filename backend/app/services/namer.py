import os
import re
import json
import logging
from typing import Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


logger = logging.getLogger("cluster_namer")

# Default config
DEFAULT_LLM_MODEL = "gemini-2.0-flash"
DEFAULT_LLM_FALLBACK = "gemini-1.5-flash"


def _load_config() -> dict:
    """Load config from config.json if present."""
    # namer.py is at /app/app/services/namer.py
    # config.json is at /app/config.json (three levels up)
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[NAMER] Failed to load config.json: {e}")
    return {}


def _extract_json_from_text(text: str) -> str | None:
    """Extract JSON object from text by finding ```json ... ``` or last {...} block."""
    json_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', text)
    if json_match:
        return json_match.group(1)
    for i, c in enumerate(text):
        if c == '{':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        return text[i:j+1]
    return None


class ClusterNamer:
    def __init__(self):
        self.client = None
        self.model_name = None

        # Load config
        config = _load_config()
        llm_config = config.get("llm_model", {})
        self.model_name = llm_config.get("name", DEFAULT_LLM_MODEL)
        fallback = llm_config.get("fallback_name", DEFAULT_LLM_FALLBACK)
        temperature = llm_config.get("temperature", 0.3)
        max_tokens = llm_config.get("max_tokens", 2048)

        # Try to initialize Google AI
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Fallback to Cerebras if no Google API key
            api_key = os.getenv("CEREBRAS_API_KEY")
            provider = "cerebras"
        else:
            provider = "google"

        if api_key and GENAI_AVAILABLE:
            if provider == "google":
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.model_name)
                self._provider = "google"
                logger.info(f"[NAMER] Google AI client initialized with model: {self.model_name}")
            else:
                # Fallback to Cerebras
                try:
                    from cerebras.cloud.sdk import Cerebras
                    self.client = Cerebras(api_key=api_key)
                    self.model_name = "gpt-oss-120b"
                    self._provider = "cerebras"
                    logger.info("[NAMER] Google AI not configured, using Cerebras fallback")
                except ImportError:
                    logger.warning("[NAMER] Cerebras SDK not installed")
                    self._provider = None
        else:
            if not api_key:
                logger.warning("[NAMER] No LLM API key set (GOOGLE_API_KEY or CEREBRAS_API_KEY)")
            if not GENAI_AVAILABLE:
                logger.warning("[NAMER] Google AI SDK (google-generativeai) not installed")
            self._provider = None

    def is_available(self) -> bool:
        return self.client is not None

    def name_clusters(self, cluster_texts: dict[int, list[str]]) -> dict[int, dict[str, str]]:
        """Generate names and descriptions for all clusters using LLM."""
        logger.info(f"[NAMER] Starting cluster naming process for {len(cluster_texts)} clusters (provider: {self._provider})")

        if not self.is_available():
            logger.warning("[NAMER] No LLM available - using generic cluster names")
            return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}

        try:
            prompt_parts = []
            for cluster_id, texts in cluster_texts.items():
                texts_sample = "\n".join(f"- {t[:100]}" for t in texts[:5])
                prompt_parts.append(f"Cluster {cluster_id + 1}:\n{texts_sample}")
            clusters_prompt = "\n\n".join(prompt_parts)

            full_prompt = f"""For each cluster, provide a short descriptive name (2-4 words) and a brief description (1-2 sentences) that captures the common theme.

{clusters_prompt}

Respond with a JSON object mapping cluster numbers to an object with "name" and "description" fields, e.g.:
{{"1": {{"name": "Database Issues", "description": "Problems related to database connectivity, queries, and performance"}}, "2": {{"name": "Network Errors", "description": "Issues involving network connectivity and communication"}}, ...}}

JSON:"""

            logger.info(f"[NAMER] Sending request to {self._provider.upper()} API ({self.model_name}) for {len(cluster_texts)} clusters")

            if self._provider == "google":
                response = self.client.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 2048,
                    }
                )
                result_text = response.text.strip()
            else:
                # Cerebras fallback
                from cerebras.cloud.sdk import Cerebras, RateLimitError as CerebrasRateLimitError
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that names clusters. Respond ONLY with valid JSON."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=8192
                )
                raw_content = response.choices[0].message.content
                if raw_content is None:
                    reasoning = response.choices[0].message.reasoning
                    if reasoning:
                        raw_content = _extract_json_from_text(reasoning)
                result_text = (raw_content or "").strip()

            logger.info(f"[NAMER] Received response from {self._provider.upper()} ({len(result_text)} chars)")

            # Parse JSON from response
            try:
                # Try to extract JSON if wrapped in markdown
                json_text = _extract_json_from_text(result_text) or result_text
                names = json.loads(json_text)
                logger.info(f"[NAMER] Successfully parsed JSON with {len(names)} cluster names")

                result = {}
                for k, v in names.items():
                    cluster_id = int(k) - 1
                    if isinstance(v, dict):
                        result[cluster_id] = {
                            "name": v.get("name", f"Cluster {cluster_id + 1}"),
                            "description": v.get("description")
                        }
                    else:
                        result[cluster_id] = {"name": str(v), "description": None}
                logger.info(f"[NAMER] Final naming result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"[NAMER] JSON parse error: {e}")
                return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}

        except Exception as e:
            logger.error(f"[NAMER] Naming failed ({self._provider}): {type(e).__name__}: {e}")
            return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}


# Singleton instance
namer = ClusterNamer()
