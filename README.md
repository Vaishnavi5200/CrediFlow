<div align="center">

<img src="https://img.shields.io/badge/CrediFlow-GST%20Compliance%20Engine-6366f1?style=for-the-badge&logo=lightning&logoColor=white" />

# CrediFlow

**Autonomous GST ITC Compliance & Vendor Nudge Engine**  
*Powered by RocketRide Cloud Multi-Agent AI Pipeline under India's Rule 60 CGST*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-credi--flow--gray.vercel.app-22c55e?style=flat-square&logo=vercel)](https://credi-flow-gray.vercel.app)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## 🧠 Overview

CrediFlow is an **autonomous GST compliance & Input Tax Credit (ITC) recovery engine** designed to enforce India's **Rule 60 CGST zero-mismatch mandate**. It ingests a buyer's Purchase Register alongside auto-drafted GSTR-2B streams, executes deterministic MOD-36 mathematical reconciliation (zero LLM arithmetic), and passes all detected discrepancies into a **RocketRide Cloud multi-agent AI pipeline**:

- **Agent A (Classifier)**: Ingests the raw discrepancy record and classifies statutory root causes (e.g., `B2B_FILED_AS_B2C`, `RATE_OR_VALUE_DISCREPANCY`, `TIMING_DIFFERENCE`).
- **Agent B (Audit Cross-Examiner)**: Independently scrutinizes the raw facts against the CGST Act 2017 and adversarial cross-examines Agent A (`AGREE`, `DISAGREE`, `PARTIALLY_AGREE`).
- **Human-in-the-Loop Gate**: Automatically routes cases with agent disagreement, confidence < 85%, exposure ≥ ₹50,000, or malformed data to finance managers.
- **Closed-Loop Resolution**: Generates formal Rule 60 notices with bilingual actionable instructions (English + Hindi), dispatches WhatsApp/Email nudges, and verifies credit recovery.

---

## 🌐 Live Application

- **Interactive Dashboard**: [https://credi-flow-gray.vercel.app](https://credi-flow-gray.vercel.app)
- **FastAPI OpenAPI Swagger**: [https://credi-flow-gray.vercel.app/docs](https://credi-flow-gray.vercel.app/docs)

---

## 📐 System Architecture

```
┌────────────────────────────────────────────────────────┐
│               CrediFlow Frontend (React)              │
│       Vite SPA · Workflow Stepper · Studio UI          │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON / FormData)
                            ▼
┌────────────────────────────────────────────────────────┐
│            CrediFlow Server (FastAPI / Python)         │
│                                                        │
│  1. GSTReconciliationEngine                            │
│     - Deterministic MOD-36 Checksum Matching           │
│     - Exact ITC Blocked Exposure Calculation           │
│                                                        │
│  2. AuditService                                       │
│     - Orchestrates audit flow & normalizes outputs     │
│                                                        │
│  3. RocketRideService                                  │
│     - Connects via RocketRide Client SDK               │
│     - WebSocket SSE streaming & session management     │
│     - Multi-tier resilience: live cloud + fallback     │
│                                                        │
│  4. HumanGate Service                                  │
│     - 4-trigger policy evaluation                      │
│                                                        │
│  5. Notice & Nudge Dispatcher                          │
│     - ReportLab PDF + Bilingual GST amendments         │
└───────────────────────────┬────────────────────────────┘
                            │ WebSocket / SSE (Encrypted)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 RocketRide Cloud                       │
│     pipelines/crediflow_audit.pipe                     │
│                                                        │
│  [Source: chat_input]                                  │
│         │                                              │
│         ├──────────────────────────┐                   │
│         ▼                          ▼                   │
│  [prompt_classifier]        [prompt_auditor]           │
│         │                          │                   │
│         ▼                          ▼                   │
│  [Agent A: Classifier]      [Agent B: Auditor]         │
│  (DeepAgent Profile)        (Adversarial Audit)        │
│         │                          ▲                   │
│         └─────────── text ─────────┘                   │
└────────────────────────────────────────────────────────┘
```

---

## 🔌 RocketRide Cloud Pipeline Integration

### 1. Environment Variables

Create or update your `.env` file in the project root:

```bash
# RocketRide Cloud / Local Engine
ROCKETRIDE_URI=wss://api.rocketride.ai  # or your dedicated cloud workspace URI
ROCKETRIDE_AUTH=your_rocketride_auth_token_here

# OpenAI API Key (injected server-side into pipeline LLM nodes)
OPENAI_API_KEY=your_openai_api_key_here

# Human Gate Policy Settings
HIGH_VALUE_THRESHOLD_INR=50000
CONFIDENCE_THRESHOLD=0.85
```

> **Security Note**: Credentials remain strictly on the backend and are **never** exposed to browser/client-side code.

---

### 2. Pipeline Definition File

The pipeline specification is stored in:
- [`pipelines/crediflow_audit.pipe`](pipelines/crediflow_audit.pipe)

#### Pipeline Flow:
```
Input (Chat Source)
  │
  ├──► [prompt_classifier] ──► [Agent A: Classifier] ──► LLM (OpenAI)
  │                                     │
  │                                     ▼ (Cross-Examination Lane)
  └──► [prompt_auditor]    ──► [Agent B: Auditor]    ──► LLM (OpenAI)
```

---

### 3. Manual RocketRide Cloud Setup Steps

To deploy and link this pipeline to your **RocketRide Cloud workspace**:

1. **Log in to RocketRide**: Navigate to your RocketRide Cloud dashboard at [https://app.rocketride.ai](https://app.rocketride.ai).
2. **Open Pipeline Builder**: Click **New Pipeline** or **Import Pipeline**.
3. **Import `.pipe` Configuration**: Select `Import from JSON` and upload `pipelines/crediflow_audit.pipe`.
4. **Configure LLM Providers**:
   - In the `OpenAI (Classifier)` node, select or add your OpenAI credentials.
   - In the `OpenAI (Auditor)` node, verify the profile association.
5. **Publish / Deploy**: Click **Publish** in the top right to deploy the pipeline to your Cloud Workspace.
6. **Obtain Connection Details**:
   - Copy your **Workspace WebSocket URI** (e.g. `wss://<workspace-id>.rocketride.ai`).
   - Generate an **Auth Token / API Key** under *Settings → API Keys*.
7. **Update CrediFlow Server**:
   ```bash
   ROCKETRIDE_URI=wss://<workspace-id>.rocketride.ai
   ROCKETRIDE_AUTH=<your-api-key>
   ```

---

## 🔄 Dual Execution Modes: Cloud vs. Fallback

CrediFlow is engineered for **resilience and deterministic compliance**:

| Feature | RocketRide Cloud Pipeline | Statutory Fallback Engine |
|---|---|---|
| **Root-Cause Classification** | Live LLM via Agent A (DeepAgent) | Deterministic Rule 60 GST Taxonomy |
| **Audit Cross-Examination** | Adversarial Agent B Cross-Examiner | Statutory Section 16(2) Validator |
| **Mathematical Reconcile** | 100% Deterministic Python MOD-36 | 100% Deterministic Python MOD-36 |
| **Human Risk Gate** | Evaluated on all 4 triggers | Evaluated on all 4 triggers |
| **Output Schema** | Normalized JSON Findings & Evidence | Normalized JSON Findings & Evidence |
| **Indicator in UI** | `● ROCKETRIDE CLOUD LIVE` | `● STATUTORY RULE 60 ENGINE` |

> CrediFlow **never fakes execution**. The UI clearly shows which engine processed each run.

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Setup Backend

```bash
# Clone the repository
git clone https://github.com/Vaishnavi5200/CrediFlow.git
cd CrediFlow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
uvicorn backend.app.main:app --port 8000 --reload
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:3000** for Vite development or **http://localhost:8000** for the unified backend.

---

## 🧪 Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run test suite
pytest backend/tests/ -v
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/demo-data` | Returns the official 45-invoice demo dataset |
| `POST` | `/api/reconcile` | Runs deterministic Purchase Register vs GSTR-2B reconciliation |
| `POST` | `/api/audit` | Executes RocketRide dual-agent AI audit & Human Gate routing |
| `POST` | `/api/reconcile-custom` | Audits custom uploaded CSV/XLSX/JSON files |
| `GET` | `/api/human-gate/queue` | Lists items pending manual review |
| `POST` | `/api/human-gate/decide` | Submits human APPROVE / REJECT / EDIT decision |
| `POST` | `/api/nudge/dispatch` | Dispatches Rule 60 notice via WhatsApp + Email |
| `GET` | `/api/benchmarks?count=1000` | Measures batch throughput and cost metrics |
| `GET` | `/docs` | Interactive OpenAPI Swagger documentation |

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">
  <sub>CrediFlow · Built with FastAPI, React, RocketRide, and Rule 60 CGST</sub>
</div>
