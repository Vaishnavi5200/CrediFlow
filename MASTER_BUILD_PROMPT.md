<USER_REQUEST>
# MASTER BUILD PROMPT — CrediFlow (VendorFix)
### RocketRide Buildathon — HackWithUP 2026 — Team Nexora

Paste this whole document into Antigravity as your build instruction. It is self-contained: product context, RocketRide's actual winning bar, exact architecture, and every submission requirement. Do not skip any numbered section — each one maps directly to a named judging criterion or a named disqualifier from the official RocketRide docs.

---

## 0. ROLE

You are building a **real, publishable web application** for the RocketRide Buildathon, not a hackathon toy. A stranger should be able to sign up and get value from it without me explaining it to them. RocketRide must be the engine doing the actual work — not one model call sitting behind a landing page. Build incrementally: one pipeline node at a time, run it, confirm it works, then add the next. Do not wire five nodes and debug at the end.

---

## 1. PRODUCT CONTEXT — DO NOT DRIFT FROM THIS

**Product**: CrediFlow (also called VendorFix) — an AI-driven vendor GST compliance nudge system.

**Specific named user** (not a category): A Finance Manager at an Indian MSME with 30+ recurring B2B vendors, who currently loses 30+ hours/month manually chasing vendors in Excel when purchase invoices don't match GSTR-2B, and is under real regulatory pressure — India's Rule 60 CGST zero-mismatch policy (April 2026) blocks provisional ITC claims on unmatched invoices, and unresolved mismatches for FY 2025-26 permanently lapse after the September 2026 GSTR-3B filing deadline.

**Core workflow** (preserve this — it's the product's spine):
`DETECT → QUANTIFY → NUDGE → RESOLVE → VERIFY`

1. **DETECT** — reconcile an uploaded purchase register against GSTR-2B data, flag mismatches (missing invoice, wrong GSTIN, value mismatch, wrong HSN code, timing difference).
2. **QUANTIFY** — compute exact ₹ ITC exposure per mismatch, deterministically (no LLM math, ever).
3. **NUDGE** — classify the root cause, draft a plain-language vendor-facing message, and send it.
4. **RESOLVE** — the vendor (simulated in demo) amends their filing.
5. **VERIFY** — re-check the mismatch is closed, restore credit eligibility, update the vendor's compliance score.

**Non-negotiable design principle from the original product spec**: deterministic math and LLM reasoning are strictly separated. LLMs never compute tax numbers. LLMs only classify, explain, and draft language.

**Do not invent scope creep** — no WhatsApp Business API dependency if it can't be verified/approved in time (see §6), no live GST portal integration unless you confirm real API access exists (assume it does not, and build against a clearly-labeled synthetic/mock GSTR-2B dataset instead — label it as mock everywhere in the UI, never imply it's live).

---

## 2. THE EXACT WINNING BAR — TREAT EVERY LINE AS A REQUIREMENT

From RocketRide's own judging table, build to satisfy every row:

| Judged on | You must be able to show |
|---|---|
| Is it a real app? | Publishable — a stranger signs up and gets value with no explanation needed |
| Would someone pay? | The named user above, not a vague category |
| Is RocketRide the engine? | Multiple pipeline components doing real work — not one model call behind a UI |
| Does it hold up at volume? | A real batch run (hundreds+ records), not a 3-sample demo, and the cost is sane |
| Does it know when to stop? | A validator, a confidence line, AND a human approval gate |
| Would it still run next month? | Survives malformed input, provider timeouts; you know the cost per run |

**Explicit disqualifiers — build so that NONE of these are true**:
- Works only on a handful of sample inputs
- No path to a human anywhere in the flow
- No idea what a run costs
- A single model call with a landing page wrapped around it

---

## 3. RocketRide MECHANICS YOU MUST USE CORRECTLY

- Everything is a `.pipe` file: JSON, with a `components` array. Each component has `id`, `provider`, `config`, optional `input` (data lane — solid line, sequential flow) and `control` (invoke connection — dashed line, a capability a node calls on demand, like an agent calling a model or a tool).
- **Data lanes = the pipeline itself.** **Control/invoke connections = capabilities handed to an agent** (a model, a tool, memory) that it calls as many times as it needs, not in a fixed sequence.
- Build the `.pipe` file(s) via the VS Code Canvas, Cloud Pipeline Builder, or by writing the JSON directly (you, the coding agent, may write it directly — that's a valid and fast path).
- Build and test in **Local mode** first (free, no account). Switch to **Cloud mode** only for the deployed/demo version — same `.pipe` file, unchanged, one dropdown change.
- If deploying to Cloud, addresses must be `https://` or `wss://` — `http://`/`ws://` silently downgrades with no error. `ws://localhost:...` is correct only for local.
- Use the Python SDK (`pip install rocketride python-dotenv`) for anything with a UI or script driving the pipeline: `connect → use() → send() → terminate()`. **Always call `terminate()`** — leaving it out orphans a running pipeline on the engine even after the socket disconnects.
- Model cost: RocketRide's own infra is covered by the promo code; model API calls are billed separately by the provider. Either use a real OpenAI/Anthropic key, or use Ollama (`ollama pull llama3.2`) as a genuinely free fallback — "runs on Ollama, no API cost" is an explicitly accepted answer for the required cost disclosure. Decide this early and design the cost dashboard (§8) to work with whichever you pick.

---

## 4. PIPELINE ARCHITECTURE TO BUILD

Map the five product stages onto RocketRide components as follows. This is the load-bearing core — build this before anything else.

**Stage 1–2 (DETECT + QUANTIFY) — deterministic, no LLM:**
- Ingestion component: accepts an uploaded CSV/Excel purchase register (this is the "automatic input" — a real upload, not copy-paste).
- Reconciliation component: deterministic diff against a mock GSTR-2B dataset (checksums, GSTIN validation, amount/HSN matching).
- Exposure calculator: deterministic ₹ exposure per mismatch. No LLM in this path, ever.

**Stage 3 (NUDGE) — this is where "load-bearing multi-agent" must be real, not decorative:**
- **Agent A — Classifier**: an LLM node that reads each mismatch and classifies root cause (GSTIN error / value mismatch / HSN error / timing issue) and drafts a plain-language explanation.
- **Agent B — Auditor**: a second, independently-invoked LLM node (via a `control`/invoke connection, not just chained data) whose only job is to check Agent A's classification against the raw mismatch data and either confirm it, correct it, or flag it as uncertain. This is the actual "specialist AIs checking each other's work" requirement — it must be visibly two separate calls with two separate roles, not one prompt doing both jobs.
- **Disagreement/low-confidence handling**: if Agent B disagrees with Agent A, or confidence is below your chosen threshold, do **not** auto-send — route to the human gate (§5).
- **Message drafting**: once classification is confirmed, draft the vendor-facing plain-language nudge (Hindi/English).

**Stage 4–5 (RESOLVE + VERIFY):**
- Simulated vendor action (for demo purposes, a controllable "vendor responds" trigger is acceptable and should be clearly labeled as simulated).
- Re-check component: re-runs the deterministic match, closes the mismatch, updates a persistent vendor compliance score.

---

## 5. HUMAN-IN-THE-LOOP GATE — THIS IS A HARD REQUIREMENT, NOT POLISH

Build an explicit approval step in the UI, wired into the pipeline, that fires when **any** of these are true:
- Agent B (Auditor) disagrees with Agent A, or confidence is below threshold
- ₹ exposure for a mismatch is above a configurable high-value threshold
- Any malformed or unrecognized input row (see §7)

The human (Finance Manager) sees the AI's proposed classification and drafted message, and can **Approve / Edit / Reject** before anything is sent. Log every human decision — this is also your audit trail. Do not let anything above-threshold auto-send. This single feature is explicitly what separates a passing submission from a disqualified one ("no path to a human anywhere").

---

## 6. REAL-WORLD ACTION — CHOOSE THE RELIABLE ONE FIRST

WhatsApp Business API requires account approval with lead time you likely don't have. **Do not depend on it for the live demo.** Build in this priority order:

1. **Primary, must work live**: send a real email (SMTP) to a test address representing the vendor, OR create a real record/ticket in a database with a visible status change, OR generate and store a real downloadable PDF/report per resolved mismatch. Pick at least one and make it fully real, not mocked.
2. **Secondary, nice to have**: a WhatsApp-style message rendered and logged in the UI (clearly labeled as the intended channel, not necessarily live-sent) — this preserves the product's actual differentiator without betting the demo on API approval timing.
3. Whatever you pick as primary, it must be a genuine external action a judge can verify happened, not a string printed to a log file.

---

## 7. RESILIENCE & ERROR HANDLING — BUILD AND DEMONSTRATE THIS DELIBERATELY

- Include deliberately malformed rows in your batch test file (bad GSTIN format, missing amount, duplicate invoice number, non-UTF8 garbage).
- The pipeline must not crash on these — it must catch them, and **escalate what it will not guess on** to the human gate (§5), with a clear reason shown.
- Add basic retry/backoff on any external call (mock portal check, email send) and surface failures in the UI rather than failing silently.
- This directly answers "would it still run next month?" — make sure your demo includes at least one moment where a bad row is caught live, not just a slide claiming it's handled.

---

## 8. BATCH PROCESSING + COST + EXECUTION TIME — REQUIRED, VISIBLE, MEASURED

- Build a synthetic batch dataset of at least several hundred to a few thousand mock invoices across many vendors — this is what "holds up at volume" means. A 3-invoice demo is an explicit disqualifier.
- On every batch run, capture and display: **record count, total run cost (or "$0 — Ollama" if applicable), and wall-clock time.** RocketRide's live trace view shows token usage per node — surface this in your own dashboard rather than making a judge dig for it.
- This same data is required verbatim in your README (§10) — build the dashboard so a screenshot of it satisfies that requirement directly.

---

## 9. TECH STACK

- **Frontend**: React/Next.js + Tailwind — Finance Manager dashboard (upload register, view batch runs, approval queue, vendor compliance scores, cost/time metrics).
- **Backend**: FastAPI or Node, calling RocketRide via the Python (or TypeScript) SDK — `use()` to start a pipeline run per batch, `send()` to push the uploaded file/payload, `terminate()` after completion. Never omit `terminate()`.
- **Storage**: Postgres for transactional data (mismatches, vendor scores, approval log); simple file storage for uploaded registers and generated reports.
- **Deploy**: Local engine for development; switch to RocketRide Cloud for the deployed demo link. A live link beats a video; a video beats a promise — prioritize getting a live Cloud-deployed link working over polish.

---

## 10. SUBMISSION CHECKLIST — BUILD THESE AS YOU GO, NOT AT THE END

- [ ] Public GitHub repo with **all `.pipe` files committed** (if you use Cloud Pipeline Builder at any point, download and commit the files — this is called out as the most common way a good project loses marks)
- [ ] `.env.example` present, all secrets gitignored, every RocketRide variable named `ROCKETRIDE_*`
- [ ] README that explains what it does and how to run it in **five lines**, plus the batch run numbers (record count / cost / wall-clock time) from §8
- [ ] Demonstrated bad-input handling in the repo/demo (§7)
- [ ] A live Cloud deployment link (preferred) or a demo video (fallback)
- [ ] App link if deployed separately from the pipeline
- [ ] Slides only if you make them — not required
- [ ] Submit via the official form (one per team, editable until deadline) and also post in Discord `#showcase`

---

## 11. FINAL SELF-CHECK BEFORE YOU CALL IT DONE

Before finishing, verify against RocketRide's own disqualifier list — if any of these is true, fix it before submitting:
- Does it only work on a handful of sample inputs? → run the real batch (§8)
- Is there anywhere the AI acts above-threshold with no human path? → fix the gate (§5)
- Do you know what a run costs? → the dashboard must show it (§8)
- Is this actually one model call behind a UI? → confirm Agent A and Agent B are genuinely separate, independently-invoked components (§4), not one prompt doing two jobs.

Build in this order: deterministic reconciliation → Agent A classifier → Agent B auditor + disagreement routing → human approval gate → real-world action → batch runner + cost/time dashboard → error injection/resilience pass → Cloud deploy → README + repo cleanup.# ADDENDUM — Read together with `CrediFlow_RocketRide_Master_Build_Prompt.md`

**This document does not replace, weaken, reorder, or remove anything in the master build prompt.** The master prompt is the target logical architecture and full requirement set. This addendum adds constraints that govern *how* you implement it, and takes precedence only on the specific points below where the master prompt made an assumption that may not hold in the real environment.

Give Antigravity both files together, in this order: master prompt first, this addendum second.

---

## Before implementing anything

1. **Inspect the existing CrediFlow repository first.** Preserve all useful working functionality, UI, business logic, and product identity already present. Do not rebuild or replace the project unnecessarily — extend it.

2. **Inspect the actual RocketRide version, installed components/providers, node reference, and supported SDK in the current environment before building.** The architecture in the master prompt (§4: ingestion, reconciliation, exposure calculator, Classifier agent, Auditor agent, message drafting, re-check) is the **target logical architecture**, not a guarantee that those exact node/provider names exist. Never invent unsupported RocketRide nodes, providers, config fields, SDKs, or capabilities. If a node the architecture calls for doesn't exist under that name, find the real equivalent — don't fabricate one.

3. **The official RocketRide documentation is the source of truth** whenever the master prompt's assumptions and the installed/current RocketRide environment differ.

4. **Use only the officially supported RocketRide SDK/lifecycle available in the environment.** If using Python: `connect → use() → send() → terminate()`, and `terminate()` is mandatory — never omit it, per the master prompt's own warning about orphaned pipelines. Do not assume a TypeScript SDK exists unless the official documentation confirms it for this environment.

## Scope discipline

5. **Do not force unnecessary features or infrastructure.** Reuse the existing CrediFlow stack/storage where practical instead of the master prompt's suggested stack in §9. Do not add PostgreSQL, authentication, microservices, WhatsApp, or live GST APIs unless genuinely required and actually supported in this environment — the master prompt's §9 tech stack and §6 action priority are defaults, not mandates, when the existing repo already covers the need.

6. **Batch benchmark (§8 of the master prompt): report only the largest batch that actually executes successfully.** Design for thousands of records; prefer 1,000+ if stable. Never fabricate benchmark, cost, token, or performance numbers — if the real number is smaller than the target, report the real number.

7. **Any real external action (§6) must go to a dedicated test/sandbox recipient or environment.** Never send automated messages to real vendors using synthetic demo data.

8. **A signup/auth system is not mandatory** unless the existing product or actual judging requirements require it. Prioritize a stranger being able to understand and use the core workflow with no explanation, per the master prompt's §0 — that bar can be met without an account system.

## Build discipline

9. **Build and test incrementally.** After every major RocketRide milestone, actually run it, inspect the result, fix failures, and verify it before continuing. Do not silently implement the entire system in one pass.

10. **Before touching frontend polish, prove the smallest real RocketRide pipeline works end-to-end.** Then expand stage by stage, matching the build order at the end of the master prompt (§11): deterministic reconciliation → Agent A → Agent B + disagreement routing → human gate → real-world action → batch runner + cost/time dashboard → resilience pass → Cloud deploy → README/repo cleanup.

11. **If any master-prompt requirement is technically impossible in the currently available RocketRide environment, do not fake it.** Clearly identify the limitation and implement the strongest valid alternative, then note the limitation plainly in the README rather than hiding it.     Read all documents completely before making changes.

The Master Build Prompt defines WHAT we are building.
The Addendum defines HOW you must implement it safely.

Do not start by building the frontend.

First inspect the existing CrediFlow repository and the actual RocketRide environment, then follow the build order specified in the documents.

Do not modify or replace the master requirements.
Do not invent RocketRide capabilities.
Do not fabricate results.

Begin with the smallest working RocketRide pipeline and verify it before proceeding to the next stage.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-08-26T14:07:53+05:30.
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from Claude Sonnet 4.6 (Thinking) to Gemini 3.7 Flash (Medium). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>