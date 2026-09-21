# Phase 04 — Knowledge Graph Construction (Layer 6)

> **Priority:** MUST
> **Estimated Time:** 3–4 hours
> **Dependencies:** Phase 01 (DB), extraction contract from Nadija (use mocks)
> **Blocks:** Phases 05, 06, 07, 08 (all depend on the graph)

---

## Goal

Build the knowledge graph that links entities across documents in a shipment. This is the **core data structure** for all reasoning, and Layer 6 XAI (the "wow moment" knowledge graph visualization).

## Why

The knowledge graph captures what no pairwise comparison can: **transitive relationships across multiple documents**. It's also the most visually impressive part of the demo — judges will see entities connected to documents, with conflicts glowing red.

## Implementation

### 4.1 Create `knowledge_graph.py`

```python
# backend/reasoning/knowledge_graph.py
import networkx as nx
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re


class ShipmentKnowledgeGraph:
    """
    Builds a knowledge graph from extracted entities across multiple documents.
    
    Structure:
    - Document nodes: represent each uploaded document
    - Entity nodes: represent canonical fields (GROSS_WEIGHT, CONSIGNEE_NAME, etc.)
    - Edges: connect documents to entities with the extracted value and confidence
    
    Conflicts appear when multiple documents connect to the same entity node
    with different values.
    """
    
    # Fields that should be compared across documents
    CROSS_DOCUMENT_FIELDS = [
        "GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT",
        "CONSIGNEE_NAME", "SHIPPER_NAME", "INCOTERM",
        "HS_CODE", "CURRENCY_CODE", "TOTAL_AMOUNT",
        "COUNTRY_OF_ORIGIN", "PORT_OF_LOADING", "PORT_OF_DISCHARGE",
        "SHIPPING_MARKS", "VESSEL_NAME", "FREIGHT_AMOUNT", "INSURANCE_AMOUNT"
    ]

    # Numeric fields (evaluated with mathematical percentage tolerance)
    # NOTE: HS_CODE is deliberately NOT here (must be treated as an exact string)
    NUMERIC_FIELDS = [
        "GROSS_WEIGHT", "NET_WEIGHT", "TARE_WEIGHT", 
        "PACKAGE_COUNT", "TOTAL_AMOUNT", "FREIGHT_AMOUNT", "INSURANCE_AMOUNT"
    ]

    # Document authority weights (0.0 to 1.0; higher = legal evidentiary truth)
    DOCUMENT_AUTHORITY = {
        "commercial_invoice": {
            "TOTAL_AMOUNT": 0.95,
            "CURRENCY_CODE": 0.95,
            "INCOTERM": 0.95,
            "CONSIGNEE_NAME": 0.90,
            "SHIPPER_NAME": 0.90,
            "HS_CODE": 0.90,
            "GOODS_DESCRIPTION": 0.95,
            "PORT_OF_LOADING": 0.80,
            "PORT_OF_DISCHARGE": 0.80,
            "PACKAGE_COUNT": 0.80,
            "GROSS_WEIGHT": 0.75,
        },
        "packing_list": {
            "GROSS_WEIGHT": 0.95,
            "NET_WEIGHT": 0.98,
            "TARE_WEIGHT": 0.98,
            "PACKAGE_COUNT": 0.95,
            "SHIPPING_MARKS": 0.95,
            "HS_CODE": 0.70,
            "CONSIGNEE_NAME": 0.80,
            "SHIPPER_NAME": 0.80,
        },
        "bl": {  # Bill of Lading (Sea Freight)
            "VESSEL_NAME": 0.98,
            "PORT_OF_LOADING": 0.95,
            "PORT_OF_DISCHARGE": 0.95,
            "BL_NUMBER": 0.99,
            "SHIPPING_MARKS": 0.90,
            "PACKAGE_COUNT": 0.90,
            "GROSS_WEIGHT": 0.85,
            "CONSIGNEE_NAME": 0.85,
            "SHIPPER_NAME": 0.85,
        },
        "awb": {  # Air Waybill (Air Freight)
            "FLIGHT_NUMBER": 0.98,
            "PORT_OF_LOADING": 0.95,
            "PORT_OF_DISCHARGE": 0.95,
            "AWB_NUMBER": 0.99,
            "PACKAGE_COUNT": 0.90,
            "GROSS_WEIGHT": 0.85,
            "CONSIGNEE_NAME": 0.85,
            "SHIPPER_NAME": 0.85,
        },
        "certificate_of_origin": {
            "COUNTRY_OF_ORIGIN": 0.99,
            "HS_CODE": 0.95,
            "INVOICE_NUMBER": 0.90,
            "SHIPPER_NAME": 0.90,
            "CONSIGNEE_NAME": 0.85,
            "GROSS_WEIGHT": 0.75,
        },
        "letter_of_credit": {
            "CURRENCY_CODE": 0.99,
            "TOTAL_AMOUNT": 0.95,
            "INCOTERM": 0.95,
            "CONSIGNEE_NAME": 0.95,
            "SHIPPER_NAME": 0.95,
            "PORT_OF_LOADING": 0.90,
            "PORT_OF_DISCHARGE": 0.90,
        },
        "freight_invoice": {
            "FREIGHT_AMOUNT": 0.99,
            "CURRENCY_CODE": 0.95,
            "INVOICE_NUMBER": 0.85,
        },
        "insurance_certificate": {
            "INSURANCE_AMOUNT": 0.99,
            "CURRENCY_CODE": 0.95,
            "VESSEL_NAME": 0.85,
        }
    }
    
    def __init__(self):
        self.graph = nx.Graph()
        self.documents = {}    # doc_id → document info
        self.entities = {}     # entity_type → list of (doc_id, value, confidence)
        self.conflicts = []    # detected conflicts
    
    def add_document(self, document_id: str, document_type: str, 
                     entities: List[Dict], filename: str = ""):
        """Add a document's entities to the knowledge graph."""
        
        # Add document node
        self.graph.add_node(document_id, 
                          node_type="document",
                          document_type=document_type,
                          label=filename or document_type,
                          color=self._doc_color(document_type))
        
        self.documents[document_id] = {
            "document_type": document_type,
            "filename": filename,
            "entity_count": len(entities)
        }
        
        # Add entity nodes and edges
        for entity in entities:
            entity_type = entity["entity_type"]
            value = entity.get("normalized_value", entity["value"])
            confidence = entity.get("extraction_confidence", 0.5)
            
            # Create entity node if it doesn't exist
            if entity_type not in [n for n, d in self.graph.nodes(data=True) 
                                    if d.get("node_type") == "entity"]:
                self.graph.add_node(entity_type,
                                   node_type="entity",
                                   label=self._entity_label(entity_type),
                                   status="pending",  # Will be updated after conflict detection
                                   color="#888888")
            
            # Add edge: document → entity
            self.graph.add_edge(document_id, entity_type,
                              value=str(value),
                              raw_value=entity["value"],
                              confidence=confidence,
                              page=entity.get("page", 1),
                              bbox=entity.get("bbox", []))
            
            # Track for conflict detection
            if entity_type not in self.entities:
                self.entities[entity_type] = []
            self.entities[entity_type].append({
                "document_id": document_id,
                "document_type": document_type,
                "value": value,
                "raw_value": entity["value"],
                "confidence": confidence,
                "page": entity.get("page", 1),
                "bbox": entity.get("bbox", [])
            })
    
    def detect_conflicts(self, numeric_tolerance: float = 0.005,
                         text_similarity_threshold: float = 0.90) -> List[Dict]:
        """
        Traverse the graph and find entities with conflicting values
        across documents.
        """
        self.conflicts = []
        
        for entity_type, sources in self.entities.items():
            if len(sources) < 2:
                continue  # Need at least 2 documents to compare
            
            if entity_type not in self.CROSS_DOCUMENT_FIELDS:
                continue  # Skip fields not meant for cross-document comparison
            
            if entity_type in self.NUMERIC_FIELDS:
                conflicts = self._check_numeric_conflict(entity_type, sources, numeric_tolerance)
            else:
                conflicts = self._check_text_conflict(entity_type, sources, text_similarity_threshold)
            
            self.conflicts.extend(conflicts)
        
        # Check internal consistency (e.g., PL: net + tare == gross)
        self._check_internal_consistency()
        
        # Update graph node colors based on conflict status
        self._update_node_status()
        
        # Calculate Truth Scores and generate recommendations
        self._generate_recommendations()
        
        return self.conflicts
    
    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """Safely extract and convert numeric values, ignoring units/text."""
        if isinstance(val, (float, int)):
            return float(val)
        if isinstance(val, str):
            val = val.replace(",", "")
            match = re.search(r"[-+]?\d*\.\d+|\d+", val)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    pass
        return None

    def _check_numeric_conflict(self, entity_type, sources, tolerance):
        """Compare numeric values across documents."""
        conflicts = []
        values = []
        for s in sources:
            val = self._safe_float(s.get("value"))
            if val is not None:
                values.append((s["document_id"], s["document_type"], val, s["confidence"]))
        
        # Compare all pairs
        has_conflict = False
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                doc_a, type_a, val_a, conf_a = values[i]
                doc_b, type_b, val_b, conf_b = values[j]
                
                if val_a == 0 and val_b == 0:
                    continue
                
                variance = abs(val_a - val_b) / max(val_a, val_b, 1)
                
                if variance > tolerance:
                    has_conflict = True
        
        if has_conflict:
            conflicts.append({
                "entity_type": entity_type,
                "sources": sources,
                "conflict_type": "numeric_variance"
            })
        
        return conflicts
    

    def _check_text_conflict(self, entity_type, sources, threshold):
        """Compare text values across documents using fuzzy matching."""
        conflicts = []
        
        current_threshold = threshold
        if entity_type == "HS_CODE":
            current_threshold = 1.0  # Must be a 100% exact match
            
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                val_a = str(sources[i]["value"]).lower().strip()
                val_b = str(sources[j]["value"]).lower().strip()
                
                similarity = SequenceMatcher(None, val_a, val_b).ratio()
                
                if similarity < current_threshold:
                    conflicts.append({
                        "entity_type": entity_type,
                        "sources": [sources[i], sources[j]],
                        "conflict_type": "text_mismatch",
                        "similarity": round(similarity, 3),
                        "detail": "CRITICAL: HS Codes must match exactly." if entity_type == "HS_CODE" else None
                    })
        
        return conflicts


    
    def _check_internal_consistency(self):
        """Check within-document consistency (e.g., net + tare = gross)."""
        for doc_id, doc_info in self.documents.items():
            doc_entities = {e["entity_type"]: e for sources in self.entities.values() 
                          for e in sources if e["document_id"] == doc_id}
            
            # Weight consistency: net + tare should equal gross
            if all(k in doc_entities for k in ["GROSS_WEIGHT", "NET_WEIGHT", "TARE_WEIGHT"]):
                gross = self._safe_float(doc_entities["GROSS_WEIGHT"].get("value"))
                net = self._safe_float(doc_entities["NET_WEIGHT"].get("value"))
                tare = self._safe_float(doc_entities["TARE_WEIGHT"].get("value"))
                
                if gross is not None and net is not None and tare is not None:
                    if abs((net + tare) - gross) > 0.5:  # More than 0.5kg discrepancy
                        self.conflicts.append({
                            "entity_type": "WEIGHT_CONSISTENCY",
                            "sources": [doc_entities["GROSS_WEIGHT"], doc_entities["NET_WEIGHT"], doc_entities["TARE_WEIGHT"]],
                            "conflict_type": "internal_inconsistency",
                            "detail": f"net({net}) + tare({tare}) = {net + tare} ≠ gross({gross})",
                            "document_id": doc_id
                        })
            
            # CIF Financial Consistency
            if all(k in doc_entities for k in ["TOTAL_AMOUNT", "FREIGHT_AMOUNT", "INSURANCE_AMOUNT"]):
                total_val = self._safe_float(doc_entities["TOTAL_AMOUNT"].get("value"))
                freight = self._safe_float(doc_entities["FREIGHT_AMOUNT"].get("value"))
                ins = self._safe_float(doc_entities["INSURANCE_AMOUNT"].get("value"))
                
                # Check the Incoterm to know how to do the math
                incoterm = ""
                if "INCOTERM" in doc_entities:
                    incoterm = str(doc_entities["INCOTERM"].get("value")).upper()
                
                if total_val is not None and freight is not None and ins is not None:
                    if "FOB" in incoterm or "EXW" in incoterm:
                        calculated_cif = total_val + freight + ins
                    elif "CIF" in incoterm or "CIP" in incoterm:
                        calculated_cif = total_val # Total already is CIF
                    else:
                        continue # Unhandled incoterm, skip math to be safe
                    
                    if "CIF_TOTAL" in doc_entities:
                        cif_total = self._safe_float(doc_entities["CIF_TOTAL"].get("value"))
                        if cif_total is not None and abs(calculated_cif - cif_total) > 1.0:
                            self.conflicts.append({
                                "entity_type": "FINANCIAL_CONSISTENCY",
                                "sources": [doc_entities["TOTAL_AMOUNT"], doc_entities["FREIGHT_AMOUNT"], doc_entities["INSURANCE_AMOUNT"]],
                                "conflict_type": "internal_inconsistency",
                                "detail": f"Calculated CIF({calculated_cif}) ≠ Declared CIF({cif_total}) based on {incoterm} terms.",
                                "document_id": doc_id
                            })
    
    def _generate_recommendations(self):
        """
        Evaluate conflicts and calculate a 'Truth Score' based on legal document 
        authority and AI extraction confidence to provide a recommendation.
        """
        for conflict in self.conflicts:
            entity_type = conflict.get("entity_type")
            sources = conflict.get("sources", [])
            
            # For mathematical inconsistencies, suggest manual review
            if conflict.get("conflict_type") == "internal_inconsistency":
                conflict["recommendation"] = {
                    "suggested_value": None,
                    "reasoning": "Mathematical consistency check failed. Please verify the physical documents or cargo to resolve this discrepancy."
                }
                continue

            # For text or numeric conflicts, evaluate competing sources
            value_scores = {}
            
            for source in sources:
                doc_type = source.get("document_type", "unknown")
                raw_val = source.get("value")
                
                # Fetch base authority. Default to 0.5 if not found in dictionary.
                doc_authority = self.DOCUMENT_AUTHORITY.get(doc_type, {}).get(entity_type, 0.5)
                ai_confidence = source.get("confidence", 0.5)
                
                # Truth Score calculation
                truth_score = doc_authority * ai_confidence
                
                group_key = str(raw_val).lower().strip()
                
                if group_key not in value_scores:
                    value_scores[group_key] = {
                        "score": 0.0, 
                        "supporting_docs": [],
                        "raw_val": raw_val
                    }
                
                value_scores[group_key]["score"] += truth_score
                
                # Format document name nicely
                doc_name = doc_type.replace("_", " ").title()
                if doc_type == "awb": doc_name = "AWB"
                elif doc_type == "bl": doc_name = "Bill of Lading"
                
                value_scores[group_key]["supporting_docs"].append(doc_name)

            if not value_scores:
                continue

            # Pick the value with the highest cumulative Truth Score
            best_group = max(value_scores.values(), key=lambda x: x["score"])
            winning_value = best_group["raw_val"]
            winning_docs = best_group["supporting_docs"]
            
            # Construct reasoning explanation
            if len(winning_docs) == 1:
                reasoning = f"We recommend '{winning_value}' because the {winning_docs[0]} has the highest legal authority and extraction confidence for {self._entity_label(entity_type)}."
            else:
                reasoning = f"We recommend '{winning_value}' because it is supported by the highest combined authority from ({', '.join(winning_docs)})."
                
            conflict["recommendation"] = {
                "suggested_value": winning_value,
                "reasoning": reasoning
            }

    def _update_node_status(self):
        """Update entity node colors based on conflict status."""
        conflicted_entities = set()
        for c in self.conflicts:
            # If it's a standard conflict, grab the entity type
            if c["entity_type"] in self.CROSS_DOCUMENT_FIELDS:
                conflicted_entities.add(c["entity_type"])
            # If it's a math consistency error, grab the entity types from the sources
            for source in c.get("sources", []):
                conflicted_entities.add(source["entity_type"])
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "entity":
                if node_id in conflicted_entities:
                    self.graph.nodes[node_id]["status"] = "conflict"
                    self.graph.nodes[node_id]["color"] = "#FF6B6B"  # Red
                else:
                    self.graph.nodes[node_id]["status"] = "match"
                    self.graph.nodes[node_id]["color"] = "#50C878"  # Green
    
    def _doc_color(self, doc_type):
        colors = {
            "commercial_invoice": "#4A90D9",
            "packing_list": "#50C878",
            "awb": "#FFB347",
            "bl": "#DDA0DD",
            "delivery_order": "#87CEEB",
            "freight_invoice": "#F0E68C",
            "letter_of_credit": "#CD853F",
            "certificate_of_origin": "#F4A460",
            "insurance_certificate": "#98FB98"
        }
        return colors.get(doc_type, "#CCCCCC")
    
    def _entity_label(self, entity_type):
        labels = {
            "GROSS_WEIGHT": "Gross Weight",
            "NET_WEIGHT": "Net Weight",
            "TARE_WEIGHT": "Tare Weight",
            "PACKAGE_COUNT": "Package Count",
            "CONSIGNEE_NAME": "Consignee",
            "SHIPPER_NAME": "Shipper",
            "INCOTERM": "Incoterm",
            "INVOICE_NUMBER": "Invoice #",
            "AWB_NUMBER": "AWB #",
            "BL_NUMBER": "B/L #",
            "TOTAL_AMOUNT": "Total Amount",
            "VESSEL_NAME": "Vessel",
            "HS_CODE": "HS Code",
            "CURRENCY_CODE": "Currency",
            "COUNTRY_OF_ORIGIN": "Origin",
            "PORT_OF_LOADING": "POL",
            "PORT_OF_DISCHARGE": "POD",
            "SHIPPING_MARKS": "Shipping Marks",
            "FREIGHT_AMOUNT": "Freight",
            "INSURANCE_AMOUNT": "Insurance",
            "FLIGHT_NUMBER": "Flight #",
            "GOODS_DESCRIPTION": "Description"
        }
        return labels.get(entity_type, entity_type.replace("_", " ").title())
    
    def to_vis_json(self) -> Dict:
        """Serialize graph for vis.js frontend visualization."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node = {
                "id": node_id,
                "label": data.get("label", node_id),
                "type": data.get("node_type", "unknown"),
                "color": data.get("color", "#CCCCCC"),
            }
            if data.get("node_type") == "entity":
                node["status"] = data.get("status", "pending")
            if data.get("node_type") == "document":
                node["document_type"] = data.get("document_type", "unknown")
            nodes.append(node)
        
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": str(data.get("value", "")),
                "confidence": data.get("confidence", 0),
            })
        
        return {"nodes": nodes, "edges": edges}
```

## Acceptance Criteria

- [ ] Graph builds from extraction results (real or mock)
- [ ] Document nodes and entity nodes are distinct types
- [ ] Conflicts detected for numeric variances > 0.5%
- [ ] Conflicts detected for text mismatches < 90% similarity
- [ ] Internal consistency check works (net + tare vs gross)
- [ ] `to_vis_json()` returns format compatible with vis.js
- [ ] Entity nodes turn red for conflicts, green for matches

## Outputs

- `backend/reasoning/knowledge_graph.py`
- Graph data ready for Kaveen's vis.js visualization
