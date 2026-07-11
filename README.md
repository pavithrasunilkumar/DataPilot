<div align="center">

# DataPilot

### The AI Analyst for Every Business

Ask your data a question, get an analyst-grade answer — powered by RAG, MCP, and a LangGraph agent

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Version](https://img.shields.io/badge/version-0.1.0-blue) ![License](https://img.shields.io/badge/license-MIT-lightgrey) ![React](https://img.shields.io/badge/React-18-61DAFB) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688) ![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-purple)

[Live Demo](#) &nbsp;·&nbsp; [Features](#features) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Tech Stack](#tech-stack) &nbsp;·&nbsp; [Engineering Challenges](#engineering-challenges--how-they-were-solved) &nbsp;·&nbsp; [Getting Started](#getting-started) &nbsp;·&nbsp; [API Reference](#api-reference)

</div>

---

## Overview

DataPilot is a full-stack AI-driven analytics platform designed to replace the manual data-analyst workflow — clean, analyze, visualize, model, explain — with a single conversational interface. Instead of manually building charts in a BI tool, a user asks a question in plain English and receives an evidence-backed answer, grounded in real SQL execution and statistical testing, not a language model's guess.

The system combines a **React + TypeScript** frontend, a **FastAPI** backend, a **DuckDB/Pandas** analytics engine, and a **LangGraph-orchestrated agent** that uses **RAG** for business-specific context and an **MCP tool layer** for standardized, auditable tool-calling. Every AI/ML component in the stack runs on a free tier or is fully open-source and self-hosted.

---

## Features

**For Business Users**
- Ask a question in plain English and receive a SQL-backed answer, chart, and confidence-scored explanation
- Automatic data quality report on upload — missing values, duplicates, outliers, quality score
- One-click automated cleaning, or manual control per column
- Domain-aware dashboards — the platform detects whether data is Finance, Retail, Healthcare, etc. and adjusts KPIs accordingly
- Forecasting, churn prediction, and anomaly detection with SHAP-based explainability
- One-click executive PDF/PPT report generation

**For Analysts**
- Full visibility into every AI-generated SQL query, plus a manual query editor against the same dataset
- Cohort, RFM segmentation, funnel, and hypothesis-testing modules
- Statistically grounded answers — comparisons are backed by real significance tests, not model intuition
- Exportable, audit-ready analysis with documented assumptions

**Platform**
- RAG context layer — retrieves schema meaning, business glossary, and prior findings so answers reflect the specific dataset, not generic definitions
- MCP tool server — core capabilities exposed as standard, callable tools for any MCP-compatible client
- LangGraph agent orchestration — branching, stateful pipeline with retries and ML-vs-SQL routing
- JWT authentication, role-based access, background job processing via Celery/Redis
- Entirely free-tier stack — no paid API required to build or run

---

## Demo Flow

**Business User**
Register → Create Project → Upload Dataset → Data Quality Report → Auto Clean → Domain Detected & Dashboard Generated → Ask a Question → SQL + Chart + Explanation Returned → Generate Executive Report

**Analyst**
Login → Open Query Panel → Review Generated SQL → Run Custom Queries → Train a Model → Review SHAP Explanation → Schedule KPI Monitoring Alert

---

## Architecture

```
                            User
                              │
                              ▼
                    React + TypeScript (Vite)
                              │
                              ▼
                       FastAPI Backend
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   Data Engine             AI Engine              ML Engine
 (Pandas, DuckDB,     (Groq / Ollama LLM,     (Scikit-learn,
  profiling,           LangGraph graph,        XGBoost, Prophet,
  cleaning)            Chroma RAG,             SHAP)
                        MCP tool server)
        └─────────────────────┼──────────────────────┘
                              ▼
                Dashboards, Reports & Alerts
                              │
                              ▼
             PostgreSQL (Supabase) + Redis / Celery
```

Frontend: `:3000` · Backend: `:8000` · Redis (Celery broker): `:6379`

---

## Tech Stack

### Application Engineering

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18, TypeScript, Vite | UI framework and build tooling |
| Styling | Tailwind CSS | Utility-first styling |
| Charts | Recharts, Plotly.js | Interactive dashboards |
| Backend | FastAPI (Python) | REST API server |
| Background Jobs | Celery, Redis | Asynchronous cleaning and training |
| Database | PostgreSQL (Supabase free tier) | Persistence |
| Auth | JWT, bcrypt | Authentication and session management |
| Deployment | Docker, GitHub Actions, Render / Hugging Face Spaces, Vercel | CI/CD and hosting |

### Data Analysis & Statistics

| Area | Technology / Method | Purpose |
|---|---|---|
| Querying | SQL (via DuckDB), Pandas | Data extraction and transformation |
| Descriptive Statistics | NumPy, SciPy | Central tendency, dispersion, distributions |
| Inferential Statistics | t-test, chi-square, ANOVA (SciPy) | Testing whether a pattern is statistically significant |
| Correlation Analysis | Pearson, Spearman | Relationship strength between variables |
| Segmentation | RFM analysis, cohort analysis | Customer value tiers, retention behavior |
| Funnel Analysis | Custom aggregation pipelines | Conversion drop-off by stage |
| Experimentation | A/B test analysis with power analysis and confidence intervals | Validating business experiments |
| Data Visualization | Plotly, Matplotlib, Seaborn | Static and interactive chart generation |
| Reporting | Excel/CSV export, PDF and PPTX generation | Business-ready deliverables |
| BI Interoperability | CSV/JSON export compatible with Power BI and Tableau | Downstream reporting flexibility |

### Machine Learning

| Layer | Technology | Purpose |
|---|---|---|
| Modeling | Scikit-learn, XGBoost, LightGBM | Regression, classification, clustering |
| Time Series | Prophet, statsmodels | Forecasting |
| Explainability | SHAP | Feature-level prediction explanation |

### GenAI / Agent Layer

| Layer | Technology | Purpose |
|---|---|---|
| LLM | Groq API (Llama 3.3), Ollama (local fallback) | Natural language to SQL, explanation generation |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free embedding generation |
| Vector Store | Chroma | Schema documentation, glossary, and prior insight retrieval |
| Orchestration | LangChain, LangGraph | Stateful, branching agent execution |
| Tool Protocol | Model Context Protocol (MCP) | Standardized, auditable tool-calling interface |

Every tool listed above is available on a permanent free tier or is open-source and self-hostable. The project has no required paid dependency.

---

## Engineering Challenges & How They Were Solved

**Bottleneck: LLMs cannot be trusted to compute numbers correctly.**
Language models are prone to arithmetic and logical errors when asked to reason directly about numeric data. This was solved by strictly separating responsibilities: the LLM only translates a natural-language question into a SQL query and later translates a result set into an explanation. All computation — aggregation, correlation, and significance testing — is executed by DuckDB and SciPy. The LLM never performs arithmetic itself.

**Bottleneck: Generic LLM answers ignore business-specific definitions.**
A term like "churn" or "active customer" means something different for every business, and a base LLM has no way to know the local definition. This was solved with a RAG layer: schema documentation, a business glossary, and prior findings are embedded locally and retrieved as context before every query generation step, so answers stay grounded in the specific dataset.

**Bottleneck: A single linear pipeline cannot handle varied question types or failures.**
A fixed sequence (question → SQL → explanation) breaks when a query returns empty results, or when the question actually requires a forecast rather than a lookup. This was solved by rebuilding the pipeline as a LangGraph state graph with conditional edges: failed or empty queries trigger a bounded retry with a reformulated query, and questions implying prediction are routed to the ML module instead of the SQL path.

**Bottleneck: Ad hoc function-calling does not scale or generalize.**
Wiring each capability (`run_sql`, `train_model`, `generate_chart`) directly into the agent's prompt logic makes the system brittle and unusable outside the app itself. This was solved by exposing these capabilities as MCP tools, giving the platform a standardized interface that any MCP-compatible client can call.

**Bottleneck: Auto-cleaning without judgment can silently corrupt data.**
Blindly imputing or dropping data can remove signal or introduce bias, particularly when missingness is high or non-random. This was solved by setting explicit thresholds: columns with high missingness are flagged for user review rather than auto-imputed, and outliers are capped rather than deleted to avoid discarding legitimate variation.

**Bottleneck: Large or high-cardinality datasets slow down interactive analysis.**
Loading full datasets into memory for every query does not scale. This was solved by using DuckDB as the query engine, which executes SQL directly against on-disk or in-memory columnar data without requiring the full dataset to be duplicated into Pandas for every operation.

---

## Getting Started

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Node.js | 18+ | `node -v` |
| Python | 3.11+ | `python --version` |
| Docker | latest | `docker -v` |
| Groq API key (free), or Ollama installed locally | — | console.groq.com |

### Installation

```bash
git clone https://github.com/<your-username>/datapilot.git
cd datapilot
```

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Set GROQ_API_KEY, or LLM_PROVIDER=ollama for a fully local setup

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

**Or, with Docker**
```bash
docker-compose up --build
```

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Register a new user |
| POST | `/login` | Login, returns a JWT |

### Data

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/datasets/upload` | Yes | Upload CSV, XLSX, or JSON |
| GET | `/datasets/:id/quality-report` | Yes | Data profiling and quality score |
| POST | `/datasets/:id/clean` | Yes | Run automated or manual cleaning |

### AI Analyst

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/analyst/ask` | Yes | Question in, returns SQL, chart config, explanation, and confidence |
| GET | `/analyst/history/:datasetId` | Yes | Prior questions and insights (RAG memory) |

### Machine Learning

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/ml/train` | Yes | Trains and evaluates a model for a given target column |
| GET | `/ml/:modelId/explain` | Yes | SHAP feature importance |

### Reports

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/reports/generate` | Yes | Generates a downloadable PDF or PPTX report |

### MCP Tools

| Tool | Description |
|---|---|
| `run_sql` | Executes a read-only DuckDB query against the active dataset |
| `train_model` | Trains a model and returns metrics and a SHAP summary |
| `generate_chart` | Returns a chart configuration for a given result set |
| `send_report` | Sends a generated report to Slack or email |

---

## Project Structure

```
datapilot/
├── frontend/
│   ├── src/
│   │   ├── pages/            Upload, Ask, Dashboard, Reports
│   │   ├── components/       ChartCard, QueryPanel, KpiCard
│   │   └── api/               API client
│   ├── .env.example
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/                Route definitions
│   │   ├── data/               Ingestion, profiling, cleaning
│   │   ├── analytics/          Descriptive and diagnostic engine
│   │   ├── rag/                 Embeddings and Chroma retrieval
│   │   ├── ai_analyst/         NL-to-SQL-to-explanation pipeline
│   │   ├── mcp_server/         MCP tool definitions
│   │   ├── ml/                  Model training, selection, SHAP
│   │   ├── graph/               LangGraph state graph
│   │   └── reports/            PDF and PPTX generation
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Security

- Passwords hashed with bcrypt
- JWT-based session authentication
- All protected routes require `Authorization: Bearer <token>`
- SQL execution sandboxed to read-only, with row limits and query timeouts
- CORS restricted to known frontend origins

---

## Roadmap

- [x] Data ingestion and profiling
- [x] Automated cleaning
- [x] Analytics engine — descriptive and diagnostic
- [x] RAG context retrieval
- [x] AI Analyst — natural language to SQL to explanation
- [x] MCP tool server
- [x] LangGraph orchestration
- [x] ML module — classification, forecasting, SHAP
- [x] Dashboard builder
- [x] Automated report generation
- [ ] Monitoring and anomaly alerts
- [ ] Multi-agent specialization (v3)

---

## Author

**Your Name**
LinkedIn: `https://linkedin.com/in/your-handle`
GitHub: `https://github.com/your-username`
Portfolio: `https://your-portfolio-link`

## License

MIT
