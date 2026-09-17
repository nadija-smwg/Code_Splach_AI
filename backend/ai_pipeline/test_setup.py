# backend/ai_pipeline/test_setup.py
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='en')
result = ocr.ocr('path/to/any/test.pdf', cls=True)

for page in result:
    for line in page:
        bbox = line[0]
        text = line[1][0]
        confidence = line[1][1]
        print(f"Text: {text}, Confidence: {confidence:.2f}, BBox: {bbox}")
