# DataPilot — The AI Analyst for Every Business

🌐 Live Deployment — *Add your deployed link here*

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Version](https://img.shields.io/badge/version-0.1.0-blue) ![React](https://img.shields.io/badge/React-18-61DAFB) ![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688) ![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-purple) ![RAG](https://img.shields.io/badge/RAG-Chroma-orange) ![MCP](https://img.shields.io/badge/MCP-Tool%20Protocol-black) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

Ask your data a question, get an analyst-grade answer · RAG + MCP + LangGraph agent · $0 free-tier stack

[Features](#-features) · [Demo Flow](#-demo-flow) · [Architecture](#️-architecture) · [Tech Stack](#️-tech-stack) · [Getting Started](#-getting-started) · [API Reference](#-api-reference)

---

DataPilot is a full-stack AI-driven analytics platform designed to replace the manual data-analyst workflow — clean, analyze, visualize, model, explain — with a single conversational interface. Instead of dragging chart widgets around a BI dashboard, a user simply asks a question in plain English and gets back an evidence-backed answer.

The system integrates a **React + TypeScript** frontend, a **FastAPI** backend, a **DuckDB/Pandas** analytics engine, and a **LangGraph-orchestrated AI agent** that combines **RAG** (for business-specific context) and an **MCP tool layer** (for standardized, auditable tool-calling) to turn natural-language questions into real SQL queries, statistical tests, and plain-English explanations — not guesses.

Every LLM/embedding/vector-store component runs on a permanent free tier or fully open-source/self-hosted, so the entire project costs $0 to build and demo.

---

## ✨ Features

### For Business Users
- **Ask-a-Question AI Analyst** — type "why did revenue drop this quarter?" and get a real SQL-backed answer, chart, and confidence-scored explanation
- **Auto Data Quality Report** — upload a CSV/Excel/JSON and instantly see missing values, duplicates, outliers, and a quality score
- **One-Click Auto Clean** — automated imputation, duplicate removal, and outlier handling, or switch to manual control per column
- **Domain-Aware Dashboards** — DataPilot detects whether your data is Finance, Retail, Healthcare, etc. and auto-builds the relevant KPI dashboard
- **Forecasting & Prediction** — churn prediction, demand forecasting, anomaly detection, with SHAP-based explanations of *why* the model predicted what it did
- **Executive Reports** — one click generates a downloadable PDF/PPT summary with insights, risks, and recommendations

### Platform / Engineering
- **RAG Context Layer** — retrieves schema meaning, business glossary, and past findings so answers reflect *your* data's definitions, not generic ones
- **MCP Tool Server** — `run_sql`, `train_model`, `generate_chart`, `send_report` exposed as standard MCP tools, callable from any MCP-compatible client
- **LangGraph Agent Orchestration** — the question → SQL → stats → explanation flow runs as a branching, stateful graph with retries and ML-vs-SQL routing
- **JWT Authentication** — secure login, role-based access
- **Background Jobs** — Celery + Redis handle cleaning/training without blocking the API
- **Fully Free Stack** — Groq (or local Ollama), Chroma, sentence-transformers, Supabase — no paid API required anywhere

---

## 🎬 Demo Flow

**Business User**
Register → Create Project → Upload Dataset (or connect DB) → Auto Data Quality Report → Auto Clean → Domain Detected + Dashboard Generated → Ask "why did revenue drop?" → SQL + Chart + Explanation returned → Generate Executive Report (PDF)

**Analyst / Power User**
Login → Open Query Panel → View AI-generated SQL → Edit/run custom SQL against same DuckDB table → Train a churn model → View SHAP explanation → Schedule KPI monitoring alert

---

## 🏗️ Architecture

```
                        User
                          │
                          ▼
                React + TypeScript (Vite)
                          │
                          ▼
                   FastAPI Backend
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   Data Engine        AI Engine           ML Engine
 (Pandas, DuckDB,   (Groq/Ollama LLM,   (Scikit-learn,
  profiling &        LangGraph graph,    XGBoost, Prophet,
  cleaning)          Chroma RAG,         SHAP explainability)
                      MCP tool server)
        └─────────────────┼──────────────────┘
                          ▼
              Dashboards, Reports & Alerts
                          │
                          ▼
                PostgreSQL (Supabase) + Redis/Celery
```
`:3000` frontend · `:8000` FastAPI backend · `:6379` Redis (Celery broker)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + TypeScript | UI framework |
| Styling | Tailwind CSS | Utility-first CSS |
| Charts | Recharts / Plotly.js | Interactive dashboards |
| Backend | FastAPI (Python) | REST API server |
| Background Jobs | Celery + Redis | Async cleaning/training |
| Database | PostgreSQL (Supabase free tier) | Persistence |
| Data Engine | Pandas, Polars, NumPy, SciPy | Cleaning & stats |
| Query Engine | DuckDB | SQL execution over uploaded data |
| ML | Scikit-learn, XGBoost, LightGBM, Prophet, SHAP | Prediction & explainability |
| LLM | Groq API (Llama 3.3) / Ollama (local fallback) | NL → SQL, explanations |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free RAG embeddings |
| Vector Store | Chroma | Schema docs, glossary, past insights |
| Orchestration | LangChain / LangGraph | Stateful agent graph |
| Tool Protocol | MCP (Model Context Protocol) | Standardized tool-calling |
| Auth | JWT + bcrypt | Secure authentication |
| Deployment | Docker, GitHub Actions, Render/Hugging Face Spaces, Vercel | CI/CD & hosting |

Every tool above has a permanent free tier or is fully open-source and self-hostable — **$0/month to build and demo.**

---

## 🚀 Getting Started

### Prerequisites
| Tool | Version | Check |
|---|---|---|
| Node.js | 18+ | `node -v` |
| Python | 3.11+ | `python --version` |
| Docker | latest | `docker -v` |
| Groq API key (free) *or* Ollama installed locally | — | [console.groq.com](https://console.groq.com) |

### Installation

Clone the repository
```bash
git clone https://github.com/<your-username>/datapilot.git
cd datapilot
```

**Terminal 1 — Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Add GROQ_API_KEY, or set LLM_PROVIDER=ollama for fully local/offline

uvicorn app.main:app --reload
# ✅ Running on http://localhost:8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
# ✅ Running on http://localhost:3000
```

**Or, everything at once with Docker**
```bash
docker-compose up --build
```

---

## 📡 API Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Register a new user |
| POST | `/login` | Login → returns JWT |

### Data
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/datasets/upload` | ✅ | Upload CSV/XLSX/JSON |
| GET | `/datasets/:id/quality-report` | ✅ | Data profiling & quality score |
| POST | `/datasets/:id/clean` | ✅ | Run auto/manual cleaning |

### AI Analyst
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/analyst/ask` | ✅ | `{question}` → `{sql, chart_config, explanation, confidence}` |
| GET | `/analyst/history/:datasetId` | ✅ | Past questions & insights (RAG memory) |

### ML
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/ml/train` | ✅ | `{target_column, model_type}` → trains + evaluates model |
| GET | `/ml/:modelId/explain` | ✅ | SHAP feature importance |

### Reports
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/reports/generate` | ✅ | Generates downloadable PDF/PPTX executive report |

### MCP Tools
| Tool | Description |
|---|---|
| `run_sql` | Executes a read-only DuckDB query against the active dataset |
| `train_model` | Trains a model and returns metrics + SHAP summary |
| `generate_chart` | Returns a chart config for a given result set |
| `send_report` | Sends a generated report to Slack/email |

---

## 📁 Project Structure

```
datapilot/
├── frontend/                     # React + Vite app
│   ├── src/
│   │   ├── pages/                # Upload, Ask, Dashboard, Reports
│   │   ├── components/           # ChartCard, QueryPanel, KpiCard
│   │   └── api/
│   ├── .env.example
│   └── package.json
│
├── backend/                      # FastAPI app
│   ├── app/
│   │   ├── api/                  # route definitions
│   │   ├── data/                 # ingestion, profiling, cleaning
│   │   ├── analytics/            # descriptive/diagnostic engine
│   │   ├── rag/                  # embeddings + Chroma retrieval
│   │   ├── ai_analyst/           # NL -> SQL -> stats -> explanation
│   │   ├── mcp_server/           # MCP tool definitions
│   │   ├── ml/                   # training, selection, SHAP
│   │   ├── graph/                # LangGraph state graph
│   │   └── reports/              # PDF/PPT generation
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🤖 How the AI Analyst Scores an Answer

1. Question is embedded and matched against schema docs, business glossary, and past insights (RAG)
2. LLM generates a DuckDB SQL query using the retrieved context + schema
3. Query executes read-only, with row limits and a timeout
4. If two groups are being compared, a real `scipy.stats` test runs — the LLM never eyeballs significance
5. A second LLM call turns the question + SQL + result + stat test into a plain-English explanation
6. Chart type is picked by rule (time column → line, category compare → bar, two numeric → scatter), not guessed by the LLM

```python
# Example
question = "Why did revenue decrease in March?"
# → SQL: SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month
# → stat test: t-test comparing March vs Feb, p=0.03 (significant)
# → explanation: "Revenue dropped 12% (~$48K) in March, driven mainly by
#    a 30% decline in repeat purchases from the mid-tier segment..."
```
If the LLM is unreachable, the pipeline falls back to the raw SQL result with a basic templated summary — no answer ever depends solely on model availability.

---

## 🔒 Security

- Passwords hashed with bcrypt
- JWT tokens for session auth
- All protected routes require `Authorization: Bearer <token>`
- SQL execution sandboxed to read-only, with row-limit and timeout guards
- CORS restricted to known frontend origins

---

## 🗺️ Roadmap

- [x] Data ingestion & profiling
- [x] Automated cleaning
- [x] Analytics engine (descriptive/diagnostic)
- [x] RAG context retrieval
- [x] AI Analyst (NL → SQL → explanation)
- [x] MCP tool server
- [x] LangGraph orchestration
- [x] ML module (classification, forecasting, SHAP)
- [x] Dashboard builder
- [x] Automated report generation
- [ ] Monitoring & anomaly alerts
- [ ] Multi-agent specialization (v3+)

---

## 👩‍💻 Author

**Your Name**
LinkedIn: `https://linkedin.com/in/your-handle`
GitHub: `https://github.com/your-username`
Portfolio: `https://your-portfolio-link`

## ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

## 📝 License

MIT
