"""
Autonomous Multi-Agent Business Intelligence System - SQL Validator

Validates generated SQL queries for syntax and safety.
"""

import logging
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """SQL validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sql_type: str
    is_safe: bool


class SQLValidator:
    """
    SQL query validator.
    
    Checks:
    - Basic syntax validation
    - Dangerous operation detection
    - Common SQL errors
    - Query safety
    """

    # Dangerous operations (block by default)
    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC",
        "EXECUTE", "xp_", "sp_", "SHUTDOWN"
    ]

    # Required clause patterns
    REQUIRED_PATTERNS = {
        "SELECT": r"\bSELECT\b",
        "FROM": r"\bFROM\b",
    }

    def __init__(self, allow_write: bool = False):
        """
        Initialize validator.
        
        Args:
            allow_write: Allow write operations (INSERT, UPDATE, etc.)
        """
        self.allow_write = allow_write
        logger.info(f"SQL Validator initialized (allow_write={allow_write})")

    def validate(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            (is_valid, list of error messages)
        """
        result = self.validate_full(sql)
        return result.is_valid, result.errors

    def validate_full(self, sql: str) -> ValidationResult:
        """
        Full validation with details.
        
        Args:
            sql: SQL query string
            
        Returns:
            ValidationResult with all details
        """
        errors = []
        warnings = []
        sql_type = "SELECT"
        is_safe = True

        # Clean SQL
        sql = sql.strip()
        sql_upper = sql.upper()

        # Check for empty query
        if not sql:
            errors.append("Empty SQL query")
            return ValidationResult(False, errors, warnings, sql_type, False)

        # Detect SQL type
        sql_type = self._detect_sql_type(sql_upper)

        # Check for dangerous operations
        dangerous = self._check_dangerous_operations(sql_upper)
        if dangerous:
            is_safe = False
            if not self.allow_write:
                errors.extend(dangerous)

        # Syntax validation
        syntax_errors = self._validate_syntax(sql)
        errors.extend(syntax_errors)

        # Check balanced parentheses
        if not self._check_balanced_parentheses(sql):
            errors.append("Unbalanced parentheses")

        # Check for common mistakes
        warnings.extend(self._check_common_mistakes(sql_upper))

        # Validate SELECT queries
        if sql_type == "SELECT":
            select_errors = self._validate_select(sql_upper)
            errors.extend(select_errors)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sql_type=sql_type,
            is_safe=is_safe
        )

    def _detect_sql_type(self, sql_upper: str) -> str:
        """Detect the type of SQL statement."""
        sql_types = [
            ("SELECT", "SELECT"),
            ("INSERT", "INSERT"),
            ("UPDATE", "UPDATE"),
            ("DELETE", "DELETE"),
            ("CREATE", "CREATE"),
            ("ALTER", "ALTER"),
            ("DROP", "DROP"),
        ]

        for keyword, sql_type in sql_types:
            if sql_upper.strip().startswith(keyword):
                return sql_type

        return "UNKNOWN"

    def _check_dangerous_operations(self, sql_upper: str) -> List[str]:
        """Check for dangerous SQL operations."""
        errors = []

        for keyword in self.DANGEROUS_KEYWORDS:
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_upper):
                errors.append(f"Dangerous operation detected: {keyword}")

        # Check for SQL injection patterns
        injection_patterns = [
            r";\s*(DROP|DELETE|TRUNCATE)",
            r"UNION\s+(ALL\s+)?SELECT.*FROM\s+information_schema",
            r"OR\s+1\s*=\s*1",
            r"--\s*$",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql_upper):
                errors.append("Potential SQL injection pattern detected")
                break

        return errors

    def _validate_syntax(self, sql: str) -> List[str]:
        """Basic syntax validation."""
        errors = []

        # Try parsing with sqlite3 (basic check)
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            
            # Use EXPLAIN to check syntax without executing
            cursor.execute(f"EXPLAIN {sql}")
            conn.close()
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            # Clean up error message
            if "no such table" not in error_msg.lower():
                errors.append(f"Syntax error: {error_msg}")
        except Exception:
            pass  # Ignore other errors for basic validation

        return errors

    def _check_balanced_parentheses(self, sql: str) -> bool:
        """Check if parentheses are balanced."""
        count = 0
        for char in sql:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            if count < 0:
                return False
        return count == 0

    def _check_common_mistakes(self, sql_upper: str) -> List[str]:
        """Check for common SQL mistakes."""
        warnings = []

        # Missing GROUP BY with aggregates
        aggregates = ["SUM(", "COUNT(", "AVG(", "MIN(", "MAX("]
        has_aggregate = any(agg in sql_upper for agg in aggregates)
        has_group_by = "GROUP BY" in sql_upper

        if has_aggregate and not has_group_by:
            # Check if it's a simple aggregate (no other columns)
            select_match = re.search(r"SELECT\s+(.+?)\s+FROM", sql_upper, re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                # If there are non-aggregate columns, warn
                non_agg = re.sub(r"(SUM|COUNT|AVG|MIN|MAX)\s*\([^)]+\)", "", select_clause)
                if re.search(r"\w+", non_agg.replace(",", "").strip()):
                    warnings.append("Query has aggregates without GROUP BY - may need GROUP BY clause")

        # SELECT *
        if "SELECT *" in sql_upper or "SELECT  *" in sql_upper:
            warnings.append("Using SELECT * - consider specifying columns explicitly")

        # Missing WHERE with aggregate
        if "WHERE" not in sql_upper and has_aggregate:
            warnings.append("No WHERE clause - query will process all rows")

        return warnings

    def _validate_select(self, sql_upper: str) -> List[str]:
        """Validate SELECT statement specifics."""
        errors = []

        # Must have FROM clause
        if "FROM" not in sql_upper:
            errors.append("SELECT query missing FROM clause")

        # Check for incomplete clauses
        incomplete_patterns = [
            (r"WHERE\s*$", "Incomplete WHERE clause"),
            (r"GROUP BY\s*$", "Incomplete GROUP BY clause"),
            (r"ORDER BY\s*$", "Incomplete ORDER BY clause"),
            (r"HAVING\s*$", "Incomplete HAVING clause"),
        ]

        for pattern, message in incomplete_patterns:
            if re.search(pattern, sql_upper):
                errors.append(message)

        return errors

    def sanitize(self, sql: str) -> str:
        """
        Sanitize SQL query (remove comments, normalize whitespace).
        
        Args:
            sql: SQL query
            
        Returns:
            Sanitized SQL
        """
        # Remove single-line comments
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)

        # Remove multi-line comments
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # Normalize whitespace
        sql = re.sub(r"\s+", " ", sql)

        # Strip
        sql = sql.strip()

        return sql

    def is_read_only(self, sql: str) -> bool:
        """
        Check if SQL is read-only.
        
        Args:
            sql: SQL query
            
        Returns:
            True if read-only
        """
        write_keywords = ["INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"]
        sql_upper = sql.upper()
        
        return not any(kw in sql_upper for kw in write_keywords)
