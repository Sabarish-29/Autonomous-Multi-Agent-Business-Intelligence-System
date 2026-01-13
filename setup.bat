@echo off
echo ======================================
echo Autonomous Multi-Agent Business Intelligence System - Windows Setup
echo ======================================
echo.

REM Check Python
echo Step 1: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo Step 2: Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Step 4: Installing dependencies...
pip install -r requirements.txt
echo.

REM Download spaCy model
echo Step 5: Downloading spaCy model...
python -m spacy download en_core_web_sm
echo.

REM Create directories
echo Step 6: Creating directories...
if not exist "data\sample" mkdir data\sample
if not exist "data\schemas" mkdir data\schemas
if not exist "data\embeddings" mkdir data\embeddings
echo.

REM Create .env if not exists
echo Step 7: Setting up configuration...
if not exist ".env" (
    copy .env.example .env
    echo Created .env file - please edit with your API keys
) else (
    echo .env file already exists
)
echo.

REM Create sample database
echo Step 8: Creating sample database...
python scripts\create_sample_data.py
echo.

REM Initialize vector store
echo Step 9: Initializing vector store...
python scripts\init_vector_store.py
echo.

echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo 1. Edit .env file with your ANTHROPIC_API_KEY
echo 2. Install Ollama from https://ollama.ai/download
echo 3. Run: ollama pull llama3:8b-instruct-q4_K_M
echo.
echo To start the application:
echo   Terminal 1: python -m uvicorn src.api.main:app --reload
echo   Terminal 2: streamlit run src/ui/streamlit_app.py
echo.
pause
