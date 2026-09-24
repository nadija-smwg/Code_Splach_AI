# backend/ai_pipeline/table_extractor.py
"""
Phase 07 -- Table / Line-Item Extraction
=========================================
Priority: SHOULD (nice-to-have for demo, not MVP-critical)

Extracts line items from tabular sections of Commercial Invoices and Packing Lists.

Architecture
------------
  Primary   : Gemini Vision reads the table image -> returns structured JSON rows
  Bbox map  : Each row's description is matched back to OCR tokens for bounding box
  Fallback  : If Gemini fails OR no API key -> returns realistic mock line items
              (acceptable for hackathon demo per spec section 6.2)

Key constraints from spec
--------------------------
  - Only extract from 1-2 pages (multi-page table merging is NOT in scope)
  - If extraction takes >3h, use mock items (this module handles that transparently)
  - Tables with merged cells must NOT crash (graceful degradation)

Author: Nadija (Phase 07)
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

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output contract dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LineItem:
    """
    One extracted line item from a table row.
    bbox covers the entire table row area.
    confidence reflects how reliably the values were read.
    """
    row_index: int
    description: str
    quantity: float
    unit: str               # "meters", "kg", "pieces", "cartons", etc.
    unit_price: float
    total_price: float
    page: int
    bbox: list              # [x1, y1, x2, y2] bounding box of the row
    confidence: float
    is_mock: bool = False   # True if this came from the fallback mock data


@dataclass
class TableExtraction:
    """Full table extraction result for one document."""
    document_id: str
    items: list = field(default_factory=list)    # list[LineItem]
    total_rows: int = 0
    extraction_method: str = "gemini_vision"     # "gemini_vision" or "mock"


# ---------------------------------------------------------------------------
# Gemini prompt for table extraction
# ---------------------------------------------------------------------------

TABLE_EXTRACTION_PROMPT = """Extract ALL line items from the table in this document image.
Return a JSON array only -- no markdown, no other text.
Each element must have exactly these keys (use 0 for missing numeric values, empty string for missing text):
[
  {
    "row_index": 1,
    "description": "100% Cotton Fabric, GSM 180, Width 58 inches",
    "quantity": 5000,
    "unit": "meters",
    "unit_price": 2.50,
    "total_price": 12500.00
  }
]
Return empty array [] if no line-item table is found in this document."""

# ---------------------------------------------------------------------------
# Realistic mock line items (used when Gemini unavailable or extraction fails)
# These match the synthetic sample documents in backend/sample_docs/
# ---------------------------------------------------------------------------

MOCK_LINE_ITEMS = [
    {
        "row_index": 1,
        "description": "100% Cotton Woven Fabric, GSM 180, Width 58 inches, Natural White",
        "quantity": 5000.0,
        "unit": "meters",
        "unit_price": 2.50,
        "total_price": 12500.00,
    },
    {
        "row_index": 2,
        "description": "100% Polyester Fabric, GSM 120, Width 60 inches, Navy Blue",
        "quantity": 3000.0,
        "unit": "meters",
        "unit_price": 1.80,
        "total_price": 5400.00,
    },
    {
        "row_index": 3,
        "description": "Cotton Polyester Blend Fabric 60/40, GSM 200, Width 58 inches",
        "quantity": 2500.0,
        "unit": "meters",
        "unit_price": 3.10,
        "total_price": 7750.00,
    },
    {
        "row_index": 4,
        "description": "Elastic Webbing, Width 1.5 inches, White",
        "quantity": 1000.0,
        "unit": "meters",
        "unit_price": 0.45,
        "total_price": 450.00,
    },
    {
        "row_index": 5,
        "description": "Zipper (Nylon Coil #5), Length 20cm, Black",
        "quantity": 5000.0,
        "unit": "pieces",
        "unit_price": 0.12,
        "total_price": 600.00,
    },
]


def _strip_fences(text: str) -> str:
    """Remove markdown code fences Gemini sometimes wraps JSON in."""
    text = text.strip()
    text = re.sub(r"^`[a-z]*\n?", "", text)
    text = re.sub(r"\n?`$", "", text)
    return text.strip()


def _row_bbox(description: str, ocr_tokens: list, page: int) -> list:
    """
    Find the OCR token row that best matches a line-item description.
    Returns the token's bbox, or a plausible fallback based on row index.
    """
    if not ocr_tokens or not description:
        return [0, 0, 595, 30]

    desc_lower = description.lower().strip()
    # Try to find any token that contains a significant substring of the description
    words = [w for w in desc_lower.split() if len(w) > 4]
    best_token = None
    best_score = 0.0

    for token in ocr_tokens:
        if token.page != page:
            continue
        tok_lower = token.text.lower().strip()
        # Score based on word overlap
        word_hits = sum(1 for w in words if w in tok_lower)
        ratio = SequenceMatcher(None, desc_lower[:40], tok_lower).ratio()
        score = max(word_hits / max(len(words), 1), ratio)
        if score > best_score:
            best_score = score
            best_token = token

    if best_token and best_score >= 0.3:
        # Extend bbox to full width to represent the whole table row
        return [0, best_token.bbox[1], 595, best_token.bbox[3] + 5]

    return [0, 0, 595, 30]


# ---------------------------------------------------------------------------
# Main TableExtractor class
# ---------------------------------------------------------------------------

class TableExtractor:
    """
    Extracts line items from tabular sections of shipping documents.

    Usage
    -----
        from ai_pipeline.table_extractor import TableExtractor
        from pdf2image import convert_from_path

        extractor = TableExtractor()
        images = convert_from_path("invoice.pdf")
        result = extractor.extract(images[0], ocr_output, "doc_001", page_num=1)

        for item in result.items:
            print(item.row_index, item.description, item.total_price)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "your_key_here":
            logger.warning(
                "GEMINI_API_KEY not set -- TableExtractor will use mock line items."
            )
            self._model = None
        else:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash")
            logger.info("TableExtractor initialised with gemini-2.0-flash")

    def extract(
        self,
        page_image,
        ocr_output: OcrOutput,
        document_id: str,
        page_num: int = 1,
        doc_type: str = "commercial_invoice",
    ) -> TableExtraction:
        """
        Extract line items from a single page image.

        Parameters
        ----------
        page_image  : PIL Image from pdf2image.convert_from_path()
        ocr_output  : OcrOutput from Phase 03 (used for bbox mapping)
        document_id : document identifier
        page_num    : which page this image is (1-indexed)
        doc_type    : document type (only commercial_invoice and packing_list have tables)

        Returns
        -------
        TableExtraction with populated items list.
        If Gemini fails, falls back to mock items with is_mock=True.
        """
        # Only commercial invoices and packing lists have line-item tables
        if doc_type not in ("commercial_invoice", "packing_list", "unknown"):
            logger.info(f"Table extraction skipped for doc_type='{doc_type}'")
            return TableExtraction(document_id=document_id, items=[], total_rows=0,
                                   extraction_method="skipped")

        all_tokens = [tok for page in ocr_output.pages for tok in page.tokens]

        # ── Try Gemini Vision ──────────────────────────────────────────────
        if self._model is not None:
            items = self._extract_with_gemini(page_image, all_tokens, page_num)
            if items:
                return TableExtraction(
                    document_id=document_id,
                    items=items,
                    total_rows=len(items),
                    extraction_method="gemini_vision",
                )
            logger.warning("Gemini returned no rows -- falling back to mock items.")

        # ── Fallback: Mock line items ──────────────────────────────────────
        return self._make_mock_result(document_id, all_tokens, page_num)

    def extract_from_pdf(
        self,
        pdf_path: str,
        ocr_output: OcrOutput,
        document_id: str,
        doc_type: str = "commercial_invoice",
    ) -> TableExtraction:
        """
        Convenience wrapper: converts PDF page to image then calls extract().
        Limits to page 1 only (multi-page tables are out of scope for demo).
        """
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            if not images:
                logger.error(f"No images from {pdf_path}")
                return self._make_mock_result(document_id, [], 1)
            return self.extract(images[0], ocr_output, document_id, page_num=1,
                                doc_type=doc_type)
        except Exception as e:
            logger.error(f"PDF conversion failed for table extraction: {e}")
            return self._make_mock_result(document_id, [], 1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_with_gemini(
        self, page_image, all_tokens: list, page_num: int
    ) -> list[LineItem]:
        """Call Gemini Vision with the table prompt and parse the response."""
        try:
            response = self._model.generate_content([TABLE_EXTRACTION_PROMPT, page_image])
            raw_text = _strip_fences(response.text)
            rows: list[dict] = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Table: Gemini returned non-JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Table: Gemini API error: {e}")
            return []

        if not isinstance(rows, list):
            logger.warning("Table: Gemini returned non-list JSON")
            return []

        line_items: list[LineItem] = []

        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                description = str(row.get("description", "")).strip()
                quantity    = float(row.get("quantity", 0) or 0)
                unit        = str(row.get("unit", "pieces")).strip()
                unit_price  = float(row.get("unit_price", 0) or 0)
                total_price = float(row.get("total_price", 0) or 0)
                row_index   = int(row.get("row_index", len(line_items) + 1))
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping malformed row {row}: {e}")
                continue

            if not description:
                continue

            bbox = _row_bbox(description, all_tokens, page_num)
            # Confidence: full if numeric values look consistent
            if unit_price > 0 and total_price > 0:
                expected = round(quantity * unit_price, 2)
                conf = 0.92 if abs(expected - total_price) < 0.02 * total_price + 0.01 else 0.75
            else:
                conf = 0.70

            line_items.append(LineItem(
                row_index=row_index,
                description=description,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                total_price=total_price,
                page=page_num,
                bbox=bbox,
                confidence=conf,
                is_mock=False,
            ))

        return line_items

    def _make_mock_result(
        self, document_id: str, all_tokens: list, page_num: int
    ) -> TableExtraction:
        """Build a realistic mock TableExtraction for demo fallback."""
        items: list[LineItem] = []
        base_y = 300  # approximate starting y position for table rows in demo PDFs

        for i, row in enumerate(MOCK_LINE_ITEMS):
            # Space mock rows 40px apart so bboxes look plausible on the PDF
            row_y1 = base_y + i * 40
            row_y2 = row_y1 + 35
            items.append(LineItem(
                row_index=row["row_index"],
                description=row["description"],
                quantity=row["quantity"],
                unit=row["unit"],
                unit_price=row["unit_price"],
                total_price=row["total_price"],
                page=page_num,
                bbox=[50, row_y1, 545, row_y2],
                confidence=0.88,
                is_mock=True,
            ))

        logger.info(f"Returning {len(items)} mock line items for '{document_id}'")
        return TableExtraction(
            document_id=document_id,
            items=items,
            total_rows=len(items),
            extraction_method="mock",
        )

    def to_dict(self, result: TableExtraction) -> dict:
        """Serialise TableExtraction to JSON-safe dict (for API response)."""
        return {
            "document_id": result.document_id,
            "total_rows": result.total_rows,
            "extraction_method": result.extraction_method,
            "items": [
                {
                    "row_index": item.row_index,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "page": item.page,
                    "bbox": item.bbox,
                    "confidence": item.confidence,
                    "is_mock": item.is_mock,
                }
                for item in result.items
            ],
        }
