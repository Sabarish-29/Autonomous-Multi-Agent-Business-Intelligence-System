# Autonomous Multi-Agent Business Intelligence System - Phase 1 Integration Guide

## 🎯 Overview

This guide walks you through integrating the new CrewAI-based hierarchical multi-agent system into your existing Text-to-SQL project.

## 📦 What's New in Phase 1

### 1. **Librarian Agent** (`src/agents/librarian.py`)
- Semantic schema retrieval using ChromaDB
- Only fetches relevant tables based on query intent
- Reduces LLM context size and improves accuracy

### 2. **Business Glossary** (`configs/business_glossary.yaml`)
- Maps business terms to SQL logic
- Defines column aliases and relationships
- Provides query pattern templates

### 3. **CrewAI Manager** (`src/agents/crewai_manager.py`)
- Hierarchical multi-agent architecture
- Manager oversees Query Analyst, SQL Architect, and Validator
- Coordinated workflow for complex queries

### 4. **New API** (`src/api/main_crewai.py`)
- FastAPI endpoints for CrewAI system
- Schema indexing endpoints
- Business glossary lookup

---

## 🚀 Installation Steps

### Step 1: Install New Dependencies

```bash
# Install CrewAI and related packages
pip install crewai>=0.11.0 crewai-tools>=0.2.0
pip install langchain-groq>=0.1.0 groq>=0.4.0
pip install pyyaml>=6.0.0

# Or install all from updated requirements.txt
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

Add to your `.env` file:

```bash
# Existing
GROQ_API_KEY=your_groq_api_key_here
ANTHROPIC_API_KEY=your_claude_key_here  # Optional

# New for Phase 1
CREWAI_TELEMETRY=false  # Disable telemetry
```

### Step 3: Create Required Directories

```bash
# Create directories for new components
mkdir -p data/schema_library
mkdir -p configs
```

### Step 4: Initialize Business Glossary

The `business_glossary.yaml` is already created at `configs/business_glossary.yaml`. 

**Customize it** with your specific business terms:

```yaml
business_terms:
  your_custom_term:
    description: "Description of what this means in your business"
    sql_logic: "SQL condition or calculation"
    related_tables:
      - your_table_name
    related_columns:
      - your_column_name
```

---

## 📚 Using the Librarian Agent

### Indexing Your Database Schemas

#### Option A: Index Example Schemas

```bash
# Run the schema indexing script with examples
python scripts/index_schemas.py --mode example
```

#### Option B: Index from SQLite Database

```bash
# Index your existing database
python scripts/index_schemas.py --mode sqlite --db-path ./data/your_database.sqlite
```

#### Option C: Index Programmatically

```python
from src.agents.librarian import LibrarianAgent

librarian = LibrarianAgent(db_path="./data/schema_library")

# Index a table
librarian.index_table_schema(
    table_name="customers",
    schema_definition="CREATE TABLE customers (...)",
    columns=[
        {'name': 'customer_id', 'type': 'INTEGER', 'description': 'Primary key'},
        {'name': 'email', 'type': 'VARCHAR(255)', 'description': 'Customer email'}
    ],
    metadata={'database': 'prod', 'category': 'customer_data'}
)
```

### Using Librarian for Schema Retrieval

```python
from src.agents.librarian import LibrarianAgent

librarian = LibrarianAgent()

# Get relevant schemas for a query
query = "Show me customer purchase history"
context = librarian.build_focused_context(query, max_tables=3)

# This returns a formatted string with only relevant table schemas
print(context)
```

---

## 🤖 Using CrewAI Manager

### Starting the New API Server

```bash
# Start the CrewAI-powered API
python -m uvicorn src.api.main_crewai:app --host 127.0.0.1 --port 8000
```

### Making Requests to CrewAI API

```python
import requests

# Generate SQL using hierarchical multi-agent process
response = requests.post(
    "http://127.0.0.1:8000/query",
    json={
        "query": "Show me total revenue by region for active customers this month",
        "database": "default",
        "use_crewai": True
    }
)

result = response.json()
print(result['sql'])
print(result['agents_involved'])  # ['manager', 'query_analyst', 'sql_architect', 'validator']
```

### Direct Python Usage

```python
from src.agents.crewai_manager import DataOpsManager, BusinessGlossary
from src.agents.librarian import LibrarianAgent
import os

# Initialize components
librarian = LibrarianAgent(db_path="./data/schema_library")
glossary = BusinessGlossary(glossary_path="./configs/business_glossary.yaml")

# Create DataOps Manager
manager = DataOpsManager(
    llm_api_key=os.getenv("GROQ_API_KEY"),
    librarian_agent=librarian,
    business_glossary=glossary,
    model_name="llama-3.3-70b-versatile"
)

# Generate SQL
result = manager.generate_sql_hierarchical(
    user_query="What are our top 5 products by revenue?",
    database="default"
)

print(result['sql'])
```

---

## 🔄 Integration with Existing Code

### Option 1: Keep Both Systems (Recommended for Testing)

Run both the old and new systems side by side:

```bash
# Terminal 1: Old system
python -m uvicorn src.api.main:app --port 8000

# Terminal 2: New CrewAI system
python -m uvicorn src.api.main_crewai:app --port 8001
```

### Option 2: Add CrewAI as Optional Mode

Modify your existing `main.py` to add CrewAI as an option:

```python
from src.agents.crewai_manager import DataOpsManager, BusinessGlossary
from src.agents.librarian import LibrarianAgent

# Initialize at startup
@app.on_event("startup")
async def startup():
    global dataops_manager
    
    librarian = LibrarianAgent()
    glossary = BusinessGlossary()
    dataops_manager = DataOpsManager(
        llm_api_key=os.getenv("GROQ_API_KEY"),
        librarian_agent=librarian,
        business_glossary=glossary
    )

# Add new parameter to query endpoint
@app.post("/query")
async def query(request: QueryRequest):
    if request.use_crewai:
        # Use new hierarchical system
        result = dataops_manager.generate_sql_hierarchical(
            user_query=request.query,
            database=request.database
        )
    else:
        # Use existing system
        result = sql_generator.generate(request.query)
    
    return result
```

### Option 3: Full Migration

Replace your existing pipeline with CrewAI:

1. Backup your old files
2. Replace `src/api/main.py` with `src/api/main_crewai.py`
3. Update your startup scripts

---

## 🎯 Testing the New System

### Test 1: Verify Librarian Agent

```bash
python scripts/index_schemas.py --mode example

# Test retrieval
python -c "
from src.agents.librarian import LibrarianAgent
librarian = LibrarianAgent()
print(librarian.build_focused_context('Show customer orders', max_tables=2))
"
```

### Test 2: Verify Business Glossary

```bash
python -c "
from src.agents.crewai_manager import BusinessGlossary
glossary = BusinessGlossary()
print(glossary.get_term_definition('active_user'))
"
```

### Test 3: End-to-End CrewAI Query

```bash
# Start server
python -m uvicorn src.api.main_crewai:app --port 8000

# In another terminal, test query
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me revenue from active customers this month",
    "database": "default"
  }'
```

---

## 📊 Project Structure After Integration

```
autonomous-multi-agent-bi-system/
├── src/
│   ├── agents/
│   │   ├── librarian.py              # NEW: Semantic schema retrieval
│   │   ├── crewai_manager.py         # NEW: CrewAI hierarchical system
│   │   ├── orchestrator.py           # OLD: Sequential orchestrator (keep for now)
│   │   ├── planner_agent.py          # OLD: Sequential planner (keep for now)
│   │   └── ...                       # Other agents
│   ├── api/
│   │   ├── main.py                   # OLD: Original API (keep as fallback)
│   │   └── main_crewai.py            # NEW: CrewAI-powered API
│   └── ...
├── configs/
│   └── business_glossary.yaml        # NEW: Business term definitions
├── data/
│   ├── schema_library/               # NEW: ChromaDB for Librarian Agent
│   └── ...
├── scripts/
│   ├── index_schemas.py              # NEW: Schema indexing utility
│   └── ...
└── docs/
    └── PHASE1_INTEGRATION.md         # This file
```

---

## 🔧 Troubleshooting

### Issue: ChromaDB SQLite Error

**Error:** `no such column: collections.topic`

**Solution:**
```bash
# Delete corrupted ChromaDB
rm -rf data/schema_library

# Re-index schemas
python scripts/index_schemas.py --mode example
```

### Issue: CrewAI Import Error

**Error:** `ModuleNotFoundError: No module named 'crewai'`

**Solution:**
```bash
pip install --upgrade crewai crewai-tools
```

### Issue: Groq API Key Not Found

**Error:** `GROQ_API_KEY not found in environment`

**Solution:**
```bash
# Add to .env file
echo "GROQ_API_KEY=your_key_here" >> .env

# Or export directly
export GROQ_API_KEY=your_key_here
```

### Issue: Business Glossary Not Loading

**Error:** `Business glossary not found`

**Solution:**
```bash
# Ensure YAML file exists
ls configs/business_glossary.yaml

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('configs/business_glossary.yaml'))"
```

---

## 📈 Performance Comparison

### Before (Sequential Agents):
- All agents run sequentially
- Full schema passed to LLM (high token cost)
- Limited business context

### After (CrewAI Hierarchical):
- Manager coordinates parallel/sequential execution
- Only relevant schemas retrieved (lower token cost)
- Business glossary enriches context
- Better error handling and validation

### Expected Improvements:
- **20-30% faster** query processing
- **40-50% reduction** in LLM token usage
- **Higher accuracy** due to focused context
- **Better scalability** for large databases

---

## 🎓 Next Steps

### Phase 2 (Future Enhancements):
1. **Parallel Agent Execution**: Run multiple agents concurrently
2. **Query Optimization Agent**: Analyze and optimize generated SQL
3. **Feedback Loop**: Learn from query corrections
4. **Multi-Database Support**: Handle multiple databases simultaneously
5. **Real-time Schema Updates**: Auto-update Librarian when schema changes

### Immediate Actions:
1. ✅ Index your database schemas
2. ✅ Customize business glossary for your domain
3. ✅ Test CrewAI system with sample queries
4. ✅ Compare results with old system
5. ✅ Monitor token usage and performance

---

## 📞 Support

If you encounter issues:
1. Check logs: `tail -f logs/datagenie.log`
2. Review API health: `curl http://127.0.0.1:8000/health`
3. Test components individually (see Testing section)
4. Check GitHub Issues or create a new one

---

**Congratulations! You've integrated CrewAI Phase 1! 🎉**
