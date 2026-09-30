"""Measure real PaddleOCR on generated PDFs without OpenAI calls or mocks.

Run: backend/venv/Scripts/python.exe backend/scripts/benchmark_ocr_samples.py
Supports the installed PaddleOCR 3.x and the project's pinned 2.x version.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import re
import statistics
import sys
import time

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("FLAGS_use_onednn", "0")

from pdf2image import convert_from_path
import numpy as np
from paddleocr import PaddleOCR

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "output/pdf/ocr_samples"
sys.path.insert(0, str(ROOT / "backend"))


def normalize(text):
    """Ignore whitespace, punctuation and case only; retain every letter/digit."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def reading_order(tokens):
    """Group tokens by vertical center, then read each row left to right."""
    rows = []
    for token in sorted(tokens, key=lambda t: (t["bbox"][1] + t["bbox"][3]) / 2):
        center = (token["bbox"][1] + token["bbox"][3]) / 2
        if not rows or abs(center - rows[-1][0]) > 14:
            rows.append((center, [token]))
        else:
            rows[-1][1].append(token)
    return "\n".join(" ".join(t["text"] for t in sorted(row, key=lambda t: t["bbox"][0]))
                     for _, row in rows)


def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for index, char in enumerate(a, 1):
        current = [index]
        for other_index, other in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[other_index] + 1,
                               previous[other_index - 1] + (char != other)))
        previous = current
    return previous[-1]


def extract(engine, image, major):
    tokens = []
    if major >= 3:
        prediction = next(iter(engine.predict(np.asarray(image))))
        data = prediction.json
        if callable(data):
            data = data()
        if isinstance(data, str):
            data = json.loads(data)
        data = data.get("res", data)
        for text, score, box in zip(data["rec_texts"], data["rec_scores"], data["rec_boxes"]):
            tokens.append({"text": text, "confidence": float(score),
                           "bbox": [float(v) for v in box]})
    else:
        result = engine.ocr(np.asarray(image), cls=True)
        for box, (text, score) in (result[0] or []):
            tokens.append({"text": text, "confidence": float(score),
                           "bbox": [min(p[0] for p in box), min(p[1] for p in box),
                                    max(p[0] for p in box), max(p[1] for p in box)]})
    return tokens


def main():
    version = importlib.metadata.version("paddleocr")
    major = int(version.split(".")[0])
    kwargs = {"lang": "en"}
    if major >= 3:
        kwargs.update(use_doc_orientation_classify=False, use_doc_unwarping=False,
                      use_textline_orientation=False, device="cpu", cpu_threads=4,
                      enable_mkldnn=False)
    else:
        kwargs.update(use_angle_cls=True, use_gpu=False, show_log=False)
    print(f"Initializing real PaddleOCR {version}", flush=True)
    engine = PaddleOCR(**kwargs)
    from ai_pipeline.classifier import KeywordClassifier
    from ai_pipeline.ocr_engine import OcrToken, OcrPage, OcrOutput, OcrEngine
    manifest = json.loads((DIRECTORY / "ground_truth.json").read_text(encoding="utf-8"))
    report = {"paddleocr_version": version, "paddlepaddle_version": importlib.metadata.version("paddlepaddle"),
              "raster_dpi": 200, "engine": "real PaddleOCR CPU; no mocks or API extraction",
              "metric_note": "CER ignores case/whitespace/punctuation, includes reading order. Field recovery checks the labelled value in OCR text; it is not end-to-end entity extraction accuracy.",
              "documents": []}
    for document in manifest["documents"]:
        start = time.perf_counter()
        path = DIRECTORY / document["file"]
        images = convert_from_path(str(path), dpi=200)
        assert len(images) == 1
        tokens = extract(engine, images[0], major)
        text = reading_order(tokens)
        actual, expected = normalize(text), normalize("\n".join(document["expected_lines"]))
        fields = {}
        for key, field in document["expected_fields"].items():
            target = normalize(f"{field['label']}: {field['value']}")
            fields[key] = {"expected": field["value"], "label_and_value_recovered": target in actual}
        recovered = sum(f["label_and_value_recovered"] for f in fields.values())
        ocr_output = OcrOutput(str(path), 1, [OcrPage(1, images[0].width, images[0].height,
            [OcrToken(t["text"], 1, t["bbox"], t["confidence"]) for t in tokens])])
        classification = KeywordClassifier().classify(ocr_output)
        errors = edit_distance(expected, actual)
        result = {"file": document["file"], "token_count": len(tokens),
                  "mean_ocr_confidence": statistics.mean(t["confidence"] for t in tokens) if tokens else 0,
                  "normalized_character_error_rate": errors / len(expected),
                  "normalized_character_edits": errors, "expected_character_count": len(expected),
                  "labelled_fields_recovered": recovered, "expected_field_count": len(fields),
                  "fields": fields, "keyword_document_type": classification.document_type,
                  "keyword_classification_confidence": classification.confidence,
                  "expected_document_type": document["document_type"],
                  "elapsed_seconds": round(time.perf_counter() - start, 2),
                  "recognized_text": text, "tokens": tokens}
        report["documents"].append(result)
        print(f"{document['file']}: confidence={result['mean_ocr_confidence']:.4%}, "
              f"CER={result['normalized_character_error_rate']:.4%}, "
              f"fields={recovered}/{len(fields)}, type={classification.document_type}", flush=True)
        (DIRECTORY / "ocr_benchmark.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # Exercise the repository's current PDF entry point as well. Reuse the model
    # to avoid expensive initialization; distinguish compatibility from layout.
    repository_engine = OcrEngine.__new__(OcrEngine)
    repository_engine.ocr = engine
    original = repository_engine.extract(str(DIRECTORY / "commercial_invoice.pdf"))
    report["repository_pdf_entry_point"] = {
        "total_pages": original.total_pages,
        "tokens": sum(len(p.tokens) for p in original.pages),
        "compatible": original.total_pages > 0 and any(p.tokens for p in original.pages),
        "note": "Repository OcrEngine.extract tested separately; see console for errors."}
    (DIRECTORY / "ocr_benchmark.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
