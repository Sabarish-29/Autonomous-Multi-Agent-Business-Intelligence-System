"""
Autonomous Multi-Agent Business Intelligence System Phase 4 - Installation Test Script
=================================================

This script verifies that all Phase 4 components are properly installed
and configured.

Run this after installing Phase 4 dependencies:
    pip install apscheduler tavily-python websockets

Usage:
    python scripts/test_phase4_setup.py
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_status(message, status='info'):
    """Print colored status message"""
    if status == 'success':
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == 'error':
        print(f"{RED}❌ {message}{RESET}")
    elif status == 'warning':
        print(f"{YELLOW}⚠️  {message}{RESET}")
    elif status == 'info':
        print(f"{BLUE}ℹ️  {message}{RESET}")


def check_python_version():
    """Check Python version is 3.10+"""
    print("\n" + "="*60)
    print("1. Checking Python Version")
    print("="*60)
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", 'success')
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} detected. Requires 3.10+", 'error')
        return False


def check_dependencies():
    """Check Phase 4 dependencies are installed"""
    print("\n" + "="*60)
    print("2. Checking Phase 4 Dependencies")
    print("="*60)
    
    dependencies = {
        'apscheduler': 'APScheduler (Background monitoring)',
        'tavily': 'Tavily Python (Web search)',
        'websockets': 'WebSockets (Real-time alerts)',
        'crewai': 'CrewAI (Multi-agent system)',
        'pandas': 'Pandas (Data analysis)',
        'sqlalchemy': 'SQLAlchemy (Database)',
        'fastapi': 'FastAPI (Web framework)'
    }
    
    all_installed = True
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print_status(f"{description}: Installed", 'success')
        except ImportError:
            print_status(f"{description}: NOT INSTALLED", 'error')
            all_installed = False
    
    return all_installed


def check_environment_variables():
    """Check required environment variables"""
    print("\n" + "="*60)
    print("3. Checking Environment Variables")
    print("="*60)
    
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_status("Loaded .env file", 'success')
    except ImportError:
        print_status("python-dotenv not installed - skipping .env", 'warning')
    
    required_vars = {
        'GROQ_API_KEY': 'Groq API (Fast LLM)',
        'OPENAI_API_KEY': 'OpenAI API (Reasoning LLM)',
        'TAVILY_API_KEY': 'Tavily API (Web search)'
    }
    
    optional_vars = {
        'SQLALCHEMY_DB_URL': 'Database URL'
    }
    
    all_set = True
    
    # Check required
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print_status(f"{description} ({var}): {masked}", 'success')
        else:
            print_status(f"{description} ({var}): NOT SET", 'error')
            all_set = False
    
    # Check optional
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_status(f"{description} ({var}): {value}", 'success')
        else:
            print_status(f"{description} ({var}): Not set (using default)", 'info')
    
    return all_set


def check_file_structure():
    """Check Phase 4 files exist"""
    print("\n" + "="*60)
    print("4. Checking Phase 4 File Structure")
    print("="*60)
    
    base_path = Path(__file__).parent.parent
    
    required_files = [
        'src/agents/sentry.py',
        'src/agents/researcher.py',
        'src/agents/crewai_manager.py',
        'src/api/main_crewai.py',
        'docs/PHASE4_MONITORING.md',
        'PHASE4_SUMMARY.md'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print_status(f"{file_path} ({size_kb:.1f} KB)", 'success')
        else:
            print_status(f"{file_path}: NOT FOUND", 'error')
            all_exist = False
    
    return all_exist


def test_sentry_agent():
    """Test Anomaly Sentry Agent initialization"""
    print("\n" + "="*60)
    print("5. Testing Anomaly Sentry Agent")
    print("="*60)
    
    try:
        from src.agents.sentry import AnomalySentryAgent, MetricDefinition
        
        # Test initialization
        sentry = AnomalySentryAgent(
            database_uri="sqlite:///data/sample/sample.db",
            check_interval_minutes=5
        )
        
        print_status("AnomalySentryAgent imported successfully", 'success')
        print_status(f"Default metrics: {len(sentry.metrics)}", 'success')
        
        # Test metric definition
        test_metric = MetricDefinition(
            name="test_metric",
            query="SELECT 1 as value",
            description="Test metric"
        )
        
        print_status("MetricDefinition created successfully", 'success')
        
        return True
        
    except Exception as e:
        print_status(f"Sentry Agent test failed: {e}", 'error')
        return False


def test_researcher_agent():
    """Test Researcher Agent initialization"""
    print("\n" + "="*60)
    print("6. Testing Researcher Agent")
    print("="*60)
    
    try:
        from src.agents.researcher import ResearcherAgent, TavilySearchTool
        
        # Check if Tavily API key is set
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            print_status("TAVILY_API_KEY not set - tool will be disabled", 'warning')
        
        # Test tool initialization
        tool = TavilySearchTool(api_key=tavily_key)
        print_status("TavilySearchTool imported successfully", 'success')
        
        if tavily_key:
            print_status("Tavily API key configured", 'success')
        
        return True
        
    except Exception as e:
        print_status(f"Researcher Agent test failed: {e}", 'error')
        return False


def test_crewai_manager():
    """Test CrewAI Manager updates"""
    print("\n" + "="*60)
    print("7. Testing CrewAI Manager Integration")
    print("="*60)
    
    try:
        from src.agents.crewai_manager import DataOpsManager
        
        # Check if generate_with_research method exists
        if hasattr(DataOpsManager, 'generate_with_research'):
            print_status("generate_with_research() method found", 'success')
        else:
            print_status("generate_with_research() method NOT FOUND", 'error')
            return False
        
        print_status("CrewAI Manager Phase 4 integration confirmed", 'success')
        return True
        
    except Exception as e:
        print_status(f"CrewAI Manager test failed: {e}", 'error')
        return False


def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n" + "="*60)
    print("8. Testing API Endpoint Definitions")
    print("="*60)
    
    try:
        # Read main_crewai.py and check for Phase 4 endpoints
        api_file = Path(__file__).parent.parent / 'src' / 'api' / 'main_crewai.py'
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        endpoints = {
            '/ws/alerts': 'WebSocket alerts endpoint',
            '/alerts/recent': 'Recent alerts endpoint',
            '/alerts/check': 'Manual metric check endpoint',
            '/query/research': 'Unified research endpoint'
        }
        
        all_found = True
        
        for endpoint, description in endpoints.items():
            if endpoint in content:
                print_status(f"{description} ({endpoint})", 'success')
            else:
                print_status(f"{description} ({endpoint}): NOT FOUND", 'error')
                all_found = False
        
        return all_found
        
    except Exception as e:
        print_status(f"API endpoint test failed: {e}", 'error')
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = 'success' if result else 'error'
        print_status(test_name, status)
    
    print("\n" + "-"*60)
    
    if passed == total:
        print_status(f"ALL TESTS PASSED ({passed}/{total})", 'success')
        print("\n🎉 Phase 4 is ready to use!")
        print("\nNext steps:")
        print("  1. Start the backend: python -m uvicorn src.api.main_crewai:app --reload")
        print("  2. Check health: curl http://localhost:8000/health")
        print("  3. Test WebSocket: Connect to ws://localhost:8000/ws/alerts")
        return True
    else:
        print_status(f"TESTS FAILED ({total - passed}/{total})", 'error')
        print("\n⚠️  Please fix the errors above before proceeding.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Set environment variables in .env file")
        print("  - Check file paths are correct")
        return False


def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "Autonomous Multi-Agent Business Intelligence System Phase 4 Setup Test" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Environment Variables': check_environment_variables(),
        'File Structure': check_file_structure(),
        'Sentry Agent': test_sentry_agent(),
        'Researcher Agent': test_researcher_agent(),
        'CrewAI Manager': test_crewai_manager(),
        'API Endpoints': test_api_endpoints()
    }
    
    success = print_summary(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
