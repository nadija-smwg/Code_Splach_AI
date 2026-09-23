# backend/reasoning/discrepancy_engine.py

class DiscrepancyEngine:
    """Converts knowledge graph conflicts into structured discrepancy records."""
    
    # A comprehensive, expert-backed tier list for ClearanceX
    ENTITY_SEVERITY_TIERS = {
        # 🔴 HIGH SEVERITY (Critical)
        "GROSS_WEIGHT": "high",
        "NET_WEIGHT": "high",
        "TOTAL_AMOUNT": "high",
        "HS_CODE": "high",              
        "INCOTERM": "high",             
        "CURRENCY_CODE": "high",        
        "COUNTRY_OF_ORIGIN": "high",    
        "WEIGHT_CONSISTENCY": "high",   
        "FINANCIAL_CONSISTENCY": "high",
        
        # 🟡 MEDIUM SEVERITY (Warning)
        "PACKAGE_COUNT": "medium",      
        "FREIGHT_AMOUNT": "medium",     
        "INSURANCE_AMOUNT": "medium",   
        "PORT_OF_LOADING": "medium",    
        "PORT_OF_DISCHARGE": "medium",  
        "VESSEL_NAME": "medium",        
        
        # ⚪ LOW SEVERITY (Info)
        "CONSIGNEE_NAME": "low",
        "SHIPPER_NAME": "low",
        "SHIPPING_MARKS": "low"         
    }
    
    def process(self, conflicts: list, shipment_id: str) -> list:
        """Convert graph conflicts into discrepancy records with tier-based severity."""
        discrepancies = []
        
        for i, conflict in enumerate(conflicts):
            entity_type = conflict["entity_type"]
            
            # 1. Assign severity purely based on the entity type (default to medium if unknown)
            severity = self.ENTITY_SEVERITY_TIERS.get(entity_type, "medium")
            
            # 2. Assign a simple numeric rank just so we can sort them later
            sort_weight = {"high": 3, "medium": 2, "low": 1}[severity]
            
            discrepancies.append({
                "discrepancy_id": f"disc_{shipment_id[:8]}_{i+1:03d}",
                "field": entity_type,
                "severity": severity,
                "sort_weight": sort_weight,
                
                # The bbox and page data are natively preserved inside this sources array!
                "sources": conflict["sources"],
                "conflict_type": conflict.get("conflict_type", "unknown"),
                
                # XAI layers will be added in subsequent phases:
                "reasoning_chain": None,    # Phase 06
                "confidence": None,         # Phase 07
                "counterfactual": None      # Phase 08
            })
        
        # 3. Sort by severity (highest rank first)
        discrepancies.sort(key=lambda d: d["sort_weight"], reverse=True)
        
        return discrepancies
