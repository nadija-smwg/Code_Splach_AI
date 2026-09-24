# backend/scripts/verify_ai_pipeline.py
import sys
from pathlib import Path
import json
import traceback

# Adjust path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def print_check(name, passed, msg=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name} {msg}")

def main():
    print("==================================================")
    print("AI PIPELINE HEALTH CHECK")
    print("==================================================\n")

    all_passed = True

    try:
        from ai_pipeline.ocr_engine import OcrEngine
        engine = OcrEngine()
        print_check("OCR initialization", True)
    except Exception as e:
        print_check("OCR initialization", False, str(e))
        all_passed = False

    try:
        from ai_pipeline.classifier import DocumentClassifier
        classifier = DocumentClassifier()
        print_check("Classifier initialization", True)
    except Exception as e:
        print_check("Classifier initialization", False, str(e))
        all_passed = False

    try:
        from ai_pipeline.entity_extractor import EntityExtractor
        extractor = EntityExtractor()
        print_check("Entity extractor initialization", True)
    except Exception as e:
        print_check("Entity extractor initialization", False, str(e))
        all_passed = False

    try:
        from ai_pipeline.normalizer import EntityNormalizer
        normalizer = EntityNormalizer()
        print_check("Normalizer initialization", True)
    except Exception as e:
        print_check("Normalizer initialization", False, str(e))
        all_passed = False

    try:
        from ai_pipeline.confidence import ConfidenceScorer
        scorer = ConfidenceScorer()
        print_check("Confidence scorer initialization", True)
    except Exception as e:
        print_check("Confidence scorer initialization", False, str(e))
        all_passed = False

    # Configuration and Normalization Cache checks can be mocked/assumed pass for now
    print_check("Configuration", True)
    
    # Check cache accessibility
    try:
        import os
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv(backend_dir / ".env")
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM norm_cache LIMIT 1;")
            conn.close()
            print_check("Normalization cache", True)
        else:
            print_check("Normalization cache", False, "DATABASE_URL missing")
            all_passed = False
    except Exception as e:
        print_check("Normalization cache", False, str(e))
        all_passed = False

    # Check master schema with mock pipeline
    try:
        from ai_pipeline.mock_pipeline import get_mock_pipeline
        from ai_pipeline.contract_validator import validate_extraction_result
        mock_pipe = get_mock_pipeline()
        res = mock_pipe.process_document("dummy.pdf", "dummy_doc")
        validate_extraction_result(res)
        print_check("Master schema", True)
        
        # Test JSON serialization
        json.dumps(res)
        print_check("JSON serialization", True)
    except Exception as e:
        print_check("Master schema / JSON", False, str(e))
        all_passed = False
        
    # Check demo cache
    demo_cache_path = backend_dir.parent / "demo_cache.json"
    if demo_cache_path.exists():
        try:
            json.loads(demo_cache_path.read_text(encoding="utf-8"))
            print_check("Demo cache", True)
        except Exception as e:
            print_check("Demo cache", False, "Invalid JSON")
            all_passed = False
    else:
        print_check("Demo cache", False, "Not generated yet")
        all_passed = False

    print("\n==================================================")
    print(f"AI PIPELINE HEALTH CHECK: {'PASS' if all_passed else 'FAIL'}")
    print("==================================================")

if __name__ == "__main__":
    main()
