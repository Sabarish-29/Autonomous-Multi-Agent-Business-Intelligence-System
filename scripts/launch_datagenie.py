"""
Autonomous Multi-Agent Business Intelligence System - Quick Launch Script
====================================

Launches both the FastAPI backend and Streamlit frontend simultaneously.

Usage:
    python scripts/launch_datagenie.py

Options:
    --backend-only    Launch only the FastAPI backend
    --frontend-only   Launch only the Streamlit UI
    --port            Backend port (default: 8000)
    --ui-port         Frontend port (default: 8501)
"""

import subprocess
import sys
import time
import os
import argparse
from pathlib import Path


def print_banner():
    """Print Autonomous Multi-Agent Business Intelligence System startup banner"""
    print("\n" + "="*60)
    print("🧞  Autonomous Multi-Agent Business Intelligence System - AI-Powered SQL Generation System")
    print("="*60)


def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required = ['fastapi', 'uvicorn', 'streamlit', 'crewai']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True


def check_environment():
    """Check environment variables"""
    print("\n🔑 Checking environment variables...")

    # Match actual runtime behavior:
    # - GROQ_API_KEY is required for the Phase 4/CrewAI backend startup
    # - OPENAI_API_KEY is optional (can be disabled via DATAGENIE_DISABLE_OPENAI=1)
    # - TAVILY_API_KEY is optional (research mode degrades gracefully)
    groq = os.getenv("GROQ_API_KEY")
    openai = os.getenv("OPENAI_API_KEY")
    tavily = os.getenv("TAVILY_API_KEY")
    disable_openai = os.getenv("DATAGENIE_DISABLE_OPENAI") == "1"

    if groq:
        print("  ✅ Groq API (Fast LLM)")
    else:
        print("  ❌ Groq API (Fast LLM) - NOT SET (required for backend)")

    if disable_openai:
        print("  ✅ OpenAI disabled (DATAGENIE_DISABLE_OPENAI=1)")
    elif openai:
        print("  ✅ OpenAI API (Reasoning) (optional)")
    else:
        print("  ⚠️  OpenAI API (Reasoning) - NOT SET (optional)")

    if tavily:
        print("  ✅ Tavily API (Research) (optional)")
    else:
        print("  ⚠️  Tavily API (Research) - NOT SET (optional)")

    if not groq:
        print("\n⚠️  GROQ_API_KEY is required to start the Phase 4 backend.")
        print("Create a .env file (or export env vars) and set GROQ_API_KEY.")
        return False

    return True


def launch_backend(port=8000):
    """Launch FastAPI backend"""
    print(f"\n🚀 Starting FastAPI backend on port {port}...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.main_crewai:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for startup
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ Backend running at http://localhost:{port}")
            print(f"📖 API docs: http://localhost:{port}/docs")
            return process
        else:
            print("❌ Backend failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None


def launch_frontend(port=8501):
    """Launch Streamlit frontend"""
    print(f"\n🎨 Starting Streamlit UI on port {port}...")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "app/streamlit_ui.py",
        "--server.port", str(port),
        "--server.address", "127.0.0.1"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for startup
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ Frontend running at http://localhost:{port}")
            return process
        else:
            print("❌ Frontend failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None


def main():
    """Main launcher"""
    parser = argparse.ArgumentParser(description="Launch Autonomous Multi-Agent Business Intelligence System")
    parser.add_argument('--backend-only', action='store_true', help='Launch only backend')
    parser.add_argument('--frontend-only', action='store_true', help='Launch only frontend')
    parser.add_argument('--port', type=int, default=8000, help='Backend port')
    parser.add_argument('--ui-port', type=int, default=8501, help='Frontend port')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency checks')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Pre-flight checks
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)
        if not check_environment():
            sys.exit(1)
    
    processes = []
    
    try:
        # Launch components
        if not args.frontend_only:
            backend = launch_backend(args.port)
            if backend:
                processes.append(('backend', backend))
        
        if not args.backend_only:
            frontend = launch_frontend(args.ui_port)
            if frontend:
                processes.append(('frontend', frontend))
        
        if not processes:
            print("\n❌ No services started")
            sys.exit(1)
        
        # Summary
        print("\n" + "="*60)
        print("✅ Autonomous Multi-Agent Business Intelligence System is running!")
        print("="*60)
        
        if not args.frontend_only:
            print(f"🔧 Backend:  http://localhost:{args.port}")
            print(f"📖 API Docs: http://localhost:{args.port}/docs")
        
        if not args.backend_only:
            print(f"🎨 Frontend: http://localhost:{args.ui_port}")
        
        print("\n💡 Press Ctrl+C to stop all services")
        print("="*60 + "\n")
        
        # Keep running and show output
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} process stopped unexpectedly")
                    raise KeyboardInterrupt
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Autonomous Multi-Agent Business Intelligence System...")
        
        for name, process in processes:
            try:
                print(f"  Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print("✅ All services stopped")
        print("👋 Goodbye!\n")


if __name__ == "__main__":
    main()
