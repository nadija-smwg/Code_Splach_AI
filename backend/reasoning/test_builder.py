from backend.reasoning.knowledge_builder import KnowledgeBuilder
from backend.xai_types import ExtractedEntity

def test():
    kb = KnowledgeBuilder()
    
    # Mock Document
    kb.add_document_node("doc_1", "commercial_invoice", "invoice.pdf")
    
    # Mock Entity
    ent = ExtractedEntity(
        entity_type="GROSS_WEIGHT",
        value="450.0",
        normalized_value=450.0,
        unit="KG",
        page=1,
        bbox=[10, 20, 30, 40],
        extraction_confidence=0.95,
        ocr_text="Total Gross Weight: 450.0 KG"
    )
    
    kb.add_entity_node("node_1", ent, "doc_1")
    
    # Mock second entity to test relationship
    ent2 = ExtractedEntity(
        entity_type="GROSS_WEIGHT",
        value="450",
        normalized_value=450.0,
        unit="KG",
        page=1,
        bbox=[100, 200, 300, 400],
        extraction_confidence=0.98,
        ocr_text="450 KGs"
    )
    kb.add_document_node("doc_2", "awb", "airwaybill.pdf")
    kb.add_entity_node("node_2", ent2, "doc_2")
    
    # Add MUST_MATCH relationship
    kb.add_relationship("node_1", "node_2", "MUST_MATCH")
    
    print("Graph built successfully.")
    print("Nodes:", kb.get_graph().nodes(data=True))
    print("Edges:", kb.get_graph().edges(data=True))
    print("Vis.js output:", kb.to_vis_json())

if __name__ == "__main__":
    test()
