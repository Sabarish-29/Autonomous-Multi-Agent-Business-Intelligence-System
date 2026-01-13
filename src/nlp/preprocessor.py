"""
Autonomous Multi-Agent Business Intelligence System - Text Preprocessor

Text preprocessing utilities for NLP pipeline.
Handles cleaning, normalization, and tokenization.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreprocessedQuery:
    """Preprocessed query representation."""
    original: str
    cleaned: str
    normalized: str
    tokens: List[str]
    metadata: Dict[str, Any]


class TextPreprocessor:
    """
    Text preprocessing for BI queries.
    
    Features:
    - Text cleaning and normalization
    - Abbreviation expansion
    - Number formatting
    - Query type detection
    """

    # Common BI abbreviations
    ABBREVIATIONS = {
        "ytd": "year to date",
        "mtd": "month to date",
        "qtd": "quarter to date",
        "yoy": "year over year",
        "mom": "month over month",
        "qoq": "quarter over quarter",
        "rev": "revenue",
        "qty": "quantity",
        "avg": "average",
        "num": "number",
        "pct": "percent",
        "vs": "versus",
        "dept": "department",
        "mgr": "manager",
        "emp": "employee",
        "cust": "customer",
        "prod": "product",
        "cat": "category",
        "subcat": "subcategory",
    }

    # Date format patterns
    DATE_PATTERNS = [
        (r"\d{4}-\d{2}-\d{2}", "ISO date"),
        (r"\d{2}/\d{2}/\d{4}", "US date"),
        (r"\d{2}-\d{2}-\d{4}", "EU date"),
        (r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}", "named date"),
        (r"q[1-4]\s*\d{4}", "quarter year"),
    ]

    def __init__(self, expand_abbreviations: bool = True):
        """
        Initialize preprocessor.
        
        Args:
            expand_abbreviations: Whether to expand abbreviations
        """
        self.expand_abbreviations = expand_abbreviations
        logger.info("Text preprocessor initialized")

    def preprocess(self, query: str) -> PreprocessedQuery:
        """
        Preprocess a query.
        
        Args:
            query: Raw query string
            
        Returns:
            PreprocessedQuery object
        """
        original = query
        metadata = {}

        # Clean
        cleaned = self._clean_text(query)

        # Normalize
        normalized = self._normalize_text(cleaned)

        # Expand abbreviations if enabled
        if self.expand_abbreviations:
            normalized = self._expand_abbreviations(normalized)

        # Tokenize
        tokens = self._tokenize(normalized)

        # Extract metadata
        metadata = self._extract_metadata(original)

        return PreprocessedQuery(
            original=original,
            cleaned=cleaned,
            normalized=normalized,
            tokens=tokens,
            metadata=metadata
        )

    def _clean_text(self, text: str) -> str:
        """Clean text by removing noise."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\?\!\-\/\$\%\']', '', text)
        text = text.strip()
        return text

    def _normalize_text(self, text: str) -> str:
        """Normalize text to standard form."""
        text = text.lower()
        text = re.sub(r'(\d),(\d)', r'\1\2', text)
        text = re.sub(r'\$\s*(\d)', r'\1 dollars', text)
        text = re.sub(r'(\d+)\s*%', r'\1 percent', text)
        return text

    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        words = text.split()
        expanded_words = []
        for word in words:
            clean_word = word.strip('.,!?')
            if clean_word in self.ABBREVIATIONS:
                expanded = self.ABBREVIATIONS[clean_word]
                if word != clean_word:
                    expanded = expanded + word[len(clean_word):]
                expanded_words.append(expanded)
            else:
                expanded_words.append(word)
        return ' '.join(expanded_words)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        tokens = text.split()
        tokens = [t for t in tokens if t.strip()]
        return tokens

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text."""
        metadata = {
            "length": len(text),
            "word_count": len(text.split()),
            "has_numbers": bool(re.search(r'\d', text)),
            "has_date": False,
            "has_question": text.strip().endswith('?'),
            "date_formats": [],
        }
        for pattern, name in self.DATE_PATTERNS:
            if re.search(pattern, text.lower()):
                metadata["has_date"] = True
                metadata["date_formats"].append(name)
        return metadata

    def detect_query_type(self, query: str) -> Dict[str, Any]:
        """Detect the type of query."""
        query_lower = query.lower()
        query_types = {
            "question": query.strip().endswith('?'),
            "command": any(query_lower.startswith(cmd) for cmd in [
                "show", "get", "find", "list", "display", "calculate"
            ]),
            "comparison": any(kw in query_lower for kw in [
                "compare", "vs", "versus", "difference", "between"
            ]),
            "trend": any(kw in query_lower for kw in [
                "trend", "over time", "growth", "change"
            ]),
            "ranking": any(kw in query_lower for kw in [
                "top", "bottom", "best", "worst", "highest", "lowest"
            ]),
        }
        if query_types["comparison"]:
            primary = "comparison"
        elif query_types["trend"]:
            primary = "trend"
        elif query_types["ranking"]:
            primary = "ranking"
        elif query_types["question"]:
            primary = "question"
        elif query_types["command"]:
            primary = "command"
        else:
            primary = "statement"
        return {"primary_type": primary, "types": query_types}

    def extract_time_expressions(self, text: str) -> List[Dict[str, Any]]:
        """Extract time-related expressions."""
        time_expressions = []
        text_lower = text.lower()
        patterns = [
            (r"last\s+(month|quarter|year|week|day)", "relative"),
            (r"this\s+(month|quarter|year|week|day)", "relative"),
            (r"past\s+(\d+)\s+(days?|weeks?|months?|years?)", "relative_offset"),
            (r"ytd|year\s+to\s+date", "ytd"),
            (r"mtd|month\s+to\s+date", "mtd"),
            (r"q[1-4](?:\s+\d{4})?", "quarter"),
        ]
        for pattern, expr_type in patterns:
            for match in re.finditer(pattern, text_lower):
                time_expressions.append({
                    "text": match.group(),
                    "type": expr_type,
                    "start": match.start(),
                    "end": match.end()
                })
        return time_expressions
