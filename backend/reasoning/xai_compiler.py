import networkx as nx
from typing import Dict, List
from xai_types import (
    XAIBlock, XAILayer1_Provenance, XAILayer2_ReasoningChain,
    XAILayer3_Confidence, XAILayer4_Counterfactual
)
from reasoning.rule_evaluator import RuleFailure


class XAICompiler:
    """
    Translates deterministic rule failures into the 4-layer XAI payload.
    """
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def compile(self, failure: RuleFailure) -> XAIBlock:
        node_a = self.graph.nodes[failure.node_a_id]
        node_b = self.graph.nodes[failure.node_b_id]

        # ── Layer 1: Provenance ───────────────────────────────────────────
        layer1 = XAILayer1_Provenance(
            source_documents=[node_a.get("source_doc", ""), node_b.get("source_doc", "")],
            ocr_snippets=[node_a.get("ocr_text", ""), node_b.get("ocr_text", "")],
            bboxes=[node_a.get("bbox", []), node_b.get("bbox", [])]
        )

        # ── Layer 2: Reasoning Chain ──────────────────────────────────────
        steps = [
            f"Extracted {node_a.get('entity_type')} from '{node_a.get('source_doc')}': {failure.value_a}",
            f"Extracted {node_b.get('entity_type')} from '{node_b.get('source_doc')}': {failure.value_b}",
            f"Applied constraint: {failure.description}",
            f"Constraint failed — {failure.delta}",
        ]
        layer2 = XAILayer2_ReasoningChain(
            failed_rule_id=failure.rule_id,
            failed_rule_description=failure.description,
            logical_steps=steps,
            conclusion="Discrepancy detected between source documents."
        )

        # ── Layer 3: Confidence ───────────────────────────────────────────
        conf_a = float(node_a.get("extraction_confidence", 1.0))
        conf_b = float(node_b.get("extraction_confidence", 1.0))
        # Use mean OCR confidence as a proxy (extraction_confidence embeds OCR quality)
        ocr_conf = round((conf_a + conf_b) / 2, 4)
        overall_conf = round(conf_a * conf_b, 4)  # Joint probability

        level = "high"
        if overall_conf < 0.7:
            level = "low"
        elif overall_conf < 0.9:
            level = "medium"

        layer3 = XAILayer3_Confidence(
            ocr_confidence=ocr_conf,
            extraction_confidence=overall_conf,
            semantic_match_confidence=round(failure.semantic_score, 4),
            overall_confidence=overall_conf,
            confidence_explanation=(
                f"Joint extraction confidence: {conf_a:.2f} × {conf_b:.2f} = {overall_conf:.4f}. "
                f"Semantic similarity score: {failure.semantic_score:.4f}."
            ),
            confidence_level=level
        )

        # ── Layer 4: Counterfactual ───────────────────────────────────────
        if isinstance(failure.value_a, (int, float)) and isinstance(failure.value_b, (int, float)):
            delta_val = round(float(failure.value_a) - float(failure.value_b), 4)
            recommendation = (
                f"Adjust GROSS_WEIGHT in '{node_b.get('source_doc')}' by "
                f"{delta_val:+.2f} to match '{node_a.get('source_doc')}', "
                f"or verify the physical measurement and update the source of truth."
            )
            delta_str = f"{delta_val:+.4f}"
        else:
            recommendation = (
                f"Reconcile {node_a.get('entity_type')} between "
                f"'{node_a.get('source_doc')}' and '{node_b.get('source_doc')}'. "
                f"Verify the original document and update the discrepant value."
            )
            delta_str = failure.delta

        layer4 = XAILayer4_Counterfactual(
            recommended_action=recommendation,
            delta_required=delta_str,
        )

        return XAIBlock(
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=layer4,
        )
