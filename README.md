<div align="center">

# DataPilot

### The AI Analyst for Every Business

Upload a spreadsheet. Get it profiled, cleaned, analyzed, dashboarded, predicted on, and explained — through natural language.

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Version](https://img.shields.io/badge/version-0.3.0-blue) ![License](https://img.shields.io/badge/license-MIT-lightgrey)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white) ![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Orchestration-purple) ![RAG](https://img.shields.io/badge/RAG-ChromaDB-orange) ![XGBoost](https://img.shields.io/badge/ML-XGBoost%20%2B%20SHAP-red) ![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-black) ![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)

[Features](#features) · [Architecture](#architecture) · [Tech Stack](#tech-stack) · [How It Works](#how-it-works) · [Getting Started](#getting-started) · [Deployment](#deployment) · [API Reference](#api-reference)

</div>

---

## Overview

DataPilot takes a raw spreadsheet through the entire analyst workflow — profile, clean, analyze, visualize, predict, explain, and report — through a single conversational and dashboard-driven interface. Everything computed is backed by real code (SQL, statistics, trained models); the LLM's role is strictly to translate natural language in and plain-English explanations out. It never performs arithmetic or asserts a statistical claim on its own.

**What makes this different from a typical "chat with your data" tool:**

- Every number is computed by DuckDB, pandas, scikit-learn, XGBoost, or SciPy — never invented by the LLM.
- A **Skeptic Agent** critiques every AI Analyst answer for small sample sizes, insufficient history, and marginal significance, and derives a confidence score from those checks rather than asserting one.
- **Insight Diffing** remembers past findings on the same dataset and flags contradictions.
- **RAG** grounds every answer in the dataset's own schema and a domain-specific business glossary.
- The analysis pipeline is a **LangGraph agent** — it routes diagnostic vs. forecast questions differently and retries automatically on a failed query.
- **Auto-cleaning** is conservative by design — it never silently guesses on a column that's missing 30%+ of its data; it flags it for manual review instead.
- Everything — LLM, embeddings, vector store, ML training — runs on free tiers or open-source, self-hosted components.

---

## Features

**Project & data management**
- Multiple projects per user, each an isolated workspace
- Upload CSV, Excel, or JSON — multiple datasets per project

**Automatic data profiling**
- Row/column counts, per-column dtype, missing value %, duplicate row %, IQR-based outlier detection, and an overall quality score — computed the moment a file is uploaded

**AI-driven auto-cleaning**
- One click cleans the dataset: median/mode imputation, duplicate removal, IQR outlier capping (never deletion), mistyped-column correction (numbers/dates stored as text get converted), and categorical encoding
- Columns missing 30%+ of their data are never silently imputed — they're flagged for manual review instead, and the full before/after quality score and a complete action log are returned

**Autonomous analysis**
- Runs automatically (no question required): correlation analysis across all numeric columns, trend detection with fit quality (R²), and a set of variables flagged as business-important
- A plain-English summary of these findings, grounded in the computed numbers

**Interactive dashboard generation**
- KPI cards, a time-series chart, top-category bar charts, distribution histograms, a missing-value chart, and a feature-importance chart (once a model has been trained) — generated automatically from the current (cleaned, if available) dataset, no manual chart-building required

**AI Analyst (natural language querying)**
- Ask a question in plain English; a LangGraph agent classifies it as diagnostic or forecast-related and routes accordingly
- Diagnostic questions generate and execute a real SQL query, then run a genuine Welch's t-test between the two most recent periods using the underlying raw values
- Forecast questions get a linear-trend projection with a fit-quality (R²) score
- RAG grounds every answer in the dataset's own schema, a domain-specific glossary, and prior findings
- A Skeptic Agent critiques every answer; Insight Diffing flags contradictions with past questions

**Machine learning**
- Train a real classification model (churn, fraud flag, or any categorical target) on demand: a Logistic Regression baseline and an XGBoost model are both trained and evaluated honestly (accuracy/precision/recall/F1 on a held-out test set), with SHAP-derived feature importance explaining what actually drives the prediction

**Export**
- Download the cleaned dataset as CSV
- Generate a PDF executive report: data quality summary, correlations, trends, autonomous summary, and model results if a model has been trained

---

## Architecture

```
                              User (Browser)
                                    │
                                    ▼
                   React + TypeScript frontend (Vite)
                                    │
                                    ▼
                         FastAPI backend (Python)
                                    │
   ┌──────────────┬────────────────┼───────────────┬──────────────────┐
   ▼              ▼                ▼               ▼                  ▼
Data Engine   RAG Layer        Agent Layer      ML Module         Export
(Pandas,     (ChromaDB,       (LangGraph:      (scikit-learn,    (reportlab
 DuckDB,      per-dataset      intent routing,  XGBoost, SHAP     PDF, CSV
 cleaning,    schema/glossary/ SQL retry,        feature           download)
 profiling,   insight          Skeptic Agent,    importance)
 correlation, collections)     Insight Diffing)
 trends)
   └──────────────┴────────────────┼───────────────┴──────────────────┘
                                    ▼
                        LLM (Groq Llama 3.3, or
                     deterministic offline fallback)
                                    │
                                    ▼
                       PostgreSQL (users, projects,
                    datasets, cleaning/model state, insights)
```

Frontend: `:3000` · Backend: `:8000` · PostgreSQL: `:5432` · Redis: `:6379`

---

## Tech Stack

### Application Engineering

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18, TypeScript, Vite, React Router | UI and client-side routing |
| Backend | FastAPI (Python) | REST API server |
| Database | PostgreSQL | Users, projects, datasets, cleaning/model state, insight history |
| Auth | JWT, bcrypt | Authentication and session management |
| Background Jobs | Celery, Redis | Reserved for long-running cleaning/training tasks at larger scale |
| Deployment | Docker, GitHub Actions, Vercel (frontend), Render (backend) | CI/CD and hosting |

### Data Analysis, Cleaning & Statistics

| Area | Technology / Method | Purpose |
|---|---|---|
| Querying | SQL via DuckDB, Pandas | Executing AI-generated queries against uploaded data |
| Data Quality | IQR-based outlier detection, missingness/duplicate scoring | Automated data profiling |
| Auto-Cleaning | Median/mode imputation, IQR winsorization, dtype coercion, categorical encoding | Conservative, explainable one-click cleaning |
| Correlation Analysis | Pearson correlation matrix + top-pair ranking | Relationship detection across numeric columns |
| Trend Detection | Linear regression (NumPy polyfit) with R² fit quality | Dataset-wide trend overview |
| Inferential Statistics | Welch's t-test (SciPy) | Real significance testing between time periods |
| Text Similarity | TF-IDF + cosine similarity (scikit-learn) | Insight diffing — detecting similar past questions |

### Machine Learning

| Layer | Technology | Purpose |
|---|---|---|
| Baseline Model | Logistic Regression (scikit-learn) | Honest baseline for comparison |
| Boosted Model | XGBoost | Higher-accuracy classification (churn, fraud, etc.) |
| Explainability | SHAP (TreeExplainer) | Real per-feature importance, not guessed |
| Forecasting | Linear trend extrapolation | Directional projection for forecast-type questions |

### GenAI / Agentic Layer

| Layer | Technology | Purpose |
|---|---|---|
| LLM | Groq API (Llama 3.3), deterministic fallback client | Natural language → SQL, and result → explanation |
| Vector Store | ChromaDB (persistent, per-dataset collections) | Schema docs, business glossary, past insights |
| Embeddings | Pluggable: HashingVectorizer (default, zero-dependency) or sentence-transformers (optional, true semantic matching) | Powers RAG retrieval |
| Orchestration | LangGraph | Stateful agent graph — intent routing, SQL retry, sequential critique/diff steps |
| Self-critique | Custom Skeptic Agent module | Concrete, checklist-based critique of every finding |

### Export

| Layer | Technology | Purpose |
|---|---|---|
| PDF Reports | ReportLab (Platypus) | Structured executive report generation |
| CSV Export | Pandas | Cleaned dataset download |

Every component above runs on a free tier or is open-source and self-hostable.

---

## How It Works

**Upload → Profile → Clean**
1. A file is uploaded; pandas reads it and the profiling engine computes missing %, duplicate %, IQR outliers, and a quality score per column
2. Domain is detected from column names (retail, finance, healthcare, SaaS, or general), which seeds a starter business glossary into the RAG store
3. On request, the cleaning engine fixes what profiling found — imputing, deduplicating, capping outliers, and correcting mistyped columns — while flagging (not guessing on) any column too sparse to safely auto-fill

**Autonomous analysis & dashboard**
4. Correlation and trend detection run automatically over the (cleaned) dataset
5. The dashboard endpoint assembles KPI cards, a time series, category bar charts, distribution histograms, and a feature-importance chart (if a model has been trained) into a single structured response the frontend renders with Recharts

**Ask a question (AI Analyst)**
6. A LangGraph agent classifies the question as diagnostic or forecast-related
7. RAG retrieves schema notes, glossary terms, and prior findings for this specific dataset
8. Diagnostic path: the LLM (or offline fallback) generates a DuckDB SQL query, which executes with a retry-once-on-empty-result policy; a real Welch's t-test compares the two most recent periods using raw values
9. Forecast path: a linear trend is fit directly on the historical data and projected forward
10. The LLM writes a plain-English explanation grounded in the computed numbers — never inventing a significance claim
11. The Skeptic Agent flags small sample sizes, insufficient history, marginal significance, or poor trend fit, and derives a confidence score from those flags
12. Insight Diffing compares the new answer against the most similar past question on this dataset and surfaces any contradiction

**Predict**
13. Training a model on a chosen target column runs a real train/test split, trains both a Logistic Regression baseline and an XGBoost model, evaluates both honestly, and explains the better one with SHAP

**Export**
14. The cleaned dataset can be downloaded as CSV; a PDF report packages the quality summary, correlations, trends, autonomous summary, and model results into a shareable document

```python
question = "Why did revenue decrease in March?"
# -> LangGraph classifies: diagnostic
# -> RAG context: business glossary + schema notes for this dataset
# -> SQL: SELECT date_trunc('month', date), SUM(revenue) FROM dataset GROUP BY 1
# -> stat test: Welch's t-test, March vs February, p = 0.03 (significant)
# -> explanation: grounded in the p-value and glossary above
# -> skeptic: flags "only 6 months of history — seasonality not ruled out"
# -> diff: "last month a similar question found pricing was the driver — this
#           month it's usage decline; pricing is no longer significant"
```

---

## Getting Started

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Node.js | 18+ | `node -v` |
| Python | 3.11+ | `python --version` |
| Docker | latest (optional, recommended) | `docker -v` |
| Groq API key (free, optional) | — | console.groq.com |

DataPilot runs immediately with **no API key** — the AI Analyst and autonomous analysis both use a deterministic offline fallback, so the entire pipeline is testable and demoable with zero setup. Add a Groq key later for real natural-language SQL generation and explanations.

### Option A — Docker (recommended)

```bash
git clone https://github.com/<your-username>/datapilot.git
cd datapilot
cp backend/.env.example backend/.env
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend docs (Swagger): http://localhost:8000/docs

### Option B — Run manually

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Optionally set GROQ_API_KEY in .env for real LLM responses

uvicorn app.main:app --reload
# Running on http://localhost:8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
# Running on http://localhost:3000
```

### Running the tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
# 14 tests covering auth, profiling, cleaning, autonomous analysis,
# ML training, dashboard generation, PDF export, RAG, and the
# agentic AI Analyst pipeline (including the Skeptic Agent and diffing)
```

---

## Deployment

DataPilot deploys as two separate services: the **frontend on Vercel** and the **backend + database on Render**. FastAPI with a persistent database, ML training, and AI pipeline calls doesn't fit Vercel's serverless model well, so the backend needs a real always-on host — Render's free tier works well here.

### Backend → Render

1. Push this repository to GitHub.
2. In Render: **New → Blueprint**, select this repo. Render reads `render.yaml` at the repo root and provisions the API service and a free Postgres database automatically.
3. Once deployed, open the service's **Environment** tab and set `GROQ_API_KEY` (optional — leave unset to keep running in offline demo mode).
4. Note the deployed backend URL (e.g. `https://datapilot-api.onrender.com`) — you'll need it for the frontend.

### Frontend → Vercel

1. In Vercel: **Add New → Project**, import this repository.
2. Set the **Root Directory** to `frontend`.
3. Vercel auto-detects the Vite framework and reads `frontend/vercel.json` for build settings.
4. Under **Environment Variables**, add:
   ```
   VITE_API_URL = https://<your-render-backend-url>
   ```
5. Deploy. Vercel will build and serve the frontend as a static SPA.

### Notes

- Render's free tier spins down after inactivity — the first request after idling will be slow (cold start) while the instance wakes up, and ML training (XGBoost + SHAP) adds noticeable import time on cold start specifically.
- CORS: the backend's allowed origins are set in `backend/app/main.py`. Add your deployed Vercel URL there before going live.
- Uploaded files, cleaned datasets, and the Chroma vector store are written to local disk on the backend service. On Render's free tier this storage is ephemeral (cleared on redeploy) — for persistent production use, mount a persistent disk or move file storage to S3/Supabase Storage.

---

## API Reference

| Area | Endpoint | Description |
|---|---|---|
| Auth | `POST /register`, `POST /login` | Account creation and JWT login |
| Projects | `POST /projects`, `GET /projects` | Workspace management |
| Datasets | `POST /datasets/upload`, `GET /datasets` | Upload and list datasets |
| Datasets | `GET /datasets/{id}/quality-report` | Data quality profiling |
| Cleaning | `POST /datasets/{id}/clean` | Runs the auto-cleaning engine |
| Cleaning | `GET /datasets/{id}/export/cleaned` | Downloads the cleaned CSV |
| Analysis | `GET /datasets/{id}/analysis` | Autonomous correlation/trend analysis + summary |
| Dashboard | `GET /datasets/{id}/dashboard` | Full dashboard spec (KPIs, charts, feature importance) |
| AI Analyst | `POST /analyst/{id}/ask` | Natural-language question → SQL/forecast, explanation, critique, diff |
| AI Analyst | `GET /analyst/{id}/history` | Past questions and findings |
| ML | `POST /ml/{id}/train?target_column=...` | Trains and evaluates a classification model |
| ML | `GET /ml/{id}/model-info` | Retrieves the last trained model's results |
| Export | `POST /datasets/{id}/export/report` | Generates and downloads a PDF executive report |

Full interactive documentation is available at `/docs` (Swagger UI) once the backend is running.

---

## Project Structure

```
datapilot/
├── frontend/
│   ├── src/
│   │   ├── api/                 API client (typed fetch wrapper)
│   │   ├── context/              Auth, default project, and dataset state
│   │   ├── pages/                Login, Datasets, Dashboard, AskAnalyst, History
│   │   ├── components/           Shared UI primitives (Bezel, ReadoutCard, etc.)
│   │   └── styles/               Global theme (CSS variables)
│   ├── vercel.json
│   ├── .env.example
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/                  Route definitions (auth, projects, datasets, analyst, ml)
│   │   ├── core/                 Config, database session, security/JWT
│   │   ├── models/                SQLAlchemy models
│   │   ├── schemas/               Pydantic request/response schemas
│   │   ├── data/                  Profiling, auto-cleaning, autonomous analysis
│   │   ├── rag/                   Embeddings, vector store, auto-context generation
│   │   ├── ai_analyst/            LLM client, SQL execution, stats, forecasting,
│   │   │                          Skeptic Agent, insight diffing, LangGraph orchestration
│   │   ├── ml/                    Classification training (XGBoost + SHAP)
│   │   ├── dashboard/             Dashboard spec generator
│   │   └── export/                PDF report generator
│   ├── tests/                     14 tests across every module above
│   ├── .env.example
│   └── requirements.txt
│
├── render.yaml
├── docker-compose.yml
├── .github/workflows/backend-ci.yml
├── .gitignore
└── README.md
```

---

## Engineering Notes & Known Limitations

Being direct about what's simplified, since this matters for anyone evaluating the project:

- **Default RAG embeddings use a hashing vectorizer, not a true semantic model.** Deliberate zero-dependency default so the project runs immediately with no model download. It catches shared-word similarity well but misses synonyms. Set `EMBEDDING_BACKEND=sentence-transformers` (and `pip install sentence-transformers`) for genuine semantic matching.
- **Forecasting uses linear trend extrapolation**, not a seasonally-aware model like Prophet. It's intentionally simple so the LangGraph forecast branch has a real, working path.
- **The ML module handles classification only** (churn, fraud flags, any categorical target with ≤10 classes) — regression targets and continuous prediction aren't supported by the current `/ml/train` endpoint.
- **Statistical significance testing compares only the two most recent time periods** with a Welch's t-test — it doesn't yet generalize to arbitrary group comparisons implied by more complex questions.
- **File storage is local disk**, not S3/object storage — fine for demo/portfolio use, but should be swapped for persistent storage before any real production use.
- **No multi-user collaboration/sharing yet** — each project is private to its owner. Invite links and shared permissions are a natural next step but a genuinely separate auth feature, not yet built.

---

## Roadmap

- [x] Data ingestion, profiling, and domain detection
- [x] Auto-cleaning engine (imputation, dedup, outlier capping, dtype correction, encoding)
- [x] Autonomous analysis (correlation, trend detection, plain-English summary)
- [x] Interactive dashboard generation (KPIs, time series, histograms, feature importance)
- [x] RAG-grounded AI Analyst (SQL generation + explanation)
- [x] Real statistical significance testing (Welch's t-test)
- [x] Skeptic Agent (structured self-critique)
- [x] Insight Diffing (contradiction detection across questions)
- [x] LangGraph agentic orchestration (intent routing, SQL retry)
- [x] ML module (XGBoost classification + SHAP explainability)
- [x] Export: cleaned CSV + PDF executive report
- [x] Frontend wired to every endpoint above
- [x] Vercel + Render deployment configuration
- [ ] Regression / continuous-target ML support
- [ ] Prophet-based seasonal forecasting
- [ ] Multi-user collaboration and project sharing
- [ ] Monitoring and scheduled anomaly alerts
- [ ] Sentence-transformer embeddings as the default RAG backend

---

## License

MIT
