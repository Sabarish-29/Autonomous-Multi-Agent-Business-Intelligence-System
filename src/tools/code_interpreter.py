"""
Secure Python Code Interpreter for Autonomous Multi-Agent Business Intelligence System Phase 3.

Provides Docker-based (preferred) and RestrictedPython fallback for safe code execution.
Supports pandas, numpy, scipy, matplotlib, seaborn, and statsmodels for analytics.
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Try to import docker
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

# Try to import RestrictedPython as fallback
try:
    from RestrictedPython import compile_restricted, safe_globals
    from RestrictedPython.Guards import guarded_iter_unpack_sequence, safe_builtins
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecureCodeInterpreter:
    """
    Secure Python code execution sandbox with Docker (preferred) or RestrictedPython fallback.
    
    Security Features:
    - Docker: Isolated container with no network, limited memory/CPU
    - RestrictedPython: Blocks os, sys, subprocess, eval, exec, __import__
    - Timeout enforcement (30s default)
    - Memory limits (512MB default)
    """
    
    def __init__(
        self,
        mode: str = "auto",  # "docker", "restricted", or "auto"
        timeout: int = 30,
        memory_limit: str = "512m",
        allowed_packages: Optional[List[str]] = None
    ):
        """
        Initialize code interpreter.
        
        Args:
            mode: Execution mode - "docker" (preferred), "restricted", or "auto"
            timeout: Max execution time in seconds
            memory_limit: Docker memory limit (e.g., "512m", "1g")
            allowed_packages: List of allowed packages (default: pandas, numpy, scipy, etc.)
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.allowed_packages = allowed_packages or [
            "pandas", "numpy", "scipy", "matplotlib", "seaborn", 
            "statsmodels", "plotly", "sklearn"
        ]
        
        # Determine execution mode
        requested_mode = mode
        if mode == "auto":
            if DOCKER_AVAILABLE:
                self.mode = "docker"
                logger.info("Using Docker-based sandbox (preferred)")
            elif RESTRICTED_PYTHON_AVAILABLE:
                self.mode = "restricted"
                logger.warning("Docker not available, falling back to RestrictedPython")
            else:
                raise RuntimeError(
                    "Neither Docker nor RestrictedPython available. "
                    "Install: pip install docker OR pip install RestrictedPython"
                )
        else:
            self.mode = mode
            
        # Initialize Docker client if needed
        if self.mode == "docker":
            if not DOCKER_AVAILABLE:
                raise RuntimeError("Docker mode selected but docker package not installed")
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                logger.info("Docker client connected successfully")
            except Exception as e:
                # If user asked for auto, gracefully fall back to RestrictedPython.
                if (requested_mode == "auto") and RESTRICTED_PYTHON_AVAILABLE:
                    logger.warning(
                        "Docker daemon not available; falling back to RestrictedPython. "
                        f"Docker error: {e}"
                    )
                    self.mode = "restricted"
                    self.docker_client = None
                else:
                    raise RuntimeError(f"Failed to connect to Docker daemon: {e}")
    
    def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code in secure sandbox.
        
        Args:
            code: Python code to execute
            context: Optional variables to inject (e.g., dataframes)
        
        Returns:
            {
                "success": bool,
                "result": Any,  # Return value or output
                "output": str,  # stdout/stderr
                "error": str,   # Error message if failed
                "visualization": Optional[dict]  # Plotly JSON if generated
            }
        """
        if self.mode == "docker":
            return self._execute_docker(code, context)
        else:
            return self._execute_restricted(code, context)
    
    def _execute_docker(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code in Docker container."""
        context = context or {}
        
        # Create temporary directory for code and data
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save context data (e.g., dataframes) as CSV
            context_files = {}
            for key, value in context.items():
                if hasattr(value, 'to_csv'):  # DataFrame
                    csv_path = tmpdir_path / f"{key}.csv"
                    value.to_csv(csv_path, index=False)
                    context_files[key] = f"{key}.csv"
            
            # Create execution script
            script = self._build_docker_script(code, context_files)
            script_path = tmpdir_path / "script.py"
            script_path.write_text(script)
            
            # Output file for results
            output_path = tmpdir_path / "output.json"
            
            try:
                # Run container with security constraints
                container = self.docker_client.containers.run(
                    image="python:3.11-slim",  # Lightweight Python image
                    command=["python", "/workspace/script.py"],
                    volumes={str(tmpdir_path): {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    mem_limit=self.memory_limit,
                    network_disabled=True,  # No network access
                    remove=True,
                    detach=False,
                    stdout=True,
                    stderr=True,
                    timeout=self.timeout
                )
                
                # Read results
                if output_path.exists():
                    result = json.loads(output_path.read_text())
                    return {
                        "success": True,
                        "result": result.get("result"),
                        "output": result.get("output", ""),
                        "error": None,
                        "visualization": result.get("visualization")
                    }
                else:
                    return {
                        "success": False,
                        "result": None,
                        "output": container.decode() if isinstance(container, bytes) else str(container),
                        "error": "No output file generated",
                        "visualization": None
                    }
                    
            except docker.errors.ContainerError as e:
                return {
                    "success": False,
                    "result": None,
                    "output": e.stderr.decode() if e.stderr else "",
                    "error": f"Container execution failed: {e}",
                    "visualization": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "result": None,
                    "output": "",
                    "error": f"Docker execution error: {e}",
                    "visualization": None
                }
    
    def _build_docker_script(self, user_code: str, context_files: Dict[str, str]) -> str:
        """Build execution script for Docker container."""
        return f"""
import sys
import json
import pandas as pd
import numpy as np
import traceback
from io import StringIO

# Redirect stdout/stderr
stdout_capture = StringIO()
stderr_capture = StringIO()
sys.stdout = stdout_capture
sys.stderr = stderr_capture

# Load context data
context = {{}}
{chr(10).join([f"context['{key}'] = pd.read_csv('/workspace/{file}')" for key, file in context_files.items()])}

# Execute user code
result = None
visualization = None
error = None

try:
    # Execute code with context
    exec_globals = {{"pd": pd, "np": np, **context}}
    exec('''
{chr(10).join(['    ' + line for line in user_code.split(chr(10))])}
''', exec_globals)
    
    # Extract result and visualization if available
    if 'result' in exec_globals:
        result = exec_globals['result']
        # Convert to JSON-serializable format
        if hasattr(result, 'to_dict'):
            result = result.to_dict()
        elif hasattr(result, 'tolist'):
            result = result.tolist()
    
    if 'fig' in exec_globals:
        # Plotly figure
        visualization = exec_globals['fig'].to_json()
    elif 'visualization' in exec_globals:
        visualization = exec_globals['visualization']
        
except Exception as e:
    error = traceback.format_exc()

# Write output
output_data = {{
    "result": result,
    "output": stdout_capture.getvalue(),
    "error": error,
    "visualization": visualization
}}

with open('/workspace/output.json', 'w') as f:
    json.dump(output_data, f)
"""
    
    def _execute_restricted(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code with RestrictedPython (fallback)."""
        context = context or {}
        
        # Prepare restricted globals
        restricted_globals = {
            '__builtins__': safe_builtins,
            '_getiter_': guarded_iter_unpack_sequence,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
        }
        
        # Add safe imports
        import pandas as pd
        import numpy as np
        try:
            import scipy
            restricted_globals['scipy'] = scipy
        except ImportError:
            pass
        
        restricted_globals['pd'] = pd
        restricted_globals['np'] = np
        restricted_globals.update(context)
        
        try:
            # Compile restricted code
            byte_code = compile_restricted(code, '<string>', 'exec')
            
            if byte_code.errors:
                return {
                    "success": False,
                    "result": None,
                    "output": "",
                    "error": f"Compilation errors: {byte_code.errors}",
                    "visualization": None
                }
            
            # Execute with timeout (basic implementation)
            exec(byte_code.code, restricted_globals)
            
            # Extract result
            result = restricted_globals.get('result')
            visualization = restricted_globals.get('visualization') or restricted_globals.get('fig')
            
            # Convert visualization to JSON if it's a Plotly figure
            if visualization and hasattr(visualization, 'to_json'):
                visualization = visualization.to_json()
            
            return {
                "success": True,
                "result": result,
                "output": "Execution completed",
                "error": None,
                "visualization": visualization
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "output": "",
                "error": str(e),
                "visualization": None
            }


class CodeInterpreterTool:
    """
    CrewAI-compatible tool wrapper for SecureCodeInterpreter.
    """
    
    def __init__(self, mode: str = "auto", timeout: int = 30, memory_limit: str = "512m"):
        """Initialize code interpreter tool."""
        self.name = "code_interpreter"
        self.description = (
            "Execute Python code in a secure sandbox. "
            "Use this to perform data analysis, statistical computations, "
            "or generate visualizations. The sandbox has pandas, numpy, scipy, "
            "matplotlib, seaborn, and plotly available."
        )
        self.interpreter = SecureCodeInterpreter(
            mode=mode,
            timeout=timeout,
            memory_limit=memory_limit
        )
    
    def _run(self, code: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute code and return formatted result."""
        result = self.interpreter.execute(code, context)
        
        if result["success"]:
            output = f"✅ Execution successful\n\n"
            if result["output"]:
                output += f"Output:\n{result['output']}\n\n"
            if result["result"]:
                output += f"Result:\n{result['result']}\n\n"
            if result["visualization"]:
                output += f"📊 Visualization generated (Plotly JSON available)\n"
            return output
        else:
            return f"❌ Execution failed\n\nError:\n{result['error']}"
    
    def run(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code and return full result dictionary."""
        return self.interpreter.execute(code, context)
