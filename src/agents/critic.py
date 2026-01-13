"""
SQL Critic Agent for Autonomous Multi-Agent Business Intelligence System

Performs dry-run style reasoning (EXPLAIN / logical checks) on generated SQL,
returns structured feedback, and proposes a correction plan.
"""

import json
import logging
from typing import Dict, Any
from crewai import Agent
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_critic_agent(reasoning_llm: ChatOpenAI) -> Agent:
    """
    Build the SQL Critic agent that specializes in error detection and correction planning.

    Args:
        reasoning_llm: High-accuracy LLM (e.g., OpenAI o1) for deep reasoning
    """
    return Agent(
        role="SQL Critic & Dry-Runner",
        goal="Stress-test SQL with EXPLAIN-style reasoning, surface errors, and propose fixes",
        backstory=(
            "You are a meticulous database reliability engineer. You mentally run EXPLAIN / DRY-RUN "
            "on SQL, find syntax or logical issues, and propose concrete fixes with minimal tokens."
        ),
        verbose=True,
        allow_delegation=False,
        llm=reasoning_llm
    )


def parse_critic_feedback(raw_feedback: str) -> Dict[str, Any]:
    """Parse critic feedback into a structured dict.

    The critic is asked to return JSON. We attempt to parse, but fall back gracefully.
    """
    def _strip_json(text: str) -> str:
        # Remove markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
        # Grab substring between first '{' and last '}'
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]
        return text

    try:
        cleaned = _strip_json(raw_feedback)
        data = json.loads(cleaned)
        # Normalize keys
        status = data.get("status", "error").lower()
        return {
            "status": status,
            "error_message": data.get("error_message") or data.get("error") or "",
            "correction_plan": data.get("correction_plan") or data.get("fix_plan") or "",
            "corrected_sql": data.get("corrected_sql") or data.get("sql"),
            "issues": data.get("issues", []),
            "raw": raw_feedback,
        }
    except Exception as exc:
        logger.warning(f"Failed to parse critic feedback, returning fallback: {exc}")
        return {
            "status": "error",
            "error_message": raw_feedback,
            "correction_plan": "",
            "corrected_sql": None,
            "issues": [],
            "raw": raw_feedback,
        }
