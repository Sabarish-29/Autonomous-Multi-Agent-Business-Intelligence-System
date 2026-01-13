"""
Planner Agent for Autonomous Multi-Agent Business Intelligence System.

This agent converts a natural language BI question
into a simple analytical plan.

Rules:
- Do NOT generate SQL
- Do NOT call any external service
- Return deterministic output
"""

class PlannerAgent:
    def plan(self, query: str) -> dict:
        """
        Return a structured plan with:
        - goal
        - steps (list of strings)
        """
        query_lower = query.lower()
        
        # Detect analytical intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        metrics = self._extract_metrics(query_lower)
        dimensions = self._extract_dimensions(query_lower)
        
        # Build analytical plan
        plan = {
            "goal": intent,
            "steps": self._build_steps(intent, metrics, dimensions, query_lower)
        }
        return plan
    
    def _detect_intent(self, query: str) -> str:
        """Detect the analytical intent of the query."""
        keywords = {
            "total": "Summarize total metrics",
            "trend": "Analyze trends over time",
            "comparison": "Compare metrics across dimensions",
            "distribution": "Analyze distribution patterns",
            "ranking": "Rank entities by metric",
            "top": "Identify top performers",
            "bottom": "Identify bottom performers",
            "growth": "Measure growth rates",
            "forecast": "Generate forecasts",
        }
        for keyword, intent in keywords.items():
            if keyword in query:
                return intent
        return "Generate analytical insights"
    
    def _extract_metrics(self, query: str) -> list:
        """Extract metric names from query."""
        metric_keywords = [
            "sales", "revenue", "profit", "cost", "quantity", "count",
            "average", "sum", "total", "min", "max", "percentage"
        ]
        metrics = [m for m in metric_keywords if m in query]
        return metrics or ["metrics"]
    
    def _extract_dimensions(self, query: str) -> list:
        """Extract dimension names from query."""
        dimension_keywords = [
            "region", "customer", "product", "category", "date", "month",
            "year", "quarter", "channel", "segment", "team"
        ]
        dimensions = [d for d in dimension_keywords if d in query]
        return dimensions or ["dimensions"]
    
    def _build_steps(self, intent: str, metrics: list, dimensions: list, query: str) -> list:
        """Build a list of analytical steps."""
        steps = [f"Identify target {metrics[0] if metrics else 'metrics'}"]
        
        if any(word in query for word in ["by", "across", "for each"]):
            steps.append(f"Group by {dimensions[0] if dimensions else 'dimensions'}")
        
        if any(word in query for word in ["trend", "over time", "by month", "by year"]):
            steps.append("Apply time-series analysis")
        
        if any(word in query for word in ["top", "bottom", "rank"]):
            steps.append("Sort and limit results")
        
        if any(word in query for word in ["percentage", "ratio", "proportion"]):
            steps.append("Calculate percentages")
        
        steps.append(f"Present findings on {dimensions[0] if dimensions else 'dimension'}")
        return steps
