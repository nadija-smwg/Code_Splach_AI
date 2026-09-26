import logging
import math
import sys
import os

# Add ai_pipeline to sys.path so we can import OpenAIClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_pipeline.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class SemanticFallback:
    """
    Prevents false positives on string mismatches using OpenAI neural embeddings.
    """
    def __init__(self):
        self.client = OpenAIClient()
        if self.client._client is None:
            logger.warning("OPENAI_API_KEY not set. SemanticFallback will fallback to string matching.")

    def check_similarity(self, string_a: str, string_b: str, threshold: float = 0.85) -> bool:
        score = self.similarity_score(string_a, string_b)
        return score >= threshold

    def _fallback_jaccard(self, str_a: str, str_b: str) -> float:
        set_a = set(str_a.split())
        set_b = set(str_b.split())
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union

    def similarity_score(self, string_a: str, string_b: str) -> float:
        if not isinstance(string_a, str) or not isinstance(string_b, str):
            return 0.0

        str_a = string_a.lower().strip().replace(".", "")
        str_b = string_b.lower().strip().replace(".", "")

        if str_a == str_b:
            return 1.0

        if not self.client._client:
            return self._fallback_jaccard(str_a, str_b)

        emb_a = self.client.get_embedding(str_a)
        emb_b = self.client.get_embedding(str_b)

        if not emb_a or not emb_b:
            return self._fallback_jaccard(str_a, str_b)

        return cosine_similarity(emb_a, emb_b)
