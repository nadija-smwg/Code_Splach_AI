import networkx as nx
from typing import Dict
from backend.xai_types import ExtractedEntity

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
            node = {
                "id": node_id,
                "label": data.get("label", node_id),
                "type": data.get("node_type", "unknown"),
            }
            nodes.append(node)
        
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": data.get("relationship", ""),
            })
        
        return {"nodes": nodes, "edges": edges}
