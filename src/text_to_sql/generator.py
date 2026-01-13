"""
Autonomous Multi-Agent Business Intelligence System - Text-to-SQL Generator

Main SQL generation engine with 92% accuracy target.
Uses hybrid LLM approach with RAG enhancement.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..llm.router import LLMRouter, TaskType, get_llm_router
from ..rag.retriever import RAGRetriever
from ..nlp.ner_extractor import NERExtractor
from ..nlp.intent_classifier import IntentClassifier
from ..agents.orchestrator import AgentOrchestrator
from .schema_manager import SchemaManager
from .validator import SQLValidator

logger = logging.getLogger(__name__)


@dataclass
class SQLGenerationResult:
    """Result of SQL generation."""
    sql: str
    confidence: float
    explanation: str
    complexity: str
    entities: List[Dict]
    intent: Dict
    cost_estimate: float
    provider: str
    validation_status: str
    validation_errors: List[str]


class TextToSQLGenerator:
    """
    Text-to-SQL generation engine.
    
    Pipeline:
    1. Extract entities (NER)
    2. Classify intent
    3. Retrieve context (RAG)
    4. Generate SQL (LLM)
    5. Validate SQL
    6. Explain query
    """

    # SQL generation prompt template
    SQL_PROMPT_TEMPLATE = """You are an expert SQL query generator. Convert natural language queries to SQL.

IMPORTANT RULES:
1. Generate only valid SQL syntax
2. Use appropriate aggregation functions (SUM, COUNT, AVG) for metrics
3. Include GROUP BY for aggregated queries
4. Use proper date filtering for time-based queries
5. Add ORDER BY and LIMIT for ranking queries
6. Return ONLY the SQL query, no explanations

{schema_context}

{examples}

User Query: {query}

SQL:"""

    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        rag_retriever: Optional[RAGRetriever] = None,
        ner_extractor: Optional[NERExtractor] = None,
        intent_classifier: Optional[IntentClassifier] = None
    ):
        """
        Initialize SQL generator.
        
        Args:
            llm_router: LLM routing service
            rag_retriever: RAG retrieval service
            ner_extractor: NER extraction service
            intent_classifier: Intent classification service
        """
        self.llm_router = llm_router or get_llm_router()
        self.rag_retriever = rag_retriever
        if not self.rag_retriever:
            try:
                self.rag_retriever = RAGRetriever()
            except Exception as e:
                logger.warning(f"Failed to initialize RAG Retriever: {e}")
                self.rag_retriever = None
        self.ner_extractor = ner_extractor or NERExtractor()
        self.intent_classifier = intent_classifier or IntentClassifier(
            use_transformers=False  # Use lightweight rules for speed
        )
        self.schema_manager = SchemaManager()
        self.validator = SQLValidator()
        
        logger.info("Text-to-SQL Generator initialized")

    def generate(
        self,
        query: str,
        database: str = "default",
        use_rag: bool = True,
        validate: bool = True
    ) -> SQLGenerationResult:
        """
        Generate SQL from natural language query.
        
        Args:
            query: Natural language query
            database: Target database name
            use_rag: Whether to use RAG for context
            validate: Whether to validate generated SQL
            
        Returns:
            SQLGenerationResult with SQL and metadata
        """
        logger.info(f"Generating SQL for: {query[:50]}...")

        # Step 1: Extract entities
        entities = self.ner_extractor.extract_entities_dict(query)
        logger.debug(f"Extracted {len(entities)} entities")

        # Step 2: Classify intent
        intent = self.intent_classifier.classify_dict(query)
        logger.debug(f"Classified intent: {intent['intent']}")

        # Step 3: Analyze complexity
        complexity = self._analyze_complexity(query, entities, intent)

        # Step 4: Get schema context
        schema_context = self.schema_manager.get_schema_for_prompt(database)

        # Step 5: Get RAG examples
        examples = ""
        if use_rag and self.rag_retriever:
            examples = self.rag_retriever.get_few_shot_examples(query, n_examples=3)

        # Step 6: Build prompt
        prompt = self.SQL_PROMPT_TEMPLATE.format(
            schema_context=schema_context,
            examples=f"Examples:\n{examples}" if examples else "",
            query=query
        )

        # Step 7: Determine task type and generate SQL
        task_type = TaskType.SIMPLE_SQL if complexity == "low" else TaskType.COMPLEX_SQL

        response = self.llm_router.route_query(
            prompt=prompt,
            task_type=task_type,
            max_tokens=500,
            temperature=0.1  # Low temp for deterministic SQL
        )

        sql = self._extract_sql(response["content"])

        # Step 8: Validate SQL
        validation_status = "valid"
        validation_errors = []
        
        if validate:
            is_valid, errors = self.validator.validate(sql)
            validation_status = "valid" if is_valid else "invalid"
            validation_errors = errors

            # Retry once with Groq (adjusted prompt) if validation fails
            if not is_valid and task_type == TaskType.SIMPLE_SQL:
                logger.info("Retrying with Groq due to validation error")
                sql, validation_status, validation_errors = self._retry_with_groq(
                    query, schema_context, examples, errors
                )

        # Step 9: Calculate confidence
        confidence = self._calculate_confidence(
            sql, query, complexity, validation_status, bool(examples)
        )

        # Step 10: Generate explanation
        explanation = self._generate_explanation(sql, query, entities)

        return SQLGenerationResult(
            sql=sql,
            confidence=confidence,
            explanation=explanation,
            complexity=complexity,
            entities=entities,
            intent=intent,
            cost_estimate=response.get("cost", 0.0),
            provider=response.get("provider", "unknown"),
            validation_status=validation_status,
            validation_errors=validation_errors
        )

    def _analyze_complexity(
        self,
        query: str,
        entities: List[Dict],
        intent: Dict
    ) -> str:
        """
        Analyze query complexity for routing.
        
        Returns:
            'low', 'medium', or 'high'
        """
        query_lower = query.lower()

        # High complexity indicators
        high_indicators = [
            "join", "subquery", "nested", "window function", "partition",
            "union", "intersect", "except", "cte", "recursive"
        ]

        # Medium complexity indicators
        medium_indicators = [
            "group by", "having", "case when", "multiple", "across",
            "compare", "trend", "versus", "vs"
        ]

        # Count indicators
        high_count = sum(1 for ind in high_indicators if ind in query_lower)
        medium_count = sum(1 for ind in medium_indicators if ind in query_lower)

        # Consider intent
        complex_intents = {"comparison", "trend_analysis", "executive_summary"}
        intent_complexity = 1 if intent["intent"] in complex_intents else 0

        # Consider entity count
        entity_complexity = 1 if len(entities) > 4 else 0

        # Determine complexity
        score = high_count * 2 + medium_count + intent_complexity + entity_complexity

        if score >= 3 or high_count >= 1:
            return "high"
        elif score >= 1:
            return "medium"
        return "low"

    def _extract_sql(self, response: str) -> str:
        """
        Extract SQL from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned SQL string
        """
        sql = response.strip()

        # Remove markdown code blocks
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0]
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0]

        # Remove common prefixes
        prefixes = ["SQL:", "Query:", "sql:", "query:"]
        for prefix in prefixes:
            if sql.startswith(prefix):
                sql = sql[len(prefix):]

        # Clean whitespace
        sql = sql.strip()

        # Ensure semicolon
        if not sql.endswith(";"):
            sql += ";"

        return sql

    def _calculate_confidence(
        self,
        sql: str,
        query: str,
        complexity: str,
        validation_status: str,
        has_examples: bool
    ) -> float:
        """
        Calculate confidence score (0-1).
        """
        base_confidence = 0.85

        # Adjust for validation
        if validation_status == "invalid":
            base_confidence -= 0.15

        # Adjust for complexity
        complexity_adj = {"low": 0.05, "medium": 0.0, "high": -0.05}
        base_confidence += complexity_adj.get(complexity, 0)

        # Boost if RAG examples available
        if has_examples:
            base_confidence += 0.03

        # Penalize very long SQL
        if len(sql) > 500:
            base_confidence -= 0.05

        return round(min(max(base_confidence, 0.5), 0.98), 2)

    def _generate_explanation(
        self,
        sql: str,
        query: str,
        entities: List[Dict]
    ) -> str:
        """
        Generate human-readable explanation.
        """
        # Simple rule-based explanation
        parts = []

        # Detect operation type
        sql_upper = sql.upper()
        if "SELECT" in sql_upper:
            parts.append("This query retrieves")
        
        # Add metrics
        metrics = [e for e in entities if e["label"] == "METRIC"]
        if metrics:
            metric_names = [m["text"] for m in metrics]
            parts.append(f"the {', '.join(metric_names)}")

        # Add dimensions
        dimensions = [e for e in entities if e["label"] == "DIMENSION"]
        if dimensions:
            dim_names = [d["text"] for d in dimensions]
            parts.append(f"grouped by {', '.join(dim_names)}")

        # Add time period
        time_periods = [e for e in entities if e["label"] == "TIME_PERIOD"]
        if time_periods:
            parts.append(f"for {time_periods[0]['text']}")

        # Add aggregation info
        if "SUM" in sql_upper or "COUNT" in sql_upper or "AVG" in sql_upper:
            parts.append("with aggregation")

        # Add ordering info
        if "ORDER BY" in sql_upper:
            if "DESC" in sql_upper:
                parts.append("ordered from highest to lowest")
            else:
                parts.append("ordered from lowest to highest")

        if "LIMIT" in sql_upper:
            parts.append("limited to top results")

        return " ".join(parts) + "." if parts else "Retrieves data based on your query."

    def _retry_with_groq(
        self,
        query: str,
        schema_context: str,
        examples: str,
        errors: List[str]
    ) -> tuple:
        """
        Retry SQL generation with Groq after validation failure.
        """
        error_context = "\n".join([f"- {e}" for e in errors])
        examples_block = f"Examples:\n{examples}" if examples else ""

        retry_prompt = (
            self.SQL_PROMPT_TEMPLATE.format(
                schema_context=schema_context,
                examples=examples_block,
                query=query
            )
            + f"""

        IMPORTANT: The previous attempt had these errors:
        {error_context}

        Please generate a corrected SQL query that avoids these issues.

        SQL:"""
        )


        response = self.llm_router.route_query(
            prompt=retry_prompt,
            task_type=TaskType.COMPLEX_SQL,
            max_tokens=600,
            temperature=0.05
        )

        sql = self._extract_sql(response["content"])
        is_valid, new_errors = self.validator.validate(sql)

        return sql, "valid" if is_valid else "invalid", new_errors

    def generate_dict(
        self,
        query: str,
        database: str = "default",
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Generate SQL and return as dictionary.
        """
        result = self.generate(query, database, use_rag)
        return {
            "sql": result.sql,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "complexity": result.complexity,
            "entities": result.entities,
            "intent": result.intent,
            "cost_estimate": result.cost_estimate,
            "provider": result.provider,
            "validation_status": result.validation_status,
            "validation_errors": result.validation_errors
        }

    # Optional agentic entrypoint that uses AgentOrchestrator
    # This must NOT modify existing generate() behavior
    # It should:
    # - Instantiate AgentOrchestrator
    # - Run agentic pipeline (planning → SQL → validation → correction → insights)
    # - Return enriched output including sql, plan, insights, and agent_trace

    def generate_agentic(self, query: str, database: str = "default") -> dict:
        """
        Use AgentOrchestrator to run agentic pipeline.
        Do NOT modify existing generate() method.
        Return sql, plan, insights, agent_trace, and attempts.
        """
        orchestrator = AgentOrchestrator(self)
        return orchestrator.run(query=query, database=database)

