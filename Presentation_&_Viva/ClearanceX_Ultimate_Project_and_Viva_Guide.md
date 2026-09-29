# ClearanceX: finalist project and viva guide

**Team Ants · CodeSplash’26 · University of Moratuwa**  
**Format:** 10-minute English presentation + 10-minute English viva  
**Review date:** 30 September 2026  
**Code baseline:** `83ef75c`, plus the supplied title slide. This guide describes the reviewed code, not a certification of production readiness.

> Your most defensible message: **ClearanceX helps a shipping executive reconcile conflicting document evidence before preparing a customs declaration. It preserves the sources and keeps the reviewer in control.**

## How to use this pack

1. Read sections 1–5 to understand the complete system.
2. Rehearse with `ClearanceX_10_Minute_Presentation_Script.md` and the PowerPoint speaker notes.
3. Study the limitations in section 7 before memorizing the Q&A. Knowing where the prototype stops is part of knowing the project.
4. Use `ClearanceX_Demo_and_Final_Day_Checklist.md` for the live demonstration.
5. Practise section 10 with a teammate interrupting and asking follow-up questions. Answer the question first, then offer evidence.

The code review did **not** change the application. Findings below remain open unless the team subsequently fixes and retests them. No competition result can be promised. A precise explanation and a repeatable demo give you a much stronger case than inflated claims.

## 1. The project in language you can say aloud

### One sentence

“ClearanceX is an explainable document reconciliation assistant that helps shipping teams identify and resolve inconsistencies before preparing a customs declaration.”

### Thirty seconds

“A shipment arrives with an invoice, a packing list, and a transport document. Each document describes the same shipment, but the values may disagree. ClearanceX extracts those values, links them to their source documents, and compares them at shipment level. When it finds a conflict, it shows the evidence and the rule that failed. A reviewer chooses the verified value, and the application checks whether the declaration has enough information for XML export.”

### Why the problem matters

The target user is a shipping executive, freight forwarder, or customs broker preparing a declaration from several independently produced documents. The difficult step is deciding whether the evidence is consistent and complete. The prototype focuses on apparel-related shipping dossiers, with English PDFs as its practical input scope.

Avoid the README’s assertion that the whole customs process is “entirely manual.” Sri Lanka Customs already operates ASYCUDA World and has published a paperless submission pilot. Our product opportunity is the **upstream preparation and reconciliation work**, not replacing a nonexistent digital customs system. Sources: [Sri Lanka Customs ICT Directorate](https://www.customs.gov.lk/about-us/directorates-and-divisions/ict-directorate/) and [paperless CusDec pilot announcement](https://www.customs.gov.lk/sri-lanka-customs-launches-pilot-program-on-paperless-submission-of-customs-declarations/).

### The project’s strongest technical contribution

The code represents an extracted value as a **source assertion**, distinct from a **canonical shipment field**. It can propose a consensus without deleting the disagreeing evidence. This gives the reviewer a traceable basis for deciding what to use.

For example:

| Document | Gross weight | Role in the example |
|---|---:|---|
| Commercial invoice | 450.00 kg | Supports proposed consensus |
| Packing list | 450.00 kg | Supports proposed consensus |
| Air waybill | 448.50 kg | Outlying assertion |

The proposed consensus is 450.00 kg. The difference is 1.50 kg. **Two agreeing documents do not prove physical truth.** The reviewer must check authoritative evidence or the issuer before accepting a correction. This is a repository test/demo example, not a real customer case or an accuracy benchmark.

## 2. Complete workflow

| Stage | What actually happens | Important boundary |
|---|---|---|
| Upload | React sends multiple PDFs to `POST /api/upload`. The API saves them and schedules background processing. | One dossier is assumed to represent one shipment. |
| OCR | PaddleOCR produces text tokens, page numbers, bounding boxes, and token confidence. | Poor scans and layout ambiguity still affect extraction. |
| Classification | The active pipeline invokes a keyword/signature classifier. | A legacy Gemini fallback exists, but this call does not provide the PDF path needed to use it. |
| Extraction | Local label/regex rules run first. OpenAI vision fallback attempts missing header fields. | The missing-field vision fallback uses page 1. It is not a fully validated multipage table pipeline. |
| Party-role checks | Spatial labels and name heuristics distinguish consignee from carrier, bank, shipper, and other roles. | Heuristics can misclassify unfamiliar names and layouts. |
| Normalization | Weights, numeric formats, identifiers, and other values become comparable. Semantic normalization can use a database cache and model fallback. | Preserve units and raw evidence. Normalization errors can affect later decisions. |
| Confidence scoring | A weighted heuristic overwrites each entity’s confidence. | The current pipeline omits some expected inputs, so defaults can dominate. |
| Storage | Dossiers and document extraction JSON go into PostgreSQL. | Availability and error handling need hardening. |
| Resolution | Assertions cluster into a canonical field. Most corroborated value wins, then confidence sum breaks ties. | Consensus is a proposal, not authority. |
| Knowledge graph | NetworkX links shipment, fields, documents, and assertions. | An in-memory evidence graph, not a graph neural network or graph database. |
| Discrepancy evaluation | Rules identify outlying numeric or string values and produce structured failures. | Current numeric equality tolerance is absolute `0.01`, not the README’s ±1%. |
| Explanation | The XAI compiler emits provenance, rule steps, confidence, and a counterfactual. | The explanation is a trace of application logic, not access to a model’s internal reasoning. |
| Human review | A reviewer chooses a source assertion or enters a normalized value, optionally with a reason. | Saved `resolved_by` is currently a generic `reviewer`, not an authenticated identity. |
| Readiness | Required evidence, declaration metadata, and goods rows determine export blockers. | Passing this local gate does not establish official customs acceptance. |
| Export | ElementTree builds XML using the repository’s user-confirmed compatibility template. | No live ASYCUDA submission or official acceptance test was verified. |

## 3. Architecture you should be able to explain on a whiteboard

```text
Browser: React + TypeScript
  Dossiers / Review / Key fields / Discrepancies / Graph / Export
                         |
                    REST via Axios
                         |
FastAPI API and in-process BackgroundTasks
  Upload -> OCR -> classify -> extract -> normalize -> store
                         |
PostgreSQL: dossier records, JSON extraction, reviewer resolutions,
            declaration metadata, goods rows, normalization cache
                         |
Canonical resolver -> NetworkX graph -> RuleEvaluator -> XAICompiler
                         |
Reviewer decision -> readiness blockers -> compatibility XML download

External model requests occur only on relevant configured fallback paths.
```

### Why these choices are reasonable

**React and TypeScript:** The review workflow needs coordinated document, field, and graph views. Types help maintain the frontend/backend contract, although runtime API validation is still necessary.

**FastAPI:** Convenient Python integration with OCR and reasoning code, typed request tooling, and API documentation. An `async` endpoint does not automatically make synchronous database or OCR work nonblocking.

**PaddleOCR:** Provides local text and geometry. Geometry makes it possible to associate values with labels and document regions. We integrate a pretrained OCR engine; we did not train PaddleOCR.

**Local rules plus model fallback:** Label patterns handle predictable fields. A model can help when patterns miss information. This design aims to reduce unnecessary model requests, but a cost saving percentage needs measured telemetry.

**PostgreSQL:** Durable workflow and reviewer records, plus JSON/JSONB for variable extraction structures. The application uses both SQLAlchemy and psycopg2 paths, which increases integration and transaction complexity.

**NetworkX:** A simple way to preserve and traverse evidence relationships for a prototype. PostgreSQL stores business records; NetworkX builds a working graph. A graph database is a future option if graph size and queries justify it.

**Docker Compose:** Describes frontend, backend, and PostgreSQL services for evaluator setup. The local hackathon instructions require Docker and a reproducible README, and say external deployment is unnecessary. A Compose file alone is not proof that a clean build succeeds.

### Main API map

| Endpoint | Purpose |
|---|---|
| `POST /api/upload` | Accept dossier PDFs and start background processing |
| `GET /api/upload/{id}/status` | Poll dossier/document status |
| `GET /api/dossiers` | List stored dossiers |
| `GET /api/shipments/{id}/extraction` | Read extraction evidence |
| `GET /api/shipments/{id}/key-fields` | Read canonical values and assertions |
| `GET /api/shipments/{id}/graph` | Read visualization nodes and edges |
| `GET /api/shipments/{id}/discrepancies` | Read rule failures and XAI blocks |
| `POST /api/shipments/{id}/field-resolutions` | Save reviewer choice |
| `POST /api/shipments/{id}/declaration-metadata` | Save declarant/profile values |
| `POST /api/shipments/{id}/cusdec-line-items` | Save manually verified goods row |
| `GET /api/shipments/{id}/cusdec-readiness` | Explain export blockers |
| `GET /api/shipments/{id}/asycuda-export` | Return XML or reject blocked export |

The frontend still has a legacy upload fallback on any error. Know this distinction when troubleshooting: an HTTP response is not proof of successful extraction.

## 4. The reasoning core in detail

### Canonical field versus source assertion

A canonical field means “gross weight for shipment X.” An assertion means “document Y says gross weight is 448.5 kg on page 1 at this bounding box.” The assertion retains raw and normalized values and confidence. A reviewer override changes the resolved value while keeping the source assertions.

Graph relationships include `HAS_FIELD`, `CONTAINS`, and `ASSERTS_VALUE_FOR`. The active graph contains `shipment`, `document`, `canonical_field`, and `source_assertion` nodes. Some legacy paths retain `MUST_MATCH` edges for compatibility.

### Consensus algorithm

1. Group eligible entities by canonical entity type.
2. Cluster numeric values within an absolute difference of `0.01`; compare text after lowercasing and removing non-alphanumeric characters.
3. Select the largest cluster. Use the summed extraction confidence to break cluster-size ties.
4. Preserve every assertion and label outliers.
5. Set `pending` for a single assertion, `match` for agreement, `conflict` for disagreement, or `warning` for matching numbers with differing nonempty units.
6. Overlay saved manual decisions as `resolved`.

Tie-breaking can still depend on input order when size and confidence sum tie. Repeated/copied documents can create false corroboration because the algorithm counts assertions rather than independent sources. It also does not solve matching of individual goods rows.

### Rule evaluation

`RuleEvaluator` evaluates conflicting canonical fields. Numeric discrepancies use `RULE_001_NUMERIC_MATCH` and an absolute `0.01` tolerance. String discrepancies use `RULE_002_STRING_MATCH`; similarity of at least `0.85` suppresses a failure. The similarity path uses configured embeddings with a Jaccard fallback.

The resolver and evaluator do not apply identical text equivalence rules. A field can remain `conflict` in the canonical view while the semantic evaluator produces no discrepancy. Export readiness looks at the field status, so a “no discrepancies” view does not necessarily mean “ready to export.”

### The four XAI layers

| Layer | Example | What it does not prove |
|---|---|---|
| Provenance | Invoice and AWB source IDs, snippets, bounding boxes | That OCR read the physical document correctly |
| Rule explanation | Compare 450.0 with 448.5; numeric difference 1.5 | A legal violation or hidden model reasoning |
| Confidence | Product of the two entity confidence scores | Calibrated probability that a declaration is correct |
| Counterfactual | A value change of +1.5 would make the selected pair agree | Permission to alter an issuer’s document or proof which source is right |

Say: “The counterfactual describes the mathematical condition for agreement. The user must verify the factual correction.”

### Confidence mathematics

The scorer computes `0.55 × OCR + 0.35 × bbox_match + 0.10 × warning_factor`, rounds to two decimals, and caps the result at `0.95`. The warning factor is `1.0`, or `0.85` when normalization warns.

The pipeline currently does not put `ocr_confidence` and `bbox_match_ratio` into the dictionary passed to this scorer. Defaults of `0.8` and `0.75` therefore yield `0.8025`, rounded to `0.80`, when there is no warning. The XAI compiler then multiplies entity scores, for example `0.80 × 0.80 = 0.64`.

These are **heuristic indicators**. Calling the product a statistically valid joint probability would require calibration and an independence argument that the implementation does not supply. Confidence, severity, and source authority are different ideas.

## 5. Export: the accurate explanation

The readiness module currently requires **12 extracted header fields**: invoice number, consignee, shipper, amount, currency, Incoterm, gross weight, package count, country of origin, loading port, discharge port, and HS code. It also requires **11 declaration/profile fields**, an AWB or B/L field, and goods rows.

Single-source required fields remain pending until reviewed or corroborated. Required fields with conflict, warning, or pending status block export. The API returns HTTP 422 when blockers remain. This is a useful implementation of a human review checkpoint.

The serializer declares `TEMPLATE_VERSION = "user-confirmed-asycuda-template-v1"`. It writes an `ASYCUDA` root with identification, trader, declarant, transport, financial, and item sections. It has a structure test. **That is compatibility-template serialization, not official XSD validation or proof of Sri Lanka Customs acceptance.**

Important remaining gaps include per-item HS code and weight allocation, line-total reconciliation, finite numeric validation, metadata code-list checks, and fields required by readiness but not serialized, such as `manifest_reference`. Source country names longer than two characters do not become country codes in the serializer. Sri Lanka Customs publishes XML-message guidance through its [ICT Directorate](https://www.customs.gov.lk/about-us/directorates-and-divisions/ict-directorate/); validate against the relevant current specification and a permitted test workflow before claiming operational compatibility.

## 6. What you can honestly claim

| Say this | Avoid saying this |
|---|---|
| “We built a prototype for evidence-based document reconciliation.” | “We guarantee compliant customs declarations.” |
| “The reviewer can inspect conflicting source assertions.” | “The AI always knows which document is correct.” |
| “The current pipeline uses keyword classification and local extraction with a model fallback.” | “Every PDF is classified by GPT-4o Vision.” |
| “We integrate pretrained OCR and configurable model APIs.” | “We trained our own model,” unless you have actual training evidence. |
| “Our active explanation payload has four layers.” | “Six layers of XAI,” without separating the earlier plan from the current payload. |
| “The current numeric comparison uses an absolute tolerance of 0.01.” | “Customs requires ±1%,” or “we implement ±1%.” |
| “A local readiness gate controls XML generation.” | “We have a certified direct ASYCUDA integration.” |
| “Authentication is simulated in the prototype.” | “PKI tokens and broker accounts are verified.” |
| “The current audit view is a prototype.” | “Our logs are immutable, tamper-proof, or blockchain-backed.” |
| “Batch and tariff screens include demo data.” | “We have live tariff synchronization and production batch filing.” |
| “We will measure review time and false negatives in a pilot.” | “90% faster,” “99% accurate,” “under $0.05,” without a reproducible benchmark. |
| “We focus on a specific reviewer workflow.” | “There is no competitor or existing tool.” |

The signatures in the classifier cover six named document categories: commercial invoice, packing list, AWB, B/L, freight invoice, and delivery order. Presence of a signature is not proof of equal end-to-end accuracy for every category. Lead the demonstration with the primary invoice/packing/transport workflow.

## 7. Loopholes and limitations, ranked for action

These are defensive review findings on this repository. “Observed” means the relevant code or check supports the statement. “Risk” describes a consequence requiring further testing. Do not present a static finding as a successfully exploited attack.

| Priority | Finding and evidence | Why it matters | Recommended next action |
|---|---|---|---|
| P0 before real data | Simulated sign-in and no visible authentication dependencies on dossier routes. `ScreenAuth.tsx`, `api/routes.py`, `main.py`. | No demonstrated access control or tenant isolation. | Add server-side identity, authorization on every dossier, and isolation tests. |
| P0 before shared hosting | Upload destination incorporates the client filename. `api/upload_router.py`, `dest = dossier_dir / upload.filename`. | Path confinement is not enforced; duplicate filenames can overwrite. No exploit attempted. | Generate storage names, sanitize display names, resolve and check containment, handle duplicates. |
| P0 before shared hosting | `/uploads` is a public static mount. `main.py`. | Possession of a URL may expose sensitive shipping documents. | Authorized download endpoints or short-lived signed links with ownership checks. |
| P0 before public upload | Extension-only validation, whole-file reads, no explicit size/page limits. `upload_router.py`. | Malformed or very large PDFs can consume resources. | Validate type/content, stream bounded uploads, cap pages, isolate parsers. |
| P1 before claims of successful processing | `AIPipeline` returns `errors[]`, but `DossierManager` marks returned results done unless an exception escapes. | An empty/error result can look completed. | Define success, partial, and failed result contracts; persist warnings/errors; test transitions. |
| P1 demo preparation | Docker daemon unavailable during review. Backend environment lacks `openai`; pytest hits an unrelated local `py.py`. | Clean end-to-end execution was not verified. | Start Docker and rebuild; verify a fresh dossier and record the run. |
| P1 confidence | Expected scoring inputs are absent from the entity dict, then defaults overwrite confidence. `pipeline.py`, `confidence.py`. | Scores can look informative while being nearly uniform. | Carry measured inputs, separate uncertainty types, calibrate with labeled cases. |
| P1 audit | In-memory registry and 16-hex-character hash over only timestamp/module/action/outcome. `audit_trail.py`. | No durable hash chain, no protection of reasoning/details, no authenticated actor. | Persist append-only events, full payload hash, chaining/signing and verification policy. |
| P1 audit honesty | Discrepancy and audit routes call `build_demo_trail` for shipments without a trail. | Synthetic events and hardcoded weight values can appear for real dossiers. | Limit fixture trails to explicit demo IDs; record actual events only. |
| P1 export correctness | Shipment-level HS code, package count, and weight repeat on each XML item. `cusdec_xml.py`. | Multiple goods items may carry inappropriate classification or double-counted totals. | Resolve per-item identity, classification, and allocations; reconcile totals. |
| P1 validation | Readiness checks mostly existence/status, not official schemas or reference codes. | “Ready” may still be invalid for the target system. | Validate typed metadata, finite numbers, transport status, country codes, and official schema. |
| P1 numerical safety | Goods-row route accepts `float(...)` values without `isfinite`; package counts need not be integers in readiness. | Nonfinite values or fractional counts can bypass intended checks. | Use constrained finite decimal/integer models and boundary tests. |
| P1 consensus | Assertion count wins without source-independence checks. `entity_resolution.py`. | Duplicate evidence can outvote the authoritative source. | Detect duplicates and document lineage; show ties; require review of material conflicts. |
| P1 consistency | Canonical text comparison and semantic evaluator differ. | A discrepancy view may appear clear while export remains blocked. | Share equivalence decisions and explain all unresolved states in one contract. |
| P1 goods integration | Table extractor exists, but active `AIPipeline` does not call it or return goods rows. | “Automatic multiline goods extraction end to end” overstates current wiring. | Integrate, persist, and validate tables; keep the manual source-reference path available. |
| P1 model fallback | Classification retains legacy Gemini code; active call omits `pdf_path`. Vision extraction defaults to `fast_model`. | README architecture/model routing differs from actual execution. | Consolidate provider paths and expose actual model telemetry. |
| P1 multipage | Missing-field vision fallback requests page 1 only. | Later-page details can remain missing even though OCR spans pages. | Select evidence-bearing pages and evaluate long documents. |
| P1 reviewer history | Field resolutions overwrite a row, reason is optional, actor is generic. | Previous decisions and responsibility may be lost. | Version decisions, require material-change reasons, bind actor identity, invalidate stale choices. |
| P2 reliability | In-process background tasks, sequential per-dossier processing, no durable job queue. | Restart recovery and larger workloads are unproven. | Durable queue, idempotent jobs, bounded concurrency, retries and dead-letter handling. |
| P2 UI/API | Frontend upload retries legacy endpoint on any error. | Validation or transient failures may trigger an unintended second upload. | Distinguish unsupported route from failed operation; use idempotency keys. |
| P2 test disagreement | One selected party-role test expects unknown for an AIR-named company, but current heuristic returns carrier. | Test and intended behavior diverge; heuristics may overgeneralize. | Agree on intended policy; update the correct implementation/test and add real-layout cases. |
| P2 governance | No validated accuracy/cost dataset or business pilot results found in reviewed materials. | Outcomes and economics cannot yet be quantified credibly. | Run the evaluation plan below and report sample size and limitations. |
| P2 UI claims | Tariff entries and batch rows are hardcoded; some auth/PKI copy implies real integrations. | Judges may challenge an impressive screen that has no integration behind it. | Label demonstrations, remove unsupported claims, prioritize core workflow in the pitch. |
| P2 stale documentation | README, old plans, and active code disagree on roles, XAI layer count, rules, and provider. | Team answers can contradict each other. | Align public documentation and ownership before the final. |

**If time is short:** first make the demo repeatable and the claims accurate. Then address processing status, confidence inputs, and synthetic audit leakage. Before any use with real customer data, fix access controls and upload protection. Do not hide known issues by editing confidence labels or selecting only easy cases.

### Additional edge cases to understand

- One file may contain several document types, while the current classification is document-level.
- Shipping dossiers may include master/house AWBs, multiple currencies, split consignments, and several HS codes. Shipment-level grouping alone cannot model all of these safely.
- Bbox mapping can match repeated values to the wrong location. Missing geometry must remain visibly uncertain.
- The pipeline deduplicates equal values by type/value, potentially losing repeated locations within a document.
- A document can contain malicious instructions aimed at a model. Treat document text as data, restrict outputs to a schema, validate results, and never give extraction models operational authority.
- Model/API errors, database failures, and normalization errors must stay visible to the reviewer. Empty output must not mean “clean.”

## 8. Validation record and evaluation plan

### Checks actually performed for this pack

| Check | Result | Scope |
|---|---|---|
| Frontend `npm run build` | Passed | TypeScript and Vite production build; warnings about a large chunk and ineffective dynamic import remain. |
| 16 existing pure test functions across resolution, readiness, XML, party roles | 15 passed, 1 failed | Direct invocation using bundled Python. No-fixture tests only; not a full pytest run. |
| Full pytest command in existing venv | Blocked | Import encountered unrelated `Python311/py.py` calling `input()`. |
| Existing backend dependency probe | `openai` unavailable | Applies to that local venv, not necessarily a rebuilt container. |
| `docker compose ps` | Blocked | Docker Desktop Linux engine pipe unavailable. |
| Full OCR/model/DB/browser journey | Not verified | No claim of a passing live demo or official XML import. |

The failed function is `test_unlabelled_organisation_is_not_emitted_as_a_consignee`. It expects `None` type/role for `MSA AIR PVT LTD`, while current name heuristics classify it as a carrier. Both paths exclude it from consignee resolution, but the expected classification differs. Do not describe this as a demonstrated consignee data leak.

### A credible pilot design

Use permissioned, redacted dossiers from several suppliers and layouts. Separate development documents from a held-out evaluation set. Have a domain reviewer label document types, field values, party roles, conflict cases, and evidence locations. Report both document count and shipment count.

| Metric | Definition | Why judges should care |
|---|---|---|
| Field exact-match accuracy | Correct extracted normalized fields / labeled fields | Measures extraction, not presentation polish |
| Conflict precision | True conflict flags / all conflict flags | Measures reviewer noise |
| Conflict recall | Detected true conflicts / all true conflicts | Measures missed discrepancies |
| False-clear rate | Unsafe/incorrect cases marked ready / evaluated cases | Tests the most consequential outcome |
| Evidence localization | Correct source page/region for each value | Tests whether explanations support verification |
| Review time | Paired manual vs assisted review on comparable cases | Tests operational value |
| Reviewer override rate | Proposed values changed by reviewers / proposals | Reveals automation quality and trust |
| p50 / p95 processing latency | Median and 95th percentile per dossier | Exposes slow scans and model calls |
| Cost per dossier | Model usage + compute + storage + review effort | Supports sustainable pricing |
| Authorized import acceptance | Accepted outputs / submitted permitted test outputs | Validates integration rather than XML appearance |

Targets are proposals until measured. A staged pilot might start with 20–30 diverse, consented dossiers to find failure patterns, then expand. This is a suggested experiment size, not an existing dataset or statistically sufficient guarantee. Use field-level and shipment-level metrics separately.

## 9. Value, differentiation, and business case

### Who uses and buys it

Initial user hypothesis: a shipping executive or broker who repeatedly prepares dossiers. Buyer hypothesis: the brokerage, freight forwarder, or apparel exporter/importer that bears preparation and rework costs. Validate both roles through interviews. Do not invent customer names, revenue, partnerships, or endorsements.

### Alternatives and your position

Manual review offers domain judgment but can require repeated cross-checking. A generic OCR system extracts text but may not connect several documents into one review decision. A general-purpose chat interface can help read documents but does not automatically provide this repository’s persistent field-resolution workflow. Customs management systems already exist. ClearanceX’s proposed place is before submission, where documentary disagreement needs explicit review.

This is a positioning argument, not a completed competitor study. Never claim to be the first or only product without a current market investigation.

### Commercial hypothesis

Test a per-dossier or monthly team subscription. Estimate value using:

`monthly review value = dossiers/month × verified minutes saved/dossier ÷ 60 × reviewer hourly cost`

Add rework reduction only after measuring it. Subtract API, infrastructure, support, and onboarding costs. Do not quote a price or margin as validated yet. A customer's willingness to pay and data-sharing constraints may matter more than model token cost.

### Defensibility

The durable value would come from domain-validated rules, reliable source mapping, quality reviewer workflows, permissioned evaluation data, and established integration processes. Calling an API by itself is not a moat. The current prototype demonstrates the intended workflow but still needs validation and operational hardening.

## 10. Viva Q&A bank

Use the short answer first. Add the evidence or limitation only as needed. Do not memorize answers you cannot explain in your own words.

### Product and motivation

**1. What problem do you solve?**  
We help shipping teams reconcile values across shipment documents before declaration preparation. The key task is finding and explaining disagreements that would otherwise require manual cross-checking.

**2. Who is your primary user?**  
A shipping executive or customs broker reviewing an invoice, packing list, and transport document for the same shipment. Our starting context is Sri Lankan apparel trade.

**3. What is new about your solution?**  
Our contribution is the combination of source-preserving canonical fields, cross-document comparisons, and a reviewer workflow. The UI connects a proposed value to its original evidence and an explicit rule result.

**4. Why not use a spreadsheet?**  
A spreadsheet can compare already-entered values. We also address extraction and evidence location, preserve competing assertions, and connect reviewer decisions to export readiness. We still need to measure whether that reduces review time.

**5. Why not use a general AI chat tool?**  
A chat tool can assist document reading. We built a repeatable application workflow with stored dossier state, source assertions, review decisions, and explicit export blockers. The value depends on reliability and integration, not merely the underlying model.

**6. Does ASYCUDA already solve this?**  
ASYCUDA already supports customs processes and electronic declarations. Our intended role is preparing and reconciling the upstream document evidence. We would validate fit with brokers and the relevant customs workflow rather than claim to replace ASYCUDA.

**7. What proves customers need this?**  
The workflow and document inconsistencies motivate the prototype. We have not established a customer pilot or quantified demand in this review. Our next evidence would be broker interviews and observed preparation tasks.

**8. What is the main benefit?**  
The reviewer can see which source disagrees and why, instead of receiving an unexplained final value. Time savings and fewer missed discrepancies are hypotheses we would measure.

### AI pipeline

**9. Where is the AI?**  
PaddleOCR recognizes document text, and configurable OpenAI calls can recover missing header fields or assist semantic tasks. Deterministic code handles much of the normalization, grouping, comparison, and explanation assembly.

**10. Did you train a model?**  
No custom training was verified. We integrate pretrained OCR and model services, then build domain extraction rules, evidence mapping, and reconciliation logic around them.

**11. What is the classification method?**  
The active pipeline uses keyword signatures. The classifier contains a legacy Gemini fallback, but the pipeline does not pass the PDF path needed to trigger it. We should describe the running path, not the old plan.

**12. Which OpenAI model processes images?**  
The wrapper has configurable model names. Its vision call currently defaults to `fast_model`, whose default is `gpt-4o-mini`; simply defining `vision_model` does not mean all calls use it. We would show configuration and call telemetry for a specific run.

**13. Why combine OCR and a language/vision model?**  
OCR gives local text and coordinates. Local patterns handle common fields. A model can fill gaps where those patterns fail. Coordinates let the reviewer check whether an extracted value corresponds to the actual source.

**14. Can hallucinations still occur?**  
Yes. Structured output only constrains format, not factual truth. Source mapping, missing-value handling, cross-document checks, and human review reduce risk but do not eliminate it.

**15. What happens without internet or an API key?**  
Local OCR and deterministic paths can still contribute when dependencies are available, but model fallbacks cannot. Explicit demo fixtures can support a demonstration. The full real-data journey is not guaranteed offline, and missing extraction must remain visible.

**16. Do you support handwritten or non-English documents?**  
We have not validated those cases. Our demonstrated scope should be English shipping PDFs. We would evaluate additional languages and handwriting separately.

**17. Can it read multipage PDFs?**  
OCR processes pages, but the missing-header vision fallback currently uses page 1. We should not promise complete recovery of later-page fields or tables until those paths are integrated and evaluated.

**18. Are goods tables fully automatic?**  
A table extractor module exists, but it is not wired into the active master pipeline output. The application provides a source-referenced manual goods-row path. End-to-end automatic goods extraction remains work to complete.

**19. Why normalize values?**  
Values such as `450.00 KG` and `450 kg` should compare as the same quantity. We retain raw values so a reviewer can see what the document actually said and detect a bad normalization.

**20. How do you avoid calling a bank the consignee?**  
Party-role logic uses label proximity and some name heuristics before a consignee value enters canonical resolution. Tests cover explicit carrier and bank exclusion, but heuristics still need broader layout testing.

### Graph and rules

**21. What is neuro-symbolic about this?**  
Neural OCR/model components interpret documents, while symbolic structures and explicit rules compare their outputs. The graph organizes evidence and the rule compiler explains the comparison. We are not claiming a trained graph neural network.

**22. Why a knowledge graph?**  
It makes the relationships among a shipment, a field, a document, and an assertion explicit. We can trace a conflict back to sources and render that evidence for review. A relational implementation could also work; NetworkX was a practical prototype choice.

**23. Is the graph stored in Neo4j?**  
No. We build an in-memory NetworkX graph from stored extraction and resolution data. PostgreSQL holds the persistent workflow records.

**24. How do you choose the correct value?**  
The resolver proposes a consensus from corroborating assertions and confidence-based tie-breaking. It does not establish truth. A reviewer must verify material conflicts and can override the proposed value.

**25. What if two wrong documents agree?**  
The majority can be wrong. We preserve the minority assertion and need source authority and independence checks. For an important conflict, external verification is more reliable than voting alone.

**26. What if someone uploads the same invoice twice?**  
That can inflate corroboration in the current design. Production handling should hash/deduplicate files and distinguish independent evidence from copies or revisions.

**27. Is your weight tolerance 1%?**  
No. The reviewed active resolver and numeric rule use an absolute tolerance of 0.01. The README’s ±1% wording is inconsistent. A domain-approved tolerance should be field-specific and versioned.

**28. What does the 450 versus 448.5 example prove?**  
It demonstrates that the code can retain the three assertions, propose 450 as consensus, and identify a 1.5 kg outlier. It does not establish extraction accuracy on unseen documents or a customs breach.

**29. Why can a field be blocked with no discrepancy card?**  
Readiness checks missing or pending required data as well as conflicts. Also, canonical text matching and semantic discrepancy suppression currently differ. We should unify those rules so the UI explains every remaining blocker consistently.

**30. Does semantic similarity mean legal identity?**  
No. Similar names can refer to different legal entities. Identifiers and explicit role evidence need stricter matching, and ambiguous cases should go to review.

### Explainability and trust

**31. What are the four XAI layers?**  
Source provenance, rule explanation, confidence indicators, and counterfactual suggestions. Together they explain where the data came from, why a check failed, how uncertain extraction is, and what agreement would require.

**32. Are you exposing the LLM’s chain of thought?**  
No. We generate an application-level explanation from source values and an explicit rule failure. It is a reproducible comparison trace, not hidden model reasoning.

**33. Does 95% confidence mean 95% accurate?**  
No. Current scores are heuristics, not calibrated empirical probabilities. We must test predictions against labeled data and calibrate before making probability claims.

**34. Why multiply confidence scores?**  
The current compiler uses a product as a conservative-looking combined indicator. A statistical interpretation would require calibrated inputs and assumptions about dependence. We currently present it as a heuristic and have identified input propagation issues to fix.

**35. Can a user just change a value to make it pass?**  
The review endpoint permits a source selection or normalized manual value. That flexibility must be paired with authorization, mandatory reasons for significant changes, and versioned audit history. Those controls are incomplete today.

**36. What does a counterfactual mean here?**  
It states a change that would remove a particular mismatch. It does not prove which value is correct or authorize altering an issuer’s original document.

**37. Is your audit trail tamper-proof?**  
No. The current runtime trail is an in-memory prototype with a truncated hash of selected event fields. A durable append-only store, authenticated actors, full-event integrity checks, and verification are still needed.

**38. Why does the audit log mention Gemini or a fixed weight example?**  
The demo trail contains older provider wording and synthetic entries. It can currently be seeded by routes outside explicit demo IDs. That is a known correctness issue; we must separate demo fixtures from real recorded events.

### Export and security

**39. Is the XML officially ASYCUDA compliant?**  
We serialize to the repository’s user-confirmed compatibility template and test part of its structure. We have not verified official schema conformance or an accepted Sri Lanka Customs import. We call it a draft export capability pending that validation.

**40. What stops an incomplete export?**  
The readiness API checks required extracted values, their resolution states, declaration metadata, a transport field, and goods rows. The export endpoint returns 422 when blockers remain. The checks still need stricter domain validation.

**41. What about multiple HS codes?**  
The current serializer uses a shipment-level HS code for every item. That limits multi-commodity correctness. Per-item classification, weights, package allocation, and valuation reconciliation are required before broader deployment.

**42. Do you submit directly to Customs?**  
No verified direct submission exists in the reviewed path. The application downloads XML for a subsequent authorized workflow.

**43. Is sign-in real?**  
The prototype explicitly simulates authentication. We need server-side identity, access control, and tenant isolation before handling real customer data.

**44. Where does sensitive data go?**  
PDFs are stored on the backend filesystem, extraction and review data in PostgreSQL, and configured model fallback paths can send page images or text to an external API. Deployment policy must define access, retention, and approved processing arrangements.

**45. How would you protect uploads?**  
Generate safe storage names, enforce path containment and size/page limits, validate content, isolate PDF processing, and serve files only after authorization. The current endpoint has gaps in these areas.

**46. How do you handle prompt injection in a PDF?**  
Treat its text as untrusted data. Restrict extraction to a validated schema and never allow embedded instructions to control tools or workflow actions. Then verify extracted values against source evidence and domain checks.

### Engineering and testing

**47. How does background processing work?**  
FastAPI BackgroundTasks schedules work inside the application process. A dossier processes documents in a loop. A production system should use durable jobs with recovery, idempotency, and bounded concurrency.

**48. What happens if the server restarts?**  
Stored records can persist, but in-process work and the in-memory audit registry are not durable. We need restart recovery and persisted job state before promising reliable continuous service.

**49. Can a processing error look like success?**  
Yes, currently the pipeline can return an error payload that the manager still marks done. We have identified that mismatch and should make success depend on explicit result validation.

**50. What tests did you run?**  
For this review the frontend production build passed. Sixteen selected existing pure test functions ran directly: fifteen passed and one party-role classification expectation failed. Full pytest and Docker execution were blocked by the local environment. We should update this answer after the final rehearsal run.

**51. What is your accuracy?**  
We do not yet have a validated held-out accuracy figure. Our next evaluation separates field extraction, conflict precision/recall, evidence localization, and false-clear rate. Passing unit tests is not model accuracy.

**52. What is your cost per dossier?**  
We have not measured a defensible end-to-end figure in this review. We would record actual model usage, OCR/compute time, storage, and reviewer effort across representative dossiers. The README estimate should not be treated as a benchmark.

**53. Why PostgreSQL and NetworkX together?**  
PostgreSQL stores durable business state; NetworkX provides a working evidence graph for comparison and visualization. They serve different purposes. We would revisit the architecture based on measured workload.

**54. What is the largest technical weakness?**  
The prototype’s workflow is stronger than its production guarantees. I would prioritize truthful processing status and confidence, durable reviewer audit, access control, and verified export mappings. These are concrete engineering tasks, not reasons to hide the core contribution.

**55. How will you scale it?**  
Measure the bottleneck first, likely OCR/model processing. Then use durable workers, bounded concurrency, model request limits, caching with version keys, and database connection management. We have not performed a load test, so we will not quote capacity.

### Team, impact, and next steps

**56. What did each team member build?**  
Use the actual commits and working knowledge. Planning files assign Nadija to AI/OCR, Aloka to reasoning/data/XAI, and Kaveen to frontend/integration; the README differs on some ownership. Confirm the final contribution split before using names. Each person should explain one implementation decision, one failure, and one test from their own work.

**57. What did you change from the initial proposal?**  
The repository moved toward PaddleOCR and OpenAI-backed extraction, while retaining some legacy Gemini code. Explain the choice in terms of integration and prototype constraints. Do not claim comparative accuracy improvements without experimental evidence.

**58. What would you build next?**  
First stabilize the data and review contracts, then complete security and audit controls. Next validate item-level export with domain experts and run a held-out broker pilot. The roadmap follows risk and evidence, not just more screens.

**59. How do you make money?**  
A team subscription or per-dossier model is a hypothesis. We would price against measured preparation/rework value, then account for processing and support costs. We do not yet have validated willingness to pay.

**60. Why should your project win?**  
“We focused on a consequential decision: which shipment value can a reviewer defend? Our prototype connects the extracted value to its source, shows the disagreement, and records a review decision before export. We can explain both the technical design and the work still needed to validate it.”

**61. What if the live demo fails?**  
“This run has encountered a dependency or connectivity problem. We will show our clearly labeled recorded run or test fixture, explain the same evidence path, and distinguish it from fresh processing.” Do not pretend a cache is a live extraction.

**62. What would make you reject your own idea?**  
If a controlled pilot shows no meaningful reduction in review effort, unacceptable false-clear rates, or data/integration constraints that users cannot accept, we should narrow or change the product. A good prototype is a way to test those assumptions.

## 11. Ten-minute viva tactics

Expect roughly 6–10 questions depending on follow-ups. Aim for a 20–35 second answer first. Use **answer, evidence, boundary**:

> “The graph preserves every source assertion. You can see that in the resolver and knowledge builder. It proposes consensus, but an authorized reviewer still needs to establish which source is correct.”

Suggested practice round:

| Minute | Question |
|---|---|
| 0–1 | What is the problem and why is your approach useful? |
| 1–2 | Where is the AI and what did you build yourselves? |
| 2–3 | Explain the canonical graph and weight example. |
| 3–4 | What does confidence mean? |
| 4–5 | Is export officially compliant? |
| 5–6 | What if the documents agree but are wrong? |
| 6–7 | Show a test or known failure. |
| 7–8 | Explain authentication and sensitive-data limits. |
| 8–9 | What was your personal contribution? |
| 9–10 | What evidence would your next pilot collect? |

If you do not know, say: “We have not verified that yet. The implementation currently does X. I would test Y before making that claim.” If a judge points out a real bug, acknowledge it and explain the consequence and fix. Avoid arguing from a README statement when the code says otherwise.

Do not let all three members answer at once. Nominate one person to route questions. Give the owner the first answer and let another member add only a useful missing detail. Never claim another member’s work.

## 12. Repository evidence map

Paths are relative to the repository root. These are the main reviewed implementation anchors, not a claim that every line in the repository was audited.

| Area | Source |
|---|---|
| Application setup, static uploads | `backend/main.py` |
| Dossier upload validation | `backend/api/upload_router.py` |
| Review, metadata, goods, readiness, export routes | `backend/api/routes.py` |
| Master pipeline and confidence input assembly | `backend/ai_pipeline/pipeline.py` |
| Background status transitions | `backend/ai_pipeline/dossier_manager.py` |
| Keyword signatures and legacy fallback | `backend/ai_pipeline/classifier.py` |
| Local extraction and page-1 fallback | `backend/ai_pipeline/entity_extractor.py` |
| Model routing defaults | `backend/ai_pipeline/openai_client.py` |
| Role safeguards | `backend/ai_pipeline/party_roles.py` |
| Unit/semantic normalization | `backend/ai_pipeline/normalizer.py` |
| Score formula | `backend/ai_pipeline/confidence.py` |
| Canonical grouping and reviewer overlay | `backend/reasoning/entity_resolution.py` |
| Evidence graph | `backend/reasoning/knowledge_builder.py` |
| Active rules | `backend/reasoning/rule_evaluator.py` |
| Semantic comparison | `backend/reasoning/semantic_fallback.py` |
| Active four-layer payload | `backend/reasoning/xai_compiler.py`, `backend/xai_types.py` |
| Additional/legacy counterfactual module | `backend/reasoning/counterfactual.py` |
| In-memory/demo audit | `backend/reasoning/audit_trail.py` |
| Export checks and template | `backend/reasoning/cusdec_readiness.py`, `backend/reasoning/cusdec_xml.py` |
| Persistence models | `backend/database/models.py`, `backend/database/connection.py` |
| Frontend API behavior | `frontend/src/utils/api.ts` |
| Review UI | `frontend/src/components/screens/ScreenReviewWorkspace.tsx`, `frontend/src/components/review/KeyFieldReconciliationPanel.tsx` |
| Simulated auth and demo screens | `frontend/src/components/screens/ScreenAuth.tsx`, `ScreenBatchFiling.tsx`, `ScreenTariffDirectory.tsx` |
| Selected existing tests | `backend/reasoning/test_entity_resolution.py`, `test_cusdec_readiness.py`, `test_cusdec_xml.py`, `backend/ai_pipeline/test_party_roles.py` |
| Setup | `docker-compose.yml`, `frontend/package.json`, `backend/requirements.txt` |
| Local organizer guidance | `Docs/hackathon_req.txt` |

External context checked for this pack: [Sri Lanka Customs ICT Directorate](https://www.customs.gov.lk/about-us/directorates-and-divisions/ict-directorate/), [Sri Lanka paperless pilot announcement](https://www.customs.gov.lk/sri-lanka-customs-launches-pilot-program-on-paperless-submission-of-customs-declarations/), and [UNCTAD ASYCUDA software overview](https://asycuda.org/en/software/). These establish context, not approval of ClearanceX. The reviewed organizer file is setup guidance, not a final-round judging rubric.

## 13. The five things to remember before walking in

1. Lead with the user’s decision, then show the source evidence.
2. Explain consensus as a proposal and confidence as a heuristic.
3. Demonstrate a blocked state as well as a successful reviewer action.
4. Distinguish implemented behavior, demo data, and future validation.
5. End with a specific pilot ask: a broker partner and permissioned dossiers to measure review time, missed conflicts, and export compatibility.
