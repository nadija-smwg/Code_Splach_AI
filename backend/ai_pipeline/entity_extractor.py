# backend/ai_pipeline/entity_extractor.py
"""
Phase 06 -- Header Entity Extraction  (Hybrid Strategy)
=========================================================
Decision (Phase 05, Option C): PaddleOCR local rules first -> OpenAI fallback only
when local extraction cannot reliably find a field.

Architecture
-------------
  PaddleOCR (Phase 03)
      |
      v
  LocalExtractor          <- regex / label-match / known patterns
      |
      +-- confident? --> accept (no OpenAI call)
      |
      +-- missing / ambiguous --> OpenAIFallback (Vision API, one call per page)
                                      |
                                      v
                               map_to_bbox() --> OCR bounding box

Extraction Responsibility Boundary
------------------------------------
  THIS FILE  : populates entity["value"]        <- raw string, as OCR/OpenAI saw it
  normalizer : populates entity["normalized_value"] and entity["unit"]   <- Phase 09
  Do NOT normalise, convert units, clean identifiers, or format dates here.

Cross-doc conflict fields (Aloka's knowledge graph):
  CROSS_DOCUMENT_FIELDS = [GROSS_WEIGHT, NET_WEIGHT, PACKAGE_COUNT,
                           CONSIGNEE_NAME, SHIPPER_NAME, INCOTERM]

Author: Nadija (Phase 06)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional, Any
from pydantic import create_model, Field

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from ai_pipeline.ocr_engine import OcrOutput, OcrToken
from ai_pipeline.classifier import ClassificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output contract dataclasses  (unchanged from Phase 05 skeleton)
# ---------------------------------------------------------------------------

@dataclass
class ExtractedEntity:
    """
    One extracted header entity.
    value            <- Phase 06: raw string exactly as OCR/OpenAI saw it
    normalized_value <- Phase 09: canonical converted form
    unit             <- Phase 09: unit string
    """
    entity_type: str
    value: str
    page: int
    bbox: list                          # [x1, y1, x2, y2]
    extraction_confidence: float
    normalized_value: object = None     # Phase 09 fills this
    unit: Optional[str] = None          # Phase 09 fills this


@dataclass
class ExtractionResult:
    """Full extraction result for one document (fed into Aloka's knowledge graph)."""
    document_id: str
    document_type: str
    classification_confidence: float
    entities: list = field(default_factory=list)   # list[ExtractedEntity]
    raw_ocr: list = field(default_factory=list)    # list[dict] mirroring OcrOutput
    warnings: list = field(default_factory=list)


@dataclass
class ExtractionTelemetry:
    """
    Hybrid strategy cost telemetry.  Printed at end of each extraction run.
    """
    fields_requested: int = 0
    local_extracted: int = 0
    openai_fallback_fields: int = 0
    openai_calls: int = 0
    openai_recovered: int = 0
    failed: int = 0
    elapsed_sec: float = 0.0

    def report(self) -> str:
        return (
            f"Fields requested: {self.fields_requested}\n"
            f"Local extraction: {self.local_extracted}\n"
            f"OpenAI fallback:  {self.openai_fallback_fields}\n"
            f"OpenAI calls:     {self.openai_calls}\n"
            f"OpenAI recovered: {self.openai_recovered}\n"
            f"Failed:           {self.failed}\n"
            f"Elapsed:          {self.elapsed_sec:.2f}s"
        )


# ---------------------------------------------------------------------------
# Entity schemas per document type
# ---------------------------------------------------------------------------

ENTITY_SCHEMAS: dict[str, list[str]] = {
    "commercial_invoice": [
        "INVOICE_NUMBER", "INVOICE_DATE", "CONSIGNEE_NAME", "CONSIGNEE_ADDRESS",
        "SHIPPER_NAME", "INCOTERM", "PAYMENT_TERMS", "TOTAL_AMOUNT",
        "CURRENCY_CODE", "GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT",
        "HS_CODE", "COUNTRY_OF_ORIGIN", "PORT_OF_LOADING", "PORT_OF_DISCHARGE",
        "VESSEL_NAME", "FREIGHT_AMOUNT", "INSURANCE_AMOUNT"
    ],
    "packing_list": [
        "GROSS_WEIGHT", "NET_WEIGHT", "TARE_WEIGHT", "PACKAGE_COUNT",
        "VOLUME", "SHIPPING_MARKS", "CONSIGNEE_NAME", "SHIPPER_NAME"
    ],
    "awb": [
        "AWB_NUMBER", "VESSEL_NAME", "ORIGIN", "DESTINATION",
        "GROSS_WEIGHT", "PACKAGE_COUNT", "SHIPPER_NAME", "CONSIGNEE_NAME",
        "TOTAL_AMOUNT", "CURRENCY_CODE", "FREIGHT_AMOUNT", "INSURANCE_AMOUNT"
    ],
    "bl": [
        "BL_NUMBER", "VESSEL_NAME", "PORT_OF_LOADING", "PORT_OF_DISCHARGE",
        "GROSS_WEIGHT", "PACKAGE_COUNT", "CONTAINER_NUMBER", "CONSIGNEE_NAME", 
        "SHIPPER_NAME"
    ],
    "freight_invoice": [
        "INVOICE_NUMBER", "INVOICE_DATE", "CONSIGNEE_NAME", "SHIPPER_NAME",
        "TOTAL_AMOUNT", "CURRENCY_CODE", "BL_NUMBER", "CONTAINER_NUMBER"
    ],
    "delivery_order": [
        "DO_NUMBER", "CONSIGNEE_NAME", "CONTAINER_NUMBER",
        "GROSS_WEIGHT", "PACKAGE_COUNT", "PORT_OF_DISCHARGE"
    ],
    "letter_of_credit": [
        "LC_NUMBER", "ISSUING_BANK", "BENEFICIARY", "CONSIGNEE_NAME",
        "TOTAL_AMOUNT", "CURRENCY_CODE", "INCOTERM", "EXPIRY_DATE"
    ],
}

FIELD_DEFINITIONS = {
    "INVOICE_NUMBER": {"type": str, "desc": "The unique commercial invoice number."},
    "INVOICE_DATE": {"type": str, "desc": "The date the invoice was issued."},
    "CONSIGNEE_NAME": {"type": str, "desc": "Name of the buyer or consignee."},
    "CONSIGNEE_ADDRESS": {"type": str, "desc": "Full address of the consignee."},
    "SHIPPER_NAME": {"type": str, "desc": "Name of the seller, exporter, or shipper."},
    "INCOTERM": {"type": str, "desc": "Incoterm (e.g., CIF, FOB, EXW)."},
    "PAYMENT_TERMS": {"type": str, "desc": "Payment terms (e.g., LC AT SIGHT, 30 Days)."},
    "TOTAL_AMOUNT": {"type": float, "desc": "Total invoice or declared amount (numeric only)."},
    "CURRENCY_CODE": {"type": str, "desc": "3-letter currency code (e.g., USD, EUR, LKR)."},
    "GROSS_WEIGHT": {"type": float, "desc": "Total gross weight (numeric only)."},
    "NET_WEIGHT": {"type": float, "desc": "Total net weight (numeric only). DO NOT extract bank account numbers."},
    "TARE_WEIGHT": {"type": float, "desc": "Tare weight of containers/packaging (numeric only)."},
    "PACKAGE_COUNT": {"type": float, "desc": "Total number of packages/cartons/rolls (numeric only)."},
    "HS_CODE": {"type": str, "desc": "Harmonized System (HS) code. Usually 6 to 10 digits."},
    "COUNTRY_OF_ORIGIN": {"type": str, "desc": "Country of origin where goods were manufactured."},
    "PORT_OF_LOADING": {"type": str, "desc": "Port or airport of departure/loading (e.g., AHMEDABAD)."},
    "PORT_OF_DISCHARGE": {"type": str, "desc": "Port or airport of arrival/destination (e.g., COLOMBO)."},
    "VESSEL_NAME": {"type": str, "desc": "Vessel name or Flight number (e.g., 6E1171)."},
    "FREIGHT_AMOUNT": {"type": float, "desc": "Cost of freight (numeric only)."},
    "INSURANCE_AMOUNT": {"type": float, "desc": "Cost of insurance (numeric only)."},
    "SHIPPING_MARKS": {"type": str, "desc": "Marks and numbers printed on packages or customer references."},
    "AWB_NUMBER": {"type": str, "desc": "11-digit Air Waybill number. Exclude text headers like 'HAWB NO'."},
    "FLIGHT_NUMBER": {"type": str, "desc": "Flight number."},
    "ORIGIN": {"type": str, "desc": "Airport of origin."},
    "DESTINATION": {"type": str, "desc": "Airport of destination."},
    "BL_NUMBER": {"type": str, "desc": "Bill of Lading number."},
    "CONTAINER_NUMBER": {"type": str, "desc": "Shipping container number."},
    "VOLUME": {"type": float, "desc": "Total volume in CBM (numeric only)."},
    "DO_NUMBER": {"type": str, "desc": "Delivery Order number."},
    "LC_NUMBER": {"type": str, "desc": "Letter of Credit (L/C) number."},
    "ISSUING_BANK": {"type": str, "desc": "Name of the issuing bank for the LC."},
    "BENEFICIARY": {"type": str, "desc": "Name of the beneficiary."},
    "EXPIRY_DATE": {"type": str, "desc": "Expiry date of the document or LC."},
}

# (Replaced old EXTRACTION_PROMPTS dict)

# Default fallback bbox when no OCR token matches
_DEFAULT_BBOX = [0, 0, 0, 0]

# Minimum OCR confidence below which a local match is considered unreliable
_MIN_OCR_CONFIDENCE = 0.60

# Minimum local extraction confidence to skip OpenAI
_LOCAL_CONFIDENCE_GATE = 1.10


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _bbox_union(bboxes: list[list]) -> list:
    """Return the bounding box that encloses all given [x1,y1,x2,y2] boxes."""
    if not bboxes:
        return _DEFAULT_BBOX
    x1 = min(b[0] for b in bboxes)
    y1 = min(b[1] for b in bboxes)
    x2 = max(b[2] for b in bboxes)
    y2 = max(b[3] for b in bboxes)
    return [x1, y1, x2, y2]


def map_to_bbox(
    gemini_value: str,
    ocr_tokens: list,
    threshold: float = 0.60,
) -> Optional[OcrToken]:
    """
    Find the OCR token whose text best matches a OpenAI/local-extracted value.

    Scoring strategy (highest wins):
      1. Exact substring containment (value in token text)  -> 1.0
      2. Token text substring of value (short tokens like "USD") -> 0.85
      3. Fuzzy SequenceMatcher ratio                        -> 0.0-1.0

    Returns the best-matching OcrToken or None if below threshold.
    """
    if not ocr_tokens or not gemini_value:
        return None

    best_token: Optional[OcrToken] = None
    best_score = 0.0
    gv_lower = gemini_value.lower().strip()

    for token in ocr_tokens:
        tok_lower = token.text.lower().strip()
        if not tok_lower:
            continue

        if gv_lower in tok_lower:
            score = 1.0
        elif tok_lower in gv_lower and len(tok_lower) > 3:
            score = 0.85
        else:
            score = SequenceMatcher(None, gv_lower, tok_lower).ratio()

        if score > best_score:
            best_score = score
            best_token = token

    return best_token if best_score >= threshold else None


def _multi_token_bbox(value: str, ocr_tokens: list) -> tuple[list, float]:
    """
    When a value may span multiple OCR tokens (e.g. "440.00" and "KG" on separate lines),
    collect all tokens whose text appears in the value and return their union bbox.

    Returns (bbox, best_ocr_confidence).
    """
    if not ocr_tokens or not value:
        return _DEFAULT_BBOX, 0.0

    val_lower = value.lower()
    matched: list[OcrToken] = []

    # First try: single token that contains the whole value
    single = map_to_bbox(value, ocr_tokens)
    if single:
        return single.bbox, single.confidence

    # Multi-token: split value on whitespace and find individual tokens
    parts = value.split()
    for part in parts:
        if len(part) < 2:
            continue
        tok = map_to_bbox(part, ocr_tokens, threshold=0.80)
        if tok and tok not in matched:
            matched.append(tok)

    if matched:
        return _bbox_union([t.bbox for t in matched]), min(t.confidence for t in matched)

    return _DEFAULT_BBOX, 0.0


def _strip_fences(text: str) -> str:
    """Remove markdown code fences OpenAI sometimes wraps JSON in."""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _is_null(v) -> bool:
    if v is None:
        return True
    if isinstance(v, (int, float)) and v == 0:
        return True
    return str(v).lower().strip() in ("null", "none", "n/a", "", "na", "0", "0.0", "0.00")


# ---------------------------------------------------------------------------
# Layer 1: Local rule-based extractor
# ---------------------------------------------------------------------------

class LocalExtractor:
    """
    Extract strongly-structured fields directly from OCR token text using
    label matching, regex, and known document patterns.

    Returns a dict:  entity_type -> (value_str, confidence, matched_tokens)
    Where matched_tokens is a list[OcrToken] used for bbox computation.
    """

    # ── Regex patterns per entity type ───────────────────────────────────

    _PATTERNS: dict[str, list[str]] = {
        "INVOICE_NUMBER": [
            r"\b(INV[-/][\d\-]+)\b",
            r"\b(IN[-/][\w\-]{4,})\b",
        ],
        "INVOICE_DATE": [
            r"\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
            r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s+\d{4})\b",
            r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        ],
        "GROSS_WEIGHT": [
            r"(\d[\d,\.]+\s*(?:KG|kg|Kg|kgs|KGS|kilogram[s]?))\b",
        ],
        "NET_WEIGHT": [
            r"(\d[\d,\.]+\s*(?:KG|kg|Kg|kgs|KGS|kilogram[s]?))\b",
        ],
        "TARE_WEIGHT": [
            r"(\d[\d,\.]+\s*(?:KG|kg|Kg|kgs|KGS))\b",
        ],
        "PACKAGE_COUNT": [
            r"(\d[\d,]*\s*(?:Carton[s]?|Ctn[s]?|pcs?|Piece[s]?|Package[s]?|Box(?:es)?|"
            r"Pallet[s]?|Unit[s]?|Roll[s]?))\b",
        ],
        "CURRENCY_CODE": [
            r"\b(USD|EUR|GBP|JPY|LKR|AUD|CAD|SGD|CHF)\b",
        ],
        "TOTAL_AMOUNT": [
            r"\b(?:USD|EUR|GBP)\s*(\d[\d,\.]+(?:\.\d{2})?)\b",
            r"(\d[\d,]+\.\d{2})\s*(?:USD|EUR|GBP)",
        ],
        "INCOTERM": [
            # Capture incoterm + optional location e.g. "FOB Colombo"
            r"\b((?:FOB|CIF|CFR|EXW|DAP|DDP|FCA|CPT|CIP|DAT)(?:\s+[A-Za-z][A-Za-z\s]{1,20})?)\b",
        ],
        "AWB_NUMBER": [
            r"\b(\d{3}[-\s]\d{4}\s?\d{4})\b",
            r"\b(\d{3}-\d{8})\b",
        ],
        "FLIGHT_NUMBER": [
            r"\b([A-Z]{2}\s*\d{2,4})\b",
        ],
        "BL_NUMBER": [
            r"\b([A-Z]{4}\d{9,12})\b",
            r"\b(BL[-/][\w\-]{5,})\b",
        ],
        "CONTAINER_NUMBER": [
            r"\b([A-Z]{4}\d{7})\b",
        ],
        "VOLUME": [
            r"(\d[\d,\.]+\s*(?:CBM|m3|M3|cubic\s*m(?:etr(?:e|er)?)?[s]?))\b",
        ],
        "PAYMENT_TERMS": [
            r"(\d+\s*Days?\s*(?:from|after)\s*[\w\s/]+)\b",
            r"\b(T/T|L/C|D/P|D/A|CAD|Open\s+Account)\b",
        ],
        "ORIGIN": [
            r"(?:From|Origin|Departure):\s*(.+?)(?:\n|$)",
        ],
        "DESTINATION": [
            r"(?:To|Destination|Dest\.?):\s*(.+?)(?:\n|$)",
        ],
        "VOLUME": [
            r"(\d[\d,\.]+\s*(?:CBM|m3|M3|cubic\s*meter[s]?))\b",
        ],
    }

    # ── Label-to-entity mapping for nearby-token detection ────────────────

    _LABELS: dict[str, list[str]] = {
        "INVOICE_NUMBER":    ["invoice no", "invoice number", "inv no", "inv#", "invoice #"],
        "INVOICE_DATE":      ["invoice date", "date of issue", "issue date", "date"],
        "CONSIGNEE_NAME":    ["consignee", "consignee name", "bill to", "buyer"],
        "CONSIGNEE_ADDRESS": ["consignee address", "consignee:", "buyer address"],
        "SHIPPER_NAME":      ["shipper", "exporter", "seller", "shipped by"],
        "INCOTERM":          ["incoterm", "incoterms", "terms of sale", "delivery terms"],
        "PAYMENT_TERMS":     ["payment terms", "payment", "terms of payment"],
        "TOTAL_AMOUNT":      ["total invoice value", "total amount", "grand total", "invoice total", "total"],
        "CURRENCY_CODE":          ["currency"],
        "GROSS_WEIGHT":      ["gross weight", "total gross weight", "gross wt", "gross"],
        "NET_WEIGHT":        ["net weight", "total net weight", "net wt", "net"],
        "TARE_WEIGHT":       ["tare weight", "tare wt", "tare"],
        "PACKAGE_COUNT":     ["total cartons", "no. of cartons", "number of packages",
                              "total pieces", "packages", "cartons", "package count"],
        "VOLUME":            ["total volume", "volume", "cbm", "total cbm"],
        "SHIPPING_MARKS":    ["shipping marks", "marks", "marks & numbers"],
        "AWB_NUMBER":        ["awb number", "awb no", "air waybill", "airwaybill no"],
        "FLIGHT_NUMBER":     ["flight no", "flight number", "flight"],
        "ORIGIN":            ["departure airport", "origin", "airport of departure", "from"],
        "DESTINATION":       ["destination airport", "destination", "airport of destination", "to"],
        "BL_NUMBER":         ["bl number", "bill of lading no", "b/l no", "b/l number"],
        "VESSEL_NAME":       ["vessel", "vessel name", "ship name", "m/v", "mv"],
        "PORT_OF_LOADING":      ["port of loading", "load port", "pol"],
        "PORT_OF_DISCHARGE":    ["port of discharge", "discharge port", "pod", "destination port"],
        "CONTAINER_NUMBER":  ["container no", "container number", "ctn no", "cntr"],
        "DO_NUMBER":         ["delivery order no", "do no", "do number"],
        "LC_NUMBER":         ["l/c number", "lc no", "letter of credit no", "lc number"],
        "ISSUING_BANK":      ["issuing bank", "issuing bank name"],
        "BENEFICIARY":       ["beneficiary", "beneficiary name"],
        "EXPIRY_DATE":       ["expiry date", "expiry", "valid until", "lc expiry"],
    }

    def extract(
        self,
        entity_types: list[str],
        ocr_tokens: list,
        doc_type: str,
    ) -> dict[str, tuple]:
        """
        Try to extract each entity_type from the OCR token list.

        Returns dict:
            entity_type -> (value_str, confidence, matched_tokens: list[OcrToken])
            Only includes entities that were found with confidence >= _LOCAL_CONFIDENCE_GATE.
        """
        results: dict[str, tuple] = {}

        # Build a flat joined text for regex scanning
        full_text = " ".join(t.text for t in ocr_tokens)

        for entity_type in entity_types:
            result = self._try_label_match(entity_type, ocr_tokens, doc_type)
            if result is None:
                result = self._try_regex(entity_type, ocr_tokens, full_text)
            if result:
                value, conf, tokens = result
                if conf >= _LOCAL_CONFIDENCE_GATE:
                    results[entity_type] = (value, conf, tokens)

        return results

    def _try_label_match(
        self, entity_type: str, ocr_tokens: list, doc_type: str
    ) -> Optional[tuple]:
        """
        Find the label token then grab the value from adjacent tokens.
        Handles two token styles:
          a) "Label: VALUE"  -- value is in the same token after the colon
          b) "Label:"        -- value is in the next 1-3 tokens
        Returns (value, confidence, [token]) or None.
        """
        labels = self._LABELS.get(entity_type, [])
        if not labels:
            return None

        for i, token in enumerate(ocr_tokens):
            # Strip trailing colon for comparison but keep original text
            tok_cmp = token.text.lower().strip().rstrip(":")

            for label in labels:
                label_match = (
                    label == tok_cmp
                    or label in tok_cmp
                    or SequenceMatcher(None, label, tok_cmp).ratio() >= 0.85
                )
                if not label_match:
                    continue

                # Style (a): "Label: Value" — value follows colon in same token
                if ":" in token.text:
                    colon_val = self._extract_after_colon(token.text, entity_type)
                    if colon_val:
                        conf = min(0.88, token.confidence)
                        return colon_val, conf, [token]

                # Style (b): label is standalone, value is the next non-label token
                for j in range(i + 1, min(i + 4, len(ocr_tokens))):
                    candidate = ocr_tokens[j].text.strip()
                    if self._looks_like_value(candidate, entity_type):
                        conf = min(0.85, ocr_tokens[j].confidence)
                        return candidate, conf, [ocr_tokens[j]]

        return None

    def _try_regex(
        self, entity_type: str, ocr_tokens: list, full_text: str
    ) -> Optional[tuple]:
        """
        Try regex patterns on the full OCR text.  When a match is found,
        look up which token(s) produced it for bbox.
        """
        patterns = self._PATTERNS.get(entity_type, [])
        for pattern in patterns:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                value = m.group(1) if m.lastindex else m.group(0)
                value = value.strip()
                # Find which token(s) contributed to this match
                matched_tokens = [
                    t for t in ocr_tokens
                    if value.lower() in t.text.lower() or t.text.lower() in value.lower()
                ]
                conf = 0.80 if matched_tokens else 0.65
                if matched_tokens:
                    # Average OCR confidence of matched tokens weighted toward lower
                    conf = min(0.90, min(t.confidence for t in matched_tokens) + 0.05)
                return value, conf, matched_tokens
        return None

    def _extract_after_colon(self, text: str, entity_type: str) -> Optional[str]:
        """Extract the part after a colon in 'Label: VALUE' style tokens."""
        if ":" not in text:
            return None
        parts = text.split(":", 1)
        value = parts[1].strip()
        if not value or len(value) < 2:
            return None
        if self._looks_like_value(value, entity_type):
            return value
        return None

    def _looks_like_value(self, candidate: str, entity_type: str) -> bool:
        """Heuristic: does this candidate look like a real value for this entity?"""
        c = candidate.strip()
        if not c or len(c) < 2:
            return False
        # Reject if it looks like a label itself
        lower = c.lower()
        for labels in self._LABELS.values():
            for lbl in labels:
                if SequenceMatcher(None, lbl, lower).ratio() > 0.90:
                    return False

        weight_like = bool(re.search(r"\d[\d,\.]+\s*(?:KG|kg|kgs|KGS|lbs?|LBS)", c))
        number_like = bool(re.search(r"\d[\d,\.]+", c))
        code_like   = bool(re.search(r"\b[A-Z0-9]{3,}\b", c))
        text_like   = len(c.split()) >= 2

        numeric_fields = {
            "GROSS_WEIGHT", "NET_WEIGHT", "TARE_WEIGHT", "PACKAGE_COUNT",
            "TOTAL_AMOUNT", "VOLUME"
        }
        if entity_type in numeric_fields:
            return weight_like or number_like
        if entity_type in {"CURRENCY_CODE"}:
            return bool(re.match(r"^(USD|EUR|GBP|JPY|LKR|AUD|CAD|SGD|CHF)$", c, re.I))
        if entity_type in {"INVOICE_NUMBER", "AWB_NUMBER", "BL_NUMBER",
                           "CONTAINER_NUMBER", "DO_NUMBER", "LC_NUMBER"}:
            return code_like or bool(re.search(r"[-/]\d+", c))
        if entity_type in {"CONSIGNEE_NAME", "SHIPPER_NAME", "VESSEL_NAME",
                           "ISSUING_BANK", "BENEFICIARY"}:
            return text_like
        return number_like or text_like or code_like


# ---------------------------------------------------------------------------
# Layer 2: OpenAI Vision fallback
# ---------------------------------------------------------------------------

class OpenAIFallback:
    """
    Calls OpenAI Vision API using Pydantic Structured Outputs.
    """

    def __init__(self, client):
        self.client = client

    def extract_missing(
        self,
        missing_fields: list[str],
        doc_type: str,
        page_image,
    ) -> tuple[dict[str, str], str]:
        if not missing_fields or self.client is None or page_image is None:
            return {}, ""

        from pydantic import BaseModel, Field, create_model
        
        schema_fields = {}
        for f in missing_fields:
            field_meta = FIELD_DEFINITIONS.get(f, {"type": str, "desc": ""})
            schema_fields[f] = (field_meta["type"], Field(description=field_meta["desc"]))

        DynamicSchema = create_model(f"{doc_type.capitalize()}Schema", **schema_fields)

        prompt = (
            f"Extract the requested missing fields from this {doc_type}. "
            f"Return ONLY valid JSON according to the schema. "
            f"If a field is not visibly present in the document, return an empty string for text, or 0.0 for numbers."
        )
        
        try:
            data = self.client.get_vision_completion(prompt, page_image, schema=DynamicSchema)
            return data or {}, ""
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            return {}, f"OpenAI Vision extraction failed: {e}"

        from pydantic import BaseModel, Field, create_model
        
        schema_fields = {}
        for f in missing_fields:
            field_meta = FIELD_DEFINITIONS.get(f, {"type": str, "desc": ""})
            schema_fields[f] = (field_meta["type"], Field(description=field_meta["desc"]))

        DynamicSchema = create_model(f"{doc_type.capitalize()}Schema", **schema_fields)

        prompt = (
            f"Extract the requested missing fields from this {doc_type}. "
            f"Return ONLY valid JSON according to the schema. "
            f"If a field is not visibly present in the document, return an empty string for text, or 0.0 for numbers."
        )
        
        try:
            data = self.client.get_vision_completion(prompt, page_image, schema=DynamicSchema)
            return data or {}
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            return {}



# ---------------------------------------------------------------------------
# Main EntityExtractor class
# ---------------------------------------------------------------------------

class EntityExtractor:
    """
    Hybrid header entity extractor.

    Phase 06 strategy:
      1. LocalExtractor  tries all fields via label-match + regex on OCR tokens.
      2. Fields with confidence >= _LOCAL_CONFIDENCE_GATE are accepted.
      3. Remaining fields are sent to OpenAIFallback (ONE API call per page).
      4. All found values are mapped to OCR bounding boxes via map_to_bbox().

    Usage
    -----
        extractor = EntityExtractor()
        result, telemetry = extractor.extract(ocr_output, classification, "doc.pdf")
        for entity in result.entities:
            print(entity.entity_type, entity.value, entity.bbox)
        print(telemetry.report())
    """

    def __init__(self):
        from .openai_client import OpenAIClient
        self.client = OpenAIClient()
        if self.client._client is None:
            logger.warning(
                "OPENAI_API_KEY not set. EntityExtractor will run local-only mode "
                "(no OpenAI fallback)."
            )
            self.client = None
        else:
            logger.info(f"EntityExtractor: OpenAI fallback initialised")

        self._local = LocalExtractor()
        self._openai_fallback = OpenAIFallback(self.client)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        ocr_output: OcrOutput,
        classification: ClassificationResult,
        pdf_path: str,
        document_id: str = "doc_001",
    ) -> tuple[ExtractionResult, ExtractionTelemetry]:
        """
        Extract header entities from a document using the hybrid strategy.

        Returns
        -------
        (ExtractionResult, ExtractionTelemetry)
        """
        t0 = time.time()
        doc_type = classification.document_type
        entity_schema = ENTITY_SCHEMAS.get(doc_type, [])

        telemetry = ExtractionTelemetry(fields_requested=len(entity_schema))

        raw_ocr = self._build_raw_ocr(ocr_output)
        result = ExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            classification_confidence=round(classification.confidence, 4),
            entities=[],
            raw_ocr=raw_ocr,
        )

        if not entity_schema:
            logger.info(f"No schema for doc_type='{doc_type}' -- returning empty.")
            telemetry.elapsed_sec = time.time() - t0
            return result, telemetry

        # Flatten all tokens (all pages)
        all_tokens = [tok for page in ocr_output.pages for tok in page.tokens]

        if not all_tokens:
            logger.warning(f"No OCR tokens found in '{pdf_path}'")
            telemetry.elapsed_sec = time.time() - t0
            return result, telemetry

        # ── Layer 1: Local extraction ──────────────────────────────────
        local_results = self._local.extract(entity_schema, all_tokens, doc_type)
        telemetry.local_extracted = len(local_results)

        # ── Build entities from local results ─────────────────────────
        for entity_type, (value, conf, tokens) in local_results.items():
            bbox, ocr_conf = _multi_token_bbox(value, tokens if tokens else all_tokens)
            page = tokens[0].page if tokens else (all_tokens[0].page if all_tokens else 1)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                value=value,            # raw, not normalised
                page=page,
                bbox=bbox,
                extraction_confidence=round(min(conf, 0.97), 4),
                normalized_value=None,  # Phase 09
                unit=None,              # Phase 09
            ))

        # ── Layer 2: OpenAI fallback for remaining fields ──────────────
        locally_found = {e.entity_type for e in result.entities}
        missing = [f for f in entity_schema if f not in locally_found]
        telemetry.openai_fallback_fields = len(missing)

        if missing and self._model is not None:
            # Convert PDF page 1 to image for OpenAI
            page_image = self._get_page_image(pdf_path, page_num=1)

            if page_image is not None:
                telemetry.openai_calls += 1
                openai_data = self._openai_fallback.extract_missing(missing, doc_type, page_image)
                telemetry.openai_recovered = len(openai_data)

                for entity_type, value in openai_data.items():
                    # Map OpenAI value back to OCR bbox
                    bbox, ocr_conf = _multi_token_bbox(value, all_tokens)
                    page = self._value_page(value, all_tokens)
                    conf = self._openai_fallback_confidence(bbox, ocr_conf)

                    result.entities.append(ExtractedEntity(
                        entity_type=entity_type,
                        value=value,
                        page=page,
                        bbox=bbox,
                        extraction_confidence=round(conf, 4),
                        normalized_value=None,
                        unit=None,
                    ))
            else:
                logger.warning("Could not load page image for OpenAI -- skipping fallback.")
        elif missing:
            logger.info(
                f"OpenAI not available. {len(missing)} fields not extracted: {missing}"
            )

        # ── Count failures (fields still missing after both layers) ───
        found_types = {e.entity_type for e in result.entities}
        telemetry.failed = len([f for f in entity_schema if f not in found_types])

        telemetry.elapsed_sec = round(time.time() - t0, 3)
        logger.info(
            f"Phase 06 done | doc={document_id} type={doc_type} "
            f"entities={len(result.entities)} | {telemetry.report()}"
        )
        return result, telemetry

    # ------------------------------------------------------------------
    # Serialisation helper (Aloka's knowledge graph contract)
    # ------------------------------------------------------------------

    def to_dict(self, result: ExtractionResult) -> dict:
        """Serialise ExtractionResult to JSON-safe dict for API/KG consumption."""
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_page_image(self, pdf_path: str, page_num: int = 1):
        """Convert a PDF page to a PIL Image for OpenAI Vision."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
            return images[0] if images else None
        except Exception as e:
            logger.error(f"PDF->image conversion failed: {e}")
            return None

    def _value_page(self, value: str, ocr_tokens: list) -> int:
        """Return the page number of the best-matching OCR token for this value."""
        tok = map_to_bbox(value, ocr_tokens)
        return tok.page if tok else 1

    def _openai_confidence(self, bbox: list, ocr_conf: float) -> float:
        """
        Confidence for a OpenAI-extracted entity.
        - If bbox matched an OCR token: blend OpenAI base (0.82) with OCR conf
        - If no bbox match: lower confidence (0.55) -- OpenAI found it but we couldn't verify
        """
        if bbox == _DEFAULT_BBOX or bbox == [0, 0, 0, 0]:
            return 0.55
        return min(0.93, (0.82 + ocr_conf) / 2)

    def _build_raw_ocr(self, ocr_output: OcrOutput) -> list[dict]:
        """Mirror OcrOutput as list[dict] for the output contract."""
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
