"""
Autonomous Multi-Agent Business Intelligence System - Intent Classifier

BERT-based intent classification for BI queries.
Classifies user intent to route to appropriate handlers.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Intent classification result."""
    intent: str
    confidence: float
    all_scores: Dict[str, float]
    secondary_intents: List[Tuple[str, float]]


class IntentClassifier:
    """
    BERT-based intent classifier for BI queries.
    
    Classifies into categories:
    - data_retrieval: "Show me sales data"
    - aggregation: "What's total revenue?"
    - comparison: "Compare Q1 vs Q2"
    - trend_analysis: "Show revenue trend"
    - filtering: "Sales for California"
    - ranking: "Top 10 products"
    - visualization: "Create a chart showing..."
    - executive_summary: "Summarize Q3 performance"
    """

    # Intent categories
    INTENTS = [
        "data_retrieval",
        "aggregation",
        "comparison",
        "trend_analysis",
        "filtering",
        "ranking",
        "visualization",
        "executive_summary",
    ]

    # Keywords for rule-based fallback
    INTENT_KEYWORDS = {
        "data_retrieval": ["show", "display", "list", "get", "retrieve", "find", "what are"],
        "aggregation": ["total", "sum", "count", "average", "how many", "how much"],
        "comparison": ["compare", "vs", "versus", "difference", "between"],
        "trend_analysis": ["trend", "over time", "growth", "change", "progression"],
        "filtering": ["where", "filter", "only", "for", "in", "with"],
        "ranking": ["top", "bottom", "best", "worst", "highest", "lowest", "rank"],
        "visualization": ["chart", "graph", "plot", "visualize", "diagram"],
        "executive_summary": ["summary", "summarize", "overview", "report", "brief"],
    }

    def __init__(self, use_transformers: bool = True):
        """
        Initialize intent classifier.
        
        Args:
            use_transformers: Whether to use BERT model (False for lightweight)
        """
        self.use_transformers = use_transformers
        self.model = None
        self.tokenizer = None
        self.device = "cpu"

        if use_transformers:
            self._initialize_bert()

        logger.info(f"Intent classifier initialized (transformers={use_transformers})")

    def _initialize_bert(self):
        """Initialize BERT model for classification."""
        try:
            import torch
            from transformers import (
                AutoTokenizer,
                AutoModelForSequenceClassification,
                pipeline
            )

            # Use lightweight DistilBERT for efficiency
            model_name = "distilbert-base-uncased"

            logger.info(f"Loading BERT model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Use zero-shot classification for flexibility
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )

            # Set device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"BERT classifier loaded on {self.device}")

        except ImportError as e:
            logger.warning(f"Transformers not available: {e}")
            self.use_transformers = False
        except Exception as e:
            logger.warning(f"Failed to load BERT model: {e}")
            self.use_transformers = False

    def classify(self, query: str) -> IntentResult:
        """
        Classify query intent.
        
        Args:
            query: User query text
            
        Returns:
            IntentResult with classification
        """
        if self.use_transformers and self.classifier:
            return self._classify_bert(query)
        else:
            return self._classify_rules(query)

    def _classify_bert(self, query: str) -> IntentResult:
        """
        Classify using BERT zero-shot classification.
        
        Args:
            query: User query
            
        Returns:
            IntentResult
        """
        try:
            # Prepare candidate labels with descriptions
            candidate_labels = [
                "retrieving or showing data",
                "calculating totals or aggregations",
                "comparing values or periods",
                "analyzing trends over time",
                "filtering data by criteria",
                "ranking or finding top/bottom items",
                "creating visualizations or charts",
                "generating executive summaries",
            ]

            result = self.classifier(
                query,
                candidate_labels,
                multi_label=True
            )

            # Map back to intent names
            label_to_intent = dict(zip(candidate_labels, self.INTENTS))

            scores = {}
            for label, score in zip(result["labels"], result["scores"]):
                intent = label_to_intent.get(label, "data_retrieval")
                scores[intent] = score

            # Get top intent
            top_intent = max(scores.items(), key=lambda x: x[1])

            # Get secondary intents
            secondary = sorted(
                [(k, v) for k, v in scores.items() if k != top_intent[0]],
                key=lambda x: x[1],
                reverse=True
            )[:2]

            return IntentResult(
                intent=top_intent[0],
                confidence=top_intent[1],
                all_scores=scores,
                secondary_intents=secondary
            )

        except Exception as e:
            logger.warning(f"BERT classification failed: {e}, falling back to rules")
            return self._classify_rules(query)

    def _classify_rules(self, query: str) -> IntentResult:
        """
        Classify using keyword-based rules (fallback).
        
        Args:
            query: User query
            
        Returns:
            IntentResult
        """
        query_lower = query.lower()
        scores = {intent: 0.0 for intent in self.INTENTS}

        # Score each intent based on keyword matches
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent] += 0.3

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            # Default to data_retrieval
            scores["data_retrieval"] = 1.0

        # Apply softmax-like transformation for smoother distribution
        scores = self._softmax_scores(scores)

        # Get top intent
        top_intent = max(scores.items(), key=lambda x: x[1])

        # Get secondary intents
        secondary = sorted(
            [(k, v) for k, v in scores.items() if k != top_intent[0]],
            key=lambda x: x[1],
            reverse=True
        )[:2]

        return IntentResult(
            intent=top_intent[0],
            confidence=top_intent[1],
            all_scores=scores,
            secondary_intents=secondary
        )

    def _softmax_scores(self, scores: Dict[str, float], temperature: float = 2.0) -> Dict[str, float]:
        """
        Apply softmax to scores for smoother distribution.
        
        Args:
            scores: Raw scores
            temperature: Softmax temperature
            
        Returns:
            Normalized scores
        """
        values = np.array(list(scores.values()))
        exp_values = np.exp(values / temperature)
        softmax_values = exp_values / exp_values.sum()
        
        return dict(zip(scores.keys(), softmax_values.tolist()))

    def classify_dict(self, query: str) -> Dict[str, Any]:
        """
        Classify and return as dictionary.
        
        Args:
            query: User query
            
        Returns:
            Dict with classification results
        """
        result = self.classify(query)
        return {
            "intent": result.intent,
            "confidence": result.confidence,
            "all_scores": result.all_scores,
            "secondary_intents": [
                {"intent": i, "confidence": c}
                for i, c in result.secondary_intents
            ]
        }

    def classify_batch(self, queries: List[str]) -> List[IntentResult]:
        """
        Classify multiple queries.
        
        Args:
            queries: List of queries
            
        Returns:
            List of IntentResults
        """
        return [self.classify(query) for query in queries]

    def get_intent_description(self, intent: str) -> str:
        """
        Get human-readable description of intent.
        
        Args:
            intent: Intent name
            
        Returns:
            Description string
        """
        descriptions = {
            "data_retrieval": "Retrieve and display data from the database",
            "aggregation": "Calculate totals, sums, counts, or averages",
            "comparison": "Compare values across different dimensions or periods",
            "trend_analysis": "Analyze how metrics change over time",
            "filtering": "Filter data by specific criteria",
            "ranking": "Find top or bottom items by a metric",
            "visualization": "Create charts or visual representations",
            "executive_summary": "Generate a summary or overview report",
        }
        return descriptions.get(intent, "Unknown intent")

    def get_sql_hints(self, intent: str) -> Dict[str, Any]:
        """
        Get SQL generation hints based on intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            Dict with SQL hints
        """
        hints = {
            "data_retrieval": {
                "clauses": ["SELECT", "FROM"],
                "aggregations": False,
                "group_by": False,
            },
            "aggregation": {
                "clauses": ["SELECT", "FROM", "GROUP BY"],
                "aggregations": True,
                "functions": ["SUM", "COUNT", "AVG", "MIN", "MAX"],
            },
            "comparison": {
                "clauses": ["SELECT", "FROM", "GROUP BY", "HAVING"],
                "aggregations": True,
                "joins": True,
            },
            "trend_analysis": {
                "clauses": ["SELECT", "FROM", "GROUP BY", "ORDER BY"],
                "aggregations": True,
                "time_grouping": True,
            },
            "filtering": {
                "clauses": ["SELECT", "FROM", "WHERE"],
                "aggregations": False,
                "where_clause": True,
            },
            "ranking": {
                "clauses": ["SELECT", "FROM", "ORDER BY", "LIMIT"],
                "aggregations": True,
                "limit": True,
            },
            "visualization": {
                "clauses": ["SELECT", "FROM", "GROUP BY", "ORDER BY"],
                "aggregations": True,
                "chart_type": True,
            },
            "executive_summary": {
                "clauses": ["SELECT", "FROM", "GROUP BY"],
                "aggregations": True,
                "multiple_queries": True,
            },
        }
        return hints.get(intent, hints["data_retrieval"])
