import os
import re
import json
from cerebras.cloud.sdk import Cerebras
import logging
from typing import Optional


logger = logging.getLogger("cluster_namer")


def _extract_json_from_text(text: str) -> str | None:
    """Extract JSON object from text by finding {"texts": or last {...} block."""
    # Try to find ```json ... ``` code block first (greedy to capture outermost braces)
    json_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', text)
    if json_match:
        return json_match.group(1)
    # Try to find {"texts": ...} pattern
    texts_marker = re.search(r'["\']texts["\']\s*:\s*\[', text)
    if texts_marker:
        search_start = max(0, texts_marker.start() - 200)
        search_region = text[search_start:texts_marker.end()]
        brace_pos = -1
        for i, c in enumerate(search_region):
            if c == '{':
                brace_pos = i
        if brace_pos >= 0:
            start = search_start + brace_pos
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
    # Last resort: find the FIRST { that eventually closes at depth 0.
    # This captures the outermost JSON object even when inner objects share the same line.
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
        self.cerebras_client = None
        api_key = os.getenv("CEREBRAS_API_KEY")
        if api_key:
            self.cerebras_client = Cerebras(api_key=api_key)
            logger.info("Cerebras client initialized for cluster naming")
        else:
            logger.warning("Cerebras client not initialized - CEREBRAS_API_KEY not set")

    def is_available(self) -> bool:
        return self.cerebras_client is not None

    def name_clusters(self, cluster_texts: dict[int, list[str]]) -> dict[int, dict[str, str]]:
        """Generate names and descriptions for all clusters using Cerebras."""
        logger.info(f"[NAMER] Starting cluster naming process for {len(cluster_texts)} clusters")

        if not self.is_available():
            logger.warning("[NAMER] Cerebras not available - using generic cluster names")
            return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}

        try:
            # Build a single prompt for all clusters
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

            logger.info(f"[NAMER] Sending request to Cerebras API for {len(cluster_texts)} clusters")
            logger.debug(f"[NAMER] Prompt preview: {full_prompt[:500]}...")

            response = self.cerebras_client.chat.completions.create(
                model="gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that names clusters. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=8192
            )

            raw_content = response.choices[0].message.content
            # Cerebras reasoning models put content in 'reasoning' field when content is None
            if raw_content is None:
                reasoning = response.choices[0].message.reasoning
                logger.info(f"[NAMER] Using reasoning field content ({len(reasoning) if reasoning else 0} chars)")
                if reasoning:
                    raw_content = _extract_json_from_text(reasoning)
                    logger.info(f"[NAMER] Extracted JSON: {len(raw_content) if raw_content else 0} chars")

            if raw_content is None:
                logger.error(f"[NAMER] Cerebras returned None content. Full response: {response}")
                return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}

            result_text = raw_content.strip()
            logger.info(f"[NAMER] Received response from Cerebras ({len(result_text)} chars)")
            logger.debug(f"[NAMER] Raw response: {result_text[:1000]}")

            # Try to parse JSON from response
            try:
                names = json.loads(result_text)
                logger.info(f"[NAMER] Successfully parsed JSON with {len(names)} cluster names")
                # Convert string keys to int and ensure all clusters have names + descriptions
                result = {}
                for k, v in names.items():
                    cluster_id = int(k) - 1
                    if isinstance(v, dict):
                        result[cluster_id] = {
                            "name": v.get("name", f"Cluster {cluster_id + 1}"),
                            "description": v.get("description")
                        }
                        logger.debug(f"[NAMER] Cluster {cluster_id}: name='{result[cluster_id]['name']}', description='{result[cluster_id]['description']}'")
                    else:
                        # Handle case where LLM returns just a string
                        result[cluster_id] = {"name": v, "description": None}
                        logger.warning(f"[NAMER] Cluster {cluster_id} returned string instead of object, using as name only")
                logger.info(f"[NAMER] Final naming result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"[NAMER] JSON parse error: {e}")
                logger.debug(f"[NAMER] Failed response was: {result_text[:500]}")
                return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}

        except Exception as e:
            logger.error(f"[NAMER] Cerebras naming failed: {type(e).__name__}: {e}")
            return {i: {"name": f"Cluster {i+1}", "description": None} for i in cluster_texts.keys()}


# Singleton instance
namer = ClusterNamer()
