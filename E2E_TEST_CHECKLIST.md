# E2E Test Execution Checklist

Use this checklist before running the E2E Master Test Suite to ensure everything is properly configured.

---

## ✅ Pre-Execution Checklist

### 1. Environment Setup

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated (if using venv/conda)
- [ ] Current directory is project root (`autonomous-multi-agent-bi-system/`)

### 2. Dependencies Installed

```bash
# Test Framework
pip install pytest pytest-asyncio httpx websockets

# Phase 1-6 Dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pytest, httpx, websockets; print('✅ Test dependencies OK')"
```

- [ ] pytest installed
- [ ] pytest-asyncio installed
- [ ] httpx installed
- [ ] websockets installed
- [ ] All requirements.txt packages installed

### 3. Environment Variables Configured

Create/verify `.env` file:

```env
# Required
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...

# Optional
TAVILY_API_KEY=tvly-...
SQLALCHEMY_DB_URL=sqlite:///data/sample/sample.db
```

- [ ] `.env` file exists in project root
- [ ] GROQ_API_KEY set
- [ ] OPENAI_API_KEY set
- [ ] TAVILY_API_KEY set (optional)
- [ ] Database URL configured

### 4. Database & Sample Data

```bash
# Ensure sample database exists
python scripts/create_sample_data.py
```

- [ ] `data/sample/sample.db` exists
- [ ] Sample data populated

### 5. Directory Structure

Verify these directories exist:
```
autonomous-multi-agent-bi-system/
├── tests/
│   ├── e2e_master_test.py      ← Main test file
│   ├── E2E_QUICK_REFERENCE.md
│   └── __init__.py
├── exports/                     ← Will be created by tests
├── reports/                     ← Will be created by tests
└── src/
    ├── api/
    │   └── main_crewai.py
    ├── agents/
    └── tools/
```

- [ ] `tests/e2e_master_test.py` exists
- [ ] `src/api/main_crewai.py` exists
- [ ] All agent files present in `src/agents/`

### 6. Port Availability

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

- [ ] Port 8000 is available (not in use)
- [ ] If blocked, kill process or change port in test file

---

## 🚀 Execution Steps

### Step 1: Run Health Check Test First

```bash
pytest tests/e2e_master_test.py::TestSystemHealth::test_health_check_all_components -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestSystemHealth::test_health_check_all_components PASSED [100%]
```

- [ ] Health check test PASSED
- [ ] All components show as initialized
- [ ] No import errors

### Step 2: Run Security Tests

```bash
pytest tests/e2e_master_test.py::TestSecuritySandbox -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestSecuritySandbox::test_sandbox_blocks_malicious_code PASSED
tests/e2e_master_test.py::TestSecuritySandbox::test_sandbox_blocks_file_access PASSED
```

- [ ] Malicious code blocked
- [ ] File access blocked
- [ ] No security vulnerabilities

### Step 3: Run Phase 1-2 Tests (Core Logic)

```bash
pytest tests/e2e_master_test.py::TestPhase1And2Logic -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestPhase1And2Logic::test_pii_guardrail_masks_email PASSED
tests/e2e_master_test.py::TestPhase1And2Logic::test_librarian_retrieves_schemas PASSED
tests/e2e_master_test.py::TestPhase1And2Logic::test_self_healing_loop_completes PASSED
```

- [ ] PII detection working
- [ ] Librarian retrieves schemas
- [ ] Self-healing loop completes

### Step 4: Run Phase 3-4 Tests (Analytics & Research)

```bash
pytest tests/e2e_master_test.py::TestPhase3And4Analytics -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestPhase3And4Analytics::test_scientist_generates_plotly_chart PASSED
tests/e2e_master_test.py::TestPhase3And4Analytics::test_researcher_provides_external_context PASSED
```

- [ ] Plotly charts generated
- [ ] Research data fetched (or warning if API key missing)

### Step 5: Run Phase 5-6 Tests (Reporting)

```bash
pytest tests/e2e_master_test.py::TestPhase5And6Reporting -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestPhase5And6Reporting::test_pdf_report_generation PASSED
tests/e2e_master_test.py::TestPhase5And6Reporting::test_pptx_report_generation PASSED
```

- [ ] PDF report generated
- [ ] PPTX deck generated
- [ ] Files saved to `exports/` directory

### Step 6: Run Monitoring Tests

```bash
pytest tests/e2e_master_test.py::TestPhase4Monitoring -v
```

**Expected Output:**
```
tests/e2e_master_test.py::TestPhase4Monitoring::test_anomaly_sentry_triggers_alert PASSED
tests/e2e_master_test.py::TestPhase4Monitoring::test_websocket_alert_broadcast PASSED
```

- [ ] Anomaly detection working
- [ ] WebSocket connections established

### Step 7: Run Full Test Suite

```bash
pytest tests/e2e_master_test.py -v
```

**Expected Output:**
```
============================== 12 passed in ~60s ==============================
```

- [ ] All 12 tests PASSED
- [ ] No failures or errors
- [ ] Total time < 90 seconds

---

## 🔍 Post-Execution Verification

### 1. Check Test Artifacts

```bash
# Windows
dir exports\
dir reports\

# Linux/Mac
ls -lh exports/
ls -lh reports/
```

**Expected Files:**
- [ ] `exports/test_report.pdf` (>1KB)
- [ ] `exports/test_presentation.pptx` (>5KB)

### 2. Verify PDF Content

Open `exports/test_report.pdf`:
- [ ] Cover page visible
- [ ] Multiple pages (5-8 pages)
- [ ] Tables formatted properly
- [ ] SQL queries visible

### 3. Verify PPTX Content

Open `exports/test_presentation.pptx`:
- [ ] 3 slides present
- [ ] Slide 1: Overview
- [ ] Slide 2: Key Findings
- [ ] Slide 3: Market Context

### 4. Review Test Logs

Check console output for:
- [ ] No ERROR level messages
- [ ] All ✅ PASS indicators present
- [ ] Component initialization successful
- [ ] No unhandled exceptions

---

## ❌ Troubleshooting Checklist

If tests fail, verify:

### Server Issues
- [ ] Port 8000 not blocked by another process
- [ ] No firewall blocking localhost:8000
- [ ] Sufficient memory (>2GB available)
- [ ] FastAPI starts without errors

### Dependency Issues
- [ ] All packages in requirements.txt installed
- [ ] No version conflicts in pip
- [ ] Python 3.11+ (check: `python --version`)
- [ ] Virtual environment activated

### API Key Issues
- [ ] GROQ_API_KEY valid and not expired
- [ ] OPENAI_API_KEY valid and not expired
- [ ] Keys have sufficient credits/quota
- [ ] .env file in correct location

### Database Issues
- [ ] SQLite database file exists
- [ ] Database has sample data
- [ ] No file permission issues
- [ ] Database not corrupted

### Import Errors
- [ ] All src/ modules accessible
- [ ] PYTHONPATH includes project root
- [ ] __init__.py files present
- [ ] No circular imports

---

## 📊 Test Result Matrix

| Test | Expected Time | Status | Notes |
|------|--------------|--------|-------|
| Health Check | 2s | ☐ | Critical - must pass |
| PII Guardrail | 3s | ☐ | May warn if disabled |
| Librarian | 5s | ☐ | Requires embeddings |
| Self-Healing | 8s | ☐ | May take 2-3 attempts |
| Plotly Charts | 6s | ☐ | Optional feature |
| Research | 10s | ☐ | Requires Tavily API key |
| PDF Report | 4s | ☐ | Requires fpdf2 |
| PPTX Report | 3s | ☐ | Requires python-pptx |
| Sandbox Code | 1s | ☐ | Critical - security |
| Sandbox File | 1s | ☐ | Critical - security |
| Anomaly Alert | 3s | ☐ | May warn if no data |
| WebSocket | 2s | ☐ | May timeout if idle |

**Total Expected Time:** 48-65 seconds

---

## 🎯 Success Criteria

### Minimum Requirements (Critical)
- [ ] Server starts successfully
- [ ] Health check passes
- [ ] Security tests pass (sandbox blocking)
- [ ] At least 8/12 tests pass

### Full Success (Optimal)
- [ ] All 12 tests pass
- [ ] No warnings or errors
- [ ] Reports generated
- [ ] Execution time < 90s

### Acceptable Warnings (Non-Critical)
- ⚠️ PII not detected (if disabled)
- ⚠️ Research data missing (if no API key)
- ⚠️ Visualization not found (if optional)
- ⚠️ WebSocket timeout (if no alerts)

---

## 🔄 Rerun Strategy

If tests fail, follow this order:

1. **Check logs** for specific error message
2. **Run individual test** that failed:
   ```bash
   pytest tests/e2e_master_test.py::TestClass::test_name -v -s
   ```
3. **Verify dependencies** for that specific phase
4. **Check API keys** if research/LLM test fails
5. **Restart server** if timeout errors occur
6. **Clear cache** if import errors persist:
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```
7. **Rerun full suite** after fixes

---

## 📝 Test Run Log Template

```
Test Run: [Date/Time]
Environment: [OS] / Python [Version]
Executed By: [Name]

Pre-Execution Checklist: [✅/❌]
- Dependencies: [✅/❌]
- Environment Variables: [✅/❌]
- Database: [✅/❌]
- Port Available: [✅/❌]

Test Results:
- Total Tests: 12
- Passed: [X]
- Failed: [X]
- Warnings: [X]
- Execution Time: [X]s

Failed Tests (if any):
1. [Test Name]: [Error Message]
2. [Test Name]: [Error Message]

Artifacts Generated:
- PDF Report: [✅/❌] [File Size]
- PPTX Deck: [✅/❌] [File Size]

Overall Status: [PASS/FAIL]
Notes: [Additional observations]
```

---

## 🎓 Next Steps After Successful Run

1. **Review Artifacts**
   - Open PDF report in Adobe Reader
   - Open PPTX deck in PowerPoint
   - Verify content quality

2. **Run Performance Profiling** (Optional)
   ```bash
   pytest tests/e2e_master_test.py --durations=10
   ```

3. **Generate HTML Report** (Optional)
   ```bash
   pytest tests/e2e_master_test.py --html=report.html --self-contained-html
   ```

4. **Set up CI/CD**
   - Configure GitHub Actions
   - Add secrets for API keys
   - Enable automated testing

5. **Create Baseline**
   - Document current pass/fail state
   - Save artifacts as reference
   - Track performance metrics

---

**Last Updated:** January 11, 2026  
**Version:** 1.0  
**Maintainer:** Sabarish-29  

---

## ✅ Sign-Off

- [ ] All checklist items completed
- [ ] Test results documented
- [ ] Artifacts verified
- [ ] Ready for production deployment

**Tester:** ________________  
**Date:** ________________  
**Signature:** ________________
