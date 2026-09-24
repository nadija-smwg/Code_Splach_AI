import networkx as nx
from typing import List, Any
from dataclasses import dataclass
from backend.reasoning.semantic_fallback import SemanticFallback

@dataclass
class RuleFailure:
    rule_id: str
    description: str
    node_a_id: str
    node_b_id: str
    value_a: Any
    value_b: Any
    delta: str

class RuleEvaluator:
    """
    The Symbolic Logic engine. It evaluates the Knowledge Graph against 
    deterministic compliance rules.
    """
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.semantic_fallback = SemanticFallback()
        self.failures: List[RuleFailure] = []

    def evaluate(self) -> List[RuleFailure]:
        self.failures = []
        for u, v, data in self.graph.edges(data=True):
            relationship = data.get("relationship")
            
            if relationship == "MUST_MATCH":
                self._check_must_match(u, v)
                
        return self.failures

    def _check_must_match(self, node_a: str, node_b: str):
        data_a = self.graph.nodes[node_a]
        data_b = self.graph.nodes[node_b]
        
        val_a = data_a.get("value")
        val_b = data_b.get("value")
        
        if val_a is None or val_b is None:
            return
            
        # 1. Numeric constraint evaluation
        if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
            difference = abs(val_a - val_b)
            if difference > 0.01:
                self.failures.append(RuleFailure(
                    rule_id="RULE_001_NUMERIC_MATCH",
                    description=f"{data_a.get('entity_type', 'Value')} must match between documents.",
                    node_a_id=node_a,
                    node_b_id=node_b,
                    value_a=val_a,
                    value_b=val_b,
                    delta=f"Variance of {difference:.2f}"
                ))
                
        # 2. String constraint evaluation with Semantic Fallback
        elif isinstance(val_a, str) and isinstance(val_b, str):
            if not self.semantic_fallback.check_similarity(val_a, val_b):
                self.failures.append(RuleFailure(
                    rule_id="RULE_002_STRING_MATCH",
                    description=f"{data_a.get('entity_type', 'Text')} must match semantically.",
                    node_a_id=node_a,
                    node_b_id=node_b,
                    value_a=val_a,
                    value_b=val_b,
                    delta="Semantic mismatch detected"
                ))
