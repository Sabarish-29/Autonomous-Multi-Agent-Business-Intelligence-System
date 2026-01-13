"""
SQLQueryResultTool - safe SQL execution utility for CrewAI tasks.

Executes read-only SELECT queries with a configurable row limit and returns
results as a markdown-formatted table string for easy inspection.
"""

import logging
from typing import Optional, Any

import pandas as pd
from crewai.tools import BaseTool
from pydantic import Field, PrivateAttr
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class SQLQueryResultTool(BaseTool):
    """Safely execute SELECT queries and return a compact result preview."""

    name: str = "sql_query_result_tool"
    description: str = (
        "Executes read-only SQL queries with a LIMIT to prevent large scans. "
        "Returns a markdown table preview of the result set."
    )

    db_url: str = Field(description="SQLAlchemy database URL")
    row_limit: int = Field(default=50, description="Maximum rows to preview")
    _engine: Any = PrivateAttr(default=None)

    def __init__(self, db_url: str, row_limit: int = 50):
        super().__init__(db_url=db_url, row_limit=row_limit)
        try:
            self._engine = create_engine(self.db_url, pool_pre_ping=True)
            logger.info("SQLQueryResultTool initialized with provided DB URL")
        except Exception as exc:
            logger.error(f"Failed to initialize SQL engine: {exc}")
            self._engine = None

    def _run(self, sql: str, limit: Optional[int] = None) -> str:
        """Execute a SQL query safely with a LIMIT.

        Args:
            sql: SQL query string (must be SELECT)
            limit: Optional override for row limit
        """
        if not self._engine:
            return "Engine not initialized. Cannot execute query."

        safe_limit = limit or self.row_limit
        sql_lower = sql.strip().lower()
        if not sql_lower.startswith("select") and not sql_lower.startswith("with"):
            return "Only read-only SELECT queries are allowed."

        # Enforce a LIMIT if not present
        if " limit " not in sql_lower:
            sql = f"{sql.rstrip(';')} LIMIT {safe_limit}"

        try:
            with self._engine.connect() as conn:
                df = pd.read_sql_query(text(sql), conn)
            if df.empty:
                return "Query executed successfully. No rows returned."
            preview = df.head(safe_limit)
            return preview.to_markdown(index=False)
        except Exception as exc:
            logger.error(f"SQL execution failed: {exc}")
            return f"Execution error: {exc}"
