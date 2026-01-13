"""
Autonomous Multi-Agent Business Intelligence System - LLM Router

Smart routing between local (Ollama) and cloud (Claude/Groq) LLMs
based on query complexity, resource availability, and cost.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .ollama_service import OllamaService
from .claude_service import ClaudeService
from .groq_service import GroqService
from ..config import settings

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task types for routing decisions."""
    SIMPLE_SQL = "simple_sql"
    COMPLEX_SQL = "complex_sql"
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"
    RAG_SYNTHESIS = "rag_synthesis"
    EXECUTIVE_SUMMARY = "executive_summary"
    EXPLANATION = "explanation"
    VALIDATION = "validation"


class LLMRouter:
    """
    Intelligent LLM router for hybrid local/cloud deployment.
    
    Routing Strategy:
    - Simple tasks → Local Ollama (fast, free)
    - Complex tasks → Claude API (accurate, paid)
    - Fallback logic when primary unavailable
    """

    # Routing configuration
    LOCAL_TASKS = {
        TaskType.SIMPLE_SQL,
        TaskType.INTENT_CLASSIFICATION,
        TaskType.ENTITY_EXTRACTION,
        TaskType.VALIDATION,
    }

    CLOUD_TASKS = {
        TaskType.COMPLEX_SQL,
        TaskType.RAG_SYNTHESIS,
        TaskType.EXECUTIVE_SUMMARY,
        TaskType.EXPLANATION,
    }

    def __init__(self):
        """Initialize LLM router with available services."""
        self._ollama: Optional[OllamaService] = None
        self._claude: Optional[ClaudeService] = None
        self._groq: Optional[GroqService] = None
        self._initialize_services()

    def _initialize_services(self):
        """Initialize Groq service only."""
        # Initialize Groq if API key available
        if settings.has_groq_key:
            try:
                self._groq = GroqService()
                logger.info("Groq service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
                raise RuntimeError("Groq API is required but failed to initialize")
        else:
            logger.error("Groq API key not found in configuration")
            raise RuntimeError("GROQ_API_KEY must be set in .env file")

    def _is_any_available(self) -> bool:
        """Check if Groq service is available."""
        return self._groq is not None

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of Groq service.
        
        Returns:
            Dict with service availability status
        """
        return {
            "groq": {
                "enabled": settings.has_groq_key,
                "available": self._groq is not None,
                "model": settings.groq_model,
            }
        }

    def route_query(
        self,
        prompt: str,
        task_type: TaskType | str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        force_provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route query to appropriate LLM based on task type.
        
        Args:
            prompt: User prompt
            task_type: Type of task (determines routing)
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_provider: Override routing ('ollama' or 'claude')
            **kwargs: Additional parameters
            
        Returns:
            Dict with 'content', 'provider', 'tokens', 'cost'
        """
        # Convert string to enum if needed
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.SIMPLE_SQL

        logger.info(f"Routing task: {task_type.value}")

        # Handle forced provider
        if force_provider:
            return self._route_to_provider(
                force_provider, prompt, system_prompt, max_tokens, temperature, **kwargs
            )

        # Route all tasks to Groq (Groq-only architecture)
        return self._route_to_groq(
            prompt, system_prompt, max_tokens, temperature, task_type, **kwargs
        )

    def _route_to_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        task_type: TaskType,
        **kwargs
    ) -> Dict[str, Any]:
        """Route all queries to Groq."""
        if not self._groq:
            raise RuntimeError("Groq service not initialized")
        
        try:
            logger.info(f"Routing {task_type.value} to Groq")
            return self._groq.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Groq failed: {e}")
            raise RuntimeError(f"Groq API request failed: {e}")

    def _route_local_first(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        task_type: TaskType,
        **kwargs
    ) -> Dict[str, Any]:
        """Legacy method - redirects to Groq."""
        return self._route_to_groq(
            prompt, system_prompt, max_tokens, temperature, task_type, **kwargs
        )

    def _route_cloud_first(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        task_type: TaskType,
        **kwargs
    ) -> Dict[str, Any]:
        """Legacy method - redirects to Groq."""
        return self._route_to_groq(
            prompt, system_prompt, max_tokens, temperature, task_type, **kwargs
        )

    def _route_to_provider(
        self,
        provider: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Force routing to specific provider."""
        if provider.lower() == "groq":
            if not self._groq:
                raise RuntimeError("Groq not configured")
            return self._groq.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

        raise ValueError(f"Unknown provider: {provider}. Only 'groq' is supported.")

    def estimate_cost(
        self,
        task_type: TaskType | str,
        estimated_tokens: int = 1000
    ) -> Dict[str, float]:
        """
        Estimate cost for Groq queries.
        
        Args:
            task_type: Type of task
            estimated_tokens: Estimated token count
            
        Returns:
            Dict with cost estimates
        """
        # Convert string to enum
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.SIMPLE_SQL

        # Groq cost estimation (very affordable)
        # Llama 3.1 70B: ~$0.00059/1K input, $0.00079/1K output
        input_tokens = int(estimated_tokens * 0.4)
        output_tokens = int(estimated_tokens * 0.6)
        groq_cost = (input_tokens * 0.00059 / 1000) + (output_tokens * 0.00079 / 1000)

        return {
            "groq": round(groq_cost, 6),
            "provider": "groq",
            "task_type": task_type.value
        }

    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity to determine best routing.
        
        Args:
            query: Natural language query
            
        Returns:
            Dict with complexity analysis
        """
        query_lower = query.lower()

        # Complex indicators
        complex_indicators = [
            "join", "subquery", "having", "window function", "partition",
            "case when", "union", "intersect", "complex", "nested",
            "multiple tables", "across", "compare", "trend", "forecast"
        ]

        # Medium indicators
        medium_indicators = [
            "group by", "order by", "filter", "aggregate", "sum", "count",
            "average", "total", "by region", "by month", "top", "bottom"
        ]

        # Count indicators
        complex_count = sum(1 for ind in complex_indicators if ind in query_lower)
        medium_count = sum(1 for ind in medium_indicators if ind in query_lower)

        # Determine complexity
        if complex_count >= 2 or (complex_count >= 1 and medium_count >= 2):
            complexity = "high"
            recommended_task = TaskType.COMPLEX_SQL
        elif medium_count >= 2 or complex_count >= 1:
            complexity = "medium"
            recommended_task = TaskType.COMPLEX_SQL
        else:
            complexity = "low"
            recommended_task = TaskType.SIMPLE_SQL

        return {
            "complexity": complexity,
            "recommended_task_type": recommended_task.value,
            "complex_indicators_found": complex_count,
            "medium_indicators_found": medium_count,
            "recommended_provider": "ollama" if complexity == "low" else "claude"
        }


# Create singleton instance
_router_instance: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create LLM router singleton."""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance
