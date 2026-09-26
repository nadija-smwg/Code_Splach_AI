"""Evaluate canonical-field assertions rather than pairwise document edges."""
from dataclasses import dataclass, field
from typing import Any, List
import networkx as nx
from reasoning.semantic_fallback import SemanticFallback


@dataclass
class RuleFailure:
    rule_id: str
    description: str
    node_a_id: str                 # representative consensus assertion
    node_b_id: str                 # outlying assertion
    value_a: Any
    value_b: Any
    delta: str
    semantic_score: float = field(default=0.0)
    canonical_field_id: str = ""
    entity_type: str = ""


class RuleEvaluator:
    """Evaluates all source assertions attached to a canonical field."""

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.semantic_fallback = SemanticFallback()
        self.failures: List[RuleFailure] = []

    def evaluate(self) -> List[RuleFailure]:
        self.failures = []
        canonical_nodes = [node_id for node_id, data in self.graph.nodes(data=True)
                           if data.get("node_type") == "canonical_field"]
        if canonical_nodes:
            for field_id in canonical_nodes:
                self._evaluate_field(field_id)
        else:
            # Compatibility for the legacy test graph.
            for left, right, data in self.graph.edges(data=True):
                if data.get("relationship") == "MUST_MATCH":
                    self._evaluate_pair(left, right)
        return self.failures

    def _evaluate_field(self, field_id: str) -> None:
        field = self.graph.nodes[field_id]
        assertions = [node for node in self.graph.neighbors(field_id)
                      if self.graph.nodes[node].get("node_type") == "source_assertion"]
        if len(assertions) < 2 or field.get("status") != "conflict":
            return
        consensus_value = field.get("consensus_value")
        consensus_nodes = [node for node in assertions
                           if not self.graph.nodes[node].get("is_outlier")]
        if not consensus_nodes:
            return
        representative = consensus_nodes[0]
        for outlier in (node for node in assertions if self.graph.nodes[node].get("is_outlier")):
            self._create_failure(representative, outlier, field_id, consensus_value)

    def _evaluate_pair(self, left: str, right: str) -> None:
        self._create_failure(left, right, "", self.graph.nodes[left].get("value"))

    def _create_failure(self, left: str, right: str, field_id: str, consensus_value: Any) -> None:
        first, second = self.graph.nodes[left], self.graph.nodes[right]
        left_value, right_value = first.get("value"), second.get("value")
        entity_type = first.get("entity_type", "Value")
        if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
            difference = abs(float(left_value) - float(right_value))
            if difference <= 0.01:
                return
            self.failures.append(RuleFailure(
                rule_id="RULE_001_NUMERIC_MATCH", entity_type=entity_type,
                canonical_field_id=field_id,
                description=f"{entity_type.replace('_', ' ').title()} differs from the resolved shipment consensus.",
                node_a_id=left, node_b_id=right, value_a=left_value, value_b=right_value,
                delta=f"Variance of {difference:.2f}", semantic_score=1.0,
            ))
        elif isinstance(left_value, str) and isinstance(right_value, str):
            score = self.semantic_fallback.similarity_score(left_value, right_value)
            if score >= 0.85:
                return
            self.failures.append(RuleFailure(
                rule_id="RULE_002_STRING_MATCH", entity_type=entity_type,
                canonical_field_id=field_id,
                description=f"{entity_type.replace('_', ' ').title()} differs from the resolved shipment consensus.",
                node_a_id=left, node_b_id=right, value_a=left_value, value_b=right_value,
                delta="Semantic mismatch detected", semantic_score=score,
            ))
