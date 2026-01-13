"""
Autonomous Multi-Agent Business Intelligence System - Streamlit User Interface

Web-based interface for the BI assistant.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional

# Page Configuration
st.set_page_config(
    page_title="Autonomous Multi-Agent Business Intelligence System",
    page_icon="🧞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = "http://localhost:8000"

# Session State
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# Helper Functions
def check_api_health() -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"status": "unhealthy"}

def process_query(query: str, database: str, use_rag: bool, agentic: bool = False) -> Optional[Dict]:
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query, "database": database, "use_rag": use_rag, "agentic": agentic},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()
        # Surface server error details for easier debugging
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        st.error(f"API Error: {response.status_code}: {detail}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Start the server with: uvicorn src.api.main:app --reload")
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again or simplify the query.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return None

def get_examples():
    try:
        response = requests.get(f"{API_URL}/examples", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"examples": ["Show me total revenue", "Top 10 products by sales"]}

# Sidebar
with st.sidebar:
    st.title("Autonomous Multi-Agent Business Intelligence System")
    st.markdown("---")
    
    st.header("⚙️ Settings")
    database = st.selectbox("Database", ["default", "sales_db", "marketing_db"])
    use_rag = st.checkbox("Use RAG Enhancement", value=True)
    agentic = st.checkbox("🤖 Enable Agentic Mode (Multi-Agent Pipeline)", value=True)
    
    st.markdown("---")
    
    st.header("🔌 API Status")
    health = check_api_health()
    if health.get("status") == "healthy":
        st.success("✅ Connected")
        llm_status = health.get("llm_status", {})
        groq_ok = llm_status.get("groq", {}).get("available", False)
        model = llm_status.get("groq", {}).get("model", "")
        st.write(f"Groq: {'✅' if groq_ok else '❌'} {model}")
    else:
        st.error("❌ Disconnected")
    
    st.markdown("---")
    
    st.header("💡 Examples")
    examples = get_examples().get("examples", [])
    for ex in examples[:5]:
        if st.button(ex[:35] + "..." if len(ex) > 35 else ex, key=ex):
            st.session_state.query_input = ex

# Main Content
st.title("Autonomous Multi-Agent Business Intelligence System")
st.markdown("Transform natural language into SQL queries")

# Query Input
col1, col2 = st.columns([5, 1])
with col1:
    query = st.text_input(
        "Ask a question about your data",
        value=st.session_state.get("query_input", ""),
        placeholder="e.g., Show me total revenue by region for last quarter"
    )
with col2:
    st.write("")
    submit = st.button("🚀 Generate", type="primary")

# Process Query
if submit and query:
    with st.spinner("🧠 Generating SQL..." + (" with AI Agents..." if agentic else "")):
        result = process_query(query, database, use_rag, agentic)
        if result:
            st.session_state.current_result = result
            st.session_state.query_history.append({
                "query": query,
                "sql": result["sql"],
                "confidence": result["confidence"]
            })

# Display Results
if st.session_state.current_result:
    result = st.session_state.current_result
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Confidence", f"{result['confidence']:.0%}")
    col2.metric("Intent", result['intent']['intent'].replace("_", " ").title())
    col3.metric("Complexity", result['complexity'].title())
    col4.metric("Cost", f"${result['cost_estimate']:.4f}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 SQL", "🔍 Analysis", "🤖 Agent Plan", "📜 History"])
    
    with tab1:
        st.subheader("Generated SQL")
        st.code(result["sql"], language="sql")
        
        # Display correction metadata for self-correction transparency
        if "attempts" in result:
            attempts = result["attempts"]
            if attempts > 1:
                st.info(f"🔧 **Auto-corrected:** SQL was refined {attempts} times by the correction agent for accuracy")
        
        if result["validation_status"] == "valid":
            st.success("✅ SQL Validated")
        else:
            st.warning("⚠️ Validation Issues")
            for error in result.get("validation_errors", []):
                st.error(error)
        
        st.subheader("Explanation")
        st.info(result["explanation"])
        
        st.download_button("📋 Download SQL", result["sql"], "query.sql", "text/plain")
    
    with tab2:
        st.subheader("Extracted Entities")
        if result["entities"]:
            df = pd.DataFrame(result["entities"])
            st.dataframe(df[["text", "label", "confidence"]])
        else:
            st.info("No entities extracted")
        
        st.subheader("Intent Scores")
        scores = result["intent"].get("all_scores", {})
        if scores:
            df = pd.DataFrame([{"Intent": k, "Score": v} for k, v in scores.items()])
            fig = px.bar(df.sort_values("Score"), x="Score", y="Intent", orientation="h")
            st.plotly_chart(fig)
    
    with tab3:
        st.subheader("🤖 Agentic Analysis Plan")
        plan = result.get("plan")
        if plan:
            st.success("✅ Multi-Agent Pipeline Active")
            
            # Display Plan Goal
            st.subheader("📌 Analytical Goal")
            st.info(f"**{plan.get('goal', 'No goal defined')}**")
            
            # Display Plan Steps
            st.subheader("📋 Step-by-Step Plan")
            steps = plan.get("steps", [])
            if steps:
                for i, step in enumerate(steps, 1):
                    st.write(f"**Step {i}:** {step}")
            else:
                st.info("No steps in plan")
            
            # Display Agent Trace
            agent_trace = result.get("agent_trace", [])
            if agent_trace:
                st.subheader("🔄 Agent Execution Pipeline")
                st.write(" → ".join(agent_trace))
                
                # Show individual agents
                with st.expander("🔍 Agent Details"):
                    agent_info = {
                        "memory_recall": "🧠 Memory Agent: Recalls similar past queries",
                        "planner": "📋 Planner Agent: Creates analytical plan",
                        "generator": "⚙️ Generator: Generates SQL query",
                        "validator": "✅ Validator: Validates SQL safety",
                        "corrector": "🔧 Corrector: Auto-fixes SQL errors",
                        "insight": "💡 Insight Agent: Generates business insights",
                        "memory_remember": "💾 Memory Agent: Stores query for future use"
                    }
                    for agent in agent_trace:
                        st.write(f"✓ {agent_info.get(agent, agent)}")
            
            # Display Insights
            insights = result.get("insights", {})
            if insights:
                st.subheader("💡 Business Insights")
                
                summary = insights.get("summary")
                if summary:
                    st.info(f"**Summary:** {summary}")
                
                key_points = insights.get("key_points", [])
                if key_points:
                    st.write("**Key Points:**")
                    for point in key_points:
                        st.write(f"• {point}")
                
                recommendations = insights.get("recommendations", [])
                if recommendations:
                    st.write("**Recommendations:**")
                    for rec in recommendations:
                        st.write(f"→ {rec}")
        else:
            st.info("ℹ️ Enable 'Agentic Mode' in settings to see the multi-agent analysis plan")
    
    with tab4:
        st.subheader("Query History")
        for item in reversed(st.session_state.query_history[-10:]):
            with st.expander(item['query'][:50]):
                st.code(item['sql'], language="sql")
        if st.button("Clear History"):
            st.session_state.query_history = []
            st.rerun()

# Footer
st.markdown("---")
st.caption("Autonomous Multi-Agent Business Intelligence System - Powered by LangChain, Groq API & ChromaDB")
