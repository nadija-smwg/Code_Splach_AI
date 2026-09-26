"""NetworkX construction for canonical shipment-field knowledge graphs."""
from typing import Any, Dict
import networkx as nx


class KnowledgeBuilder:
    """Builds a provenance-preserving graph from resolved shipment fields."""

    def __init__(self):
        self.graph = nx.Graph()

    def add_shipment_node(self, shipment_id: str) -> None:
        self.graph.add_node(shipment_id, node_type="shipment", label="Shipment Dossier")

    def add_document_node(self, document_id: str, document_type: str, filename: str = "") -> None:
        self.graph.add_node(document_id, node_type="document", document_type=document_type, label=filename or document_type.replace("_", " ").title())

    def add_canonical_field_node(self, field: dict[str, Any], shipment_id: str) -> None:
        field_id = field["canonical_field_id"]
        self.graph.add_node(field_id,
                            node_type="canonical_field", entity_type=field["entity_type"],
                            value=field["consensus_value"], consensus_value=field["consensus_value"],
                            unit=field.get("unit"), status=field["status"],
                            resolution_confidence=field.get("resolution_confidence", 0.0),
                            label=field["label"])
        self.graph.add_edge(shipment_id, field_id, relationship="HAS_FIELD")

    def add_source_assertion_node(self, assertion: dict[str, Any]) -> None:
        assertion_id = assertion["assertion_id"]
        self.graph.add_node(assertion_id,
                            node_type="source_assertion", entity_type=assertion["entity_type"],
                            value=assertion["normalized_value"], raw_value=assertion["raw_value"],
                            source_doc=assertion["document_id"], bbox=assertion.get("bbox", []),
                            source_doc_label=assertion["document_label"], source_doc_type=assertion["document_type"],
                            page=assertion.get("page", 1), extraction_confidence=assertion.get("extraction_confidence", 0.0),
                            ocr_text=assertion.get("ocr_text", ""), is_outlier=assertion.get("is_outlier", False),
                            label=f"{assertion['document_label']}: {assertion['raw_value']}")
        self.graph.add_edge(assertion["document_id"], assertion_id, relationship="CONTAINS")
        self.graph.add_edge(assertion_id, assertion["canonical_field_id"], relationship="ASSERTS_VALUE_FOR")

    # Retained for standalone legacy tests.
    def add_entity_node(self, node_id: str, entity: Any, source_doc_id: str) -> None:
        self.graph.add_node(node_id, node_type="source_assertion", entity_type=entity.entity_type,
                            value=entity.normalized_value or entity.value, raw_value=entity.value,
                            source_doc=source_doc_id, bbox=entity.bbox,
                            extraction_confidence=entity.extraction_confidence, ocr_text=entity.ocr_text,
                            label=f"{entity.entity_type} ({entity.value})")
        self.graph.add_edge(source_doc_id, node_id, relationship="CONTAINS")

    def add_relationship(self, node_a_id: str, node_b_id: str, relationship_type: str) -> None:
        self.graph.add_edge(node_a_id, node_b_id, relationship=relationship_type)

    def get_graph(self) -> nx.Graph:
        return self.graph

    def to_vis_json(self) -> Dict:
        styles = {
            "shipment": ({"background": "#312e81", "border": "#818cf8"}, "diamond", 24),
            "document": ({"background": "#1d4ed8", "border": "#60a5fa"}, "box", 20),
            "canonical_field": ({"background": "#7e22ce", "border": "#c084fc"}, "hexagon", 18),
            "source_assertion": ({"background": "#10b981", "border": "#34d399"}, "dot", 12),
        }
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "source_assertion")
            color, shape, size = styles.get(node_type, styles["source_assertion"])
            status = data.get("status", "conflict" if data.get("is_outlier") else "match")
            if status == "conflict" or data.get("is_outlier"):
                color = {"background": "#dc2626", "border": "#fca5a5"}
            elif status == "warning":
                color = {"background": "#d97706", "border": "#fcd34d"}
            nodes.append({"id": node_id, "label": data.get("label", node_id), "type": node_type,
                          "color": color, "shape": shape, "size": size, "status": status,
                          "document_type": data.get("document_type"), "shadow": True,
                          "font": {"color": "#e2e8f0"}})

        edge_styles = {"HAS_FIELD": ("#818cf8", 2), "CONTAINS": ("#64748b", 1),
                       "ASSERTS_VALUE_FOR": ("#c084fc", 2), "MUST_MATCH": ("#f59e0b", 2)}
        edges = []
        for source, target, data in self.graph.edges(data=True):
            relationship = data.get("relationship", "")
            color, width = edge_styles.get(relationship, ("#64748b", 1))
            edges.append({"from": source, "to": target, "label": relationship,
                          "confidence": 1.0, "width": width, "color": {"color": color},
                          "font": {"color": "#94a3b8", "size": 10}})
        return {"nodes": nodes, "edges": edges}
