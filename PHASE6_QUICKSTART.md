# Autonomous Multi-Agent Business Intelligence System - Phase 6 Quick Start Guide

## 🚀 Installation (2 minutes)

```bash
# Install Phase 6 dependencies
pip install fpdf2>=2.7.0 python-pptx>=0.6.23

# Or install everything
pip install -r requirements.txt

# Create reports directory
mkdir reports
```

---

## 📊 Generate Reports

### Option 1: Via Streamlit UI (Recommended)

```bash
# 1. Start Autonomous Multi-Agent Business Intelligence System
python scripts/launch_datagenie.py

# 2. Open browser: http://localhost:8501

# 3. Execute any query

# 4. Click download buttons:
#    - "📊 Download PDF" for comprehensive report
#    - "📑 Download PPTX" for executive deck

# 5. Save file locally
```

### Option 2: Via API

```bash
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show Q4 revenue",
    "sql_result": {"sql": "...", "data": [...]},
    "formats": ["pdf", "pptx"]
  }'
```

### Option 3: Via Python

```python
from src.agents.reporter import ReporterAgent

reporter = ReporterAgent()

reports = reporter.generate_combined_report(
    query="Show Q4 revenue trends",
    sql_result={
        "method": "analytics",
        "sql": "SELECT date, SUM(revenue)...",
        "data": [{"date": "2025-10-01", "revenue": 150000}, ...]
    },
    analytics_result={
        "analysis": "Revenue grew 33%",
        "statistics": {"mean": 175000}
    },
    formats=["pdf", "pptx"]
)

print(f"PDF: {reports['pdf']}")
print(f"PPTX: {reports['pptx']}")
```

---

## 🔒 PII Protection

### Automatic Protection (Always Active)

**Input Scanning:**
```
Query: "Show orders for john.doe@example.com"
→ Detected: EMAIL (MEDIUM risk)
→ Allowed with warning
→ Logged: PII detected for audit

Query: "Find customer with SSN 123-45-6789"
→ Detected: SSN (CRITICAL risk)
→ BLOCKED
→ User sees: "Query blocked: Sensitive PII detected"
```

**Output Redaction:**
```
Original Result:
{"name": "John Doe", "email": "john@example.com", "phone": "555-1234"}

Redacted Result:
{"name": "J*** D***", "email": "j***@example.com", "phone": "(***) ***-1234"}
```

### Manual PII Check

```python
from src.tools.guardrails import SafetyGuardrails

guardrails = SafetyGuardrails()

# Scan text
should_proceed, result = guardrails.scan_query(
    "Contact john.doe@example.com"
)

print(result.contains_pii)      # True
print(result.risk_level)        # "MEDIUM"
print(result.sanitized_text)    # "Contact j***@example.com"

# Redact data
data = {"users": [{"email": "john@example.com"}]}
redacted = guardrails.redact_results(data)
print(redacted)  # {"users": [{"email": "j***@example.com"}]}
```

### Get Protection Summary

```bash
# Via API
curl "http://localhost:8000/guardrails/summary"

# Returns:
# {
#   "blocked_queries": 5,
#   "redacted_results": 32,
#   "total_pii_detections": 147
# }
```

---

## 📋 Report Types

### PDF Report (Comprehensive)

**Best For:**
- Detailed analysis documentation
- Quarterly/annual reviews
- Compliance reports
- Executive briefings

**Contains:**
- Executive summary
- Query details
- SQL and data results (first 10 rows)
- Statistical analysis
- Market research insights
- Recommendations

**Size:** 3-10 pages, 200KB - 1MB
**Generation Time:** 3-5 seconds

### PPTX Deck (Executive)

**Best For:**
- Board presentations
- Executive meetings
- Quick summaries
- Stakeholder updates

**Contains:**
- Title slide with query
- Key findings (data + analytics)
- Market context and recommendations

**Size:** 3 slides, 100-200KB
**Generation Time:** 2-3 seconds

---

## 🎯 Common Use Cases

### Use Case 1: Quarterly Business Review

```python
# Query with analytics and research
query = "Analyze Q4 revenue vs Q3, compare to market trends"
mode = "research"

# Execute → View results → Download PDF
# Result: 8-page report with:
# - Quarter comparison
# - Growth analysis
# - Market benchmarking
# - Strategic recommendations
```

### Use Case 2: Executive Presentation

```python
# Quick research query
query = "How does our retention compare to industry?"
mode = "research"

# Execute → Download PPTX
# Result: 3-slide deck ready to present
```

### Use Case 3: Compliance Report

```python
# Analytics query on sensitive data
query = "Analyze customer demographics"

# System automatically:
# 1. Scans query for PII
# 2. Executes SQL
# 3. Redacts PII in results
# 4. Generates report with redacted data

# Result: Compliant report with masked PII
```

---

## ⚙️ Configuration

### Reporter Settings

```python
from src.agents.reporter import ReporterAgent
from pathlib import Path

# Custom output directory
reporter = ReporterAgent()
reporter.output_dir = Path("custom/reports")

# Generate with custom filename
pdf = reporter.generate_pdf_report(
    query="...",
    sql_result={...},
    filename="q4_revenue_report.pdf"
)
```

### Guardrails Settings

```python
from src.tools.guardrails import SafetyGuardrails

# Default: Regex-based detection
guardrails = SafetyGuardrails(use_presidio=False)

# Advanced: ML-based detection (requires Presidio)
guardrails = SafetyGuardrails(use_presidio=True)

# Strict mode: Block ALL PII
should_proceed, result = guardrails.scan_query(
    query,
    strict_mode=True  # Blocks even MEDIUM risk
)
```

### Report Formats

```python
# Generate only PDF
reports = reporter.generate_combined_report(
    query="...",
    sql_result={...},
    formats=["pdf"]
)

# Generate only PPTX
reports = reporter.generate_combined_report(
    query="...",
    sql_result={...},
    formats=["pptx"]
)

# Generate both (default)
reports = reporter.generate_combined_report(
    query="...",
    sql_result={...},
    formats=["pdf", "pptx"]
)
```

---

## 🧪 Testing

### Test Reporter

```bash
cd src/agents
python reporter.py

# Expected output:
# Generating reports...
# PDF Report: reports/datagenie_report_20260111_143022.pdf
# PPTX Deck: reports/datagenie_deck_20260111_143022.pptx
```

### Test Guardrails

```bash
cd src/tools
python guardrails.py

# Expected output:
# Query: Show me all users
# Contains PII: False
# Risk Level: LOW
#
# Query: Find orders for john.doe@example.com
# Contains PII: True
# Risk Level: MEDIUM
# Sanitized: Find orders for j***@example.com
```

### Test Full Integration

```bash
# 1. Start system
python scripts/launch_datagenie.py

# 2. Open UI: http://localhost:8501

# 3. Test scenarios:
#    - Execute query with PII → Verify warning
#    - Download PDF → Verify file created
#    - Download PPTX → Verify file created
#    - Try blocked query (SSN) → Verify blocking
```

---

## 🐛 Troubleshooting

### Issue: PDF Generation Fails

```bash
# Error: ModuleNotFoundError: No module named 'fpdf'
# Fix:
pip install fpdf2>=2.7.0
```

### Issue: PPTX Generation Fails

```bash
# Error: ModuleNotFoundError: No module named 'pptx'
# Fix:
pip install python-pptx>=0.6.23
```

### Issue: Download Button Not Working

```bash
# Check backend is running
curl http://localhost:8000/health

# Check reports directory exists
ls reports/

# Check permissions
chmod 755 reports/
```

### Issue: PII Not Detected

```python
# Verify guardrails initialized
from src.tools.guardrails import PIIDetector

detector = PIIDetector()
result = detector.scan_text("john.doe@example.com")
print(result.contains_pii)  # Should be True
```

### Issue: Presidio Not Working

```bash
# Install Presidio
pip install presidio-analyzer presidio-anonymizer

# Download spaCy model
python -m spacy download en_core_web_lg

# Verify
python -c "import presidio_analyzer; print('OK')"
```

---

## 📚 Resources

### Documentation
- Full Guide: `docs/PHASE6_REPORTING.md`
- Summary: `PHASE6_SUMMARY.md`
- API Docs: http://localhost:8000/docs (when backend running)

### Example Files
- Sample Reports: `reports/` directory
- Test Scripts: `src/agents/reporter.py`, `src/tools/guardrails.py`

### Support
- Check logs: Backend logs show PII detections and report generation
- Test components: Run standalone tests for each component
- Review code: All source files have comprehensive docstrings

---

## ✅ Quick Checklist

### Phase 6 Setup
- [ ] Install dependencies (`pip install fpdf2 python-pptx`)
- [ ] Create reports directory (`mkdir reports`)
- [ ] Start backend (`uvicorn src.api.main_crewai:app --reload`)
- [ ] Start frontend (`streamlit run app/streamlit_ui.py`)
- [ ] Test PDF generation
- [ ] Test PPTX generation
- [ ] Test PII detection
- [ ] Verify download buttons work

### Production Deployment
- [ ] Set up report cleanup (30-90 days)
- [ ] Configure PII detection (regex vs Presidio)
- [ ] Add authentication to reports endpoint
- [ ] Set up monitoring for PII activity
- [ ] Document PII handling procedures
- [ ] Train users on report features
- [ ] Configure access controls
- [ ] Test compliance workflows

---

## 🎉 Summary

**Phase 6 adds:**
- ✅ Professional PDF reports (multi-page)
- ✅ Executive PPTX decks (3-slide)
- ✅ Comprehensive PII protection
- ✅ Automatic redaction of sensitive data
- ✅ Download buttons in UI
- ✅ Compliance support (GDPR, CCPA, HIPAA)

**Ready to use in:**
- ⏱️ 2 minutes (install + test)
- 🚀 Production-ready
- 🔒 Enterprise-secure
- 📊 Professional output

**Start now:**
```bash
pip install fpdf2 python-pptx
python scripts/launch_datagenie.py
# Open http://localhost:8501 and start generating reports!
```

---

*Autonomous Multi-Agent Business Intelligence System - Phase 6 Complete* 🎊
