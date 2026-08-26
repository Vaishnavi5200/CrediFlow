<div align="center">

<img src="https://img.shields.io/badge/CrediFlow-GST%20Compliance%20Engine-6366f1?style=for-the-badge&logo=lightning&logoColor=white" />

# CrediFlow

**Autonomous GST ITC Compliance & Vendor Nudge Engine**  
*Powered by RocketRide Dual-Agent AI Pipeline under India's Rule 60 CGST*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-credi--flow--gray.vercel.app-22c55e?style=flat-square&logo=vercel)](https://credi-flow-gray.vercel.app)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## 🧠 What is CrediFlow?

CrediFlow is an **end-to-end autonomous GST ITC compliance engine** that identifies, audits, and resolves mismatches between a buyer's Purchase Register and their auto-drafted GSTR-2B. It runs a **RocketRide dual-agent AI pipeline** — Agent A classifies the root cause, Agent B independently cross-examines the verdict — and routes edge cases to a **Human-in-the-Loop gate** for manual decision.

> Built for India's **Rule 60 CGST zero-mismatch mandate** — every blocked rupee of ITC is tracked, flagged, and actioned automatically.

---

## ⚡ Live Demo

**🌐 [https://credi-flow-gray.vercel.app](https://credi-flow-gray.vercel.app)**

| Feature | URL |
|---|---|
| Dashboard | `/` |
| API Swagger Docs | `/docs` |
| Reconcile | `POST /api/reconcile` |
| Dual-Agent Audit | `POST /api/audit` |
| Human Gate Queue | `GET /api/human-gate/queue` |
| Benchmarks | `GET /api/benchmarks?count=1000` |

---

## 🗂️ Architecture

```
CrediFlow/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI app — serves API + frontend SPA
│       ├── api/
│       │   └── routes.py              # All API endpoints
│       ├── core/
│       │   ├── gst_reconciliation.py  # Deterministic MOD-36 matching engine
│       │   └── synthetic_data_generator.py
│       └── services/
│           ├── rocketride_service.py  # Dual-agent AI pipeline (Agent A + B)
│           ├── human_gate.py          # Human-in-the-loop decision queue
│           ├── notice_generator.py    # PDF + bilingual Rule 60 notice
│           └── nudge_dispatcher.py    # WhatsApp + Email dispatch
├── frontend/
│   └── src/
│       ├── App.jsx                    # Full React dashboard
│       └── index.css                  # Design system (light/dark)
├── pipelines/
│   └── crediflow_audit_pipeline.pipe  # RocketRide pipeline config
├── api/
│   └── index.py                       # Vercel serverless adapter
├── vercel.json                        # Vercel deployment config
└── pyproject.toml                     # Python project manifest
```

---

## 🚀 The RocketRide Pipeline

```
Upload PR + GSTR-2B
        ↓
   [1] INGEST  →  RocketRide Data Lanes
        ↓
   [2] RECONCILE  →  Deterministic MOD-36 Python Engine (zero LLM math)
        ↓
   [3] ITC CALC  →  ₹ Blocked Exposure per Discrepancy
        ↓
   [4] AGENT A  →  Root-Cause Classifier (B2B_FILED_AS_B2C / RATE_DIFF / HSN_MISMATCH...)
        ↓
   [5] AGENT B  →  Independent Audit Cross-Examiner (AGREE / DISAGREE / PARTIALLY_AGREE)
        ↓
   [6] VALIDATION  →  Confidence check + Risk routing
        ↓
   [7] HUMAN GATE  →  4 triggers: Agent disagreement | Confidence < 85% | High ITC | Malformed
        ↓
   [8] ACTION  →  PDF Notice + WhatsApp + Email Rule 60 nudge
        ↓
   [9] VERIFY  →  Re-reconcile after vendor amendment → ITC recovered ✓
```

### Human Gate Triggers
| Trigger | Condition |
|---|---|
| 🤖 Agent Disagreement | Agent B verdict = DISAGREE or PARTIALLY_AGREE |
| 📉 Low Confidence | Agent A or B confidence < 85% |
| 💰 High ITC Exposure | Blocked ITC ≥ ₹50,000 |
| ⚠️ Malformed Input | Invalid GSTIN checksum or negative values |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI 0.115, Python 3.10+, Pydantic v2 |
| **AI Pipeline** | RocketRide SDK (dual-agent, SSE streaming) |
| **Reconciliation** | Deterministic MOD-36 Python engine |
| **Frontend** | React 18, Vite, Vanilla CSS |
| **PDF Notices** | ReportLab |
| **Deployment** | Vercel (serverless Python + static) |
| **Dev Server** | Uvicorn (local), Vercel (production) |

---

## 🏃 Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Clone the repo

```bash
git clone https://github.com/Vaishnavi5200/CrediFlow.git
cd CrediFlow
```

### 2. Set up Python environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env — set ROCKETRIDE_URI, ROCKETRIDE_APIKEY, OPENAI_API_KEY
```

### 4. Start the backend

```bash
uvicorn backend.app.main:app --port 8000 --reload
```

### 5. Start the frontend (dev mode)

```bash
cd frontend
npm install
npm run dev        # Runs on http://localhost:3000
```

### 6. Build frontend for production

```bash
cd frontend
npm run build      # Outputs to frontend/dist/
```

Backend serves the built frontend at **http://localhost:8000**

---

## 🌐 Deploy to Vercel

```bash
# One-time setup (already linked)
npx vercel --prod --yes
```

Or just push to `main` — Vercel auto-deploys on every push.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/demo-data` | Load 45-invoice demo dataset |
| `POST` | `/api/reconcile` | Run deterministic PR vs GSTR-2B match |
| `POST` | `/api/audit` | Run RocketRide dual-agent AI audit |
| `GET` | `/api/human-gate/queue` | Get pending human review items |
| `POST` | `/api/human-gate/decide` | Submit human APPROVE / REJECT decision |
| `POST` | `/api/nudge/dispatch` | Send Rule 60 notice via WhatsApp + Email |
| `GET` | `/api/nudge/preview` | Preview bilingual nudge text |
| `POST` | `/api/simulate/vendor-amend` | Simulate vendor GST amendment |
| `POST` | `/api/simulate/re-audit` | Re-run reconciliation after amendment |
| `GET` | `/api/vendor-scorecards` | Vendor compliance risk scorecards |
| `GET` | `/api/benchmarks?count=N` | Batch performance benchmark (50–2000 records) |
| `GET` | `/docs` | Interactive Swagger UI |

---

## 📊 Benchmarks

| Metric | Value |
|---|---|
| Records processed | 1,000 |
| Throughput | ~450 invoices/sec |
| Avg latency per record | < 2.5ms |
| Dual-agent audit (fallback) | < 15ms per mismatch |
| Human review trigger rate | ~3–7% |

> Benchmarks run via `GET /api/benchmarks?count=1000` — all numbers are measured, never hardcoded.

---

## 📁 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ROCKETRIDE_URI` | WebSocket URI for RocketRide server | `ws://localhost:52257` |
| `ROCKETRIDE_APIKEY` | API key for RocketRide | `MYAPIKEY` |
| `OPENAI_API_KEY` | OpenAI key for LLM pipeline nodes | *(optional)* |
| `CONFIDENCE_THRESHOLD` | Minimum agent confidence before human gate | `0.85` |
| `HIGH_VALUE_THRESHOLD_INR` | ITC amount triggering human gate | `50000` |

---

## 🧪 Running Tests

```bash
# Activate venv first
source .venv/bin/activate

# Run all tests
pytest backend/tests/ -v
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👩‍💻 Author

**Vaishnavi Dwivedi**  
[![GitHub](https://img.shields.io/badge/GitHub-Vaishnavi5200-181717?style=flat-square&logo=github)](https://github.com/Vaishnavi5200)

---

<div align="center">
  <sub>Built with FastAPI · React · RocketRide · Rule 60 CGST</sub>
</div>
