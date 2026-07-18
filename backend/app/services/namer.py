import os
import json
import groq
import logging
from typing import Optional


logger = logging.getLogger("cluster_namer")


class ClusterNamer:
    def __init__(self):
        self.groq_client = None
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client = groq.Groq(api_key=api_key)
            logger.info("GROQ client initialized for cluster naming")
        else:
            logger.warning("GROQ client not initialized - GROQ_API_KEY not set")

    def is_available(self) -> bool:
        return self.groq_client is not None

    def name_clusters(self, cluster_texts: dict[int, list[str]]) -> dict[int, str]:
        """Generate names for all clusters using GROQ."""
        if not self.is_available():
            logger.warning("GROQ not available, using generic cluster names")
            return {i: f"Cluster {i+1}" for i in cluster_texts.keys()}

        try:
            # Build a single prompt for all clusters
            prompt_parts = []
            for cluster_id, texts in cluster_texts.items():
                texts_sample = "\n".join(f"- {t[:100]}" for t in texts[:5])
                prompt_parts.append(f"Cluster {cluster_id + 1}:\n{texts_sample}")
            clusters_prompt = "\n\n".join(prompt_parts)

            full_prompt = f"""For each cluster, provide a short descriptive name (2-4 words) that captures the common theme.

{clusters_prompt}

Respond with a JSON object mapping cluster numbers to names, e.g.:
{{"1": "Database Issues", "2": "Network Errors", ...}}

JSON:"""

            logger.info(f"Calling Groq to name {len(cluster_texts)} clusters...")
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
                max_tokens=256
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"Groq naming response received, parsing...")

            # Try to parse JSON from response
            try:
                names = json.loads(result_text)
                # Convert string keys to int and ensure all clusters have names
                result = {int(k) - 1: v for k, v in names.items()}
                logger.info(f"Successfully named clusters: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error in naming: {e}")
                return {i: f"Cluster {i+1}" for i in cluster_texts.keys()}

        except Exception as e:
            logger.error(f"GROQ naming failed: {e}")
            return {i: f"Cluster {i+1}" for i in cluster_texts.keys()}


# Singleton instance
namer = ClusterNamer()
