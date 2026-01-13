# Phase 6: Professional Reporting & Safety Guardrails

## Overview

Phase 6 completes Autonomous Multi-Agent Business Intelligence System with enterprise-grade reporting capabilities and comprehensive PII protection. This phase adds:

1. **Automated Reporter Agent**: Generates professional PDF reports and PowerPoint presentations
2. **Safety Sentinel (Guardrails)**: Detects and redacts PII in queries and results
3. **Download Integration**: Seamless report generation from Streamlit UI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomous Multi-Agent Business Intelligence System Phase 6                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query → [Safety Scan] → CrewAI Agents → Results      │
│                     ↓                            ↓          │
│              PII Detection              [Output Redaction]  │
│                     ↓                            ↓          │
│              Block/Warn                   Masked Data       │
│                                                  ↓          │
│                                         Reporter Agent      │
│                                           ↙        ↘        │
│                                        PDF        PPTX      │
│                                         ↓          ↓        │
│                                   Download Buttons in UI    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Reporter Agent (`src/agents/reporter.py`)

The Reporter Agent generates professional reports from query results.

**Features:**
- **PDF Reports**: Multi-page reports with custom letterheads and formatting
- **PowerPoint Decks**: 3-slide executive presentations
- **Comprehensive Content**: Includes SQL, data results, analytics, and research
- **Professional Templates**: Autonomous Multi-Agent Business Intelligence System branding and styling

**PDF Report Structure:**
1. Executive Summary
2. Query Details (query, date, type)
3. Generated SQL Query
4. Query Results (table format, first 10 rows)
5. Statistical Analysis (if analytics used)
6. Market Research Insights (if research used)
7. Recommendations & Next Steps

**PowerPoint Deck Structure:**
1. **Slide 1 - Overview**: Title slide with query and date
2. **Slide 2 - Key Findings**: Data results and statistical insights
3. **Slide 3 - Market Context**: Internal performance vs. market trends with recommendations

**API Integration:**

```python
from src.agents.reporter import ReporterAgent

reporter = ReporterAgent()

# Generate PDF
pdf_path = reporter.generate_pdf_report(
    query="Show me Q4 revenue",
    sql_result={
        "sql": "SELECT...",
        "data": [...]
    },
    analytics_result={
        "analysis": "Revenue grew 33%...",
        "statistics": {"mean": 175000}
    },
    research_result={
        "internal_findings": "Our Q4 revenue...",
        "external_research": "Industry average...",
        "unified_insights": "We outperformed..."
    }
)

# Generate PowerPoint
pptx_path = reporter.generate_pptx_report(...)

# Generate both
reports = reporter.generate_combined_report(
    query="...",
    sql_result={...},
    formats=["pdf", "pptx"]
)
# Returns: {"pdf": "/path/to/report.pdf", "pptx": "/path/to/deck.pptx"}
```

**PDF Customization:**
- Custom header with Autonomous Multi-Agent Business Intelligence System branding
- Page numbers and timestamps in footer
- Color-coded sections (purple gradient theme)
- Tables with alternating row colors
- Key-value pairs with formatted layout

**PowerPoint Customization:**
- 10:7.5 aspect ratio (standard presentation size)
- Custom fonts and colors (Autonomous Multi-Agent Business Intelligence System purple: RGB 102, 126, 234)
- Bullet points with proper spacing
- Professional title and subtitle formatting

### 2. Safety Guardrails (`src/tools/guardrails.py`)

The Safety Sentinel provides comprehensive PII protection.

**Supported PII Types:**
- Email addresses
- Credit card numbers
- Social Security Numbers (SSNs)
- Phone numbers
- IP addresses
- Account numbers
- Person names (optional, with Presidio)
- Addresses (optional, with Presidio)
- Dates of birth

**Detection Methods:**

1. **Regex-based detection** (default, no dependencies):
   - High-performance pattern matching
   - Predefined patterns for common PII
   - 90% confidence for matches

2. **Microsoft Presidio** (optional, advanced):
   - ML-based entity recognition
   - Higher accuracy for names and addresses
   - Confidence scores for each detection
   - Install: `pip install presidio-analyzer presidio-anonymizer`

**Input Scanning:**

```python
from src.tools.guardrails import SafetyGuardrails

guardrails = SafetyGuardrails(use_presidio=False)

# Scan user query
should_proceed, scan_result = guardrails.scan_query(
    "Show orders for john.doe@example.com",
    strict_mode=False
)

print(should_proceed)  # True (email is medium risk)
print(scan_result.contains_pii)  # True
print(scan_result.risk_level)  # "MEDIUM"
print(scan_result.sanitized_text)  # "Show orders for j***@example.com"
```

**Risk Levels:**
- **LOW**: No PII detected
- **MEDIUM**: 1-2 high-risk PII types (email, phone)
- **HIGH**: 3+ high-risk PII types
- **CRITICAL**: Any critical PII (SSN, credit card, account number)

**Blocking Logic:**
- `strict_mode=False`: Only blocks CRITICAL risk queries
- `strict_mode=True`: Blocks any query with PII
- Non-blocking PII triggers warnings in UI

**Output Redaction:**

```python
# Redact PII from query results
data = {
    "users": [
        {"name": "John Doe", "email": "john@example.com"},
        {"name": "Jane Smith", "email": "jane@example.com"}
    ]
}

redacted = guardrails.redact_results(data)

# Result:
# {
#     "users": [
#         {"name": "J*** D***", "email": "j***@example.com"},
#         {"name": "J*** S***", "email": "j***@example.com"}
#     ]
# }
```

**Masking Strategies:**
- **Email**: `john.doe@example.com` → `j***@example.com`
- **Credit Card**: `1234-5678-9012-3456` → `****-****-****-3456`
- **SSN**: `123-45-6789` → `***-**-6789`
- **Phone**: `(555) 123-4567` → `(***) ***-4567`
- **Name**: `John Doe` → `J*** D***`
- **Account**: `12345678` → `****5678`

**SQL Validation:**

```python
is_safe, reason = guardrails.validate_sql_query(
    "SELECT * FROM users"
)

print(is_safe)  # False
print(reason)  # "SELECT * from sensitive table 'users' may expose PII"
```

Checks for:
- `SELECT *` from sensitive tables (users, customers, employees, accounts)
- Queries selecting sensitive columns (email, ssn, credit_card, phone, etc.)

### 3. CrewAI Manager Integration

**Query Scanning (Automatic):**

```python
# In generate_sql_hierarchical()
should_proceed, scan_result = self.guardrails.scan_query(user_query)

if not should_proceed:
    return {
        "error": "Query blocked: Sensitive PII detected",
        "risk_level": scan_result.risk_level,
        "detections": [d.pii_type.value for d in scan_result.detections]
    }
```

**Result Redaction (Automatic):**

```python
# In execute_sql()
result = self.sql_executor_tool._run(sql=sql, limit=limit)
redacted_data = self.guardrails.redact_results(result)
return redacted_data
```

**Report Generation:**

```python
# In download_report()
reports = dataops_manager.download_report(
    query="Show me Q4 revenue",
    sql_result={...},
    analytics_result={...},
    research_result={...},
    formats=["pdf", "pptx"]
)

print(reports["pdf"])   # "/path/to/report.pdf"
print(reports["pptx"])  # "/path/to/deck.pptx"
```

### 4. FastAPI Endpoints

**POST /reports/generate**

Generate professional reports from query results.

```bash
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me Q4 revenue trends",
    "sql_result": {
      "method": "analytics",
      "sql": "SELECT date, SUM(revenue)...",
      "data": [...]
    },
    "analytics_result": {
      "analysis": "Revenue shows 33% growth...",
      "statistics": {"mean": 175000}
    },
    "research_result": {
      "internal_findings": "Our Q4 revenue...",
      "external_research": "Industry averaged...",
      "unified_insights": "We outperformed by 8%"
    },
    "formats": ["pdf", "pptx"]
  }'
```

**Response:**
```json
{
  "pdf": "reports/datagenie_report_20260111_143022.pdf",
  "pptx": "reports/datagenie_deck_20260111_143022.pptx"
}
```

**GET /guardrails/summary**

Get PII protection statistics.

```bash
curl "http://localhost:8000/guardrails/summary"
```

**Response:**
```json
{
  "status": "active",
  "summary": {
    "blocked_queries": 2,
    "redacted_results": 15,
    "total_pii_detections": 47
  },
  "pii_protection": "enabled"
}
```

### 5. Streamlit UI Integration

**Download Buttons:**

Located in Query tab results section:

```
┌──────────────────────────────────────────┐
│ 📄 Professional Reports                  │
├──────────────────────────────────────────┤
│  [📊 Download PDF]  [📑 Download PPTX]   │
└──────────────────────────────────────────┘
```

**User Flow:**

1. Execute query (Standard/Analytics/Research mode)
2. View results on screen
3. Click "📊 Download PDF" or "📑 Download PPTX"
4. Report generates (progress spinner)
5. Download button appears: "💾 Save PDF Report" or "💾 Save PPTX Deck"
6. Click to save file locally

**PII Warnings:**

If PII detected in query or results:

```
⚠️ PII Protection Active: MEDIUM risk detected - results automatically redacted
```

If query blocked (CRITICAL risk):

```
❌ Error: Query blocked: Sensitive PII detected
⚠️ Security Alert: CRITICAL risk PII detected
Detected: SSN, CREDIT_CARD
```

**Code Implementation:**

```python
# In app/streamlit_ui.py

def download_report(result, query, formats):
    """Generate reports via backend API"""
    response = requests.post(
        f"{API_BASE_URL}/reports/generate",
        json={
            "query": query,
            "sql_result": {...},
            "analytics_result": {...},
            "research_result": {...},
            "formats": formats
        }
    )
    return response.json()

# Usage in UI
if st.button("📊 Download PDF"):
    with st.spinner("Generating PDF..."):
        report_result = download_report(result, query, ["pdf"])
        if report_result.get("pdf"):
            with open(report_result["pdf"], "rb") as f:
                st.download_button(
                    "💾 Save PDF Report",
                    f,
                    file_name="datagenie_report.pdf",
                    mime="application/pdf"
                )
```

## Installation

### Phase 6 Dependencies

```bash
# PDF generation
pip install fpdf2>=2.7.0

# PowerPoint generation
pip install python-pptx>=0.6.23

# Optional: Advanced PII detection with Microsoft Presidio
pip install presidio-analyzer presidio-anonymizer
# Note: Presidio requires additional setup (spaCy models)

# Or install all at once
pip install -r requirements.txt
```

### Presidio Setup (Optional)

If using advanced PII detection:

```bash
# Install Presidio
pip install presidio-analyzer presidio-anonymizer

# Download spaCy model
python -m spacy download en_core_web_lg

# Enable in guardrails
guardrails = SafetyGuardrails(use_presidio=True)
```

## Usage Examples

### Example 1: Generate PDF Report

**Query:** "Show me Q4 2025 revenue trends"

**Steps:**
1. Execute query in Analytics mode
2. View results and chart
3. Click "📊 Download PDF"
4. Wait for generation (3-5 seconds)
5. Click "💾 Save PDF Report"
6. File saved: `datagenie_report_20260111_143022.pdf`

**PDF Contents:**
- Executive Summary: "Revenue grew 33% in Q4..."
- Query Details: Date, type, parameters
- SQL Query: Full generated SQL
- Results Table: First 10 rows
- Statistical Analysis: Mean, growth rate, total
- Recommendations: 6 action items

### Example 2: Generate PowerPoint Deck

**Query:** "Is our 10% growth good compared to market?"

**Steps:**
1. Execute query in Research mode
2. View side-by-side comparison (Internal vs Market)
3. Click "📑 Download PPTX"
4. Wait for generation (2-3 seconds)
5. Click "💾 Save PPTX Deck"
6. File saved: `datagenie_deck_20260111_143022.pptx`

**PPTX Contents:**
- **Slide 1**: Title - "Autonomous Multi-Agent Business Intelligence System Executive Report"
- **Slide 2**: Key findings from SQL and analytics
- **Slide 3**: Market context and recommendations

### Example 3: PII Detection and Blocking

**Query:** "Show orders where customer_ssn = '123-45-6789'"

**Result:**
```
❌ Error: Query blocked: Sensitive PII detected
⚠️ Security Alert: CRITICAL risk PII detected
Detected: SSN

Please remove sensitive information from your query.
```

**Safe Alternative:** "Show orders for customer ID 1234"

### Example 4: Automatic PII Redaction

**Query:** "List customers with their contact info"

**Original Result:**
```json
[
  {"name": "John Doe", "email": "john.doe@example.com", "phone": "555-123-4567"},
  {"name": "Jane Smith", "email": "jane.smith@example.com", "phone": "555-987-6543"}
]
```

**Redacted Result (Automatic):**
```json
[
  {"name": "J*** D***", "email": "j***@example.com", "phone": "(***) ***-4567"},
  {"name": "J*** S***", "email": "j***@example.com", "phone": "(***) ***-6543"}
]
```

**UI Display:**
```
⚠️ PII Protection Active: MEDIUM risk detected - results automatically redacted
```

## Configuration

### Reporter Agent Settings

```python
# Default output directory
reporter = ReporterAgent()
# Reports saved to: ./reports/

# Custom directory
reporter.output_dir = Path("custom/reports")
```

### Guardrails Settings

```python
# Regex-based detection (default)
guardrails = SafetyGuardrails(use_presidio=False)

# Advanced ML-based detection
guardrails = SafetyGuardrails(use_presidio=True)

# Strict mode (block all PII)
should_proceed, result = guardrails.scan_query(query, strict_mode=True)
```

### PII Type Selection

```python
from src.tools.guardrails import PIIType

# Scan only specific PII types
scan_result = detector.scan_text(
    text="Contact: john@example.com, 555-1234",
    pii_types=[PIIType.EMAIL, PIIType.PHONE]
)
```

## Testing

### Test Reporter Agent

```bash
cd src/agents
python reporter.py
```

**Output:**
```
Generating reports...
PDF Report: reports/datagenie_report_20260111_143022.pdf
PPTX Deck: reports/datagenie_deck_20260111_143022.pptx
```

### Test Guardrails

```bash
cd src/tools
python guardrails.py
```

**Output:**
```
=== Testing Query Scanning ===
Query: Show me all users
Should Proceed: True
Contains PII: False
Risk Level: LOW

Query: Find orders for john.doe@example.com
Should Proceed: True
Contains PII: True
Risk Level: MEDIUM
Sanitized: Find orders for j***@example.com
Detections: ['EMAIL']

Query: Get customer data where ssn = '123-45-6789'
Should Proceed: False
Contains PII: True
Risk Level: CRITICAL
Sanitized: Get customer data where ssn = '***-**-6789'
Detections: ['SSN']
```

### Integration Test

```bash
# Start backend
python -m uvicorn src.api.main_crewai:app --reload

# In another terminal, test report generation
curl -X POST "http://localhost:8000/reports/generate" \
  -H "Content-Type: application/json" \
  -d @test_data/sample_report_request.json
```

## Best Practices

### 1. Report Generation

**Do:**
- Generate reports for important analyses (quarterly reviews, executive presentations)
- Use PDF for comprehensive documentation (10+ pages)
- Use PPTX for executive summaries (3 slides max)
- Include context (analytics + research) for richer reports

**Don't:**
- Generate reports for every simple query (performance overhead)
- Rely on reports for real-time monitoring (use Monitoring tab instead)
- Modify generated files directly (regenerate with updated data)

### 2. PII Protection

**Do:**
- Keep strict_mode=False for better UX (only blocks CRITICAL risk)
- Review redacted results to ensure necessary data is visible
- Train users on PII handling (avoid putting SSN/CC in queries)
- Use guardrails summary endpoint for compliance audits

**Don't:**
- Disable PII protection in production
- Use PII in test queries
- Share original (unredacted) results with unauthorized users
- Override blocking for CRITICAL risk queries

### 3. Performance

**Report Generation:**
- PDF: 3-5 seconds for typical report
- PPTX: 2-3 seconds for 3-slide deck
- Both formats: 5-8 seconds

**PII Scanning:**
- Regex mode: <10ms per query
- Presidio mode: 50-100ms per query
- Redaction: <50ms for typical result set (100 rows)

## Monitoring

### Guardrails Activity

```bash
# Get PII protection summary
curl "http://localhost:8000/guardrails/summary"
```

**Response:**
```json
{
  "status": "active",
  "summary": {
    "blocked_queries": 5,
    "redacted_results": 32,
    "total_pii_detections": 147
  },
  "pii_protection": "enabled"
}
```

### Report Generation Logs

Check backend logs for report activity:

```
INFO - Generating reports in formats: ['pdf', 'pptx']
INFO - Successfully generated reports: {'pdf': '...', 'pptx': '...'}
```

### PII Detection Logs

```
INFO - PII detected in query (non-blocking): MEDIUM
WARNING - Query blocked due to PII detection: CRITICAL
```

## Troubleshooting

### Issue 1: PDF Generation Fails

**Error:** `ModuleNotFoundError: No module named 'fpdf'`

**Solution:**
```bash
pip install fpdf2>=2.7.0
```

### Issue 2: PPTX Generation Fails

**Error:** `ModuleNotFoundError: No module named 'pptx'`

**Solution:**
```bash
pip install python-pptx>=0.6.23
```

### Issue 3: Presidio Not Working

**Error:** `OSError: [E050] Can't find model 'en_core_web_lg'`

**Solution:**
```bash
python -m spacy download en_core_web_lg
```

### Issue 4: Reports Not Downloadable

**Symptom:** "Download button not appearing"

**Checks:**
1. Backend running? `curl http://localhost:8000/health`
2. Reports directory exists? Check `./reports/` folder
3. File permissions? Ensure write access to `reports/` directory

**Solution:**
```bash
mkdir reports
chmod 755 reports
```

### Issue 5: PII Over-Redacting

**Symptom:** "Too much data masked, results unusable"

**Solution:**
- Adjust detection patterns in `guardrails.py`
- Use specific PII types instead of all types
- Consider using Presidio for more accurate detection

## Security Considerations

### 1. PII Handling

- **Never log unredacted PII**: All logs use sanitized text
- **Secure report storage**: Store reports in protected directory with restricted access
- **Audit trail**: Track all PII detections for compliance
- **Data retention**: Implement report deletion policy (30-90 days)

### 2. Report Access Control

```python
# Add authentication to report endpoint (recommended)
@app.post("/reports/generate")
async def generate_reports(
    request: ReportRequest,
    current_user: User = Depends(get_current_user)  # Add auth
):
    # Check user permissions
    if not current_user.can_generate_reports:
        raise HTTPException(403, "Insufficient permissions")
    
    # Generate reports...
```

### 3. File Cleanup

```python
# Implement automatic cleanup
import os
from datetime import datetime, timedelta

def cleanup_old_reports(days=30):
    """Delete reports older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    for file in Path("reports").glob("*"):
        if file.stat().st_mtime < cutoff.timestamp():
            file.unlink()
```

## Future Enhancements

### Phase 6.1: Advanced Reports
- [ ] Excel spreadsheet export with formulas
- [ ] Interactive HTML reports
- [ ] Email report delivery
- [ ] Scheduled report generation

### Phase 6.2: Enhanced PII
- [ ] Custom PII patterns per organization
- [ ] Differential privacy for aggregated data
- [ ] PII discovery scanner for existing databases
- [ ] GDPR/CCPA compliance reporting

### Phase 6.3: Report Templates
- [ ] Customizable report templates
- [ ] Brand logo and color scheme configuration
- [ ] Multi-language support
- [ ] White-label reporting

## Summary

Phase 6 completes Autonomous Multi-Agent Business Intelligence System with:

✅ **Professional Reporting**: PDF and PPTX generation with comprehensive content
✅ **PII Protection**: Automatic detection and redaction of sensitive data
✅ **Seamless Integration**: Download buttons in Streamlit UI
✅ **Enterprise-Ready**: Security, compliance, and audit capabilities

**Key Files:**
- `src/agents/reporter.py` (800 lines) - Report generation
- `src/tools/guardrails.py` (600 lines) - PII protection
- `src/agents/crewai_manager.py` (updated) - Integration
- `src/api/main_crewai.py` (updated) - API endpoints
- `app/streamlit_ui.py` (updated) - Download UI

**Next Steps:**
1. Install Phase 6 dependencies: `pip install fpdf2 python-pptx`
2. Test report generation: Execute query → Click download buttons
3. Verify PII protection: Try queries with email/phone → See redaction
4. Review reports: Check `reports/` directory for generated files

Autonomous Multi-Agent Business Intelligence System is now production-ready with complete AI-powered SQL generation, proactive monitoring, external research, and enterprise reporting! 🎉
