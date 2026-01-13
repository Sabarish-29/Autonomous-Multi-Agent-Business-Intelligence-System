# Autonomous Multi-Agent Business Intelligence System - Deployment Guide

This guide covers deploying Autonomous Multi-Agent Business Intelligence System using a hybrid approach combining your local machine with Azure cloud services.

## Prerequisites

### Hardware Requirements
- **Your System**: Intel i7-1165G7, 8GB RAM
- **Storage**: At least 20GB free space
- **Internet**: Stable connection for Azure/Claude API

### Software Requirements
- Python 3.10+
- Git
- Azure CLI
- Ollama (for local LLM)

## Deployment Options

### Option A: Local Development (Recommended to Start)

Best for: Development, testing, and demos

**Pros:**
- Free (no cloud costs)
- Fast iteration
- Private data

**Cons:**
- Limited to your machine's resources
- Not accessible externally

### Option B: Hybrid Local + Azure (Production)

Best for: Production deployment

**Architecture:**
```
┌─────────────────────┐      ┌─────────────────────┐
│   Your Machine      │      │      Azure          │
│                     │      │                     │
│  ┌───────────────┐  │      │  ┌───────────────┐  │
│  │ Ollama LLM    │  │      │  │ Claude API    │  │
│  │ (Fast queries)│  │      │  │ (Complex)     │  │
│  └───────────────┘  │      │  └───────────────┘  │
│                     │      │                     │
│  ┌───────────────┐  │      │  ┌───────────────┐  │
│  │ ChromaDB      │  │      │  │ Azure Storage │  │
│  │ (RAG)         │  │◄────►│  │ (Backup)      │  │
│  └───────────────┘  │      │  └───────────────┘  │
│                     │      │                     │
│  ┌───────────────┐  │      │  ┌───────────────┐  │
│  │ FastAPI       │  │      │  │ App Service   │  │
│  │ Streamlit     │  │      │  │ (Optional)    │  │
│  └───────────────┘  │      │  └───────────────┘  │
└─────────────────────┘      └─────────────────────┘
```

---

## Step 1: Local Setup

### 1.1 Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/Sabarish-29/Autonomous-Multi-Agent-Business-Intelligence-System.git
cd Autonomous-Multi-Agent-Business-Intelligence-System

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate.bat

# Activate (Linux/Mac)
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Install spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 1.3 Install Ollama (Local LLM)

1. Download from https://ollama.ai/download
2. Install and start Ollama
3. Pull the Llama 3 model:

```bash
ollama pull llama3:8b-instruct-q4_K_M
```

**Memory Note**: The q4_K_M variant uses ~4GB RAM, suitable for your 8GB system.

### 1.4 Configure Environment

```bash
# Copy example config
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env with your settings
notepad .env  # Windows
nano .env     # Linux
```

**Minimum .env configuration:**
```env
# Required for Claude API
ANTHROPIC_API_KEY=your_key_here

# Local settings
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=sqlite:///./data/sample/sales_db.sqlite
```

### 1.5 Initialize Data

```bash
# Create sample database
python scripts/create_sample_data.py

# Initialize vector store
python scripts/init_vector_store.py
```

### 1.6 Start Services

**Terminal 1 - API Server:**
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Streamlit UI:**
```bash
streamlit run src/ui/streamlit_app.py --server.port 8501
```

### 1.7 Access Application

- **Web UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Step 2: Azure Setup (Free Trial $132)

### 2.1 Create Azure Account

1. Go to https://azure.microsoft.com/free/
2. Sign up with your Microsoft account
3. Activate $200 free credit (actually varies by region, you mentioned $132)

### 2.2 Install Azure CLI

**Windows:**
```powershell
# Using winget
winget install Microsoft.AzureCLI

# Or download MSI from:
# https://aka.ms/installazurecliwindows
```

**Login to Azure:**
```bash
az login
```

### 2.3 Create Resource Group

```bash
az group create --name datagenie-rg --location eastus
```

### 2.4 Create Azure Storage (for backups)

```bash
# Create storage account
az storage account create \
  --name datageniestorage \
  --resource-group datagenie-rg \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name datageniestorage \
  --resource-group datagenie-rg
```

Add to your `.env`:
```env
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

### 2.5 Optional: Azure App Service (for hosting)

If you want to host the API on Azure:

```bash
# Create App Service plan (Free tier)
az appservice plan create \
  --name datagenie-plan \
  --resource-group datagenie-rg \
  --sku F1 \
  --is-linux

# Create web app
az webapp create \
  --name datagenie-api \
  --resource-group datagenie-rg \
  --plan datagenie-plan \
  --runtime "PYTHON:3.10"
```

---

## Step 3: Claude API Setup

### 3.1 Get API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create new API key

### 3.2 Configure API Key

Add to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### 3.3 Test Claude Integration

```bash
# Start API server
python -m uvicorn src.api.main:app --reload

# Test Claude endpoint
curl -X POST "http://localhost:8000/llm/test" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Claude!"}'
```

---

## Step 4: Google Colab (Optional)

For exploration and experimentation without local setup.

### 4.1 Create Colab Notebook

Open https://colab.research.google.com and create new notebook.

### 4.2 Install Dependencies

```python
!pip install langchain langchain-anthropic chromadb spacy fastapi uvicorn streamlit
!python -m spacy download en_core_web_sm
```

### 4.3 Clone Repository

```python
!git clone https://github.com/Sabarish-29/Autonomous-Multi-Agent-Business-Intelligence-System.git
%cd autonomous-multi-agent-bi-system
```

### 4.4 Set Environment Variables

```python
import os
os.environ['ANTHROPIC_API_KEY'] = 'your_key_here'
os.environ['USE_LOCAL_LLM'] = 'false'  # No Ollama in Colab
```

### 4.5 Run in Colab

```python
# Create sample data
!python scripts/create_sample_data.py

# Initialize vector store
!python scripts/init_vector_store.py

# Start API (use ngrok for external access)
!pip install pyngrok
from pyngrok import ngrok
ngrok.set_auth_token("your_ngrok_token")

# Run in background
!nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Create tunnel
public_url = ngrok.connect(8000)
print(f"API available at: {public_url}")
```

---

## Step 5: Power BI Integration (Optional)

### 5.1 Register Azure AD App

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: "Autonomous Multi-Agent Business Intelligence System Power BI"
4. Supported account types: Single tenant
5. Note the Application (client) ID and Directory (tenant) ID

### 5.2 Create Client Secret

1. Go to Certificates & secrets
2. New client secret
3. Copy the secret value immediately

### 5.3 Grant Power BI Permissions

1. Go to API permissions
2. Add permission → Power BI Service
3. Select: Dataset.Read.All, Report.Read.All, Workspace.Read.All
4. Grant admin consent

### 5.4 Configure in .env

```env
POWERBI_CLIENT_ID=your_app_id
POWERBI_CLIENT_SECRET=your_secret
POWERBI_TENANT_ID=your_tenant_id
```

---

## Performance Optimization (8GB RAM)

### Memory Management

1. **Use quantized Ollama model**: `llama3:8b-instruct-q4_K_M` uses ~4GB
2. **Limit concurrent requests**: Set `MAX_CONCURRENT_REQUESTS=2`
3. **Reduce context window**: Set `OLLAMA_NUM_CTX=4096`

### Recommended .env for 8GB System

```env
# Optimized for 8GB RAM
USE_LOCAL_LLM=true
MAX_CONCURRENT_REQUESTS=2
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_GPU=0
MAX_TOKENS_PER_REQUEST=2000
```

### When to Use Cloud vs Local

| Task Type | Use | Reason |
|-----------|-----|--------|
| Simple queries | Ollama (local) | Fast, free |
| Complex SQL | Claude (cloud) | Better accuracy |
| Intent classification | Ollama (local) | Speed |
| Executive summaries | Claude (cloud) | Better reasoning |

---

## Troubleshooting

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Check model availability
ollama list
```

### Memory Issues

```bash
# Monitor memory
# Windows
tasklist /fi "imagename eq ollama.exe"

# Linux
htop
```

If memory issues persist, disable local LLM:
```env
USE_LOCAL_LLM=false
```

### API Connection Issues

```bash
# Test API health
curl http://localhost:8000/health

# Check logs
# Look at terminal running uvicorn
```

### ChromaDB Issues

```bash
# Reset vector store
python -c "from src.rag import VectorStore; VectorStore().reset_all()"

# Reinitialize
python scripts/init_vector_store.py
```

---

## Video Demo Script

For your deployment video, follow this sequence:

1. **Introduction** (30 sec)
   - Show project overview
   - Explain hybrid architecture

2. **Local Setup** (2 min)
   - Create virtual environment
   - Install dependencies
   - Configure .env

3. **Initialize Data** (1 min)
   - Run create_sample_data.py
   - Run init_vector_store.py

4. **Start Services** (1 min)
   - Start Ollama
   - Start FastAPI
   - Start Streamlit

5. **Demo Queries** (3 min)
   - Simple query (Ollama)
   - Complex query (Claude)
   - Show entity extraction
   - Show intent classification

6. **Azure Integration** (2 min)
   - Show Azure portal
   - Storage configuration
   - Claude API setup

7. **Conclusion** (30 sec)
   - Summary of features
   - Performance metrics

---

## Support

- **Issues**: Create GitHub issue
- **Documentation**: Check `/docs` folder
- **API Reference**: http://localhost:8000/docs
