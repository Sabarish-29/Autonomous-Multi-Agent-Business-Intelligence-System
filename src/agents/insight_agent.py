"""
Insight Agent for Autonomous Multi-Agent Business Intelligence System.

This agent converts analytical context into
business-friendly insights.

Rules:
- Do NOT execute SQL
- Do NOT call any LLM
- Do NOT access databases
- Generate deterministic, explainable output
"""

class InsightAgent:
    def analyze(self, sql: str, plan: dict) -> dict:
        """
        Return a dictionary with:
        - summary (string)
        - key_points (list of strings)
        - recommendations (list of strings)
        """
        sql_upper = sql.upper()
        plan_goal = plan.get("goal", "Generate analytical insights")
        plan_steps = plan.get("steps", [])
        
        # Generate summary
        summary = self._generate_summary(plan_goal, sql_upper)
        
        # Extract key points
        key_points = self._extract_key_points(sql_upper, plan_steps)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(sql_upper, plan_goal)
        
        return {
            "summary": summary,
            "key_points": key_points,
            "recommendations": recommendations
        }
    
    def _generate_summary(self, goal: str, sql: str) -> str:
        """Generate a business-friendly summary of the analysis."""
        if "GROUP" in sql:
            return f"{goal} with grouping by one or more dimensions."
        elif "ORDER" in sql and "LIMIT" in sql:
            return f"{goal} with ranked results."
        elif "JOIN" in sql:
            return f"{goal} by combining multiple data sources."
        else:
            return f"{goal} on the available data."
    
    def _extract_key_points(self, sql: str, plan_steps: list) -> list:
        """Extract key analytical points from the SQL and plan."""
        key_points = []
        
        # Detect aggregation functions
        if "SUM(" in sql:
            key_points.append("Analysis uses total aggregation")
        if "AVG(" in sql or "AVERAGE(" in sql:
            key_points.append("Analysis includes average calculations")
        if "COUNT(" in sql:
            key_points.append("Analysis includes count metrics")
        if "MAX(" in sql or "MIN(" in sql:
            key_points.append("Analysis identifies min/max values")
        
        # Detect filtering
        if "WHERE" in sql:
            key_points.append("Results are filtered by specific criteria")
        
        # Detect grouping
        if "GROUP BY" in sql:
            key_points.append("Results are grouped for comparative analysis")
        
        # Detect sorting
        if "ORDER BY" in sql:
            if "DESC" in sql:
                key_points.append("Results are sorted in descending order")
            else:
                key_points.append("Results are sorted in ascending order")
        
        # Add plan-based insights
        if "time-series" in str(plan_steps).lower():
            key_points.append("Includes time-based trend analysis")
        
        return key_points or ["Data analysis completed"]
    
    def _generate_recommendations(self, sql: str, goal: str) -> list:
        """Generate actionable recommendations based on the analysis."""
        recommendations = []
        
        # General recommendations
        if "GROUP BY" not in sql and "DISTINCT" not in sql:
            recommendations.append("Consider grouping by key business dimensions for deeper insights")
        
        if "WHERE" not in sql:
            recommendations.append("Filter data by relevant criteria to focus analysis")
        
        if "ORDER BY" not in sql:
            recommendations.append("Sort results to identify top performers or trends")
        
        if "JOIN" not in sql:
            recommendations.append("Consider combining multiple data sources for comprehensive view")
        
        if "LIMIT" not in sql and "OFFSET" not in sql:
            recommendations.append("Consider pagination for large result sets")
        
        # Goal-based recommendations
        if "trend" in goal.lower():
            recommendations.append("Use time-series visualization to see patterns over time")
        elif "rank" in goal.lower() or "top" in goal.lower():
            recommendations.append("Focus on the top entities for strategic decision-making")
        elif "comparison" in goal.lower():
            recommendations.append("Use comparative visualizations to highlight differences")
        
        return recommendations or ["Analysis ready for business review"]
