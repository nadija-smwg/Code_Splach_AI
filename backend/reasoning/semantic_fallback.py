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
        """
        Simulates cosine similarity. 
        Returns True if the strings are semantically identical.
        """
        if not isinstance(string_a, str) or not isinstance(string_b, str):
            return False
            
        str_a = string_a.lower().strip()
        str_b = string_b.lower().strip()
        
        if str_a == str_b:
            return True
            
        str_a = str_a.replace(".", "")
        str_b = str_b.replace(".", "")
        
        abbreviations = {
            "corp": "corporation",
            "inc": "incorporated",
            "ltd": "limited",
            "co": "company"
        }
        
        # Calculate similarity
        set_a = set(abbreviations.get(w, w) for w in str_a.split())
        set_b = set(abbreviations.get(w, w) for w in str_b.split())
        
        if not set_a or not set_b:
            return False
            
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        
        return (intersection / union) >= threshold
