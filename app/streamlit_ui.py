"""
Autonomous Multi-Agent Business Intelligence System - Streamlit Dashboard
====================================

Modern web interface for the multi-agent SQL generation system.

Features:
- Real-time anomaly monitoring with WebSocket alerts
- Interactive query interface with agent tracing
- Analytics visualization (Plotly charts)
- External research integration
- Side-by-side performance metrics
- Agent reasoning visualization

Usage:
    streamlit run app/streamlit_ui.py

Requirements:
    - FastAPI backend running on http://127.0.0.1:8000 (or set API_BASE_URL)
    - All Phase 4 components installed
"""

import streamlit as st
import requests
import json
import plotly.graph_objects as go
import os
from datetime import datetime
import time
import asyncio
from typing import Dict, Any, Optional, List

# Import custom components
from components.agent_trace import AgentTraceViewer
from components.monitoring_dashboard import MonitoringDashboard

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Autonomous Multi-Agent Business Intelligence System",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .alert-card {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-card {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-card {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .agent-step {
        background: #f8f9fa;
        border-left: 3px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'current_result' not in st.session_state:
    st.session_state.current_result = None

if 'alerts' not in st.session_state:
    st.session_state.alerts = []

if 'show_agent_trace' not in st.session_state:
    st.session_state.show_agent_trace = False

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "💬 Query"

# ============================================================================
# Helper Functions
# ============================================================================

def check_backend_health() -> Dict[str, Any]:
    """Check if backend is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_query(query: str, query_type: str = "standard") -> Dict[str, Any]:
    """Execute query against Autonomous Multi-Agent Business Intelligence System API"""
    try:
        if query_type == "analytics":
            endpoint = f"{API_BASE_URL}/query/analytics"
            payload = {"query": query}
        elif query_type == "research":
            endpoint = f"{API_BASE_URL}/query/research"
            payload = {"query": query, "force_research": False}
        else:
            endpoint = f"{API_BASE_URL}/query"
            payload = {"query": query}
        
        # Handle LLM/provider quota issues gracefully, with a small auto-retry.
        # This helps smooth over short TPM cool-down windows (a few seconds).
        max_attempts = 2
        for attempt in range(max_attempts):
            response = requests.post(endpoint, json=payload, timeout=60)
            if response.status_code != 429:
                break

            retry_after_header = response.headers.get("Retry-After")
            retry_after_s: Optional[float] = None
            if retry_after_header:
                try:
                    retry_after_s = float(retry_after_header)
                except ValueError:
                    retry_after_s = None

            if attempt < (max_attempts - 1) and retry_after_s is not None and 0 < retry_after_s <= 10:
                # Add a small cushion to reduce immediate re-rate-limits.
                time.sleep(retry_after_s + 0.5)
                continue

            detail = None
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = response.text

            message = "Rate limit reached (LLM provider quota)."
            if retry_after_header:
                message += f" Retry after ~{retry_after_header}s."
            if detail:
                message += f"\n\n{detail}"

            return {
                "error": message,
                "error_type": "rate_limit",
                "retry_after_seconds": int(retry_after_s) if isinstance(retry_after_s, (int, float)) else None,
            }

        response.raise_for_status()
        
        result = response.json()
        
        # Store in history
        st.session_state.query_history.append({
            "timestamp": datetime.now(),
            "query": query,
            "type": query_type,
            "result": result
        })
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def get_recent_alerts() -> list:
    """Fetch recent anomaly alerts"""
    try:
        response = requests.get(f"{API_BASE_URL}/alerts/recent?limit=5", timeout=5)
        data = response.json()
        return data.get("alerts", [])
    except:
        return []


def download_report(result: Dict[str, Any], query: str, formats: List[str]) -> Dict[str, str]:
    """
    Generate professional reports from query results (Phase 6)
    
    Args:
        result: Query result dictionary
        query: Original user query
        formats: List of formats to generate (pdf, pptx)
        
    Returns:
        Dictionary mapping format to file path
    """
    try:
        # Prepare data for reporter
        sql_result = {
            "method": result.get("method", "standard"),
            "sql": result.get("sql", ""),
            "data": result.get("data", [])
        }
        
        analytics_result = None
        if result.get("analysis"):
            analytics_result = {
                "analysis": result.get("analysis", ""),
                "statistics": result.get("statistics", {}),
                "visualization": result.get("visualization")
            }
        
        research_result = None
        if result.get("unified_insights"):
            research_result = {
                "internal_findings": result.get("internal_findings", ""),
                "external_research": result.get("external_research", ""),
                "unified_insights": result.get("unified_insights", "")
            }
        
        # Call backend report generation endpoint
        response = requests.post(
            f"{API_BASE_URL}/reports/generate",
            json={
                "query": query,
                "sql_result": sql_result,
                "analytics_result": analytics_result,
                "research_result": research_result,
                "formats": formats
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Report generation failed: {response.text}"}
            
    except Exception as e:
        return {"error": str(e)}


def display_metric_comparison(internal_value: float, external_value: float, 
                              internal_label: str, external_label: str):
    """Display side-by-side metric cards for comparison"""
    col1, col2 = st.columns(2)
    
    with col1:
        delta = ((internal_value - external_value) / external_value * 100) if external_value != 0 else 0
        st.metric(
            label=internal_label,
            value=f"{internal_value:.2f}",
            delta=f"{delta:+.1f}% vs. market",
            delta_color="normal" if delta >= 0 else "inverse"
        )
    
    with col2:
        st.metric(
            label=external_label,
            value=f"{external_value:.2f}",
            delta=None
        )


# ============================================================================
# Main Application
# ============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-header">🧞 Autonomous Multi-Agent Business Intelligence System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered SQL Generation with Proactive Monitoring & Research</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/250x80/667eea/ffffff?text=Autonomous Multi-Agent Business Intelligence System+2.0", use_container_width=True)
        
        st.markdown("---")
        
        # Backend Health Check
        st.subheader("🔌 System Status")
        health = check_backend_health()
        
        if health.get("status") == "healthy":
            st.success("✅ Backend Connected")
            
            components = health.get("components", {})
            st.caption(f"📊 Librarian: {'✓' if components.get('librarian_agent') else '✗'}")
            st.caption(f"🧠 CrewAI: {'✓' if components.get('dataops_manager') else '✗'}")
            st.caption(f"🔍 Sentry: {'✓' if components.get('sentry_agent') else '✗'}")
            st.caption(f"🌐 WebSocket: {components.get('websocket_connections', 0)} clients")
            
            monitoring = health.get("monitoring", {})
            st.caption(f"📈 Tracking {monitoring.get('metrics_tracked', 0)} metrics")
        else:
            st.error("❌ Backend Offline")
            st.caption(f"Error: {health.get('message', 'Unknown')}")
            st.info("Start backend: `uvicorn src.api.main_crewai:app --reload`")
        
        st.markdown("---")
        
        # Query Mode Selection
        st.subheader("⚙️ Query Mode")
        query_mode = st.selectbox(
            "Select mode:",
            ["Standard", "Analytics", "Research"],
            help="Standard: SQL only | Analytics: SQL + Stats | Research: SQL + Web Search"
        )
        
        st.markdown("---")
        
        # Recent Alerts
        st.subheader("🚨 Recent Alerts")
        alerts = get_recent_alerts()
        
        if alerts:
            for alert in alerts[:3]:
                severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert.get("severity"), "⚪")
                st.caption(f"{severity_emoji} {alert.get('metric_name')}: {alert.get('deviation_percent', 0):+.0f}%")
        else:
            st.caption("No recent alerts")
        
        if st.button("📊 View Full Dashboard", use_container_width=True):
            st.session_state.active_tab = "📊 Monitoring"
            st.rerun()
        
        st.markdown("---")
        st.caption("Autonomous Multi-Agent Business Intelligence System v2.0.4")
    
    # Main Content Navigation (controllable; unlike st.tabs)
    tab_options = ["💬 Query", "📊 Monitoring", "📚 History", "⚙️ Settings"]
    if st.session_state.active_tab not in tab_options:
        st.session_state.active_tab = tab_options[0]

    active_tab = st.radio(
        "Navigation",
        tab_options,
        horizontal=True,
        key="active_tab",
        label_visibility="collapsed",
    )
    
    # ========================================================================
    # Tab 1: Query Interface
    # ========================================================================
    if active_tab == "💬 Query":
        st.header("Ask Autonomous Multi-Agent Business Intelligence System")
        
        # Query Input
        query_input = st.text_area(
            "Enter your question:",
            placeholder="e.g., Show me total revenue for the last quarter compared to industry benchmarks",
            height=100,
            help="Natural language question about your data"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            execute_btn = st.button("🚀 Execute Query", type="primary", use_container_width=True)
        
        with col2:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)
        
        with col3:
            show_trace = st.checkbox("Show Agent Trace", value=False)
        
        # Execute Query
        if execute_btn and query_input:
            with st.spinner("🤔 Autonomous Multi-Agent Business Intelligence System is thinking..."):
                mode_map = {"Standard": "standard", "Analytics": "analytics", "Research": "research"}
                result = execute_query(query_input, mode_map[query_mode])
                st.session_state.current_result = result
                st.session_state.show_agent_trace = show_trace
        
        if clear_btn:
            st.session_state.current_result = None
            st.rerun()
        
        # Display Results
        if st.session_state.current_result:
            result = st.session_state.current_result
            
            if result.get("error"):
                st.error(f"❌ Error: {result['error']}")
                
                # Check for PII-related errors
                if result.get("risk_level"):
                    st.warning(f"⚠️ Security Alert: {result.get('risk_level')} risk PII detected")
                    if result.get("detections"):
                        st.caption(f"Detected: {', '.join(result.get('detections', []))}")
            else:
                # Success Message
                st.success("✅ Query executed successfully!")
                
                # PII Detection Warning (if detected but not blocking)
                if result.get("pii_detected"):
                    st.warning(f"⚠️ PII Protection Active: {result.get('pii_risk_level', 'MEDIUM')} risk detected - results automatically redacted")
                
                # Download Report Button (Phase 6)
                col_download1, col_download2, col_download3 = st.columns([2, 1, 1])
                with col_download1:
                    st.markdown("### 📄 Professional Reports")
                with col_download2:
                    if st.button("📊 Download PDF", help="Generate comprehensive PDF report"):
                        with st.spinner("Generating PDF report..."):
                            report_result = download_report(result, query_input, ["pdf"])
                            if report_result.get("pdf"):
                                # Read and offer download
                                with open(report_result["pdf"], "rb") as f:
                                    st.download_button(
                                        label="💾 Save PDF Report",
                                        data=f,
                                        file_name=report_result["pdf"].split("/")[-1],
                                        mime="application/pdf"
                                    )
                                st.success(f"✅ PDF generated: {report_result['pdf'].split('/')[-1]}")
                            else:
                                st.error("Failed to generate PDF report")
                with col_download3:
                    if st.button("📑 Download PPTX", help="Generate Executive PowerPoint deck"):
                        with st.spinner("Generating PowerPoint..."):
                            report_result = download_report(result, query_input, ["pptx"])
                            if report_result.get("pptx"):
                                # Read and offer download
                                with open(report_result["pptx"], "rb") as f:
                                    st.download_button(
                                        label="💾 Save PPTX Deck",
                                        data=f,
                                        file_name=report_result["pptx"].split("/")[-1],
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                                    )
                                st.success(f"✅ PPTX generated: {report_result['pptx'].split('/')[-1]}")
                            else:
                                st.error("Failed to generate PPTX report")
                
                st.markdown("---")
                
                # Performance Metrics (if available)
                if query_mode == "Research" and result.get("unified_insights"):
                    st.subheader("📊 Performance Comparison")
                    
                    # Extract metrics from internal findings (simplified)
                    internal_findings = result.get("internal_findings", "")
                    
                    # Display side-by-side metrics
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🏢 Internal Performance")
                        st.info(internal_findings[:200] + "..." if len(internal_findings) > 200 else internal_findings)
                    
                    with col2:
                        st.markdown("### 🌍 Market Sentiment")
                        external_research = result.get("external_research", "")
                        st.info(external_research[:200] + "..." if len(external_research) > 200 else external_research)
                    
                    # Unified Insights
                    st.markdown("---")
                    st.subheader("💡 Unified Insights")
                    st.markdown(result.get("unified_insights"))
                
                # SQL Query
                with st.expander("📝 Generated SQL", expanded=False):
                    st.code(result.get("sql", ""), language="sql")
                
                # Data Preview
                if result.get("data"):
                    with st.expander("📊 Data Preview", expanded=True):
                        st.text(result["data"][:500] + "..." if len(str(result["data"])) > 500 else result["data"])
                
                # Analytics Visualization (Phase 3)
                if result.get("visualization"):
                    st.subheader("📈 Visualization")
                    try:
                        fig_json = json.loads(result["visualization"])
                        fig = go.Figure(fig_json)
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.warning("Could not display visualization")
                
                # Analysis Results
                if result.get("analysis_result"):
                    with st.expander("🔬 Statistical Analysis", expanded=True):
                        st.json(result["analysis_result"])
                
                # Agent Trace
                if st.session_state.show_agent_trace:
                    st.markdown("---")
                    st.subheader("🤖 Agent Reasoning Trace")
                    trace_viewer = AgentTraceViewer()
                    trace_viewer.display(result)
    
    # ========================================================================
    # Tab 2: Monitoring Dashboard
    # ========================================================================
    elif active_tab == "📊 Monitoring":
        st.header("📊 Real-time Monitoring Dashboard")
        
        dashboard = MonitoringDashboard(API_BASE_URL)
        dashboard.render()
    
    # ========================================================================
    # Tab 3: Query History
    # ========================================================================
    elif active_tab == "📚 History":
        st.header("📚 Query History")
        
        if st.session_state.query_history:
            for idx, entry in enumerate(reversed(st.session_state.query_history)):
                with st.expander(f"🕐 {entry['timestamp'].strftime('%H:%M:%S')} - {entry['query'][:50]}..."):
                    st.caption(f"Type: {entry['type'].upper()}")
                    st.code(entry['result'].get('sql', ''), language='sql')
                    
                    if entry['result'].get('data'):
                        st.text(str(entry['result']['data'])[:300] + "...")
        else:
            st.info("No queries executed yet. Try asking Autonomous Multi-Agent Business Intelligence System a question!")
    
    # ========================================================================
    # Tab 4: Settings
    # ========================================================================
    elif active_tab == "⚙️ Settings":
        st.header("⚙️ Settings")
        
        st.subheader("🔌 API Configuration")
        api_url = st.text_input("Backend URL", value=API_BASE_URL)
        
        st.subheader("🎨 Display Options")
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Show SQL by default", value=False)
            st.checkbox("Auto-expand visualizations", value=True)
        
        with col2:
            st.checkbox("Enable notifications", value=True)
            st.checkbox("Dark mode", value=False)
        
        st.markdown("---")
        
        st.subheader("🧹 Data Management")
        if st.button("Clear Query History", type="secondary"):
            st.session_state.query_history = []
            st.success("History cleared!")
        
        if st.button("Reset All Settings", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Settings reset!")
            st.rerun()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
