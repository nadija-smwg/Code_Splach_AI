# backend/ai_pipeline/entity_extractor.py
"""
Phase 06 -- Header Entity Extraction
=====================================
Hybrid approach (Option C, decided in Phase 05):
  Step 1  PaddleOCR      -> text + bounding boxes  (Phase 03, done)
  Step 2  Gemini Vision  -> entity names + values
  Step 3  map_to_bbox()  -> link Gemini values back to OCR tokens
  Result  entities with  value, page, bbox, extraction_confidence

Extraction Responsibility Boundary
-----------------------------------
  THIS FILE  : populates entity["value"]  (raw string, exactly as OCR saw it)
  normalizer : populates entity["normalized_value"] and entity["unit"]
  Do NOT normalise, convert units, or clean values here.

Aloka's knowledge graph cross-doc conflict detection relies on:
  CROSS_DOCUMENT_FIELDS = [GROSS_WEIGHT, NET_WEIGHT, PACKAGE_COUNT,
                           CONSIGNEE_NAME, SHIPPER_NAME, INCOTERM]
These 6 fields are the primary conflict triggers -- accuracy is critical.

Author: Nadija (Phase 06)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from ai_pipeline.ocr_engine import OcrOutput, OcrToken
from ai_pipeline.classifier import ClassificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output contract dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExtractedEntity:
    """
    One extracted entity from a document.
    value            <- Phase 06 fills this (raw string exactly as OCR/Gemini saw it)
    normalized_value <- Phase 09 normalizer fills this
    unit             <- Phase 09 normalizer fills this
    """
    entity_type: str
    value: str
    page: int
    bbox: list                          # [x1, y1, x2, y2]
    extraction_confidence: float
    normalized_value: object = None     # filled by Phase 09
    unit: Optional[str] = None          # filled by Phase 09


@dataclass
class ExtractionResult:
    """Full extraction output for one document (fed into Aloka knowledge graph)."""
    document_id: str
    document_type: str
    classification_confidence: float
    entities: list = field(default_factory=list)   # list[ExtractedEntity]
    raw_ocr: list = field(default_factory=list)    # list[dict] mirroring OcrOutput pages


# ---------------------------------------------------------------------------
# Gemini prompts -- one per document type
# Each prompt tells Gemini exactly which fields to find and how to format output.
# ---------------------------------------------------------------------------

EXTRACTION_PROMPTS: dict[str, str] = {
    "commercial_invoice": """Extract these fields from this Commercial Invoice image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "INVOICE_NUMBER": "value or null",
  "INVOICE_DATE": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "CONSIGNEE_ADDRESS": "value or null",
  "SHIPPER_NAME": "value or null",
  "INCOTERM": "value or null",
  "PAYMENT_TERMS": "value or null",
  "TOTAL_AMOUNT": "value or null",
  "CURRENCY": "value or null",
  "GROSS_WEIGHT": "value or null",
  "NET_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null"
}""",

    "packing_list": """Extract these fields from this Packing List image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "GROSS_WEIGHT": "value or null",
  "NET_WEIGHT": "value or null",
  "TARE_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "VOLUME": "value or null",
  "SHIPPING_MARKS": "value or null"
}""",

    "awb": """Extract these fields from this Air Waybill image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "AWB_NUMBER": "value or null",
  "FLIGHT_NUMBER": "value or null",
  "ORIGIN": "value or null",
  "DESTINATION": "value or null",
  "GROSS_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "SHIPPER_NAME": "value or null",
  "CONSIGNEE_NAME": "value or null"
}""",

    "bl": """Extract these fields from this Bill of Lading image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "BL_NUMBER": "value or null",
  "VESSEL_NAME": "value or null",
  "PORT_LOADING": "value or null",
  "PORT_DISCHARGE": "value or null",
  "GROSS_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "CONTAINER_NUMBER": "value or null"
}""",

    "freight_invoice": """Extract these fields from this Freight Invoice image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "INVOICE_NUMBER": "value or null",
  "INVOICE_DATE": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "SHIPPER_NAME": "value or null",
  "TOTAL_AMOUNT": "value or null",
  "CURRENCY": "value or null",
  "BL_NUMBER": "value or null",
  "CONTAINER_NUMBER": "value or null"
}""",

    "delivery_order": """Extract these fields from this Delivery Order image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "DO_NUMBER": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "CONTAINER_NUMBER": "value or null",
  "GROSS_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "PORT_DISCHARGE": "value or null"
}""",

    "letter_of_credit": """Extract these fields from this Letter of Credit image.
Return ONLY valid JSON with exactly these keys. Use null for any field not found.
Do not include markdown fences or any other text.
{
  "LC_NUMBER": "value or null",
  "ISSUING_BANK": "value or null",
  "BENEFICIARY": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "TOTAL_AMOUNT": "value or null",
  "CURRENCY": "value or null",
  "INCOTERM": "value or null",
  "EXPIRY_DATE": "value or null"
}""",
}

# Fallback: if Gemini is called for an unknown doc type, extract these basics
GENERIC_PROMPT = """Extract any key-value pairs you can find in this shipping document.
Return ONLY valid JSON. Use null for missing values. Include at minimum:
{
  "GROSS_WEIGHT": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "PACKAGE_COUNT": "value or null"
}"""

# Default bounding box when no OCR match is found
_DEFAULT_BBOX = [0, 0, 100, 30]


# ---------------------------------------------------------------------------
# Utility: map a Gemini value back to the best OCR bounding box
# ---------------------------------------------------------------------------

def map_to_bbox(gemini_value: str, ocr_tokens: list, threshold: float = 0.6) -> Optional[OcrToken]:
    """
    Find the OCR token whose text best matches a Gemini-extracted value.

    Scoring:
      1. Exact substring containment -> score 1.0
         (handles "Gross Weight: 450.00 KG" containing "450.00 KG")
      2. Fuzzy SequenceMatcher ratio -> handles minor OCR noise

    Returns the best-matching OcrToken, or None if nothing exceeds threshold.
    """
    if not ocr_tokens or not gemini_value:
        return None

    best_token: Optional[OcrToken] = None
    best_score = 0.0
    gv_lower = gemini_value.lower().strip()

    for token in ocr_tokens:
        tok_lower = token.text.lower().strip()
        if gv_lower in tok_lower:
            score = 1.0
        elif tok_lower in gv_lower and len(tok_lower) > 3:
            # token is a substring of the value (e.g. token "USD" inside "45,230 USD")
            score = 0.85
        else:
            score = SequenceMatcher(None, gv_lower, tok_lower).ratio()

        if score > best_score:
            best_score = score
            best_token = token

    return best_token if best_score >= threshold else None


def _strip_fences(text: str) -> str:
    """Remove markdown code fences Gemini sometimes adds around JSON."""
    text = text.strip()
    text = re.sub(r"^`[a-z]*\n?", "", text)
    text = re.sub(r"\n?`$", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------

class EntityExtractor:
    """
    Header entity extractor using Gemini Vision API + OCR bounding box mapping.

    Usage
    -----
        from ai_pipeline.entity_extractor import EntityExtractor
        from ai_pipeline.ocr_engine import OcrEngine
        from ai_pipeline.classifier import DocumentClassifier

        ocr = OcrEngine()
        clf = DocumentClassifier()
        ext = EntityExtractor()

        ocr_out     = ocr.extract("path/to/doc.pdf")
        cls_result  = clf.classify(ocr_out, pdf_path="path/to/doc.pdf")
        result      = ext.extract(ocr_out, cls_result, "path/to/doc.pdf")

        for entity in result.entities:
            print(entity.entity_type, entity.value, entity.bbox)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "your_key_here":
            logger.warning(
                "GEMINI_API_KEY not set or is placeholder. "
                "EntityExtractor will return empty results until a real key is provided."
            )
            self._model = None
        else:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash")
            logger.info("EntityExtractor initialised with gemini-2.0-flash")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        ocr_output: OcrOutput,
        classification: ClassificationResult,
        pdf_path: str,
        document_id: str = "doc_001",
    ) -> ExtractionResult:
        """
        Extract header entities from a document.

        Parameters
        ----------
        ocr_output     : OcrOutput from Phase 03 OcrEngine
        classification : ClassificationResult from Phase 04 DocumentClassifier
        pdf_path       : path to the original PDF (for Gemini Vision page images)
        document_id    : identifier for this document in the pipeline

        Returns
        -------
        ExtractionResult with populated entities list and raw_ocr snapshot
        """
        doc_type = classification.document_type

        # Build the raw_ocr snapshot (used by Kaveen for PDF overlay)
        raw_ocr = self._build_raw_ocr(ocr_output)

        result = ExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            classification_confidence=round(classification.confidence, 4),
            entities=[],
            raw_ocr=raw_ocr,
        )

        if self._model is None:
            logger.warning("No Gemini API key -- returning empty entity list.")
            return result

        if doc_type == "unknown":
            logger.info("Document type is unknown -- using generic prompt.")

        # Flatten all OCR tokens for bbox mapping
        all_tokens = [tok for page in ocr_output.pages for tok in page.tokens]

        # Process each page (header entities are usually on page 1)
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, first_page=1, last_page=2)
        except Exception as e:
            logger.error(f"Could not convert PDF to images: {e}")
            return result

        for page_idx, page_image in enumerate(images):
            page_num = page_idx + 1
            page_tokens = [t for t in all_tokens if t.page == page_num]

            # Only process page 1 for header entities (phase 07 handles tables)
            if page_num > 1:
                break

            entities = self._extract_page(
                page_image=page_image,
                doc_type=doc_type,
                page_tokens=all_tokens,   # search all tokens for bbox
                page_num=page_num,
            )
            result.entities.extend(entities)

        logger.info(
            f"Extracted {len(result.entities)} entities from '{pdf_path}' "
            f"(type={doc_type})"
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_page(
        self,
        page_image,
        doc_type: str,
        page_tokens: list,
        page_num: int,
    ) -> list[ExtractedEntity]:
        """Call Gemini Vision on one page image and map results to OCR bboxes."""
        prompt = EXTRACTION_PROMPTS.get(doc_type, GENERIC_PROMPT)

        try:
            response = self._model.generate_content([prompt, page_image])
            raw_text = _strip_fences(response.text)
            gemini_data: dict = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned non-JSON for page {page_num}: {e}")
            return []
        except Exception as e:
            logger.error(f"Gemini API call failed for page {page_num}: {e}")
            return []

        entities: list[ExtractedEntity] = []

        for entity_type, raw_value in gemini_data.items():
            # Skip nulls
            if raw_value is None or str(raw_value).lower() in ("null", "", "none"):
                continue

            value_str = str(raw_value).strip()

            # Find the best matching OCR token for the bounding box
            matched_token = map_to_bbox(value_str, page_tokens)

            if matched_token:
                bbox = matched_token.bbox
                ocr_conf = matched_token.confidence
                # Blend: Gemini confident + OCR read successfully
                extraction_confidence = round(min(0.97, (ocr_conf + 0.92) / 2), 4)
            else:
                # Gemini found it but no OCR token matched -- still include the entity
                # with a lower confidence and a default bbox
                bbox = _DEFAULT_BBOX
                extraction_confidence = 0.50
                logger.debug(
                    f"No OCR token matched for {entity_type}={value_str!r} -- "
                    f"using default bbox"
                )

            entities.append(ExtractedEntity(
                entity_type=entity_type,
                value=value_str,           # raw string, NOT normalised (Phase 09 does that)
                page=page_num,
                bbox=bbox,
                extraction_confidence=extraction_confidence,
                normalized_value=None,     # Phase 09 normalizer fills this
                unit=None,                 # Phase 09 normalizer fills this
            ))

        return entities

    def _build_raw_ocr(self, ocr_output: OcrOutput) -> list[dict]:
        """Convert OcrOutput to the list[dict] format expected by the output contract."""
        raw = []
        for page in ocr_output.pages:
            for token in page.tokens:
                raw.append({
                    "text": token.text,
                    "page": token.page,
                    "bbox": token.bbox,
                    "ocr_confidence": round(token.confidence, 4),
                })
        return raw

    def to_dict(self, result: ExtractionResult) -> dict:
        """
        Serialise an ExtractionResult to the canonical JSON contract.
        This is the format Aloka's knowledge graph and Kaveen's API consume.
        """
        return {
            "document_id": result.document_id,
            "document_type": result.document_type,
            "classification_confidence": result.classification_confidence,
            "entities": [
                {
                    "entity_type": e.entity_type,
                    "value": e.value,
                    "normalized_value": e.normalized_value,
                    "unit": e.unit,
                    "page": e.page,
                    "bbox": e.bbox,
                    "extraction_confidence": e.extraction_confidence,
                }
                for e in result.entities
            ],
            "raw_ocr": result.raw_ocr,
        }
