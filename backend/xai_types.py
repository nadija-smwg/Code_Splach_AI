from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# ==========================================
# 1. Pipeline Extraction Types
# ==========================================

@dataclass
class ExtractedEntity:
    """Represents a single field extracted from a document by the LLM."""
    entity_type: str            # e.g., "GROSS_WEIGHT", "CONSIGNEE_NAME"
    value: str                  # The raw string found in the text
    normalized_value: Any       # The canonical format (e.g., float 450.0)
    unit: Optional[str]         # e.g., "KG", "USD"
    page: int                   # Page number where it was found
    bbox: List[int]             # [x1, y1, x2, y2] bounding box from OCR
    extraction_confidence: float # 0.0 to 1.0 confidence from the LLM
    ocr_text: str = ""          # The original OCR text snippet that contained this value

# ==========================================
# 2. XAI Layer Types
# ==========================================

@dataclass
class XAILayer1_Provenance:
    """Layer 1: Source Evidence. Points directly to the raw data."""
    source_documents: List[str] = field(default_factory=list)
    ocr_snippets: List[str] = field(default_factory=list)
    bboxes: List[List[int]] = field(default_factory=list)

@dataclass
class XAILayer2_ReasoningChain:
    """Layer 2: Deductive Proof. The step-by-step logical failure."""
    failed_rule_id: str = ""
    failed_rule_description: str = ""
    logical_steps: List[str] = field(default_factory=list)
    conclusion: str = ""

@dataclass
class XAILayer3_Confidence:
    """Layer 3: Uncertainty Quantification."""
    ocr_confidence: float = 0.0
    extraction_confidence: float = 0.0
    semantic_match_confidence: float = 0.0
    overall_confidence: float = 0.0
    confidence_explanation: str = ""
    confidence_level: str = "high"  # high, medium, low

@dataclass
class XAILayer4_Counterfactual:
    """Layer 4: Actionability. How to fix the discrepancy."""
    recommended_action: str = ""
    delta_required: str = ""

@dataclass
class XAIBlock:
    """The complete 4-layer payload sent to the frontend."""
    layer1: XAILayer1_Provenance = field(default_factory=XAILayer1_Provenance)
    layer2: XAILayer2_ReasoningChain = field(default_factory=XAILayer2_ReasoningChain)
    layer3: XAILayer3_Confidence = field(default_factory=XAILayer3_Confidence)
    layer4: XAILayer4_Counterfactual = field(default_factory=XAILayer4_Counterfactual)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer1": self.layer1.__dict__,
            "layer2": self.layer2.__dict__,
            "layer3": self.layer3.__dict__,
            "layer4": self.layer4.__dict__
        }
