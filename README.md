<div align="center">

<img src="https://img.shields.io/badge/CrediFlow-GST%20ITC%20Compliance%20Engine-6366f1?style=for-the-badge&logo=lightning&logoColor=white" alt="CrediFlow Banner" />

# CrediFlow
### Autonomous GST ITC Reconciliation & Vendor Compliance Nudge Engine
*Built for MSME Finance & Tax Teams under India's Rule 60 CGST Zero-Mismatch Mandate*  
*Powered by RocketRide Cloud Multi-Agent AI Pipeline*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-credi--flow--gray.vercel.app-22c55e?style=flat-square&logo=vercel)](https://credi-flow-gray.vercel.app)
[![API Docs](https://img.shields.io/badge/Swagger%20API-FastAPI%200.115-009688?style=flat-square&logo=fastapi)](https://credi-flow-gray.vercel.app/docs)
[![RocketRide Pipeline](https://img.shields.io/badge/RocketRide-.pipe%20Load--Bearing-ff4f00?style=flat-square)](pipelines/crediflow_audit_pipeline.pipe)
[![Test Suite](https://img.shields.io/badge/Tests-32%20Passed-10b981?style=flat-square)](backend/tests/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## 📌 Executive Summary

### 1. Target User
**MSME Finance Controllers, Tax Operations Leads, and GST Compliance Teams in India.**

### 2. The Core Problem
Under **Rule 60 CGST (Zero-Mismatch Mandate)** and **Section 16(2)(aa) of the CGST Act 2017**, businesses can **only claim Input Tax Credit (ITC) if their suppliers upload corresponding invoices into GSTR-1, auto-populating the buyer's GSTR-2B**. 

For typical Indian MSMEs with ₹5 Cr – ₹50 Cr ($600K – $6M) in annual turnover:
- **₹15 Lakh – ₹45 Lakh ($18K – $55K)** in working capital gets blocked every month due to supplier non-filing, timing differences, rate disparities, or B2B invoices mistakenly filed as B2C.
- Finance teams spend **40+ hours per month manually comparing Excel spreadsheets** with GSTR-2B JSON files.
- Manual phone and email follow-ups with defaulting vendors are slow, unrecorded, and legally toothless.

### 3. The CrediFlow Solution
CrediFlow turns this multi-day manual headache into an **autonomous, 15-millisecond workflow**:
1. **Automatic Multi-Format Ingestion**: Upload Purchase Register + GSTR-2B (CSV, XLSX, or JSON) via drag-and-drop.
2. **100% Deterministic Mathematical Reconciliation**: Exact MOD-36 checksum matching with **zero LLM math** (LLMs never compute tax amounts or financial liability).
3. **Load-Bearing RocketRide Cloud Pipeline**: Discrepancies are routed into a multi-agent AI pipeline defined in `.pipe`:
   - **Agent A (Classifier)** diagnoses statutory root causes (`B2B_FILED_AS_B2C`, `HSN_TAX_RATE_MISMATCH`, etc.).
   - **Agent B (Audit Cross-Examiner)** independently audits the raw facts and cross-examines Agent A (`AGREE`, `DISAGREE`, `PARTIALLY_AGREE`).
4. **Human-in-the-Loop Risk Gate**: Financial exposure ≥ ₹50,000, low confidence (<85%), or agent disagreement triggers mandatory human review.
5. **Real-World Action**: Generates official ReportLab PDF notices, persists audit trails to SQLite (`data/crediflow.db`), and dispatches bilingual WhatsApp/Email nudges.
6. **Closed-Loop Resolution**: Vendor amendment simulation triggers re-audit, verifying that blocked ITC drops to ₹0.00.

---

## 🚀 Live Application & Repository Links

- **Production URL**: [https://credi-flow-gray.vercel.app](https://credi-flow-gray.vercel.app)
- **API Documentation (Swagger/OpenAPI)**: [https://credi-flow-gray.vercel.app/docs](https://credi-flow-gray.vercel.app/docs)
- **GitHub Repository**: [https://github.com/Vaishnavi5200/CrediFlow](https://github.com/Vaishnavi5200/CrediFlow)
- **Committed Pipeline Files**: 
  - [`pipelines/crediflow_audit_pipeline.pipe`](pipelines/crediflow_audit_pipeline.pipe)
  - [`pipelines/crediflow_audit.pipe`](pipelines/crediflow_audit.pipe)

---

## ⚙️ Architecture & Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CrediFlow Frontend (React)                        │
│            Universal Dropzone · Live Pipeline Stepper · Human Gate          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Multipart / REST (JSON)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CrediFlow Backend (FastAPI / Python)                   │
│                                                                             │
│  1. FileParser & Ingestion                                                  │
│     - OpenPyXL / CSV / JSON universal reader with column alias normalization│
│     - Isolates malformed rows without crashing entire batch                 │
│                                                                             │
│  2. GSTReconciliationEngine (100% DETERMINISTIC)                            │
│     - MOD-36 GSTIN checksum validation                                      │
│     - Zero LLM arithmetic: ITC blocked exposure mathematically proven       │
│                                                                             │
│  3. RocketRide Multi-Tier Service                                           │
│     - Webhook Priority: HTTPS POST to RocketRide staging webhook            │
│     - Cloud SDK: WebSocket connection with SSE tracing                      │
│     - Fallback: Statutory Rule 60 rulebook (honest execution labeling)      │
│                                                                             │
│  4. HumanGate Service                                                       │
│     - 4-trigger policy: Disagreement | Low Conf | Exposure ≥ ₹50k | Malform │
│                                                                             │
│  5. Persistent SQLite Database Layer (`data/crediflow.db`)                  │
│     - Tables: benchmark_runs, audit_ledger, human_decisions, notice_dispatches│
│                                                                             │
│  6. Real-World Action Dispatcher                                            │
│     - Real PDF notices generated on disk via ReportLab                      │
│     - Bilingual WhatsApp / Email amendment instructions (EN + HI)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS Webhook / WSS WebSocket
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               RocketRide Pipeline (`crediflow_audit_pipeline.pipe`)         │
│                                                                             │
│  [Source: chat_input (Deterministic Mismatch Record)]                       │
│         │                                                                   │
│         ├────────────────────────────────────┐                              │
│         ▼                                    ▼                              │
│  [prompt_classifier]                  [prompt_auditor]                      │
│         │                                    │                              │
│         ▼                                    ▼                              │
│  [Agent A: Classifier]                [Agent B: Cross-Examiner]             │
│  (Taxonomy Root-Cause)                (Adversarial Audit & Scrutiny)        │
│         │                                    ▲                              │
│         └────────── text lane ───────────────┘                              │
│                                                                             │
│  Output: { root_cause_code, audit_verdict, confidence, reasoning }          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Batch Processing Benchmarks (1,000 Invoices)

CrediFlow was benchmarked against a synthetic, production-representative dataset of **1,000 invoices** spanning 10 distinct vendors, multi-rate tax brackets (5%, 12%, 18%, 28%), and realistic mismatch scenarios:

| Metric | Measured Real Value | Notes |
|---|---|---|
| **Records Processed** | **1,000 Invoices** | Complete Purchase Register vs GSTR-2B batch |
| **Wall-Clock Processing Time** | **15.71 ms** (0.016 sec) | Deterministic matching engine |
| **Throughput** | **63,662 invoices / sec** | Sub-millisecond latency for MSME accounting |
| **Discrepancies Detected** | **89 Mismatches** | Missing in 2B, value variances, HSN rate discrepancies |
| **Total Blocked ITC Exposure** | **₹8,03,485.58** | Calculated mathematically without AI hallucination |
| **High-Risk Escalations** | **3 Cases** | Blocked exposure ≥ ₹50,000 routed to Human Gate |
| **Unhandled Crashes / Retries** | **0 Failures** | Fault-isolated row processing |
| **Estimated AI Token Usage** | **57,850 Tokens** | ~650 tokens per dual-agent audit (Agent A + B) |
| **Total Batch Cost** | **$0.0174 (₹1.51 INR)** | Based on GPT-4o-mini baseline pricing |
| **Cost Per Invoice** | **$0.000017 / invoice** | < 0.002 paise per processed invoice |

> **Cost Transparency Note**: All financial arithmetic is deterministic. The dollar cost above is the estimated LLM token inference cost when running live against OpenAI/RocketRide Cloud.

---

## 🤖 Multi-Agent System (Agent A vs Agent B)

CrediFlow does **not** rely on a single LLM prompt. It implements a dual-agent checks-and-balances architecture:

1. **Agent A (Statutory Classifier)**:
   - Input: Pre-computed deterministic discrepancy JSON (amounts, tax rates, GSTIN, HSN).
   - Mission: Assign statutory root cause (`B2B_FILED_AS_B2C`, `TIMING_DIFFERENCE`, `RATE_OR_VALUE_DISCREPANCY`, `HSN_TAX_RATE_MISMATCH`, etc.).
   - Constraint: **Never computes tax amounts**.

2. **Agent B (Audit Cross-Examiner)**:
   - Input: Raw discrepancy facts + Agent A's classification.
   - Mission: Independently audit raw facts first under CGST Act Section 16(2), then cross-examine Agent A.
   - Outputs verdict: `AGREE`, `DISAGREE`, or `PARTIALLY_AGREE`.

3. **Disagreement Detection & Consensus**:
   - If Agent B disagrees or partially agrees, the consensus check fails and immediately triggers **Human Gate Escalation**.

---

## 🛡️ Human-in-the-Loop (HITL) Gate

The Human Gate safeguards financial decisions and prevents unintended vendor friction.

### The 4 Escalation Triggers:
1. **Agent Disagreement**: Agent B returns `DISAGREE` or `PARTIALLY_AGREE`.
2. **Low AI Confidence**: Agent A or B confidence falls below 85% (`CONFIDENCE_THRESHOLD=0.85`).
3. **High Financial Exposure**: Blocked ITC ≥ ₹50,000 (`HIGH_VALUE_THRESHOLD_INR=50000`).
4. **Malformed / Corrupt Data**: Invalid GSTIN checksum or unparseable line item.

### Genuine Downstream Workflow Impact:
- **`APPROVED`**: Generates notice, updates audit log, and proceeds to vendor dispatch.
- **`EDITED`**: Reviewer's custom note or amended instruction directly overrides the notice dispatch body.
- **`REJECTED`**: **Blocks dispatch (HTTP 400)**, halts notification to the supplier, marks invoice status as `WITHHELD_MANUAL_AUDIT`, and records the rejection reason in SQLite.

---

## 📦 Real-World Actions & Closed-Loop Verification

CrediFlow ensures tangible real-world outputs rather than mock notifications:

1. **Real SQLite Database Persistence (`data/crediflow.db`)**:
   - Every benchmark run, dual-agent audit, human review decision, and notice dispatch is permanently written to disk.
   - Verified via `/api/db/summary` endpoint and displayed in UI.
2. **Real ReportLab PDF Documents on Disk**:
   - Generates statutory GST ITC notices in `data/reports/` with official formatting, Section 16(2)(aa) legal notice, line-item table, and QR/payment hold clause.
   - Direct download available via `GET /api/nudge/pdf/{invoice_number}`.
3. **Bilingual Amendment Steps (English + Hindi)**:
   - Generates exact GSTR-1 amendment instructions for supplier accountants (e.g. Table 4A vs Table 9A).
4. **Closed-Loop Verification**:
   - When vendor amends their return, `/api/simulate/re-audit` re-runs deterministic matching.
   - Verifies that ITC exposure drops to ₹0.00 and records recovered working capital.

---

## 🔒 Security & Secret Hygiene

- **Zero Secrets Committed**: All credentials are read from `.env` via `python-dotenv`.
- **Git Ignored**: `.env`, `.env.local`, `*.db`, `data/reports/`, and `data/uploads/` are strictly ignored in `.gitignore`.
- **Key Architecture Clarification**:
  - **RocketRide Private Key (`rr_...`)**: Required for backend webhook/SDK execution.
  - **Publishable Key (`pk_...`)**: Only used for public frontend sessions. Using a `pk_` key in backend causes 401/400 errors.

---

## 💻 Local Setup & Execution Guide

### 1. Prerequisites
- Python 3.9+ or 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Vaishnavi5200/CrediFlow.git
cd CrediFlow

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env

# Run all 32 tests to verify compliance
pytest backend/tests/ -v

# Start FastAPI backend
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** to use the development UI, or **http://localhost:8000** for the unified production server.

---

## 🧪 Comprehensive Test Suite (32 Passed)

```bash
pytest backend/tests/ -v
```

Includes tests for:
- Deterministic reconciliation math & Rule 60 validation.
- GSTIN MOD-36 checksum verification.
- Negative amounts & malformed row isolation.
- Dual-Agent A/B consensus & disagreement triggering HITL.
- Human Gate `REJECT` blocking notice dispatch.
- Real PDF generation with `%PDF` header validation.
- Real SQLite database CRUD operations on all 4 tables.
- 1,000-invoice batch performance & cost calculations.
- Closed-loop recovery verification.

---

## 🎬 12-Step Final Demo Walkthrough

Judges and reviewers can follow this exact flow on the live app:
1. **Open Application**: Visit [credi-flow-gray.vercel.app](https://credi-flow-gray.vercel.app).
2. **Step 1 — Upload Invoices**: Click **"Fill with Demo Dataset (45 Invoices)"** or drag and drop custom CSV/Excel files into the dropzones.
3. **Step 2 — Run Audit**: Click **`[ Run Audit ]`**. Watch the visual pipeline progress: Ingest → Reconcile → ITC Calc → Agent A → Agent B → Validation.
4. **Step 3 — Inspect Deterministic Discrepancies**: See 5 discrepancies identified totaling ₹70,580.00 at-risk ITC.
5. **Step 4 — Dual-Agent Scrutiny**: Click on `INV-0881` to view Agent A (Root-Cause Classifier) and Agent B (Audit Cross-Examiner) outputs side-by-side.
6. **Step 5 — Human Gate Review**: Navigate to the **Human Gate** tab to see high-exposure and low-confidence items queued for review.
7. **Step 6 — Human Decision**: Click **Approve** or **Reject** on a pending item. Notice how rejecting an item blocks downstream notice dispatch.
8. **Step 7 — Real Document Download**: Click **Download Official PDF Document** to inspect the real ReportLab generated notice with legal citations.
9. **Step 8 — Dispatch Nudge**: Click **Dispatch Nudge** to trigger simulated WhatsApp & Email notifications with bilingual instructions.
10. **Step 9 — Closed-Loop Resolution**: Click **Simulate Vendor Filing (ARN)** to simulate the vendor amending their GSTR-1 on the GST Portal.
11. **Step 10 — Recalculation & Recovery**: The engine automatically re-reconciles: blocked ITC drops to ₹0.00, ₹42,500 ITC recovered, and celebratory confetti triggers.
12. **Step 11 — Scalability & Cost Telemetry**: Click the **Batch Scale** tab and click **`1,000 Rows`** to execute live 1,000-record batch reconciliation in 15ms at $0.0174 cost.
13. **Step 12 — SQLite Verification**: Inspect the SQLite Audit DB status card showing real persistent records in `data/crediflow.db`.

---

<div align="center">
  <sub>CrediFlow · Team Nexora · Built for RocketRide Buildathon 2026 / HackWithUP Round 2</sub>
</div>
