# Clear shipping samples for PaddleOCR

Upload these four PDFs together as one synthetic sea-shipment dossier:

- `commercial_invoice.pdf`
- `packing_list.pdf`
- `bill_of_lading.pdf`
- `delivery_order.pdf`

All parties, identifiers and transactions are fictional. These are clean,
easy-input fixtures, not evidence of accuracy on real scans or a trained model.

## Content and layout

Each PDF is one A4 page with embedded Arial fonts, 12.5-point body text,
21-point document titles, black text on white, generous line spacing, and
one clearly labelled field per line. Tables use separate columns and light
horizontal rules; there are no logos, watermarks, handwriting or rotated text.

The documents share consignee Lanka Apparel Ltd, shipper Meridian Textiles
Ltd, 20 cartons, gross weight 480 KG, and Chennai-to-Colombo routing.
Container identifiers match between the transport and delivery documents.
The invoice goods subtotal is USD 9500; freight USD 400 and insurance USD 100
give a CIF total of USD 10000. Packing weights add to 480 KG gross and
440 KG net, with 40 KG tare. Volume sums to 2.400 CBM.

The revised invoice emphasizes the invoice number, country code `IN`,
Incoterm `CIF`, currency, HS code and total. The CIF delivery place and country
name are printed separately. Numbered goods rows now include an explicit
`meters` unit. Their values and source references are also recorded under
`expected_line_items` in the ground-truth file.

`ground_truth.json` contains 42 expected labelled fields and the complete
printed text. It contains expected data, not fabricated OCR results.

## Reproduce

From the repository root, use a Python environment containing ReportLab:

```powershell
python backend/scripts/generate_ocr_samples.py
```

Run actual OCR using the existing backend environment:

```powershell
& backend/venv/Scripts/python.exe backend/scripts/benchmark_ocr_samples.py
```

The benchmark renders pages at 200 DPI (the application's pdf2image default),
uses real PaddleOCR on CPU, and writes `ocr_benchmark.json`. It supports
PaddleOCR 2.x and 3.x. Orientation correction and unwarping are disabled for
these upright digital pages in the 3.x benchmark. No OpenAI requests, database
writes, mock extraction or pipeline confidence overrides are used.

The report distinguishes:

- Mean OCR token confidence: the model's confidence, not measured accuracy.
- Normalized character error rate: text edit distance against the printed
  ground truth, ignoring case, punctuation and whitespace. Reading order
  still matters. A zero rate does not prove punctuation was perfect.
- Labelled field recovery: exact expected label and value present in OCR
  text after the same normalization. This is not a test of the application's
  downstream entity extractor, tables, reconciliation, or final UI score.
- Keyword document classification: the repository's real keyword classifier,
  using the recognized text. Its confidence is a keyword-ratio heuristic.

There is no before/after benchmark against the existing demo documents;
the layouts are designed to be easy to recognize, and their own measured
results are supplied without claiming a measured improvement over a baseline.

## Measured results (30 September 2026)

PaddleOCR 3.7.0 / PaddlePaddle 3.3.1, PP-OCRv6 medium models, CPU, 200 DPI:

| PDF | Mean token confidence | Normalized CER | Labelled fields | Keyword type confidence |
|---|---:|---:|---:|---:|
| Commercial invoice | 99.78% | 0.00% | 19 / 19 | 49.12% |
| Packing list | 99.84% | 0.00% | 8 / 8 | 87.50% |
| Bill of lading | 99.78% | 0.00% | 9 / 9 | 77.06% |
| Delivery order | 99.76% | 0.00% | 6 / 6 | 52.38% |

Across 119 OCR tokens, mean confidence was 99.80%. All 42 labelled fields
were recovered and all four winning keyword document types were correct.
Low keyword confidence on the invoice and delivery order reflects shared
document terminology, despite near-perfect OCR. Full raw text, boxes,
scores and field-level results are retained in `ocr_benchmark.json`.

The separate repository PDF entry-point test returned zero pages and zero
tokens, logging `string index out of range`. The current nested-list parser
is incompatible with the installed PaddleOCR 3.x prediction objects. The
benchmark uses a version-aware adapter; application uploads need their OCR
integration aligned with the installed version to reproduce these results.

## Repository review relevant to accuracy

Reviewed the repository file inventory, Python syntax, existing PDFs and
generators, OCR integration and test entry points, classifier, entity/table
extraction, party-role evidence, normalization/scoring flow, dossier upload,
review UI, requirements, team overview and project documentation. This was
an OCR-focused review, not a full security or frontend behavior audit.

1. `generate_fake_pdfs.py` writes the same single-line fake document to
   multiple filenames. Do not use that generator for accuracy evaluation.
   Existing PDFs were inspected and were not overwritten.
2. Installed versions are PaddleOCR 3.7.0 and PaddlePaddle 3.3.1, while
   `backend/requirements.txt` pins 2.7.0.3 and 2.6.2. The repository's
   `OcrEngine.extract()` expects the old nested-list result. PaddleOCR 3.x
   returns prediction objects. Its actual PDF entry-point result is recorded
   separately in `ocr_benchmark.json`; the sample layout cannot fix API drift.
3. `pipeline.py` does not populate `ocr_confidence` or `bbox_match_ratio` in
   the entity dictionaries passed to `ConfidenceScorer`. Default inputs yield
   approximately 0.80 without a normalization warning; the score is capped
   at 0.95. Better OCR therefore need not raise the displayed entity score.
4. `_LOCAL_CONFIDENCE_GATE = 1.10` in `entity_extractor.py` exceeds the
   normal confidence range, routing fields to model fallback. Clear PDFs
   cannot remove that application setting or guarantee model extraction.
5. Commercial documents share keywords such as weights, cartons, and ports.
   The classifier normalizes keyword-hit fractions across document types;
   its classification confidence is separate from OCR confidence. Complete
   document fields were retained rather than removed to inflate that score.

No production pipeline, model weights, requirements, existing demo PDFs,
cached dossier output, or UI scores were changed for these samples.

## Addressing the export-blocked screenshot

The six invoice fields marked **pending** are already extracted; they have
only one source assertion. PDF changes cannot approve an existing dossier.
Adding the same text repeatedly or uploading another copy is not independent
corroboration. Re-upload the revised samples into a new dossier to process the
changed evidence, then use the existing review workflow:

1. Open **Review Workspace / Key Field Reconciliation**, expand each pending
   field, inspect the source and choose **Use [value]**. For this fictional
   fixture the values are invoice `INV-2026-0930`, total `10000.00`, currency
   `USD`, Incoterm `CIF`, country code `IN`, and HS code `520812`. Saved source
   decisions mark the fields resolved without inventing corroboration.
2. Under **CUSDEC export / Source-referenced goods**, enter the two printed
   rows if automatic table extraction did not save them. The current pipeline
   does not include table results in its document output.

   | Description | Quantity | Unit | Unit price | Line total | Source reference |
   |---|---:|---|---:|---:|---|
   | Cotton Fabric A | 1200 | meters | 4.75 | 5700.00 | commercial_invoice.pdf, page 1, goods row 1 (INV-2026-0930) |
   | Cotton Fabric B | 800 | meters | 4.75 | 3800.00 | commercial_invoice.pdf, page 1, goods row 2 (INV-2026-0930) |

   These goods totals are USD 9500; the separate freight and insurance amounts
   bring the invoice total to USD 10000. The test documents are fictional.
3. Fill **Declaration details** with the applicable consignee and declarant
   codes/TINs, exporter code, declarant name, clearance office code, declaration
   type, procedure code, manifest reference, transport mode, container flag
   and exchange rate. These 11 values come from the declaration profile,
   not the PDF extractor. No registration identifiers or exchange rates were
   fabricated to clear the gate. Use an appropriate test profile for a demo.
4. Select **Refresh checks** after saving the source decisions, goods rows
   and profile. The export gate still checks all requirements.
