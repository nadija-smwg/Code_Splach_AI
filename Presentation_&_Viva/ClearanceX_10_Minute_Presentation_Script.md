# ClearanceX: 10-minute presentation script

**English · 12 core slides + 5 viva backup slides**  
Planned delivery: **9 minutes 30 seconds**, leaving **30 seconds** for transitions or a slow demo. The viva has its own 10 minutes. Stop at slide 12 during the presentation. Open slides 13–17 only when useful for a judge’s question.

## Presenter allocation

Choose speakers by their verified contribution, not by the inconsistent ownership labels in older documentation. A practical split is speaker A for slides 1–4, speaker B for slides 5–6 and 8–9, and speaker C for the demo and slides 10–12. If one person is more fluent, they can lead while module owners handle the viva. Avoid changing speaker on every slide.

The supplied title slide retains its event artwork, team, university, and member names. Its placeholder project heading is completed in the final deck. “Theme” becomes a descriptive project focus, not an invented official competition category.

## Timing map

| Slide | Topic | Duration | Cumulative finish |
|---|---|---:|---:|
| 1 | ClearanceX | 0:25 | 0:25 |
| 2 | The document review problem | 0:45 | 1:10 |
| 3 | One shipment, conflicting values | 0:45 | 1:55 |
| 4 | The reviewer workflow | 0:50 | 2:45 |
| 5 | Architecture | 0:45 | 3:30 |
| 6 | Four layers of explanation | 0:55 | 4:25 |
| 7 | Live review demonstration | 1:40 | 6:05 |
| 8 | Export readiness | 0:45 | 6:50 |
| 9 | Engineering evidence | 0:40 | 7:30 |
| 10 | Prototype boundaries | 0:45 | 8:15 |
| 11 | Pilot and measurable value | 0:45 | 9:00 |
| 12 | Closing | 0:30 | 9:30 |

## Slide 1: ClearanceX — 25 seconds

“Good morning. We are Team Ants from the University of Moratuwa. Our project is ClearanceX, an explainable document reconciliation assistant for shipping teams.

Before a declaration is prepared, someone must decide whether several documents tell the same story. We help that person identify conflicting evidence, understand the difference, and make a recorded decision.”

**Delivery:** Look at the judges. Introduce the team once. Avoid reading all names and the university label from the slide.

## Slide 2: The document review problem — 45 seconds

“For one shipment, an executive may receive a commercial invoice, a packing list, and an air waybill or bill of lading. These documents come from different parties, so names, units, and values can differ.

The reviewer has to locate the relevant values, compare them, and decide which differences need clarification. Electronic customs systems already exist. We focus on the preparation work before submission, where document evidence still needs careful reconciliation.

Our starting user is the shipping executive or broker working with English apparel-related dossiers.”

**Emphasis:** The pain is the cross-checking decision. Do not claim the entire customs system is manual.

## Slide 3: One shipment, conflicting values — 45 seconds

“Here is a controlled example from our repository. The invoice says 450 kilograms. The packing list also says 450. The air waybill says 448.5.

ClearanceX keeps all three assertions and proposes 450 as the consensus. It identifies the air waybill’s difference as 1.5 kilograms.

But majority agreement does not establish the physical weight. The useful result is a specific question for the reviewer: which source should we verify? We preserve the disagreement so the reviewer can answer that question.”

**Point:** Indicate each row, then the difference. Explain that this is a test example, not a customer outcome or a legal tolerance breach.

## Slide 4: The reviewer workflow — 50 seconds

“The user uploads the shipment’s PDFs together. OCR reads text and locations. The pipeline classifies the document and extracts header fields, using local patterns first and a model fallback for missing information.

We normalize those values and group the evidence into shipment fields. The review screen can then show the proposed value beside every source assertion.

When the reviewer selects a verified value, we save that decision while preserving the original evidence. Finally, the readiness check explains what still needs attention before an XML export can be generated.”

**Transition:** “The architecture supports that separation between interpreting a document and deciding how its evidence should be used.”

## Slide 5: Architecture — 45 seconds

“React and TypeScript provide the review interface. FastAPI exposes the dossier and review endpoints. PostgreSQL stores extraction results and reviewer decisions.

PaddleOCR and optional model calls handle document interpretation. NetworkX connects documents, assertions, and canonical fields. Explicit rules produce discrepancy results, and the XAI compiler turns those into explanations.

This is a hybrid design: uncertain extraction supplies evidence, while explicit application logic performs the comparison. Docker Compose defines the services for local evaluation.”

**Avoid:** Claiming a graph neural network, a custom-trained LLM, or a fully parallel durable worker system.

## Slide 6: Four layers of explanation — 55 seconds

“A discrepancy needs more than a red warning. Our active explanation payload has four layers.

First, provenance identifies the source documents, snippets, and locations. Second, the rule explanation shows the values compared and the difference. Third, confidence provides an uncertainty indicator. Fourth, the counterfactual explains what change would make the selected values agree.

For our example, adding 1.5 kilograms to one value would remove the mismatch. That is a mathematical condition, not an instruction to alter a document without verification.

The current confidence scores are heuristics. We have identified calibration and input-propagation work before those scores could support probability claims.”

**Delivery:** Slow down on the distinction between a proposed correction and verified truth.

## Slide 7: Live review demonstration — 100 seconds

Use a **preprocessed dossier** whose exact data and interactions you have rehearsed. A real cached dossier and the explicit mock demo are different. State which one you use. Do not depend on live model latency.

**0–15 seconds: identify the dossier.**  
“This is our [preprocessed test dossier / explicitly labeled demo fixture]. We are using prepared data so we can spend the demonstration on the review decision.”

**15–40 seconds: show the conflict.**  
“These are the source assertions for gross weight. The proposed value is here, and this source disagrees. We can compare the extracted value with the original test PDF, which we have opened separately.”

The current Review Workspace shows extracted fields and page labels. It does not implement the original-PDF viewer with bbox overlays described in older documents. Pre-open the relevant source PDF separately if you want to show the physical source.

**40–60 seconds: show explanation.**  
“The explanation names the comparison and the difference. It also retains the evidence needed for a reviewer to check the result.”

**60–80 seconds: perform the rehearsed action.**  
“After checking the source, the reviewer can select a verified value and record a reason. The original assertions remain available.”

Only save if this is an authorized test dossier with working persistence. Do not pretend a mock demo ID has the same save behavior as a stored UUID dossier. If persistence is not verified, demonstrate the evidence and clearly describe the implemented save endpoint without clicking an untested action.

**80–100 seconds: show readiness.**  
“Resolving this field does not mean the whole declaration is ready. The readiness view still lists missing or unresolved requirements. That makes the remaining work explicit.”

If the runtime fails, say once: “The live run is unavailable. I’ll use our clearly labeled backup to show the same evidence flow.” Return to the deck’s worked example and readiness slide. Never call that a successful live run.

## Slide 8: Export readiness — 45 seconds

“The gate checks required document fields, declaration metadata, and goods rows. A required value that is missing, conflicting, or still pending prevents export. The backend also enforces that gate, rather than relying only on a disabled button.

The current serializer produces XML from a user-confirmed compatibility template. We have a structure test, but we have not demonstrated official schema validation or an accepted customs import.

Our next integration step is to validate the relevant mappings and item-level details with a broker and the permitted target workflow.”

## Slide 9: Engineering evidence — 40 seconds

“We have checked the implementation rather than treating the README as proof. The frontend production build passes. In the selected backend checks for this review, fifteen of sixteen existing pure tests passed. One party-role test disagrees with the current heuristic’s expected classification.

The full Docker and OCR journey still needs a clean final rehearsal. Unit tests demonstrate specific behavior, such as preserving an outlier and blocking pending fields. They do not establish model accuracy on unseen customer documents.”

**Update rule:** Replace these results only after rerunning the relevant checks and saving actual output. If the environment is repaired before the event, use the new verified result and date.

## Slide 10: Prototype boundaries — 45 seconds

“We are clear about the prototype boundary. Authentication is simulated, and the runtime audit trail needs durable event recording. Confidence needs measured inputs and calibration. Automatic goods-table integration and item-level export mappings also need further work.

These limitations shape our priorities. First, make failure states and review decisions reliable. Before real customer data, add access control and upload protection. Then validate export behavior and measure performance on diverse dossiers.

The contribution we demonstrate today is a traceable review workflow with explicit evidence.”

**Tone:** Calm and specific. This is engineering judgment, not an apology. Do not spend all 45 seconds enumerating every risk.

## Slide 11: Pilot and measurable value — 45 seconds

“We would test the next version with a broker or apparel shipping team using permissioned, redacted dossiers. We would compare manual and assisted review on comparable cases.

The important outcomes are review time, missed conflicts, false alerts, evidence-location accuracy, and cases incorrectly marked ready. We would also measure processing latency and total cost per dossier.

A team subscription or per-dossier service is a commercial hypothesis. We will base that on demonstrated operational value and customer willingness to pay, rather than assume that a low model cost makes the product viable.”

## Slide 12: Closing — 30 seconds

“ClearanceX makes the evidence behind a shipment value visible. It helps the reviewer see the conflict, understand the comparison, and record a decision before export preparation.

Our next ask is a broker pilot with permissioned dossiers so we can validate the workflow and its results.

We are Team Ants. Thank you. We welcome your questions.”

**Then stop.** Leave the closing slide visible. Do not automatically walk through the backup slides.

## Backup slide index

| Slide | Use when asked about |
|---|---|
| 13 | Canonical graph, evidence preservation, manual resolution |
| 14 | Confidence formula and why it is not calibrated accuracy |
| 15 | XML compatibility, readiness, item-level limitations |
| 16 | Security, reliability, and hardening priorities |
| 17 | Evaluation metrics and business validation |

## Rehearsal scoring

Score each practice from 0 to 2 on: finishing before 9:30, clear problem, correct weight explanation, successful evidence navigation, accurate limitations, clear personal contributions, and direct viva answers. A total is only a private coaching tool, not the organizer’s rubric.

Record one rehearsal. Listen for “basically,” “actually,” long pauses, reading slide text, unsupported numbers, and repeated technology names. Cut repeated claims before speaking faster. Have a teammate ask “How do you know?” after every performance or compliance claim.
