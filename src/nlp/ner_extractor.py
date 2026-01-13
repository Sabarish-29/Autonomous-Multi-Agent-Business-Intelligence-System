"""
Autonomous Multi-Agent Business Intelligence System - Named Entity Recognition (NER) Extractor

Custom NER system using spaCy with business-specific entity patterns.
Target: 87% accuracy on BI-related entities.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Extracted entity representation."""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 0.85
    normalized: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NERExtractor:
    """
    Named Entity Recognition for Business Intelligence queries.
    
    Extracts:
    - METRIC: revenue, sales, profit, orders, etc.
    - TIME_PERIOD: last quarter, YTD, this year, etc.
    - DIMENSION: region, category, department, etc.
    - AGGREGATION: total, average, sum, count, etc.
    - COMPARISON: vs, compared to, versus, etc.
    - FILTER: top, bottom, where, with, etc.
    """

    # Custom entity labels for BI domain
    CUSTOM_LABELS = [
        "METRIC",
        "TIME_PERIOD", 
        "DIMENSION",
        "AGGREGATION",
        "COMPARISON",
        "FILTER",
        "RANKING",
    ]

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NER extractor.
        
        Args:
            model_name: spaCy model to load
        """
        self.model_name = model_name
        self.nlp = None
        self._load_model()
        self._add_custom_patterns()
        logger.info("NER Extractor initialized")

    def _load_model(self):
        """Load spaCy model."""
        try:
            import spacy
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Model {self.model_name} not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", self.model_name])
            import spacy
            self.nlp = spacy.load(self.model_name)

    def _add_custom_patterns(self):
        """Add business-specific entity patterns using EntityRuler."""
        from spacy.language import Language

        # Remove existing entity_ruler if present
        if "entity_ruler" in self.nlp.pipe_names:
            self.nlp.remove_pipe("entity_ruler")

        # Add new entity ruler before NER
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")

        patterns = self._get_patterns()
        ruler.add_patterns(patterns)
        logger.info(f"Added {len(patterns)} custom patterns to EntityRuler")

    def _get_patterns(self) -> List[Dict[str, Any]]:
        """Define custom entity patterns for BI domain."""
        patterns = []

        # -------------------------------------------------------------------------
        # METRIC patterns
        # -------------------------------------------------------------------------
        metrics = [
            "revenue", "sales", "profit", "margin", "cost", "expense",
            "income", "earnings", "orders", "quantity", "units",
            "customers", "users", "visitors", "conversions", "churn",
            "retention", "growth", "roi", "mrr", "arr", "ltv", "cac",
            "aov", "nps", "csat", "transactions", "bookings"
        ]
        for metric in metrics:
            patterns.append({"label": "METRIC", "pattern": metric})
            patterns.append({"label": "METRIC", "pattern": metric.capitalize()})

        # Compound metrics
        compound_metrics = [
            [{"LOWER": "net"}, {"LOWER": "revenue"}],
            [{"LOWER": "gross"}, {"LOWER": "profit"}],
            [{"LOWER": "operating"}, {"LOWER": "margin"}],
            [{"LOWER": "customer"}, {"LOWER": "count"}],
            [{"LOWER": "order"}, {"LOWER": "value"}],
            [{"LOWER": "average"}, {"LOWER": "revenue"}],
            [{"LOWER": "total"}, {"LOWER": "sales"}],
            [{"LOWER": "monthly"}, {"LOWER": "revenue"}],
            [{"LOWER": "annual"}, {"LOWER": "revenue"}],
        ]
        for pattern in compound_metrics:
            patterns.append({"label": "METRIC", "pattern": pattern})

        # -------------------------------------------------------------------------
        # TIME_PERIOD patterns
        # -------------------------------------------------------------------------
        time_periods = [
            [{"LOWER": "last"}, {"LOWER": "quarter"}],
            [{"LOWER": "this"}, {"LOWER": "quarter"}],
            [{"LOWER": "last"}, {"LOWER": "month"}],
            [{"LOWER": "this"}, {"LOWER": "month"}],
            [{"LOWER": "last"}, {"LOWER": "year"}],
            [{"LOWER": "this"}, {"LOWER": "year"}],
            [{"LOWER": "last"}, {"LOWER": "week"}],
            [{"LOWER": "this"}, {"LOWER": "week"}],
            [{"LOWER": "past"}, {"IS_DIGIT": True}, {"LOWER": {"IN": ["days", "weeks", "months", "years"]}}],
            [{"LOWER": "last"}, {"IS_DIGIT": True}, {"LOWER": {"IN": ["days", "weeks", "months", "years"]}}],
            [{"LOWER": "ytd"}],
            [{"LOWER": "year"}, {"LOWER": "to"}, {"LOWER": "date"}],
            [{"LOWER": "mtd"}],
            [{"LOWER": "month"}, {"LOWER": "to"}, {"LOWER": "date"}],
            [{"LOWER": "qtd"}],
            [{"LOWER": "q1"}], [{"LOWER": "q2"}], [{"LOWER": "q3"}], [{"LOWER": "q4"}],
            [{"TEXT": {"REGEX": "^(Q[1-4]|q[1-4])$"}}],
            [{"TEXT": {"REGEX": "^20[0-9]{2}$"}}],  # Years like 2023, 2024
        ]
        for pattern in time_periods:
            patterns.append({"label": "TIME_PERIOD", "pattern": pattern})

        # -------------------------------------------------------------------------
        # DIMENSION patterns
        # -------------------------------------------------------------------------
        dimensions = [
            "region", "country", "state", "city", "location",
            "category", "subcategory", "product", "brand", "sku",
            "department", "team", "segment", "channel", "source",
            "salesperson", "manager", "customer", "account"
        ]
        for dim in dimensions:
            patterns.append({"label": "DIMENSION", "pattern": dim})
            patterns.append({"label": "DIMENSION", "pattern": dim.capitalize()})

        # Compound dimensions
        compound_dims = [
            [{"LOWER": "product"}, {"LOWER": "category"}],
            [{"LOWER": "customer"}, {"LOWER": "segment"}],
            [{"LOWER": "sales"}, {"LOWER": "channel"}],
            [{"LOWER": "by"}, {"LOWER": {"IN": dimensions}}],
        ]
        for pattern in compound_dims:
            patterns.append({"label": "DIMENSION", "pattern": pattern})

        # -------------------------------------------------------------------------
        # AGGREGATION patterns
        # -------------------------------------------------------------------------
        aggregations = [
            "total", "sum", "count", "average", "avg", "mean",
            "median", "min", "minimum", "max", "maximum",
            "distinct", "unique"
        ]
        for agg in aggregations:
            patterns.append({"label": "AGGREGATION", "pattern": agg})
            patterns.append({"label": "AGGREGATION", "pattern": agg.upper()})

        # -------------------------------------------------------------------------
        # COMPARISON patterns
        # -------------------------------------------------------------------------
        comparisons = [
            [{"LOWER": "vs"}],
            [{"LOWER": "versus"}],
            [{"LOWER": "compared"}, {"LOWER": "to"}],
            [{"LOWER": "compare"}],
            [{"LOWER": "difference"}, {"LOWER": "between"}],
            [{"LOWER": "growth"}, {"LOWER": "from"}],
            [{"LOWER": "change"}, {"LOWER": "from"}],
        ]
        for pattern in comparisons:
            patterns.append({"label": "COMPARISON", "pattern": pattern})

        # -------------------------------------------------------------------------
        # RANKING/FILTER patterns
        # -------------------------------------------------------------------------
        rankings = [
            [{"LOWER": "top"}, {"IS_DIGIT": True}],
            [{"LOWER": "bottom"}, {"IS_DIGIT": True}],
            [{"LOWER": "best"}, {"IS_DIGIT": True}],
            [{"LOWER": "worst"}, {"IS_DIGIT": True}],
            [{"LOWER": "highest"}],
            [{"LOWER": "lowest"}],
        ]
        for pattern in rankings:
            patterns.append({"label": "RANKING", "pattern": pattern})

        return patterns

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            List of extracted Entity objects
        """
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            confidence = self._calculate_confidence(ent)
            normalized = self._normalize_entity(ent.text, ent.label_)
            
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=confidence,
                normalized=normalized
            )
            entities.append(entity)

        # Deduplicate overlapping entities
        entities = self._deduplicate_entities(entities)

        logger.debug(f"Extracted {len(entities)} entities from: '{text[:50]}...'")
        return entities

    def extract_entities_dict(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities and return as dictionaries.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries
        """
        entities = self.extract_entities(text)
        return [
            {
                "text": e.text,
                "label": e.label,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
                "normalized": e.normalized
            }
            for e in entities
        ]

    def _calculate_confidence(self, ent) -> float:
        """
        Calculate confidence score for extracted entity.
        
        Args:
            ent: spaCy entity span
            
        Returns:
            Confidence score (0-1)
        """
        base_confidence = 0.85

        # Boost for custom patterns (EntityRuler matches)
        if ent.label_ in self.CUSTOM_LABELS:
            base_confidence = 0.92

        # Boost for exact matches
        if ent.text.lower() in ["revenue", "sales", "profit", "orders", "customers"]:
            base_confidence = 0.95

        # Slight penalty for very short entities
        if len(ent.text) < 3:
            base_confidence -= 0.05

        return min(max(base_confidence, 0.0), 1.0)

    def _normalize_entity(self, text: str, label: str) -> Optional[str]:
        """
        Normalize entity text to standard form.
        
        Args:
            text: Entity text
            label: Entity label
            
        Returns:
            Normalized text or None
        """
        text_lower = text.lower().strip()

        # Normalize time periods
        if label == "TIME_PERIOD":
            normalizations = {
                "ytd": "year_to_date",
                "mtd": "month_to_date",
                "qtd": "quarter_to_date",
                "q1": "quarter_1",
                "q2": "quarter_2",
                "q3": "quarter_3",
                "q4": "quarter_4",
            }
            return normalizations.get(text_lower, text_lower.replace(" ", "_"))

        # Normalize aggregations
        if label == "AGGREGATION":
            normalizations = {
                "avg": "average",
                "mean": "average",
                "min": "minimum",
                "max": "maximum",
            }
            return normalizations.get(text_lower, text_lower)

        return text_lower

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Remove overlapping entities, keeping higher confidence ones.
        
        Args:
            entities: List of entities
            
        Returns:
            Deduplicated list
        """
        if not entities:
            return []

        # Sort by start position, then by confidence (descending)
        sorted_entities = sorted(
            entities,
            key=lambda e: (e.start, -e.confidence)
        )

        result = []
        last_end = -1

        for entity in sorted_entities:
            if entity.start >= last_end:
                result.append(entity)
                last_end = entity.end

        return result

    def map_to_sql_components(self, entities: List[Entity]) -> Dict[str, Any]:
        """
        Map extracted entities to SQL query components.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dict with SQL components (columns, filters, groupby, etc.)
        """
        sql_mapping = {
            "select_columns": [],
            "aggregations": [],
            "group_by": [],
            "filters": [],
            "order_by": [],
            "time_filter": None,
            "limit": None,
        }

        for entity in entities:
            label = entity.label
            text = entity.normalized or entity.text.lower()

            if label == "METRIC":
                sql_mapping["select_columns"].append(text)
                # Add aggregation for metrics
                sql_mapping["aggregations"].append(f"SUM({text})")

            elif label == "DIMENSION":
                sql_mapping["group_by"].append(text)
                sql_mapping["select_columns"].append(text)

            elif label == "TIME_PERIOD":
                sql_mapping["time_filter"] = self._parse_time_period(text)

            elif label == "AGGREGATION":
                sql_mapping["aggregations"].append(text.upper())

            elif label == "RANKING":
                # Extract number from ranking (e.g., "top 10" -> 10)
                import re
                numbers = re.findall(r'\d+', entity.text)
                if numbers:
                    sql_mapping["limit"] = int(numbers[0])
                    if "bottom" in entity.text.lower() or "worst" in entity.text.lower():
                        sql_mapping["order_by"].append(("ASC", None))
                    else:
                        sql_mapping["order_by"].append(("DESC", None))

        return sql_mapping

    def _parse_time_period(self, text: str) -> Dict[str, Any]:
        """
        Parse time period text into filter parameters.
        
        Args:
            text: Normalized time period text
            
        Returns:
            Dict with time filter specification
        """
        text_lower = text.lower().replace("_", " ")

        if "last quarter" in text_lower:
            return {"type": "relative", "unit": "quarter", "offset": -1}
        elif "this quarter" in text_lower:
            return {"type": "relative", "unit": "quarter", "offset": 0}
        elif "last month" in text_lower:
            return {"type": "relative", "unit": "month", "offset": -1}
        elif "this month" in text_lower:
            return {"type": "relative", "unit": "month", "offset": 0}
        elif "last year" in text_lower:
            return {"type": "relative", "unit": "year", "offset": -1}
        elif "this year" in text_lower or "year to date" in text_lower:
            return {"type": "ytd"}
        elif "month to date" in text_lower:
            return {"type": "mtd"}
        elif "quarter" in text_lower and any(c.isdigit() for c in text_lower):
            # Extract quarter number
            import re
            match = re.search(r'(\d)', text_lower)
            if match:
                return {"type": "quarter", "quarter": int(match.group(1))}

        return {"type": "custom", "text": text}

    def get_entity_stats(self, entities: List[Entity]) -> Dict[str, Any]:
        """
        Get statistics about extracted entities.
        
        Args:
            entities: List of entities
            
        Returns:
            Dict with entity statistics
        """
        label_counts = {}
        total_confidence = 0.0

        for entity in entities:
            label_counts[entity.label] = label_counts.get(entity.label, 0) + 1
            total_confidence += entity.confidence

        avg_confidence = total_confidence / len(entities) if entities else 0.0

        return {
            "total_entities": len(entities),
            "label_distribution": label_counts,
            "average_confidence": round(avg_confidence, 3),
            "labels_found": list(label_counts.keys())
        }
