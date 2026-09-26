# backend/ai_pipeline/pipeline.py
# Phase 10 — Pipeline Orchestration
#
# Steps:
#   1. OCR              — PaddleOCR bounding-box extraction
#   2. Classification   — DocumentClassifier → document_type
#   3. Page Images      — PDF → PIL images for Gemini Vision
#   4. Entity Extraction + BBox Mapping + Normalization (per page, per entity)
#   5. Entity Deduplication / Validation
#   6. Raw OCR compilation for Kaveen Layer 1 XAI
#   7. Master Result Assembly
#
# Error policy: NEVER raises. All failures are caught and appended to errors[].

import logging
import time
from pathlib import Path

from .ocr_engine import OcrEngine
from .classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .normalizer import EntityNormalizer
from .confidence import ConfidenceScorer

logger = logging.getLogger(__name__)


class AIPipeline:

    def __init__(self):
        self.ocr = OcrEngine()
        self.classifier = DocumentClassifier()
        self.extractor = EntityExtractor()
        self.normalizer = EntityNormalizer()
        self.scorer = ConfidenceScorer()

    def process_document(
        self,
        pdf_path: str,
        document_id: str,
    ) -> dict:
        """
        Master pipeline: PDF → structured ExtractionResult.
        This is the ONLY function the rest of the system should call.

        Returns:
            {
                "document_id":                str,
                "document_type":              str,
                "classification_confidence":  float,
                "classification_evidence":    list[str],
                "entities":                   list[dict],
                "raw_ocr":                    list[dict],
                "processing_time_ms":         int,
                "errors":                     list[str],
            }
        """
        start_time = time.perf_counter()

        errors: list[str] = []
        warnings: list[str] = []
        all_entities: list[dict] = []

        # Resolve path once to avoid surprises with relative paths
        pdf_path = str(Path(pdf_path).resolve())

        # ============================================================
        # STEP 1 — OCR
        # ============================================================

        try:
            ocr_result = self.ocr.extract(pdf_path)

        except Exception as exc:
            logger.exception(
                "OCR failed for document=%s", document_id
            )
            return self._error_result(
                document_id, f"OCR failed: {exc}"
            )

        # ============================================================
        # STEP 2 — CLASSIFICATION
        # ============================================================

        try:
            classification = self.classifier.classify(ocr_result)

        except Exception as exc:
            logger.exception(
                "Classification failed for document=%s", document_id
            )
            errors.append(f"Classification failed: {exc}")
            classification = None

        if classification is None:
            document_type = "unknown"
            classification_confidence = 0.0
            classification_evidence: list[str] = []
        else:
            document_type = classification.document_type
            classification_confidence = float(classification.confidence)
            classification_evidence = list(
                getattr(classification, "evidence", []) or []
            )

        # ============================================================
        # STEP 3 — PAGE IMAGES (needed by Gemini Vision extractor)
        # ============================================================

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)

        except Exception as exc:
            logger.exception("PDF image conversion failed for document=%s", document_id)
            errors.append(f"Image conversion failed: {exc}")
            images = []

        # ============================================================
        # STEP 4 — ENTITY EXTRACTION + BBOX MAPPING + NORMALIZATION
        # The extractor handles all pages internally. We call it once
        # with the full ocr_result and classification objects.
        # ============================================================

        if document_type != "unknown":
            try:
                extraction_result, _telemetry = self.extractor.extract(
                    ocr_output=ocr_result,
                    classification=classification,
                    pdf_path=pdf_path,
                    document_id=document_id,
                )
                extracted_entities = extraction_result.entities
                if hasattr(extraction_result, "warnings") and extraction_result.warnings:
                    warnings.extend(extraction_result.warnings)  # list[ExtractedEntity]

            except Exception as exc:
                logger.exception(
                    "Entity extraction failed document=%s", document_id
                )
                errors.append(f"Entity extraction failed: {exc}")
                extracted_entities = []

            # ── 4b: Normalize each entity individually ───────────────
            # Each entity is wrapped in its own try/except so one
            # bad entity cannot abort the rest.
            for entity_obj in extracted_entities:

                # Serialise the dataclass to a plain dict for the pipeline contract
                entity: dict = {
                    "entity_type":             entity_obj.entity_type,
                    "value":                   entity_obj.value,
                    "normalized_value":        entity_obj.normalized_value,
                    "unit":                    entity_obj.unit,
                    "page":                    entity_obj.page,
                    "bbox":                    entity_obj.bbox,
                    "extraction_confidence":   entity_obj.extraction_confidence,
                    "party_role":              entity_obj.party_role,
                    "resolver_eligible":       entity_obj.resolver_eligible,
                    "classification_confidence": classification_confidence,
                    "normalization_warning":   False,
                }

                try:
                    norm = self.normalizer.normalize(
                        entity["entity_type"],
                        entity["value"],
                    )
                    entity["normalized_value"]      = norm.get("normalized_value")
                    entity["unit"]                  = norm.get("unit")
                    entity["normalization_warning"] = norm.get("warn", False)

                except Exception as exc:
                    logger.exception(
                        "Normalization failed for entity=%r", entity
                    )
                    entity["normalized_value"]      = None
                    entity["unit"]                  = None
                    entity["normalization_warning"] = True
                    errors.append(f"Normalization failed for {entity['entity_type']}: {exc}")

                all_entities.append(entity)

        # ── 4c: ConfidenceScorer — blended scoring across all entities ──
        try:
            all_entities = self.scorer.score_entities(all_entities)
        except Exception as exc:
            logger.warning("Confidence scoring failed: %s", exc)

        # ============================================================
        # STEP 5 — ENTITY DEDUPLICATION / VALIDATION
        # Removes true duplicates (same entity_type + normalized_value).
        # Does NOT merge entities with different values — those are real
        # conflicts that Aloka's reasoning engine needs to compare.
        # ============================================================

        all_entities = self._deduplicate_entities(all_entities)

        # ============================================================
        # STEP 6 — RAW OCR for Kaveen (Layer 1 XAI — bbox overlay)
        # ============================================================

        raw_ocr: list[dict] = []
        try:
            for page in ocr_result.pages:
                for token in page.tokens:
                    raw_ocr.append({
                        "text": token.text,
                        "page": token.page,
                        "bbox": token.bbox,
                        "ocr_confidence": token.confidence,
                    })
        except Exception as exc:
            logger.warning("Raw OCR compilation failed: %s", exc)

        # ============================================================
        # STEP 7 — MASTER RESULT ASSEMBLY
        # ============================================================

        processing_time_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "document_id": document_id,
            "document_type": document_type,
            "classification_confidence": classification_confidence,
            "classification_evidence": classification_evidence,
            "entities": all_entities,
            "raw_ocr": raw_ocr,
            "processing_time_ms": processing_time_ms,
            "errors": errors,
        }

    # ============================================================
    # ENTITY DEDUPLICATION
    # ============================================================

    def _deduplicate_entities(self, entities: list[dict]) -> list[dict]:
        """
        Remove true duplicate entities — same entity_type AND same
        normalized_value. When duplicates exist, keep the one with the
        highest extraction_confidence.

        IMPORTANT: entities with DIFFERENT values (e.g. GROSS_WEIGHT=450
        from invoice vs GROSS_WEIGHT=448 from AWB) are NOT deduplicated.
        Those are genuine conflicts that Aloka needs to compare.
        """
        grouped: dict[tuple, dict] = {}

        for entity in entities:
            entity_type = entity.get("entity_type")
            normalized = entity.get("normalized_value")
            raw_value = entity.get("value")

            # Use normalized when available; fall back to raw
            comparison_value = (
                normalized if normalized is not None else raw_value
            )

            key = (entity_type, str(comparison_value))

            existing = grouped.get(key)

            if existing is None:
                grouped[key] = entity
                continue

            # Duplicate found — keep higher confidence
            current_conf = float(
                entity.get("extraction_confidence", 0.0)
            )
            existing_conf = float(
                existing.get("extraction_confidence", 0.0)
            )

            if current_conf > existing_conf:
                grouped[key] = entity

        return list(grouped.values())

    # ============================================================
    # ERROR RESULT — returned on unrecoverable OCR failure
    # ============================================================

    def _error_result(self, document_id: str, error: str) -> dict:
        return {
            "document_id": document_id,
            "document_type": "unknown",
            "classification_confidence": 0.0,
            "classification_evidence": [],
            "entities": [],
            "raw_ocr": [],
            "processing_time_ms": 0,
            "errors": [error],
            "warnings": [],
        }


# ================================================================
# SINGLETON — models are initialized once and reused across requests
# ================================================================

_pipeline_instance: AIPipeline | None = None


def get_pipeline() -> AIPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = AIPipeline()
    return _pipeline_instance
