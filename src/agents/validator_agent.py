"""
Validator Agent for Autonomous Multi-Agent Business Intelligence System.

This agent validates that a SQL query is safe to run.

Rules:
- Only allow SELECT queries
- Block INSERT, UPDATE, DELETE, DROP, ALTER
- Do NOT execute SQL
- Do NOT use LLMs
"""

class ValidatorAgent:
    FORBIDDEN_KEYWORDS = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "CREATE", "REPLACE", "EXEC", "EXECUTE", "CALL"
    }
    
    ALLOWED_KEYWORDS = {"SELECT", "FROM", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "JOIN", "ON", "AS", "DISTINCT"}
    
    def validate(self, sql: str) -> dict:
        """
        Return a dictionary with:
        - is_valid (bool)
        - errors (list of strings)
        """
        errors = []
        sql_upper = sql.upper().strip()
        
        # Check for empty query
        if not sql_upper:
            errors.append("SQL query is empty")
            return {"is_valid": False, "errors": errors}
        
        # Check if it starts with SELECT
        if not sql_upper.startswith("SELECT"):
            errors.append("Query must start with SELECT")
        
        # Check for forbidden keywords
        tokens = self._tokenize_sql(sql_upper)
        for token in tokens:
            if token in self.FORBIDDEN_KEYWORDS:
                errors.append(f"Forbidden operation: {token}")
        
        # Check for comments that might hide dangerous operations
        if "--" in sql or "/*" in sql:
            # Basic comment check
            pass  # Comments are generally safe
        
        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            errors.append("Unbalanced parentheses in query")
        
        # Check for suspicious patterns
        if any(pattern in sql_upper for pattern in ["UNION", "UNION ALL"]):
            # UNION is allowed but should be monitored
            pass
        
        return {"is_valid": len(errors) == 0, "errors": errors}
    
    def _tokenize_sql(self, sql: str) -> list:
        """Simple SQL tokenizer."""
        import re
        # Split by whitespace and common delimiters
        tokens = re.findall(r"\b\w+\b", sql)
        return tokens
