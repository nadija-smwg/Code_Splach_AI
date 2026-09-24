# backend/ai_pipeline/confidence.py
# Phase 08 — Confidence Scoring
# Blends OCR confidence with extraction quality signals into a
# single per-entity extraction_confidence score.

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """
    Assigns a final extraction_confidence to each extracted entity.

    Scoring factors:
      - ocr_confidence  : how clearly the OCR read the token
      - bbox_match_ratio: how closely the Gemini value matched an OCR token
      - warn_penalty    : normalization warning reduces confidence slightly
    """

    # Weights must sum to 1.0
    _W_OCR = 0.55
    _W_BBOX = 0.35
    _W_WARN = 0.10

    def score_entity(
        self,
        ocr_confidence: float,
        bbox_match_ratio: float,
        normalization_warning: bool = False,
    ) -> float:
        """
        Compute blended extraction confidence.

        Args:
            ocr_confidence:       Raw OCR token confidence [0.0 – 1.0]
            bbox_match_ratio:     Similarity ratio between Gemini value
                                  and best-matching OCR token [0.0 – 1.0]
            normalization_warning: True if normalizer set warn=True

        Returns:
            Blended confidence score [0.0 – 1.0], rounded to 2 dp.
        """
        warn_factor = 0.85 if normalization_warning else 1.0

        raw = (
            self._W_OCR * float(ocr_confidence)
            + self._W_BBOX * float(bbox_match_ratio)
            + self._W_WARN * warn_factor
        )

        return round(min(max(raw, 0.0), 0.95), 2)

    def score_entities(self, entities: list[dict]) -> list[dict]:
        """
        Add / overwrite extraction_confidence on every entity in the list.
        Expects entities to already have: ocr_confidence, bbox_match_ratio,
        normalization_warning (all optional with sensible defaults).
        """
        for entity in entities:
            try:
                score = self.score_entity(
                    ocr_confidence=entity.get("ocr_confidence", 0.8),
                    bbox_match_ratio=entity.get("bbox_match_ratio", 0.75),
                    normalization_warning=entity.get(
                        "normalization_warning", False
                    ),
                )
                entity["extraction_confidence"] = score
            except Exception as exc:
                logger.warning(
                    "Confidence scoring failed for entity %s: %s",
                    entity.get("entity_type"),
                    exc,
                )
                entity["extraction_confidence"] = 0.5

        return entities
