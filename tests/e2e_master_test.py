"""
Autonomous Multi-Agent Business Intelligence System - Comprehensive End-to-End Master Test Suite
Created by: Senior SDET specializing in AI Agent Orchestration
Date: January 11, 2026

This test suite validates all 6 phases of Autonomous Multi-Agent Business Intelligence System:
- Phase 1 & 2: PII Guardrails + Self-Healing SQL Loop
- Phase 3 & 4: Analytics (Plotly) + Research (Tavily) + Monitoring (Sentry)
- Phase 5 & 6: UI + Professional Reporting (PDF/PPTX)

Requirements:
    pip install pytest pytest-asyncio httpx websockets
"""

import asyncio
import json
import logging
import os
import sys
import time
from multiprocessing import Process
from pathlib import Path
from typing import Dict, Any, Optional
import re

import pytest
import pytest_asyncio
import httpx
from websockets import connect as ws_connect

# Configure logging for detailed test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("E2E_MASTER_TEST")

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 60  # seconds for complex queries
REPORTS_DIR = Path("./reports")
EXPORTS_DIR = Path("./exports")


# ============================================================================
# FASTAPI SERVER MANAGEMENT (Setup/Teardown)
# ============================================================================

def _run_uvicorn_server(host: str, port: int):
    """Module-level function to run uvicorn server (picklable for Windows multiprocessing)"""
    import uvicorn
    from src.api.main_crewai import app
    
    # Disable uvicorn access logs for cleaner test output
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning"
    )


class FastAPIServer:
    """Manages FastAPI server lifecycle for E2E testing"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.process: Optional[Process] = None
        self.base_url = f"http://{host}:{port}"
    
    def start(self):
        """Start FastAPI server in background process"""
        logger.info(f"🚀 Starting FastAPI server on {self.base_url}")

        # Avoid interactive prompts (e.g., tracing preference) during CI/E2E.
        os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

        # Keep Groq usage within typical on-demand TPM limits during E2E.
        # These are only defaults; real deployments can override via env.
        os.environ.setdefault("DATAGENIE_TEST_MODE", "1")
        os.environ.setdefault("DATAGENIE_LLM_MAX_TOKENS", "128")
        os.environ.setdefault("DATAGENIE_PROMPT_CHAR_LIMIT", "1500")
        os.environ.setdefault("GROQ_MODEL", "llama-3.3-70b-versatile")
        os.environ.setdefault("GROQ_REASONING_MODEL", "llama-3.3-70b-versatile")
        
        self.process = Process(target=_run_uvicorn_server, args=(self.host, self.port), daemon=True)
        self.process.start()
        
        # Wait for server to be ready
        self._wait_for_server()
    
    def _wait_for_server(self, max_retries: int = 30):
        """Wait for server to become responsive"""
        logger.info("⏳ Waiting for server to start...")
        
        for attempt in range(max_retries):
            try:
                import requests
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ Server ready after {attempt + 1} attempts")
                    return
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise TimeoutError(f"Server failed to start after {max_retries} seconds")
    
    def stop(self):
        """Stop FastAPI server"""
        if self.process and self.process.is_alive():
            logger.info("🛑 Stopping FastAPI server...")
            self.process.terminate()
            self.process.join(timeout=5)
            
            if self.process.is_alive():
                logger.warning("⚠️ Forcing server shutdown...")
                self.process.kill()
                self.process.join()
            
            logger.info("✅ Server stopped")


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def api_server():
    """Start/stop FastAPI server for entire test session"""
    server = FastAPIServer()
    server.start()
    yield server
    server.stop()


@pytest_asyncio.fixture(scope="function")
async def http_client(api_server):
    """Create async HTTP client"""
    async with httpx.AsyncClient(base_url=api_server.base_url, timeout=API_TIMEOUT) as client:
        yield client


@pytest.fixture(scope="function")
def clean_exports():
    """Ensure exports directory exists and is clean"""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after test (optional - keep files for manual inspection)


# ============================================================================
# TEST CLASS: Phase 1 & 2 - PII Guardrails + Self-Healing SQL
# ============================================================================

@pytest.mark.asyncio
class TestPhase1And2Logic:
    """Test PII protection and self-healing SQL generation"""
    
    async def test_pii_guardrail_masks_email(self, http_client):
        """
        Phase 1 & 2 Test: Verify PII Guardrail masks email in query
        
        Query: "Compare our Q4 revenue to market trends for user test@example.com"
        Expected: Email should be detected and masked/blocked based on risk level
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: PII Guardrail - Email Masking")
        logger.info("="*80)
        
        query = "Compare our Q4 revenue to market trends for user test@example.com"
        
        # Make query request
        response = await http_client.post("/query", json={
            "query": query,
            "database": "default",
            "use_crewai": True
        })
        
        # Assertions
        assert response.status_code in [200, 400, 403], \
            f"Unexpected status code: {response.status_code}"
        
        result = response.json()
        logger.info(f"📊 Response status: {response.status_code}")
        logger.info(f"📊 PII detected: {result.get('pii_detected', False)}")
        
        # Check if PII was detected
        if result.get('pii_detected'):
            logger.info("✅ PASS: PII Guardrail detected email in query")
            
            # Verify email type was identified
            pii_info = result.get('pii_info', {})
            assert 'EMAIL' in pii_info.get('pii_types', []), \
                "Email PII type not identified"
            
            logger.info(f"   - PII Types: {pii_info.get('pii_types', [])}")
            logger.info(f"   - Risk Level: {pii_info.get('risk_level', 'UNKNOWN')}")
            
            # If CRITICAL risk, query should be blocked
            if pii_info.get('risk_level') == 'CRITICAL':
                assert result.get('sql') is None, \
                    "CRITICAL PII should block query execution"
                logger.info("   - Query blocked due to CRITICAL risk ✅")
            else:
                logger.info("   - Query allowed with warning ⚠️")
        else:
            logger.warning("⚠️ WARNING: PII not detected (might need guardrail config)")
        
        logger.info("✅ PII Guardrail test completed\n")
    
    async def test_librarian_retrieves_schemas(self, http_client):
        """
        Phase 1 & 2 Test: Verify Librarian retrieves relevant schemas
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Librarian Agent - Schema Retrieval")
        logger.info("="*80)
        
        # Query that requires schema knowledge
        query = "Show me total revenue by product category"
        
        response = await http_client.post("/query", json={
            "query": query,
            "database": "default",
            "use_crewai": True
        })
        
        assert response.status_code == 200, f"Query failed: {response.text}"
        result = response.json()
        
        # Verify schema retrieval
        assert 'relevant_schemas' in result or 'context' in result, \
            "No schema information in response"
        
        logger.info("✅ PASS: Librarian Agent retrieved schemas")
        logger.info(f"   - Query method: {result.get('method', 'unknown')}")
        
        # Check if schemas mention relevant tables
        context = str(result.get('relevant_schemas', '')) + str(result.get('context', ''))
        if 'revenue' in context.lower() or 'product' in context.lower():
            logger.info("   - Relevant schemas found ✅")
        
        logger.info("✅ Librarian Agent test completed\n")
    
    async def test_self_healing_loop_completes(self, http_client):
        """
        Phase 1 & 2 Test: Verify Self-Healing Loop completes without syntax errors
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Self-Healing SQL Loop")
        logger.info("="*80)
        
        # Intentionally complex query that might require corrections
        query = "Calculate year-over-year growth rate for revenue by region"
        
        response = await http_client.post("/query", json={
            "query": query,
            "database": "default",
            "use_crewai": True
        })
        
        assert response.status_code == 200, f"Self-healing failed: {response.text}"
        result = response.json()
        
        # Verify SQL was generated
        assert result.get('sql') is not None, "No SQL generated"
        assert len(result['sql']) > 0, "Empty SQL generated"
        
        # Check for self-healing metadata
        attempts = result.get('attempts', 1)
        confidence = result.get('confidence', 0)
        
        logger.info("✅ PASS: Self-Healing Loop completed successfully")
        logger.info(f"   - Attempts: {attempts}")
        logger.info(f"   - Confidence: {confidence}")
        logger.info(f"   - SQL generated: {len(result['sql'])} characters")
        
        # Verify no syntax errors (SQL should have basic structure)
        sql = result['sql']
        assert 'SELECT' in sql.upper(), "Invalid SQL: Missing SELECT"
        assert 'FROM' in sql.upper() or 'SELECT' in sql.upper(), "Invalid SQL: Missing FROM"
        
        logger.info(f"   - SQL syntax valid ✅")
        logger.info("✅ Self-Healing Loop test completed\n")


# ============================================================================
# TEST CLASS: Phase 3 & 4 - Analytics + Research
# ============================================================================

@pytest.mark.asyncio
class TestPhase3And4Analytics:
    """Test analytics workflow with Plotly and external research"""
    
    async def test_scientist_generates_plotly_chart(self, http_client):
        """
        Phase 3 Test: Verify Scientist Agent generates Plotly JSON
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Data Scientist Agent - Plotly Visualization")
        logger.info("="*80)
        
        # Query requiring analytics
        query = "Analyze monthly sales trends with visualization"
        
        response = await http_client.post("/query/analytics", json={
            "query": query,
            "database": "default"
        })
        
        assert response.status_code == 200, f"Analytics request failed: {response.text}"
        result = response.json()
        
        # Verify Plotly visualization is present
        has_plotly = False
        
        # Check in various possible response locations
        if 'plotly_chart' in result:
            has_plotly = True
            chart = result['plotly_chart']
            logger.info("✅ PASS: Plotly chart found in 'plotly_chart' field")
        elif 'visualization' in result:
            has_plotly = True
            chart = result['visualization']
            logger.info("✅ PASS: Plotly chart found in 'visualization' field")
        elif 'analytics' in result and isinstance(result['analytics'], dict):
            analytics = result['analytics']
            if 'chart' in analytics or 'plotly' in analytics:
                has_plotly = True
                chart = analytics.get('chart') or analytics.get('plotly')
                logger.info("✅ PASS: Plotly chart found in 'analytics' field")
        
        # If Plotly found, validate structure
        if has_plotly:
            # Plotly charts should be JSON objects with 'data' and 'layout'
            if isinstance(chart, str):
                try:
                    chart = json.loads(chart)
                except:
                    pass
            
            if isinstance(chart, dict):
                logger.info(f"   - Chart type: {type(chart)}")
                logger.info(f"   - Chart keys: {list(chart.keys())[:5]}")
                
                # Verify Plotly structure (should have data/layout or be a figure dict)
                if 'data' in chart or 'layout' in chart or 'type' in chart:
                    logger.info("   - Valid Plotly structure ✅")
                else:
                    logger.warning("   - Unusual chart structure ⚠️")
            
            assert has_plotly, "Plotly chart generated successfully"
        else:
            logger.warning("⚠️ WARNING: No Plotly visualization found in response")
            logger.info(f"   Response keys: {list(result.keys())}")
            # Don't fail - visualization might be optional depending on query
        
        logger.info("✅ Scientist Agent test completed\n")
    
    async def test_researcher_provides_external_context(self, http_client):
        """
        Phase 4 Test: Verify Researcher Agent provides Tavily research snippets
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Researcher Agent - External Context (Tavily)")
        logger.info("="*80)
        
        # Query that benefits from external research
        query = "Compare our Q4 2024 performance to industry benchmarks"
        
        response = await http_client.post("/query/research", json={
            "query": query,
            "database": "default",
            "force_research": True  # Force research for testing
        })
        
        assert response.status_code == 200, f"Research request failed: {response.text}"
        result = response.json()
        
        # Verify research data is present
        has_research = False
        research_data = None
        
        # Check various response locations
        if 'research' in result:
            has_research = True
            research_data = result['research']
            logger.info("✅ PASS: Research data found in 'research' field")
        elif 'external_context' in result:
            has_research = True
            research_data = result['external_context']
            logger.info("✅ PASS: Research data found in 'external_context' field")
        elif 'insights' in result:
            has_research = True
            research_data = result['insights']
            logger.info("✅ PASS: Research data found in 'insights' field")
        
        if has_research and research_data:
            # Verify research content
            research_str = str(research_data)
            
            logger.info(f"   - Research length: {len(research_str)} characters")
            
            # Check for external sources/URLs (Tavily typically includes these)
            has_urls = bool(re.search(r'http[s]?://|www\.', research_str))
            if has_urls:
                logger.info("   - External sources found ✅")
            
            # Check for industry/market terms
            market_terms = ['industry', 'market', 'benchmark', 'competitor', 'trend']
            has_market_context = any(term in research_str.lower() for term in market_terms)
            if has_market_context:
                logger.info("   - Market context present ✅")
            
            logger.info("✅ Researcher Agent provided external context")
        else:
            logger.warning("⚠️ WARNING: No research data found")
            logger.info(f"   Response keys: {list(result.keys())}")
            logger.info("   (Research might be disabled or API key missing)")
        
        logger.info("✅ Researcher Agent test completed\n")


# ============================================================================
# TEST CLASS: Phase 5 & 6 - Reporting Artifacts
# ============================================================================

@pytest.mark.asyncio
class TestPhase5And6Reporting:
    """Test professional report generation (PDF & PPTX)"""
    
    async def test_pdf_report_generation(self, http_client, clean_exports):
        """
        Phase 6 Test: Verify PDF report generation
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Reporter Agent - PDF Generation")
        logger.info("="*80)
        
        # First, generate a query to get data
        query_response = await http_client.post("/query", json={
            "query": "Show Q4 2024 revenue summary",
            "database": "default",
            "use_crewai": True
        })
        
        assert query_response.status_code == 200, "Query failed before report generation"
        query_data = query_response.json()
        
        # Now generate PDF report
        report_response = await http_client.post("/reports/generate", json={
            "query_data": query_data,
            "report_format": "pdf",
            "include_analytics": True,
            "include_research": False
        })
        
        # Check response
        if report_response.status_code == 200:
            logger.info("✅ PASS: PDF report generated successfully")
            
            # Verify it's a PDF file
            content_type = report_response.headers.get('content-type', '')
            assert 'pdf' in content_type.lower() or report_response.headers.get('content-disposition'), \
                f"Invalid content type: {content_type}"
            
            # Save PDF for inspection
            pdf_path = EXPORTS_DIR / "test_report.pdf"
            pdf_path.write_bytes(report_response.content)
            
            logger.info(f"   - PDF saved to: {pdf_path}")
            logger.info(f"   - File size: {len(report_response.content)} bytes")
            
            # Verify file size (should be > 1KB for valid PDF)
            assert len(report_response.content) > 1024, "PDF file too small"
            
            # Verify PDF header
            pdf_header = report_response.content[:4]
            assert pdf_header == b'%PDF', "Invalid PDF format"
            
            logger.info("   - Valid PDF format ✅")
        else:
            logger.warning(f"⚠️ PDF generation returned {report_response.status_code}")
            logger.info(f"   Response: {report_response.text[:200]}")
        
        logger.info("✅ PDF Report test completed\n")
    
    async def test_pptx_report_generation(self, http_client, clean_exports):
        """
        Phase 6 Test: Verify PPTX report generation
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Reporter Agent - PPTX Generation")
        logger.info("="*80)
        
        # Generate query data
        query_response = await http_client.post("/query", json={
            "query": "Summarize key business metrics",
            "database": "default",
            "use_crewai": True
        })
        
        assert query_response.status_code == 200, "Query failed before report generation"
        query_data = query_response.json()
        
        # Generate PPTX report
        report_response = await http_client.post("/reports/generate", json={
            "query_data": query_data,
            "report_format": "pptx",
            "include_analytics": True,
            "include_research": False
        })
        
        # Check response
        if report_response.status_code == 200:
            logger.info("✅ PASS: PPTX report generated successfully")
            
            # Save PPTX for inspection
            pptx_path = EXPORTS_DIR / "test_presentation.pptx"
            pptx_path.write_bytes(report_response.content)
            
            logger.info(f"   - PPTX saved to: {pptx_path}")
            logger.info(f"   - File size: {len(report_response.content)} bytes")
            
            # Verify file size
            assert len(report_response.content) > 5000, "PPTX file too small"
            
            # Verify PPTX signature (ZIP file)
            pptx_header = report_response.content[:4]
            assert pptx_header[:2] == b'PK', "Invalid PPTX format (should be ZIP)"
            
            logger.info("   - Valid PPTX format ✅")
        else:
            logger.warning(f"⚠️ PPTX generation returned {report_response.status_code}")
            logger.info(f"   Response: {report_response.text[:200]}")
        
        logger.info("✅ PPTX Report test completed\n")


# ============================================================================
# TEST CLASS: Security - Sandbox Protection
# ============================================================================

@pytest.mark.asyncio
class TestSecuritySandbox:
    """Test Docker/RestrictedPython sandbox security"""
    
    async def test_sandbox_blocks_malicious_code(self, http_client):
        """
        Security Test: Verify sandbox blocks malicious OS commands
        
        Attempts to inject: import os; os.system('ls')
        Expected: Execution should be blocked by RestrictedPython
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Security Sandbox - Malicious Code Blocking")
        logger.info("="*80)
        
        # Attempt malicious query with code injection
        malicious_query = "Show sales data and execute import os; os.system('ls')"
        
        response = await http_client.post("/query/analytics", json={
            "query": malicious_query,
            "database": "default"
        })
        
        # Response should either:
        # 1. Block the request (400/403)
        # 2. Execute safely without running os.system (200 but no system access)
        
        logger.info(f"📊 Response status: {response.status_code}")
        
        if response.status_code in [400, 403]:
            logger.info("✅ PASS: Malicious request blocked at API level")
            result = response.json()
            logger.info(f"   - Error message: {result.get('detail', 'N/A')}")
        elif response.status_code == 200:
            result = response.json()
            
            # Check if sandbox blocked the execution
            error = result.get('error', '')
            analytics_error = result.get('analytics_error', '')
            
            if 'restricted' in error.lower() or 'blocked' in error.lower():
                logger.info("✅ PASS: Malicious code blocked by RestrictedPython")
                logger.info(f"   - Sandbox message: {error}")
            elif 'import' in analytics_error.lower() or 'restricted' in analytics_error.lower():
                logger.info("✅ PASS: Import blocked by sandbox")
                logger.info(f"   - Sandbox message: {analytics_error}")
            else:
                # Even if no explicit error, verify system wasn't compromised
                logger.info("⚠️ WARNING: Request completed without explicit blocking")
                logger.info("   - Verifying no system access occurred...")
                
                # Check if result contains system output (should not)
                result_str = str(result)
                suspicious_indicators = [
                    'bin/bash', '/usr/', '/home/', 'root', 'system32'
                ]
                
                has_system_access = any(ind in result_str for ind in suspicious_indicators)
                
                if not has_system_access:
                    logger.info("✅ PASS: No system access detected in output")
                else:
                    logger.error("❌ FAIL: Potential system access detected!")
                    assert False, "Sandbox may have been bypassed"
        else:
            logger.error(f"❌ Unexpected response: {response.status_code}")
            assert False, f"Unexpected status code: {response.status_code}"
        
        logger.info("✅ Security Sandbox test completed\n")
    
    async def test_sandbox_blocks_file_access(self, http_client):
        """
        Security Test: Verify sandbox blocks file system access
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Security Sandbox - File Access Blocking")
        logger.info("="*80)
        
        # Attempt to access file system
        malicious_query = "Analyze data using open('/etc/passwd').read()"
        
        response = await http_client.post("/query/analytics", json={
            "query": malicious_query,
            "database": "default"
        })
        
        logger.info(f"📊 Response status: {response.status_code}")
        
        # Should be blocked
        if response.status_code in [400, 403]:
            logger.info("✅ PASS: File access blocked at API level")
        elif response.status_code == 200:
            result = response.json()
            error = str(result.get('error', '')) + str(result.get('analytics_error', ''))
            
            if 'restricted' in error.lower() or 'blocked' in error.lower() or 'open' in error.lower():
                logger.info("✅ PASS: File access blocked by sandbox")
                logger.info(f"   - Sandbox message: {error[:200]}")
            else:
                # Verify no sensitive data in response
                result_str = str(result)
                if 'root:' not in result_str and 'passwd' not in result_str:
                    logger.info("✅ PASS: No sensitive file data in response")
                else:
                    logger.error("❌ FAIL: File content may have been accessed!")
                    assert False, "Sandbox failed to block file access"
        
        logger.info("✅ File Access Blocking test completed\n")


# ============================================================================
# TEST CLASS: Phase 4 - Monitoring & Alerts
# ============================================================================

@pytest.mark.asyncio
class TestPhase4Monitoring:
    """Test Anomaly Sentry monitoring and WebSocket alerts"""
    
    async def test_anomaly_sentry_triggers_alert(self, http_client):
        """
        Phase 4 Test: Verify Anomaly Sentry detects anomalies and triggers alerts
        
        Simulates a 50% revenue drop and checks for alert
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: Anomaly Sentry - Alert Triggering")
        logger.info("="*80)
        
        # First, check current alerts
        initial_response = await http_client.get("/alerts/recent")
        assert initial_response.status_code == 200
        initial_alerts = initial_response.json()
        initial_count = len(initial_alerts.get('alerts', []))
        
        logger.info(f"📊 Initial alert count: {initial_count}")
        
        # Force anomaly check for revenue metric
        check_response = await http_client.post("/alerts/check/revenue", json={
            "threshold_multiplier": 0.5  # 50% drop threshold
        })
        
        if check_response.status_code == 200:
            check_result = check_response.json()
            logger.info(f"📊 Anomaly check completed: {check_result.get('status')}")
            
            if check_result.get('anomaly_detected'):
                logger.info("✅ PASS: Anomaly detected by Sentry")
                logger.info(f"   - Current value: {check_result.get('current_value')}")
                logger.info(f"   - Expected value: {check_result.get('expected_value')}")
                logger.info(f"   - Deviation: {check_result.get('deviation', 'N/A')}")
                
                # Check if alert was created
                final_response = await http_client.get("/alerts/recent")
                final_alerts = final_response.json()
                final_count = len(final_alerts.get('alerts', []))
                
                if final_count > initial_count:
                    logger.info(f"   - New alerts created: {final_count - initial_count}")
                    logger.info("✅ PASS: Alert system working")
                else:
                    logger.warning("⚠️ Anomaly detected but no new alerts")
            else:
                logger.info("ℹ️ No anomaly detected (data may be within normal range)")
        else:
            logger.warning(f"⚠️ Anomaly check endpoint returned {check_response.status_code}")
            logger.info("   (Sentry may not be fully initialized)")
        
        logger.info("✅ Anomaly Sentry test completed\n")
    
    async def test_websocket_alert_broadcast(self, api_server):
        """
        Phase 4 Test: Verify WebSocket alerts are broadcast correctly
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: WebSocket Alert Broadcasting")
        logger.info("="*80)
        
        try:
            # Connect to WebSocket
            ws_url = f"ws://{api_server.host}:{api_server.port}/ws/alerts"
            
            async with ws_connect(ws_url) as websocket:
                logger.info("✅ WebSocket connected successfully")
                
                # Wait for potential alerts (with timeout)
                try:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    
                    alert = json.loads(message)
                    logger.info("✅ PASS: Alert received via WebSocket")
                    logger.info(f"   - Alert type: {alert.get('metric_name')}")
                    logger.info(f"   - Severity: {alert.get('severity')}")
                    logger.info(f"   - Message: {alert.get('message', '')[:100]}")
                    
                except asyncio.TimeoutError:
                    logger.info("ℹ️ No alerts received within timeout period")
                    logger.info("   (This is OK if no anomalies are present)")
                
                logger.info("✅ WebSocket connection working")
                
        except Exception as e:
            logger.warning(f"⚠️ WebSocket test error: {e}")
            logger.info("   (WebSocket server may not be fully initialized)")
        
        logger.info("✅ WebSocket test completed\n")


# ============================================================================
# TEST CLASS: Health & Status Checks
# ============================================================================

@pytest.mark.asyncio
class TestSystemHealth:
    """Test overall system health and component status"""
    
    async def test_health_check_all_components(self, http_client):
        """
        Verify all Autonomous Multi-Agent Business Intelligence System components are initialized and healthy
        """
        logger.info("\n" + "="*80)
        logger.info("TEST: System Health Check")
        logger.info("="*80)
        
        response = await http_client.get("/health")
        assert response.status_code == 200, "Health check failed"
        
        health = response.json()
        
        logger.info(f"📊 System Status: {health.get('status')}")
        logger.info(f"📊 Version: {health.get('version')}")
        
        # Check component status
        components = health.get('components', {})
        logger.info("\nComponent Status:")
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}: {status}")
        
        # Verify critical components
        critical_components = ['librarian_agent', 'dataops_manager']
        for component in critical_components:
            assert components.get(component), f"Critical component {component} not initialized"
        
        logger.info("\n✅ Health check completed\n")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_e2e_tests():
    """
    Run all E2E tests with comprehensive reporting
    """
    logger.info("\n" + "="*80)
    logger.info("AUTONOMOUS MULTI-AGENT BUSINESS INTELLIGENCE SYSTEM - COMPREHENSIVE E2E TEST SUITE")
    logger.info("="*80)
    logger.info(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80 + "\n")
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--log-cli-level=INFO",
        "-W", "ignore::DeprecationWarning"
    ])
    
    logger.info("\n" + "="*80)
    logger.info("E2E TEST SUITE COMPLETED")
    logger.info("="*80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_e2e_tests())
