# Autonomous Multi-Agent Business Intelligence System - PowerShell Setup Script

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Autonomous Multi-Agent Business Intelligence System - Windows PowerShell Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found! Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nStep 2: Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
& .\venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host "`nStep 3: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nStep 4: Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Download spaCy model
Write-Host "`nStep 5: Downloading spaCy model..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm

# Create directories
Write-Host "`nStep 6: Creating directories..." -ForegroundColor Yellow
$dirs = @("data\sample", "data\schemas", "data\embeddings", "logs")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

# Create .env
Write-Host "`nStep 7: Setting up configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file - please edit with your API keys" -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists" -ForegroundColor Gray
}

# Create sample database
Write-Host "`nStep 8: Creating sample database..." -ForegroundColor Yellow
python scripts\create_sample_data.py

# Initialize vector store
Write-Host "`nStep 9: Initializing vector store..." -ForegroundColor Yellow
python scripts\init_vector_store.py

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Edit .env file with your ANTHROPIC_API_KEY" -ForegroundColor Gray
Write-Host "2. Install Ollama from https://ollama.ai/download" -ForegroundColor Gray
Write-Host "3. Run: ollama pull llama3:8b-instruct-q4_K_M" -ForegroundColor Gray

Write-Host "`nTo start the application:" -ForegroundColor White
Write-Host "  Terminal 1: python -m uvicorn src.api.main:app --reload" -ForegroundColor Cyan
Write-Host "  Terminal 2: streamlit run src/ui/streamlit_app.py" -ForegroundColor Cyan

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
