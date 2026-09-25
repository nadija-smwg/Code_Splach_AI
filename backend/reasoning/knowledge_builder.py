import networkx as nx
from typing import Dict
from xai_types import ExtractedEntity

class KnowledgeBuilder:
    """
    Builds a knowledge graph from normalized entities.
    Strictly handles graph construction and XAI Provenance (Layer 1) storage.
    Conflict detection is handled separately by the Rule Evaluator.
    """
    
    def __init__(self):
        self.graph = nx.Graph()
    
    def add_document_node(self, document_id: str, document_type: str, filename: str = ""):
        """Add a source document node."""
        self.graph.add_node(document_id, 
                          node_type="document",
                          document_type=document_type,
                          label=filename or document_type)
                          
    def add_entity_node(self, node_id: str, entity: ExtractedEntity, source_doc_id: str):
        """
        Add an entity node. 
        Crucial XAI Step: Stores provenance metadata directly in the node.
        """
        self.graph.add_node(node_id,
                            node_type="entity",
                            entity_type=entity.entity_type,
                            value=entity.normalized_value or entity.value,
                            raw_value=entity.value,
                            source_doc=source_doc_id,
                            bbox=entity.bbox,
                            extraction_confidence=entity.extraction_confidence,
                            ocr_text=entity.ocr_text,
                            label=f"{entity.entity_type} ({entity.value})")
                            
        # Link entity to its source document
        self.graph.add_edge(source_doc_id, node_id, relationship="EXTRACTED_FROM")
        
    def add_relationship(self, node_a_id: str, node_b_id: str, relationship_type: str):
        """
        Add logical relationships between nodes (e.g., MUST_MATCH).
        """
        self.graph.add_edge(node_a_id, node_b_id, relationship=relationship_type)
        
    def get_graph(self) -> nx.Graph:
        return self.graph
        
    def to_vis_json(self) -> Dict:
        """Serialize graph for vis.js frontend visualization."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")

            # Determine color and shape based on node type and status
            if node_type == "document":
                color = {"background": "#4A90D9", "border": "#2563eb"}
                shape = "box"
                size = 20
            else:
                # Entity node — colour by presence in MUST_MATCH edges
                neighbors = list(self.graph.neighbors(node_id))
                in_conflict = any(
                    self.graph.edges[node_id, nb].get("relationship") == "MUST_MATCH"
                    for nb in neighbors
                    if self.graph.has_edge(node_id, nb)
                )
                color = {"background": "#f59e0b", "border": "#d97706"} if in_conflict else {"background": "#10b981", "border": "#059669"}
                shape = "dot"
                size = 12

            node = {
                "id": node_id,
                "label": data.get("label", node_id),
                "type": node_type,
                "color": color,
                "shape": shape,
                "size": size,
                "document_type": data.get("document_type"),
                "status": "conflict" if node_type == "entity" and in_conflict else "pending",  # type: ignore[possibly-undefined]
                "shadow": True,
                "font": {"color": "#e2e8f0"},
            }
            nodes.append(node)

        edges = []
        for u, v, data in self.graph.edges(data=True):
            relationship = data.get("relationship", "")
            # Confidence proxy: MUST_MATCH edges carry 1.0; EXTRACTED_FROM carry 0.9
            confidence = 0.9 if relationship == "EXTRACTED_FROM" else 1.0
            edges.append({
                "from": u,
                "to": v,
                "label": relationship,
                "confidence": confidence,
                "width": 2 if relationship == "MUST_MATCH" else 1,
                "color": {"color": "#f59e0b"} if relationship == "MUST_MATCH" else {"color": "#64748b"},
                "font": {"color": "#94a3b8", "size": 10},
            })

        return {"nodes": nodes, "edges": edges}
