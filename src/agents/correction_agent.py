"""
Self-Correction Agent for Autonomous Multi-Agent Business Intelligence System

Responsibilities:
- Repair invalid or unsafe SQL queries
- Use validation errors to guide fixes
- Never introduce mutation queries
- Retry only a limited number of times
- Remain deterministic and safe

This agent does NOT execute SQL.
It only modifies SQL strings.
"""

class CorrectionAgent:
    def fix(self, sql: str, errors: list[str]) -> str:
        """
        Attempt to fix SQL query based on validation errors.
        Returns corrected SQL string.
        """
        fixed_sql = sql.strip()
        
        for error in errors:
            if "must start with SELECT" in error and not fixed_sql.upper().startswith("SELECT"):
                # Assume it's missing SELECT
                if fixed_sql.upper().startswith("FROM"):
                    fixed_sql = "SELECT * " + fixed_sql
            
            elif "Unbalanced parentheses" in error:
                # Count opening and closing parens
                open_count = fixed_sql.count("(")
                close_count = fixed_sql.count(")")
                if open_count > close_count:
                    fixed_sql += ")" * (open_count - close_count)
                elif close_count > open_count:
                    # Remove extra closing parens from the end
                    excess = close_count - open_count
                    for _ in range(excess):
                        if fixed_sql.endswith(")"):
                            fixed_sql = fixed_sql[:-1]
        
        return fixed_sql