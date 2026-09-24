import networkx as nx
from typing import Dict, List
from backend.xai_types import (
    XAIBlock, XAILayer1_Provenance, XAILayer2_ReasoningChain,
    XAILayer3_Confidence, XAILayer4_Counterfactual
)
from backend.reasoning.rule_evaluator import RuleFailure

class XAICompiler:
    """
    Translates deterministic rule failures into the 4-layer XAI payload.
    """
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def compile(self, failure: RuleFailure) -> XAIBlock:
        node_a = self.graph.nodes[failure.node_a_id]
        node_b = self.graph.nodes[failure.node_b_id]

        # Layer 1: Provenance
        layer1 = XAILayer1_Provenance(
            source_documents=[node_a.get("source_doc", ""), node_b.get("source_doc", "")],
            ocr_snippets=[node_a.get("ocr_text", ""), node_b.get("ocr_text", "")],
            bboxes=[node_a.get("bbox", []), node_b.get("bbox", [])]
        )

        # Layer 2: Reasoning Chain
        steps = [
            f"Extracted {node_a.get('entity_type')} from {node_a.get('source_doc')}: {failure.value_a}",
            f"Extracted {node_b.get('entity_type')} from {node_b.get('source_doc')}: {failure.value_b}",
            f"Evaluated constraint: {failure.description}",
            f"Constraint failed with delta: {failure.delta}"
        ]
        layer2 = XAILayer2_ReasoningChain(
            failed_rule_id=failure.rule_id,
            failed_rule_description=failure.description,
            logical_steps=steps,
            conclusion="Discrepancy detected between source documents."
        )

        # Layer 3: Confidence
        conf_a = node_a.get("extraction_confidence", 1.0)
        conf_b = node_b.get("extraction_confidence", 1.0)
        overall_conf = float(conf_a * conf_b) # Joint probability

        level = "high"
        if overall_conf < 0.7: level = "low"
        elif overall_conf < 0.9: level = "medium"

        layer3 = XAILayer3_Confidence(
            ocr_confidence=0.95, # Mock value for OCR confidence
            extraction_confidence=overall_conf,
            semantic_match_confidence=1.0 if "NUMERIC" in failure.rule_id else 0.0,
            overall_confidence=overall_conf,
            confidence_explanation=f"Calculated by multiplying extraction confidences: {conf_a:.2f} * {conf_b:.2f}",
            confidence_level=level
        )

        # Layer 4: Counterfactual
        recommendation = f"Update {node_b.get('source_doc')} to match {node_a.get('source_doc')}, or vice-versa."
        if isinstance(failure.value_a, (int, float)):
            recommendation = f"Adjust value in {node_b.get('source_doc')} by {failure.value_a - failure.value_b} to resolve."
            
        layer4 = XAILayer4_Counterfactual(
            recommended_action=recommendation,
            delta_required=failure.delta
        )

        return XAIBlock(
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=layer4
        )
