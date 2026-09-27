<div align="center">

# CrediFlow
### Autonomous GST ITC Reconciliation & Vendor Compliance Nudge Engine
*Built for MSME Finance & Tax Teams under India's Rule 60 CGST Zero-Mismatch Mandate*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-credi--flow--gray.vercel.app-22c55e?style=flat-square&logo=vercel)](https://credi-flow-gray.vercel.app)
[![API Docs](https://img.shields.io/badge/Swagger%20API-FastAPI%200.115-009688?style=flat-square&logo=fastapi)](https://credi-flow-gray.vercel.app/docs)
[![Tests](https://img.shields.io/badge/Tests-93%20Passed-10b981?style=flat-square)](backend/tests/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square&logo=python)](pyproject.toml)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## Overview

CrediFlow automates India's GST Input Tax Credit (ITC) reconciliation under **Rule 60 CGST (Zero-Mismatch Mandate)** and **Section 16(2)(aa) CGST Act 2017**.

Indian MSMEs lose ₹15–₹45 lakh per month in blocked working capital because suppliers fail to upload invoices into GSTR-1, preventing the buyer's GSTR-2B from auto-populating. Finance teams spend 40+ hours monthly comparing spreadsheets manually.

CrediFlow turns this into a **sub-100ms automated workflow**.

---

## Core Workflow

```
Mismatch Detected
→ Existing deterministic result
→ Existing English + Hindi nudge
→ Try WhatsApp Business API
→ SUCCESS → Status = Nudged
→ FAILURE → wa.me fallback
→ Vendor Amendment
→ Pending Verification
→ SAME Reconciliation Engine re-runs
→ Verified only after successful reconciliation
```

---

## Architecture

```
React / Vite Frontend
        │
        ▼
FastAPI Backend
        │
        ▼
GSTReconciliationEngine
(SINGLE SOURCE OF TRUTH)
        │
 ┌──────┴──────────┐
 │                 │
 ▼                 ▼
AI Explanation     WhatsApp
Service            Delivery Service
 │                 │
 │                 ├─ WhatsApp Business API
 │                 └─ wa.me fallback
 │
 ▼
SQLite Audit Ledger
 │
 ▼
Reports / PDF
```

### Critical Design Invariants:
- **`GSTReconciliationEngine` alone owns:**
  - Invoice matching (exact, tolerance ≤₹2, near-match, tax-head, missing)
  - ITC calculation & blocked tax exposure
  - Root cause determination
  - Reconciliation outcome & status transitions
  - Verification & re-reconciliation
- **AI Explanation Service only:**
  - Explains deterministic results with statutory references
  - Generates bilingual vendor nudges (English + Hindi)
  - Full deterministic fallback if external LLM APIs are unavailable
- **WhatsApp Delivery Service only:**
  - Delivers the generated nudge via Meta WhatsApp Business Cloud API (primary)
  - Automatically provides pre-filled `wa.me` deep-link fallback on any delivery failure
  - Records communication status (`NUDGED`) without modifying financial state
- **ITC Recovery Guarantee:**
  - ITC drops to ₹0 **only** when `GSTReconciliationEngine` re-runs and confirms match
  - Vendor amendment triggers `PENDING_VERIFICATION`, never automatic resolution

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Lucide React |
| Backend | FastAPI 0.115, Python 3.10+, Uvicorn |
| Reconciliation Engine | Pure Python deterministic engine (zero LLM arithmetic) |
| AI Explanation | Gemini Flash / Groq / OpenAI GPT-4o-mini (with full deterministic fallback) |
| WhatsApp Delivery | Meta WhatsApp Business Cloud API v20.0 + wa.me fallback |
| Reports & Notices | ReportLab PDF generator |
| Database & Audit | SQLite (immutable audit ledger) |
| Deployment | Vercel (frontend static bundle + serverless ASGI backend) |

---

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
git clone https://github.com/Vaishnavi5200/CrediFlow.git
cd CrediFlow

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in required values (see Environment Variables below)

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ── LLM Provider (optional — for AI explanation) ─────────────────────────────
GEMINI_API_KEY=AIza...           # OR
GROQ_API_KEY=gsk_...             # OR
OPENAI_API_KEY=sk-proj-...

# ── WhatsApp Business API (optional — primary delivery channel) ───────────────
# Get from Meta Business Manager > WhatsApp > API Setup
WHATSAPP_API_TOKEN=              # Permanent System User Token
WHATSAPP_PHONE_NUMBER_ID=        # Phone Number ID
WHATSAPP_API_VERSION=v20.0       # Default; usually no change needed
# If not set, /api/whatsapp/send automatically falls back to wa.me

# ── Email dispatch (optional) ─────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# ── Human Gate thresholds ─────────────────────────────────────────────────────
HIGH_VALUE_THRESHOLD_INR=50000
CONFIDENCE_THRESHOLD=0.85
```

> **Security:** All credentials are server-side only. The frontend never sees API tokens, WhatsApp credentials, or SMTP passwords.

---

## WhatsApp Integration

CrediFlow uses a **primary API → automatic wa.me fallback** pattern:

1. When a mismatch is detected and the nudge is dispatched, `POST /api/whatsapp/send` is called
2. The backend generates the bilingual nudge (English + Hindi) using the AI service (or statutory fallback)
3. **If `WHATSAPP_API_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` are set** → message is sent via Meta WhatsApp Business Cloud API → `communication_status: NUDGED`
4. **On any failure** (unconfigured, timeout, rate-limit, invalid phone, bad credentials) → returns a pre-filled `wa.me` URL → frontend opens it as a new tab automatically

### To activate live WhatsApp API sending:

```bash
# In Meta Business Manager:
# 1. Create a WhatsApp Business App
# 2. Add a phone number
# 3. Generate a Permanent System User Token
# 4. Copy the Phone Number ID from the API Setup panel

WHATSAPP_API_TOKEN=<permanent-system-user-token>
WHATSAPP_PHONE_NUMBER_ID=<phone-number-id>
```

No code changes are required to switch between API mode and wa.me fallback.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/reconcile` | POST | Run deterministic reconciliation on demo dataset |
| `/api/reconcile-custom` | POST | Reconcile custom PR + GSTR-2B (JSON body) |
| `/api/upload-and-reconcile` | POST | Upload CSV/XLSX/JSON files and reconcile |
| `/api/audit` | POST | Run statutory compliance audit |
| `/api/explain` | POST | AI explanation for a reconciliation result |
| `/api/discrepancy/explain` | POST | Explanation + bilingual nudge for an invoice |
| `/api/nudge/dispatch` | POST | Dispatch PDF + email notice |
| `/api/whatsapp/send` | POST | Send WhatsApp nudge (API primary → wa.me fallback) |
| `/api/amendment/simulate` | POST | Simulate vendor GSTR-1 amendment → PENDING_VERIFICATION |
| `/api/amendment/verify` | POST | Re-run reconciliation engine → VERIFIED or ongoing mismatch |
| `/api/human-gate/queue` | GET | List human review queue |
| `/api/human-gate/decide` | POST | Submit APPROVED / EDITED / REJECTED decision |
| `/api/vendor-scorecards` | GET | Vendor compliance health scorecards |
| `/api/benchmarks` | GET | High-volume benchmark run |
| `/api/db/summary` | GET | SQLite audit trail summary |

Full interactive docs: `http://localhost:8000/docs`

---

## Demo Workflow

1. **Open** `http://localhost:5173`
2. **Run Reconciliation** → 45 demo invoices loaded; 5 mismatches detected (₹70,580 ITC at risk)
3. **Run Audit** → Deterministic Rule 60 compliance check & risk quantification
4. **Open Human Gate** → Review flagged high-value invoices (>= ₹50,000 exposure)
5. **Dispatch Nudge** → PDF generated; WhatsApp API attempted; wa.me fallback if unconfigured
6. **Simulate Amendment** → Invoice status → `PENDING_VERIFICATION`
7. **Verify** → Same engine re-runs; ITC drops to ₹0 only on confirmed match
8. **Vendor Scorecards** → VCS formula: `100 − (0.45·S_exposure + 0.35·S_frequency + 0.20·S_aging)`

---

## Project Structure

```
CrediFlow/
│
├── backend/                         # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py            # All API endpoints
│   │   ├── core/
│   │   │   ├── gst_reconciliation.py  # Deterministic engine (single source of truth)
│   │   │   ├── synthetic_data_generator.py
│   │   │   ├── file_parser.py
│   │   │   └── db.py
│   │   ├── services/
│   │   │   ├── whatsapp_delivery_service.py  # WhatsApp API + wa.me fallback
│   │   │   ├── ai_explanation_service.py     # Gemini/OpenAI + deterministic fallback
│   │   │   ├── audit_service.py              # Compliance audit coordinator
│   │   │   ├── human_gate.py                 # Human-in-the-loop risk gate
│   │   │   ├── notice_generator.py           # Bilingual nudges + ReportLab PDF
│   │   │   └── nudge_dispatcher.py
│   │   └── main.py
│   └── tests/                       # 93-test pytest suite
│
├── frontend/                        # React + Vite dashboard
│   ├── src/
│   │   ├── App.jsx                  # Single-page compliance dashboard
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── public/                      # Static assets (icons, logos)
│   ├── package.json
│   └── vite.config.js               # Dev proxy: /api → localhost:8000
│
├── api/
│   └── index.py                     # Vercel serverless ASGI entry point
│
├── data/                            # Runtime-generated (gitignored)
│   ├── crediflow.db                 # SQLite audit trail
│   ├── reports/                     # Generated PDF notices
│   └── uploads/                     # Uploaded PR/GSTR-2B files
│
├── .env.example                     # Environment variable template
├── .gitignore
├── README.md
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata + build config
├── main.py                          # Root entry point (Vercel / direct uvicorn)
└── vercel.json                      # Vercel routing config
```

---

## Running Tests

```bash
# Full suite (93 tests)
.venv/bin/python -m pytest backend/tests/ -v

# Specific modules
.venv/bin/python -m pytest backend/tests/test_phase2_reconciliation_engine.py -v
.venv/bin/python -m pytest backend/tests/test_step7_amendment_verification.py -v
.venv/bin/python -m pytest backend/tests/test_step8_final_e2e.py -v
```

---

## Deployment

The application deploys to **Vercel** automatically on push to `main`:

- Frontend (`frontend/dist/`) is served as static assets
- API routes (`/api/*`) are handled by `api/index.py` as a Python serverless function
- Configuration: [`vercel.json`](vercel.json)

**Live URL:** [https://credi-flow-gray.vercel.app](https://credi-flow-gray.vercel.app)

---

## License

MIT © 2026 Vaishnavi Dwivedi
