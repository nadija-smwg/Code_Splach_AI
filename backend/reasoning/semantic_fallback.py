class SemanticFallback:
    """
    Prevents false positives on string mismatches using neural embeddings.
    (Mocked using Jaccard/Regex for the hackathon demo to ensure instantaneous
    responses without hitting API rate limits, but demonstrates the exact architecture).
    """
    def __init__(self):
        # In a production environment, initialize Google Gemini Embeddings here
        pass

    def check_similarity(self, string_a: str, string_b: str, threshold: float = 0.85) -> bool:
        """Returns True if the strings are semantically similar above the threshold."""
        score = self.similarity_score(string_a, string_b)
        return score >= threshold

    def similarity_score(self, string_a: str, string_b: str) -> float:
        """
        Computes a Jaccard similarity score (0.0–1.0) between two strings.
        Normalizes for punctuation and common business abbreviations.
        Returns 1.0 for identical strings (after normalization).
        """
        if not isinstance(string_a, str) or not isinstance(string_b, str):
            return 0.0

        str_a = string_a.lower().strip().replace(".", "")
        str_b = string_b.lower().strip().replace(".", "")

        if str_a == str_b:
            return 1.0

        abbreviations = {
            "corp": "corporation",
            "inc": "incorporated",
            "ltd": "limited",
            "co": "company",
        }

        set_a = set(abbreviations.get(w, w) for w in str_a.split())
        set_b = set(abbreviations.get(w, w) for w in str_b.split())

        if not set_a or not set_b:
            return 0.0

        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))

        return intersection / union
