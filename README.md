# Autonomous Multi-Agent Business Intelligence System

> AI-powered Business Intelligence assistant with a 6-agent agentic pipeline that transforms natural language queries into SQL, validates them for safety, auto-corrects errors, and generates actionable business insights.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-6%20Agents-purple.svg)
![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)
![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)

## 🎯 Key Features

- **6-Agent Agentic Pipeline**: Planner, Validator, Corrector, Memory, Insight, Orchestrator
- **Natural Language to SQL**: Context-aware SQL generation with safety validation
- **Self-Correcting SQL**: Automatic error detection and correction with transparency
- **Business Insights**: AI-generated summaries, key points, and recommendations
- **NLP Pipeline**: spaCy NER (87% accuracy) + BERT intent classification
- **RAG Architecture**: ChromaDB + Groq API for intelligent context retrieval
- **Query Memory**: Stores and recalls similar past queries (30% threshold)
- **Safety First**: Blocks dangerous SQL (INSERT, UPDATE, DELETE, DROP, ALTER, etc.)
- **Streamlit UI**: Real-time query visualization with agent plan transparency

## 🏗️ Architecture

### 6-Agent Agentic Pipeline

```
User Query
    ↓
[1] MEMORY AGENT ──→ Recalls similar past queries from history
    ↓
[2] PLANNER AGENT ──→ Analyzes intent, extracts metrics/dimensions
    ↓                  Builds step-by-step analytical plan
[3] GENERATOR ────→ Core SQL generation from plan
    ↓
[4] VALIDATOR ────→ Safety validation (blocks dangerous operations)
    ↓
[5] CORRECTOR ────→ Auto-fixes SQL errors (with transparency)
    ↓
[6] INSIGHT AGENT ─→ Generates business summaries & recommendations
    ↓
[7] MEMORY AGENT ──→ Stores successful query-SQL pair for future recall
    ↓
Response (with plan, insights, and correction metadata)
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│      Autonomous Multi-Agent Business Intelligence System              │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend Layer                                                      │
│  ┌──────────────────────┐                                            │
│  │ Streamlit UI (8501)  │                                            │
│  │ • Query Input        │                                            │
│  │ • Real-time Results  │                                            │
│  │ • 4-Tab Dashboard    │                                            │
│  └──────────────────────┘                                            │
├─────────────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI on 8000)                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │ /query       │ │ /health      │ │ /docs        │                 │
│  │ (agentic)    │ │ (status)     │ │ (Swagger UI) │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│  Agent Orchestrator Pipeline                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Memory   │→ │ Planner  │→ │Generator │→ │Validator │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
│       ↓             ↓              ↓              ↓                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Memory   │← │ Insight  │← │Corrector │← (if errors)              │
│  └──────────┘  └──────────┘  └──────────┘                           │
├─────────────────────────────────────────────────────────────────────┤
│  Processing Components                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ NER      │  │ Intent   │  │ Validator│  │ RAG      │             │
│  │Extractor │  │Classifier│  │(Safety)  │  │Retriever │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│  LLM Layer                                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Groq API (llama-3.3-70b-versatile) - Fast & Efficient        │   │
│  └──────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                           │
│  │ ChromaDB │  │ SQLite   │  │ Memory   │                           │
│  │ (Vector) │  │ (Sample) │  │ Storage  │                           │
│  └──────────┘  └──────────┘  └──────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Requirements

### Hardware (Minimum)
- **CPU**: Intel Core i7 (11th gen or later) or AMD equivalent
- **RAM**: 8GB (16GB recommended for Ollama)
- **Storage**: 20GB free space
- **GPU**: Optional (NVIDIA MX330+ for faster inference)

### Software
- Python 3.11+
- Node.js 18+ (for optional frontend)
- Ollama (for local LLM)
- SQLite (included with Python)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <your-repo-url>
cd "autonomous-multi-agent-bi-system"

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

```bash
# Copy example environment file (Windows)
copy .env.example .env

# Copy example environment file (Linux/Mac)
cp .env.example .env

# Edit with your API keys
# Required: GROQ_API_KEY (LLM provider)
# Optional: OPENAI_API_KEY (reasoning model), TAVILY_API_KEY (web research)
# Optional: POWERBI_* credentials
```

### 3. Initialize Data

```bash
# Create sample database
python scripts/create_sample_data.py

# Initialize vector store
python scripts/init_vector_store.py
```

### 4. Start Services

```bash
# Terminal 1: Start API server (FastAPI on port 8000)
python -m uvicorn src.api.main_crewai:app --host 127.0.0.1 --port 8000

# Terminal 2: Start Streamlit UI (port 8501)
python -m streamlit run app/streamlit_ui.py --server.port 8501 --server.address 127.0.0.1
```

### 4b. One-command Launch (recommended)

This starts both backend and UI (and does basic environment checks):

```bash
python scripts/launch_datagenie.py
```

### 5. Access Application

- **API Server**: http://127.0.0.1:8000
- **API Docs (Swagger)**: http://127.0.0.1:8000/docs
- **Web UI (Streamlit)**: http://127.0.0.1:8501
- **Health Check**: http://127.0.0.1:8000/health

## 📄 Reporting (PDF / PPTX)

Phase 6 report downloads require these Python packages:

- PDF: `fpdf2` (imported as `fpdf`)
- PowerPoint: `python-pptx` (imported as `pptx`)

If you installed via `pip install -r requirements.txt`, these should already be included. If you see errors like `No module named 'fpdf'` or `No module named 'pptx'`, install them into the same environment you use to run the backend:

```bash
pip install --upgrade fpdf2 python-pptx
```

## 🛠️ Common Fixes

### "Missing optional dependency 'tabulate'"

Some result formatting paths (via pandas) require `tabulate`. Install it into your active venv:

```bash
pip install --upgrade tabulate
```

## 🤖 Multi-Agent Pipeline Explained

### Agent Details

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| **Memory Agent** | Recalls past queries | User query | Similar queries from history |
| **Planner Agent** | Analyzes and plans | Query + context | Goal + step-by-step plan |
| **Generator** | Creates SQL | Plan + schema | SQL query |
| **Validator Agent** | Safety check | SQL | Validation result + errors |
| **Corrector Agent** | Fixes errors | SQL + errors | Corrected SQL |
| **Insight Agent** | Business analysis | SQL + plan | Summary + recommendations |

### Transparency Features

🔧 **Auto-Correction Display**: When the Corrector Agent refines SQL multiple times, you'll see:
> 🔧 **Auto-corrected:** SQL was refined 2 times by the correction agent for accuracy

🤖 **Agent Plan Tab**: Shows:
- Analytical goal from Planner Agent
- Step-by-step breakdown
- Agent execution pipeline trace
- Business insights and key findings

### Response Structure

```json
{
  "sql": "SELECT region, SUM(sales) FROM transactions GROUP BY region",
  "confidence": 0.95,
  "explanation": "Groups transactions by region to show total sales per region",
  "complexity": "medium",
  "entities": [{"text": "region", "label": "COLUMN"}, ...],
  "intent": {"intent": "aggregation", "all_scores": {...}},
  "cost_estimate": 0.0015,
  "provider": "groq",
  "validation_status": "valid",
  "validation_errors": [],
  "plan": {
    "goal": "Analyze total sales performance by geographic region",
    "steps": ["Extract region dimension", "Sum sales metric", ...]
  },
  "insights": {
    "summary": "Analysis reveals regional distribution of sales...",
    "key_points": ["North region leads with 35% of total sales", ...],
    "recommendations": ["Focus marketing efforts on underperforming regions", ...]
  },
  "agent_trace": ["memory_recall", "planner", "generator", "validator", "insight", "memory_remember"],
  "attempts": 1
}
```

## 🔧 Hybrid Deployment Options

### Option A: Local Only (Development) ✅ CURRENT
Best for: Development and testing
- Groq API for LLM (free tier available)
- SQLite for database
- ChromaDB for vector store (gracefully degraded if corrupted)
- Streamlit for UI

### Option B: Local + Cloud (Production Ready)
Best for: Production deployment
- Groq API: LLM inference
- PostgreSQL: Production database
- Pinecone/Azure Cognitive Search: Vector store
- Docker: Containerization

See `docs/DEPLOYMENT.md` for detailed instructions.

## 📁 Project Structure

```
autonomous-multi-agent-bi-system/
├── app/
│   ├── streamlit_ui.py              # Streamlit UI entry point
│   └── components/                  # UI components (monitoring, trace, etc.)
├── src/
│   ├── api/
│   │   ├── main_crewai.py           # FastAPI entry point (Phase 4/6)
│   │   └── main.py                  # Alternative API entry point (legacy)
│   ├── agents/                      # CrewAI / agents (librarian, reporter, sentry, ...)
│   ├── tools/                       # SQL executor, guardrails, sandbox, ...
│   └── config.py                    # Settings (.env loading)
├── scripts/
│   ├── launch_datagenie.py          # One-command launcher (backend + UI)
│   ├── create_sample_data.py
│   └── init_vector_store.py
├── data/                            # Sample DB + schema library
├── reports/                         # Generated PDF/PPTX outputs
├── requirements.txt
├── pyproject.toml
├── setup.bat
├── setup.ps1
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_sql_accuracy.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📊 Performance Metrics

| Component | Metric | Target | Achieved |
|-----------|--------|--------|----------|
| **SQL Generation** | Accuracy | 90% | 92% |
| **NER Extraction** | Accuracy | 85% | 87% |
| **Intent Classification** | Accuracy | 90% | 91% |
| **Response Time** | p95 latency | <3s | 2.1s |
| **Agent Pipeline** | End-to-end | <5s | 3.2s |
| **Agentic Mode** | Correction attempts | <3 | 1-2 avg |

## 🔒 Safety & Security

### SQL Validation
- ✅ Blocks: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, EXEC, CALL
- ✅ Tokenizes SQL for pattern matching
- ✅ Prevents malicious queries from reaching database
- ✅ Provides detailed validation error messages

### API Security
- ✅ CORS configured for production
- ✅ Rate limiting on endpoints
- ✅ API keys stored in environment variables
- ✅ No sensitive data in version control
- ✅ Error responses don't leak schema details

### Data Privacy
- ✅ Query history stored locally
- ✅ No queries sent to external logging services (unless configured)
- ✅ Vector embeddings stored locally in ChromaDB
- ✅ Sensitive data sanitization in error messages

## 📄 License

Proprietary.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📞 Support & Documentation

- **Issues**: Track issues in your repo/project
- **API Reference**: http://localhost:8000/docs (Swagger UI)
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Agent Details**: `src/agents/` folder
- **Email**: sabarishsureshofficial@gmail.com

---

**Built with ❤️ using FastAPI, Groq API, Multi-Agent Architecture, Streamlit, and ChromaDB**
