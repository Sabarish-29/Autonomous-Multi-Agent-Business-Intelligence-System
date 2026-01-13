"""
Safety Sentinel - PII Guardrails for Autonomous Multi-Agent Business Intelligence System - Phase 6

This module provides comprehensive PII (Personally Identifiable Information) detection
and redaction capabilities to protect sensitive data.

Features:
- Input query scanning for PII before SQL generation
- Output data redaction/masking before displaying to users
- Support for multiple PII types: emails, credit cards, SSNs, phone numbers, etc.
- Configurable detection patterns and masking strategies
- Integration with Microsoft Presidio (optional) for advanced detection
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Optional: Microsoft Presidio for advanced PII detection
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logging.warning("Microsoft Presidio not available. Using regex-based PII detection only.")


class PIIType(Enum):
    """Types of PII that can be detected"""
    EMAIL = "EMAIL"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    PHONE = "PHONE"
    IP_ADDRESS = "IP_ADDRESS"
    PERSON_NAME = "PERSON_NAME"
    ADDRESS = "ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"


@dataclass
class PIIDetection:
    """Represents a detected PII instance"""
    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class ScanResult:
    """Results from PII scanning"""
    contains_pii: bool
    detections: List[PIIDetection]
    original_text: str
    sanitized_text: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class PIIDetector:
    """
    Advanced PII detection using regex patterns and optional Presidio integration
    """
    
    # Regex patterns for common PII types
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        PIIType.ACCOUNT_NUMBER: r'\b[0-9]{8,17}\b',
        PIIType.DATE_OF_BIRTH: r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'
    }
    
    def __init__(self, use_presidio: bool = False):
        """
        Initialize PII detector
        
        Args:
            use_presidio: Whether to use Microsoft Presidio (if available)
        """
        self.use_presidio = use_presidio and PRESIDIO_AVAILABLE
        
        if self.use_presidio:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logging.info("PIIDetector initialized with Microsoft Presidio")
        else:
            logging.info("PIIDetector initialized with regex-based detection")
    
    def scan_text(self, text: str, pii_types: Optional[List[PIIType]] = None) -> ScanResult:
        """
        Scan text for PII
        
        Args:
            text: Text to scan
            pii_types: Specific PII types to look for (default: all)
            
        Returns:
            ScanResult with detections and sanitized text
        """
        if not text:
            return ScanResult(
                contains_pii=False,
                detections=[],
                original_text=text,
                sanitized_text=text,
                risk_level="LOW"
            )
        
        if self.use_presidio:
            return self._scan_with_presidio(text, pii_types)
        else:
            return self._scan_with_regex(text, pii_types)
    
    def _scan_with_regex(self, text: str, pii_types: Optional[List[PIIType]] = None) -> ScanResult:
        """Scan text using regex patterns"""
        detections = []
        
        # Determine which patterns to use
        patterns_to_check = self.PATTERNS
        if pii_types:
            patterns_to_check = {k: v for k, v in self.PATTERNS.items() if k in pii_types}
        
        # Scan for each PII type
        for pii_type, pattern in patterns_to_check.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9  # High confidence for regex matches
                ))
        
        # Sort detections by position
        detections.sort(key=lambda x: x.start)
        
        # Generate sanitized text
        sanitized_text = self._redact_text(text, detections)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(detections)
        
        return ScanResult(
            contains_pii=len(detections) > 0,
            detections=detections,
            original_text=text,
            sanitized_text=sanitized_text,
            risk_level=risk_level
        )
    
    def _scan_with_presidio(self, text: str, pii_types: Optional[List[PIIType]] = None) -> ScanResult:
        """Scan text using Microsoft Presidio"""
        # Map our PIIType to Presidio entity types
        presidio_entities = [
            "EMAIL_ADDRESS", "CREDIT_CARD", "US_SSN", "PHONE_NUMBER",
            "IP_ADDRESS", "PERSON", "LOCATION", "DATE_TIME"
        ]
        
        # Analyze text
        results = self.analyzer.analyze(text=text, entities=presidio_entities, language='en')
        
        # Convert Presidio results to our format
        detections = []
        for result in results:
            pii_type = self._map_presidio_type(result.entity_type)
            if pii_type:
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    value=text[result.start:result.end],
                    start=result.start,
                    end=result.end,
                    confidence=result.score
                ))
        
        # Generate sanitized text
        sanitized_text = self._redact_text(text, detections)
        
        # Determine risk level
        risk_level = self._calculate_risk_level(detections)
        
        return ScanResult(
            contains_pii=len(detections) > 0,
            detections=detections,
            original_text=text,
            sanitized_text=sanitized_text,
            risk_level=risk_level
        )
    
    def _map_presidio_type(self, presidio_type: str) -> Optional[PIIType]:
        """Map Presidio entity type to our PIIType"""
        mapping = {
            "EMAIL_ADDRESS": PIIType.EMAIL,
            "CREDIT_CARD": PIIType.CREDIT_CARD,
            "US_SSN": PIIType.SSN,
            "PHONE_NUMBER": PIIType.PHONE,
            "IP_ADDRESS": PIIType.IP_ADDRESS,
            "PERSON": PIIType.PERSON_NAME,
            "LOCATION": PIIType.ADDRESS
        }
        return mapping.get(presidio_type)
    
    def _redact_text(self, text: str, detections: List[PIIDetection]) -> str:
        """Redact PII from text"""
        if not detections:
            return text
        
        # Build sanitized text by replacing PII
        sanitized = text
        offset = 0
        
        for detection in detections:
            # Generate replacement based on PII type
            replacement = self._generate_mask(detection)
            
            # Adjust positions based on previous replacements
            start = detection.start + offset
            end = detection.end + offset
            
            # Replace in text
            sanitized = sanitized[:start] + replacement + sanitized[end:]
            
            # Update offset
            offset += len(replacement) - (detection.end - detection.start)
        
        return sanitized
    
    def _generate_mask(self, detection: PIIDetection) -> str:
        """Generate appropriate mask for detected PII"""
        value = detection.value
        
        if detection.pii_type == PIIType.EMAIL:
            # Mask email: john.doe@example.com -> j***@example.com
            parts = value.split('@')
            if len(parts) == 2:
                username = parts[0]
                if len(username) > 2:
                    return f"{username[0]}***@{parts[1]}"
                else:
                    return f"***@{parts[1]}"
            return "***@***.com"
        
        elif detection.pii_type == PIIType.CREDIT_CARD:
            # Mask credit card: 1234-5678-9012-3456 -> ****-****-****-3456
            parts = value.replace(' ', '-').split('-')
            if len(parts) >= 4:
                return f"****-****-****-{parts[-1]}"
            return "****-****-****-****"
        
        elif detection.pii_type == PIIType.SSN:
            # Mask SSN: 123-45-6789 -> ***-**-6789
            parts = value.split('-')
            if len(parts) == 3:
                return f"***-**-{parts[-1]}"
            return "***-**-****"
        
        elif detection.pii_type == PIIType.PHONE:
            # Mask phone: (555) 123-4567 -> (***) ***-4567
            cleaned = re.sub(r'[^\d]', '', value)
            if len(cleaned) >= 4:
                return f"(***) ***-{cleaned[-4:]}"
            return "(***) ***-****"
        
        elif detection.pii_type == PIIType.PERSON_NAME:
            # Mask name: John Doe -> J*** D***
            parts = value.split()
            return ' '.join([f"{p[0]}***" if p else "***" for p in parts])
        
        elif detection.pii_type == PIIType.ACCOUNT_NUMBER:
            # Mask account: 12345678 -> ****5678
            if len(value) > 4:
                return f"****{value[-4:]}"
            return "****"
        
        else:
            # Default masking
            return "***REDACTED***"
    
    def _calculate_risk_level(self, detections: List[PIIDetection]) -> str:
        """Calculate risk level based on detections"""
        if not detections:
            return "LOW"
        
        # Count critical PII types
        critical_types = {PIIType.SSN, PIIType.CREDIT_CARD, PIIType.ACCOUNT_NUMBER}
        high_risk_types = {PIIType.EMAIL, PIIType.PHONE, PIIType.DATE_OF_BIRTH}
        
        critical_count = sum(1 for d in detections if d.pii_type in critical_types)
        high_risk_count = sum(1 for d in detections if d.pii_type in high_risk_types)
        
        if critical_count > 0:
            return "CRITICAL"
        elif high_risk_count >= 3:
            return "HIGH"
        elif high_risk_count > 0:
            return "MEDIUM"
        else:
            return "LOW"


class SafetyGuardrails:
    """
    Main guardrails class for Autonomous Multi-Agent Business Intelligence System PII protection
    """
    
    def __init__(self, use_presidio: bool = False):
        """
        Initialize safety guardrails
        
        Args:
            use_presidio: Whether to use Microsoft Presidio for advanced detection
        """
        self.detector = PIIDetector(use_presidio=use_presidio)
        self.blocked_queries = []
        self.redacted_results = []
    
    def scan_query(self, query: str, strict_mode: bool = False) -> Tuple[bool, ScanResult]:
        """
        Scan user query for PII before SQL generation
        
        Args:
            query: User's natural language query
            strict_mode: If True, block queries with any PII
            
        Returns:
            Tuple of (should_proceed, scan_result)
        """
        scan_result = self.detector.scan_text(query)
        
        # Determine if query should proceed
        should_proceed = True
        
        if strict_mode and scan_result.contains_pii:
            should_proceed = False
            self.blocked_queries.append({
                "query": query,
                "reason": "PII detected in strict mode",
                "detections": scan_result.detections
            })
        elif scan_result.risk_level == "CRITICAL":
            should_proceed = False
            self.blocked_queries.append({
                "query": query,
                "reason": "Critical PII detected",
                "detections": scan_result.detections
            })
        
        return should_proceed, scan_result
    
    def redact_results(self, data: Any) -> Any:
        """
        Redact PII from query results
        
        Args:
            data: Query results (can be dict, list, or primitive)
            
        Returns:
            Redacted data with PII masked
        """
        if data is None:
            return None
        
        if isinstance(data, dict):
            return {k: self.redact_results(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [self.redact_results(item) for item in data]
        
        elif isinstance(data, str):
            scan_result = self.detector.scan_text(data)
            if scan_result.contains_pii:
                self.redacted_results.append({
                    "original_length": len(data),
                    "detections": len(scan_result.detections),
                    "risk_level": scan_result.risk_level
                })
                return scan_result.sanitized_text
            return data
        
        else:
            # Return primitive types as-is
            return data
    
    def get_guardrails_summary(self) -> Dict[str, Any]:
        """Get summary of guardrails activity"""
        return {
            "blocked_queries": len(self.blocked_queries),
            "redacted_results": len(self.redacted_results),
            "total_pii_detections": sum(
                len(q.get("detections", [])) for q in self.blocked_queries
            ) + sum(
                r.get("detections", 0) for r in self.redacted_results
            )
        }
    
    def validate_sql_query(self, sql: str) -> Tuple[bool, str]:
        """
        Validate generated SQL for potential PII exposure
        
        Args:
            sql: Generated SQL query
            
        Returns:
            Tuple of (is_safe, reason)
        """
        sql_lower = sql.lower()
        
        # Check for SELECT * which could expose PII columns
        if re.search(r'\bselect\s+\*\s+from\b', sql_lower):
            # Check if selecting from sensitive tables
            sensitive_tables = ['users', 'customers', 'employees', 'accounts', 'personal_info']
            for table in sensitive_tables:
                if table in sql_lower:
                    return False, f"SELECT * from sensitive table '{table}' may expose PII"
        
        # Check for sensitive column names
        sensitive_columns = [
            'email', 'ssn', 'social_security', 'credit_card', 'phone',
            'address', 'date_of_birth', 'dob', 'password', 'account_number'
        ]
        
        for column in sensitive_columns:
            if re.search(rf'\b{column}\b', sql_lower):
                return True, f"Query selects potentially sensitive column '{column}' - will be redacted in output"
        
        return True, "SQL query appears safe"
    
    def create_pii_report(self) -> Dict[str, Any]:
        """Generate a report of PII detections and redactions"""
        return {
            "summary": self.get_guardrails_summary(),
            "blocked_queries": self.blocked_queries,
            "redacted_results": self.redacted_results,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on activity"""
        recommendations = []
        
        if len(self.blocked_queries) > 0:
            recommendations.append(
                "High number of blocked queries detected. Consider user training on PII handling."
            )
        
        if len(self.redacted_results) > 10:
            recommendations.append(
                "Frequent PII redaction in results. Review database schema and access controls."
            )
        
        if not recommendations:
            recommendations.append("PII protection is functioning normally.")
        
        return recommendations


# Convenience functions for quick usage
def scan_for_pii(text: str, use_presidio: bool = False) -> ScanResult:
    """Quick function to scan text for PII"""
    detector = PIIDetector(use_presidio=use_presidio)
    return detector.scan_text(text)


def redact_pii(text: str, use_presidio: bool = False) -> str:
    """Quick function to redact PII from text"""
    scan_result = scan_for_pii(text, use_presidio)
    return scan_result.sanitized_text


# Example usage and testing
if __name__ == "__main__":
    # Initialize guardrails
    guardrails = SafetyGuardrails(use_presidio=False)
    
    # Test query scanning
    test_queries = [
        "Show me all users",
        "Find orders for john.doe@example.com",
        "Get customer data where ssn = '123-45-6789'",
        "What's the revenue for last month?"
    ]
    
    print("=== Testing Query Scanning ===")
    for query in test_queries:
        should_proceed, scan_result = guardrails.scan_query(query)
        print(f"\nQuery: {query}")
        print(f"Should Proceed: {should_proceed}")
        print(f"Contains PII: {scan_result.contains_pii}")
        print(f"Risk Level: {scan_result.risk_level}")
        if scan_result.contains_pii:
            print(f"Sanitized: {scan_result.sanitized_text}")
            print(f"Detections: {[d.pii_type.value for d in scan_result.detections]}")
    
    # Test result redaction
    print("\n\n=== Testing Result Redaction ===")
    test_data = {
        "users": [
            {"name": "John Doe", "email": "john.doe@example.com", "phone": "555-123-4567"},
            {"name": "Jane Smith", "email": "jane.smith@example.com", "phone": "555-987-6543"}
        ]
    }
    
    redacted_data = guardrails.redact_results(test_data)
    print(f"Original: {test_data}")
    print(f"Redacted: {redacted_data}")
    
    # Generate summary
    print("\n\n=== Guardrails Summary ===")
    summary = guardrails.get_guardrails_summary()
    print(f"Blocked Queries: {summary['blocked_queries']}")
    print(f"Redacted Results: {summary['redacted_results']}")
    print(f"Total PII Detections: {summary['total_pii_detections']}")
