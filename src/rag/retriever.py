"""
Autonomous Multi-Agent Business Intelligence System - RAG Retriever

Context retrieval for Retrieval Augmented Generation.
Combines query examples, schema info, and business insights.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Retrieved context for query generation."""
    similar_queries: List[Dict[str, Any]] = field(default_factory=list)
    relevant_schemas: List[Dict[str, Any]] = field(default_factory=list)
    business_insights: List[Dict[str, Any]] = field(default_factory=list)
    formatted_context: str = ""


class RAGRetriever:
    """
    RAG Retriever for context-aware SQL generation.
    
    Retrieves and combines:
    - Similar query examples (few-shot learning)
    - Relevant schema information
    - Business domain knowledge
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize retriever.
        
        Args:
            vector_store: VectorStore instance (creates new if None)
        """
        self.vector_store = vector_store or VectorStore()
        logger.info("RAG Retriever initialized")

    def retrieve(
        self,
        query: str,
        include_examples: bool = True,
        include_schemas: bool = True,
        include_insights: bool = True,
        max_examples: int = 3,
        max_schemas: int = 5,
        max_insights: int = 2
    ) -> RetrievalContext:
        """
        Retrieve context for a query.
        
        Args:
            query: Natural language query
            include_examples: Include similar queries
            include_schemas: Include schema info
            include_insights: Include business insights
            max_examples: Max query examples
            max_schemas: Max schema entries
            max_insights: Max insights
            
        Returns:
            RetrievalContext with all retrieved information
        """
        context = RetrievalContext()

        # Retrieve similar queries
        if include_examples:
            context.similar_queries = self.vector_store.search_similar_queries(
                query=query,
                top_k=max_examples
            )
            logger.debug(f"Retrieved {len(context.similar_queries)} similar queries")

        # Retrieve relevant schemas
        if include_schemas:
            context.relevant_schemas = self.vector_store.search_relevant_schemas(
                query=query,
                top_k=max_schemas
            )
            logger.debug(f"Retrieved {len(context.relevant_schemas)} schemas")

        # Retrieve business insights
        if include_insights:
            context.business_insights = self.vector_store.search_insights(
                query=query,
                top_k=max_insights
            )
            logger.debug(f"Retrieved {len(context.business_insights)} insights")

        # Format context for LLM
        context.formatted_context = self._format_context(context)

        return context

    def _format_context(self, context: RetrievalContext) -> str:
        """
        Format retrieved context for LLM consumption.
        
        Args:
            context: RetrievalContext object
            
        Returns:
            Formatted string for LLM prompt
        """
        parts = []

        # Format similar queries
        if context.similar_queries:
            parts.append("## Similar Query Examples")
            for i, q in enumerate(context.similar_queries, 1):
                parts.append(f"\n### Example {i} (similarity: {q['similarity']:.2f})")
                parts.append(f"Natural: {q['natural_query']}")
                parts.append(f"SQL: {q['sql_query']}")

        # Format schema information
        if context.relevant_schemas:
            parts.append("\n## Relevant Database Schema")
            for schema in context.relevant_schemas:
                parts.append(f"\n### Table: {schema['table_name']}")
                parts.append(f"Description: {schema['description']}")
                if schema.get('columns'):
                    parts.append(f"Columns: {', '.join(schema['columns'])}")

        # Format business insights
        if context.business_insights:
            parts.append("\n## Business Context")
            for insight in context.business_insights:
                parts.append(f"- {insight['content']}")

        return "\n".join(parts)

    def get_few_shot_examples(
        self,
        query: str,
        n_examples: int = 3
    ) -> str:
        """
        Get formatted few-shot examples for prompt.
        
        Args:
            query: Natural language query
            n_examples: Number of examples
            
        Returns:
            Formatted examples string
        """
        examples = self.vector_store.search_similar_queries(
            query=query,
            top_k=n_examples
        )

        if not examples:
            return ""

        formatted = []
        for ex in examples:
            formatted.append(
                f"User: {ex['natural_query']}\n"
                f"SQL: {ex['sql_query']}\n"
            )

        return "\n".join(formatted)

    def get_schema_context(
        self,
        query: str,
        max_tables: int = 5
    ) -> str:
        """
        Get formatted schema context for prompt.
        
        Args:
            query: Natural language query
            max_tables: Maximum tables to include
            
        Returns:
            Formatted schema string
        """
        schemas = self.vector_store.search_relevant_schemas(
            query=query,
            top_k=max_tables
        )

        if not schemas:
            return ""

        parts = ["Database Schema:"]
        for schema in schemas:
            table_info = f"\nTable: {schema['table_name']}"
            if schema.get('columns'):
                table_info += f"\n  Columns: {', '.join(schema['columns'])}"
            parts.append(table_info)

        return "\n".join(parts)

    def enhance_prompt(
        self,
        base_prompt: str,
        query: str,
        include_examples: bool = True,
        include_schemas: bool = True
    ) -> str:
        """
        Enhance a prompt with RAG context.
        
        Args:
            base_prompt: Original prompt template
            query: User query
            include_examples: Include few-shot examples
            include_schemas: Include schema info
            
        Returns:
            Enhanced prompt with context
        """
        context_parts = []

        if include_schemas:
            schema_context = self.get_schema_context(query)
            if schema_context:
                context_parts.append(schema_context)

        if include_examples:
            examples = self.get_few_shot_examples(query)
            if examples:
                context_parts.append(f"\nExamples:\n{examples}")

        if context_parts:
            context = "\n".join(context_parts)
            return f"{base_prompt}\n\n{context}\n\nUser Query: {query}"
        else:
            return f"{base_prompt}\n\nUser Query: {query}"
