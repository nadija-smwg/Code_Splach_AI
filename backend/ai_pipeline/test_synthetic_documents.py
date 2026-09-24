# backend/ai_pipeline/test_synthetic_documents.py
import json
from pathlib import Path
import sys

# Adjust path so we can import from ai_pipeline if run directly
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai_pipeline.pipeline import get_pipeline

pipeline = get_pipeline()

TEST_DIR = backend_dir.parent / "test_data" / "synthetic"
TEST_DIR.mkdir(parents=True, exist_ok=True)
results = {}

for pdf_path in sorted(TEST_DIR.glob("*.pdf")):
    document_id = pdf_path.stem

    print(f"\nProcessing: {pdf_path.name}")

    result = pipeline.process_document(
        pdf_path=str(pdf_path),
        document_id=document_id,
    )

    print(f"  Type: {result['document_type']} ({result['classification_confidence']:.0%})")
    print(f"  Entities: {len(result['entities'])}")
    print(f"  Processing time: {result['processing_time_ms']} ms")
    print(f"  Errors: {result['errors']}")

    results[pdf_path.name] = result

out_path = backend_dir.parent / "test_results.json"
out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

print(f"\n✅ Synthetic test results saved to {out_path.name}")
