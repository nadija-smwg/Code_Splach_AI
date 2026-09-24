import networkx as nx
from backend.xai_types import ExtractedEntity
from backend.reasoning.knowledge_builder import KnowledgeBuilder
from backend.reasoning.rule_evaluator import RuleEvaluator

def test():
    kb = KnowledgeBuilder()
    kb.add_document_node("doc_1", "commercial_invoice")
    kb.add_document_node("doc_2", "awb")
    
    # 1. Test Numeric Match Failure
    ent1 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="450.0", normalized_value=450.0, unit="KG", page=1, bbox=[0,0,0,0], extraction_confidence=0.9)
    ent2 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="500.0", normalized_value=500.0, unit="KG", page=1, bbox=[0,0,0,0], extraction_confidence=0.9)
    kb.add_entity_node("node_1", ent1, "doc_1")
    kb.add_entity_node("node_2", ent2, "doc_2")
    kb.add_relationship("node_1", "node_2", "MUST_MATCH")
    
    # 2. Test Semantic String Match Success (Should not fail!)
    ent3 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="Acme Corp.", normalized_value="Acme Corp.", unit=None, page=1, bbox=[0,0,0,0], extraction_confidence=0.9)
    ent4 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="Acme Corporation", normalized_value="Acme Corporation", unit=None, page=1, bbox=[0,0,0,0], extraction_confidence=0.9)
    kb.add_entity_node("node_3", ent3, "doc_1")
    kb.add_entity_node("node_4", ent4, "doc_2")
    kb.add_relationship("node_3", "node_4", "MUST_MATCH")
    
    # Evaluate
    evaluator = RuleEvaluator(kb.get_graph())
    failures = evaluator.evaluate()
    
    print(f"Detected {len(failures)} rule failures.")
    for f in failures:
        print(f"- [{f.rule_id}] {f.description} (Delta: {f.delta})")

if __name__ == "__main__":
    test()
