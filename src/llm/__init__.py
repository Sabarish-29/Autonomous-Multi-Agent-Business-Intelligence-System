"""
Autonomous Multi-Agent Business Intelligence System - LLM Module

Provides hybrid LLM support with intelligent routing between:
- Ollama (local) for fast, free inference
- Claude API (cloud) for complex reasoning
"""

from .ollama_service import OllamaService
from .claude_service import ClaudeService
from .router import LLMRouter, TaskType, get_llm_router

__all__ = [
    "OllamaService",
    "ClaudeService",
    "LLMRouter",
    "TaskType",
    "get_llm_router",
]
