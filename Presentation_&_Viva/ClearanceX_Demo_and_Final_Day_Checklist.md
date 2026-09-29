# ClearanceX: demo and final-day checklist

**Use with the 10-minute deck.** Application fixes are outside this presentation pack; the open items below need a verified rehearsal before the event.

## Current blockers found in the review

- Docker Desktop’s Linux engine was unavailable when `docker compose ps` ran.
- The existing backend venv did not contain `openai`.
- Full pytest startup encountered an unrelated `Python311/py.py` that asks for input.
- Direct invocation of 16 selected existing pure tests produced 15 passes and one party-role expectation failure.
- No full live OCR/model/database/browser run or official XML import was verified.

The frontend production build passed. A successful build does not guarantee the demo’s backend or external calls.

## Before rehearsal

- [ ] Confirm final-round rules, permitted live/recorded demo format, and whether questions interrupt the 10-minute pitch. The repository’s organizer file contains setup requirements, not the final judging rubric.
- [ ] Verify the title slide’s member names and the agreed speaking roles.
- [ ] Start Docker Desktop and wait for its engine to become ready.
- [ ] Check environment configuration locally. Never show `.env`, API keys, or account credentials on the projector.
- [ ] Build and start the project from the repository root using the existing documented Compose workflow.

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 80 backend
```

Inspect logs privately before sharing them; errors can contain sensitive information. Do not delete volumes to solve routine demo issues.

- [ ] Open the app at `http://localhost:3000` and health endpoint at `http://localhost:8000/health`.
- [ ] Remember that `/health` is a basic service response, not a deep OCR/database/model readiness check.
- [ ] Create a **test** dossier with non-sensitive PDFs. Confirm each document has usable extraction, not merely a completed label.
- [ ] Confirm the chosen conflict appears in both the canonical field view and the discrepancy view.
- [ ] Pre-open the original test PDF in a separate viewer at a readable zoom. The current Review Workspace shows extracted field cards and page labels, not original-PDF bbox overlays.
- [ ] Rehearse a saved resolution with a test UUID dossier and refresh to verify persistence.
- [ ] Record the original value, the verified choice, and why that choice is valid for the test case.
- [ ] Confirm that other pending fields still block export and that the API rejects it too.
- [ ] Only demonstrate a successful XML download if every required input has been legitimately supplied and the workflow has passed rehearsal.

## The 100-second demo path

| Time | Action | What to say |
|---|---|---|
| 0–15 s | Open prepared dossier | “This is preprocessed test data.” |
| 15–40 s | Open gross-weight source assertions | “These values describe the same shipment but disagree.” |
| 40–60 s | Show discrepancy explanation and source | “The system shows both the comparison and the evidence.” |
| 60–80 s | Save a rehearsed, verified test decision | “The reviewer’s choice overlays the source evidence.” |
| 80–100 s | Open readiness blockers | “Other required information still needs review before export.” |

If you use `demo` or `demo-shipment`, explicitly call it a fixture. Fixture evidence can illustrate the reasoning, but do not assume database writes or fresh OCR work for those IDs. Rehearse the exact route you plan to show.

## Backup material to prepare yourself

- [ ] Record a 90–100 second successful run with the same non-sensitive test dossier. This pack does not contain a recorded live demo.
- [ ] Capture readable screenshots of the conflict, source view, saved resolution, and readiness blockers.
- [ ] Save the test PDFs and an explanatory note beside the recording so you know which run it represents.
- [ ] Keep a local copy of the PPTX and optionally export a PDF from PowerPoint after checking the fonts on the presentation laptop.
- [ ] Test the projector aspect ratio, contrast, speaker notes, and slide navigation.
- [ ] Know how to jump directly to backup slides 13–17.

## Recovery lines

**Slow extraction:** “We’ll open the preprocessed test dossier so we can demonstrate the review logic within the time limit.”

**API/network failure:** “This live processing step is unavailable. The backup is a recorded test run, and I’ll distinguish it from fresh extraction.”

**Database save failure:** “That decision did not persist. We should not describe it as saved. Here is the evidence path and the intended review endpoint.”

**Export remains blocked:** “The gate is showing that required information is still missing. Resolving one conflict does not complete a declaration.”

**Unexpected result:** “The observed result differs from our expectation. We would inspect the source assertion and processing status before accepting it.”

## Ten-minute viva quick sheet

| Likely challenge | Your anchor answer |
|---|---|
| Why a graph? | It preserves links among shipment fields, source assertions, and documents. |
| Which source is correct? | Consensus is a proposal. The reviewer verifies authority. |
| 95% confidence? | A heuristic indicator, not measured accuracy. |
| ±1% tolerance? | Active code uses absolute 0.01; the README is inconsistent. |
| ASYCUDA certified? | Compatibility-template XML; no verified official acceptance. |
| Production security? | Simulated auth. Access control and protected uploads are required. |
| Immutable audit? | Current in-memory prototype does not provide that guarantee. |
| Accuracy/cost? | Not benchmarked on a held-out pilot in this review. |
| What did you build? | Explain your own module, its contract, one tradeoff, and one test. |
| Why should this win? | Traceable evidence and a concrete reviewer decision, with honest boundaries. |

## Last hour

- [ ] Open the final deck and verify its first slide and member names.
- [ ] Open the preprocessed dossier and keep the app in the correct starting state.
- [ ] Verify the backup recording actually plays without internet.
- [ ] Close private documents, notifications, and terminals containing secrets.
- [ ] Use a timer. The planned script ends at 9:30.
- [ ] Agree on who answers AI, reasoning, UI, and deployment questions.
- [ ] Rehearse the opening and closing once, then rest your voice.

Present the strongest working workflow. Be precise when judges ask about unfinished capabilities. A calm answer supported by source code is stronger than a feature claim that fails under one follow-up question.
