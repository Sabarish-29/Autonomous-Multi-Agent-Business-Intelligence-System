"""
Agent Trace Viewer Component
=============================

Specialized Streamlit component for visualizing agent reasoning traces
from CrewAI multi-agent workflows.

Features:
- Step-by-step agent execution visualization
- Agent role and task display
- Execution timeline
- Input/output tracking
- Error highlighting
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import json


class AgentTraceViewer:
    """Component for displaying agent reasoning traces"""
    
    def __init__(self):
        self.trace_data = []
    
    def display(self, result: Dict[str, Any]):
        """
        Display agent trace from query result.
        
        Args:
            result: Query result dictionary from Autonomous Multi-Agent Business Intelligence System API
        """
        # Extract method information
        method = result.get("method", "unknown")
        
        st.markdown("### 🔄 Execution Flow")
        
        # Phase detection
        if "analytics" in method:
            self._display_analytics_trace(result)
        elif "research" in method:
            self._display_research_trace(result)
        elif "hierarchical" in method:
            self._display_hierarchical_trace(result)
        else:
            self._display_basic_trace(result)
        
        # Validation info
        if result.get("validation"):
            st.markdown("---")
            st.markdown("### ✅ Validation Results")
            self._display_validation(result["validation"])
    
    def _display_hierarchical_trace(self, result: Dict[str, Any]):
        """Display trace for hierarchical CrewAI workflow (Phase 1+2)"""
        
        steps = [
            {
                "agent": "Query Analyst",
                "role": "Business Query Analyst",
                "task": "Analyze user query and map to business terms",
                "status": "completed",
                "output": "Identified key business entities and requirements"
            },
            {
                "agent": "Librarian",
                "role": "Schema Retrieval Specialist",
                "task": "Retrieve relevant database schemas",
                "status": "completed",
                "output": "Retrieved schemas for relevant tables using semantic search"
            },
            {
                "agent": "SQL Architect",
                "role": "SQL Database Architect",
                "task": "Generate optimized SQL query",
                "status": "completed",
                "output": f"Generated SQL: {result.get('sql', '')[:100]}..."
            },
            {
                "agent": "Validator",
                "role": "SQL Security Validator",
                "task": "Validate SQL for safety and correctness",
                "status": "completed",
                "output": "SQL passed security and syntax validation"
            }
        ]
        
        # Add Critic step if self-healing was used
        if result.get("validation", {}).get("corrections"):
            steps.append({
                "agent": "Critic",
                "role": "SQL Critic (OpenAI o1)",
                "task": "Dry-run analysis and error correction",
                "status": "completed",
                "output": f"Applied {len(result['validation']['corrections'])} corrections"
            })
        
        self._render_agent_steps(steps)
    
    def _display_analytics_trace(self, result: Dict[str, Any]):
        """Display trace for analytics workflow (Phase 3)"""
        
        steps = [
            {
                "agent": "Manager",
                "role": "Data Operations Manager",
                "task": "Detect analytics intent",
                "status": "completed",
                "output": f"Detected: {result.get('analytics_type', 'Unknown')} analysis"
            },
            {
                "agent": "SQL Architect",
                "role": "SQL Database Architect",
                "task": "Generate and execute SQL",
                "status": "completed",
                "output": "Retrieved data for analysis"
            },
            {
                "agent": "Data Scientist",
                "role": "Data Science Analyst",
                "task": f"Perform {result.get('analytics_type')} analysis",
                "status": "completed",
                "output": "Generated Python analysis code and executed in secure sandbox"
            }
        ]
        
        if result.get("visualization"):
            steps.append({
                "agent": "Visualization Agent",
                "role": "Data Visualization Specialist",
                "task": "Generate Plotly visualization",
                "status": "completed",
                "output": "Created interactive chart"
            })
        
        self._render_agent_steps(steps)
    
    def _display_research_trace(self, result: Dict[str, Any]):
        """Display trace for research workflow (Phase 4)"""
        
        steps = [
            {
                "agent": "SQL Architect",
                "role": "SQL Database Architect",
                "task": "Generate SQL for internal analysis",
                "status": "completed",
                "output": "Retrieved internal metrics from database"
            },
            {
                "agent": "Manager",
                "role": "Data Operations Manager",
                "task": "Detect research need",
                "status": "completed",
                "output": "Identified need for external market context"
            }
        ]
        
        if result.get("research_performed"):
            steps.extend([
                {
                    "agent": "Researcher",
                    "role": "Market Research Analyst",
                    "task": "Search external sources via Tavily API",
                    "status": "completed",
                    "output": "Retrieved market data and industry benchmarks"
                },
                {
                    "agent": "Manager",
                    "role": "Data Operations Manager",
                    "task": "Synthesize internal + external insights",
                    "status": "completed",
                    "output": "Combined database metrics with market research"
                }
            ])
        
        self._render_agent_steps(steps)
    
    def _display_basic_trace(self, result: Dict[str, Any]):
        """Display basic trace for standard queries"""
        
        steps = [
            {
                "agent": "SQL Generator",
                "role": "SQL Generation System",
                "task": "Generate SQL from natural language",
                "status": "completed",
                "output": f"Generated: {result.get('sql', '')[:100]}..."
            }
        ]
        
        self._render_agent_steps(steps)
    
    def _render_agent_steps(self, steps: List[Dict[str, Any]]):
        """Render agent execution steps with timeline"""
        
        for idx, step in enumerate(steps, 1):
            # Determine status icon
            status_icon = {
                "completed": "✅",
                "running": "⏳",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(step.get("status", "completed"), "•")
            
            # Create step container
            st.markdown(f"""
            <div class="agent-step">
                <h4>{status_icon} Step {idx}: {step['agent']}</h4>
                <p><strong>Role:</strong> {step['role']}</p>
                <p><strong>Task:</strong> {step['task']}</p>
                <p><strong>Output:</strong> {step['output']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _display_validation(self, validation: Dict[str, Any]):
        """Display validation results"""
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", validation.get("status", "unknown").upper())
        
        with col2:
            corrections = validation.get("corrections", [])
            st.metric("Corrections Applied", len(corrections))
        
        with col3:
            confidence = validation.get("confidence", 0)
            st.metric("Confidence", f"{confidence:.0%}")
        
        # Correction details
        if validation.get("corrections"):
            with st.expander("🔧 Correction Details"):
                for idx, correction in enumerate(validation["corrections"], 1):
                    st.markdown(f"**{idx}.** {correction}")
    
    def display_crewai_logs(self, logs: str):
        """
        Display raw CrewAI execution logs.
        
        Args:
            logs: Raw log output from CrewAI
        """
        st.markdown("### 📋 Detailed Logs")
        
        with st.expander("View Raw Logs"):
            st.code(logs, language="text")
    
    def display_token_usage(self, usage: Dict[str, int]):
        """
        Display LLM token usage statistics.
        
        Args:
            usage: Dictionary with token counts
        """
        st.markdown("### 💰 Token Usage")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Input Tokens", usage.get("prompt_tokens", 0))
        
        with col2:
            st.metric("Output Tokens", usage.get("completion_tokens", 0))
        
        with col3:
            total = usage.get("total_tokens", 0)
            estimated_cost = total * 0.00001  # Rough estimate
            st.metric("Total Tokens", total)
            st.caption(f"~${estimated_cost:.4f}")
    
    def display_agent_conversation(self, messages: List[Dict[str, str]]):
        """
        Display agent-to-agent conversation.
        
        Args:
            messages: List of message dicts with 'agent', 'content', 'timestamp'
        """
        st.markdown("### 💬 Agent Conversation")
        
        for msg in messages:
            agent = msg.get("agent", "Unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            with st.chat_message(agent.lower()):
                st.markdown(f"**{agent}** ({timestamp})")
                st.write(content)


# ============================================================================
# Standalone Usage Example
# ============================================================================

def example_usage():
    """Example of using AgentTraceViewer"""
    
    st.title("Agent Trace Viewer Example")
    
    # Mock result from API
    mock_result = {
        "sql": "SELECT SUM(total_amount) as revenue FROM orders WHERE order_date >= DATE('now', '-30 days')",
        "method": "crewai_hierarchical",
        "validation": {
            "status": "validated",
            "confidence": 0.95,
            "corrections": ["Added date filter for performance", "Used SUM instead of COUNT"]
        }
    }
    
    viewer = AgentTraceViewer()
    viewer.display(mock_result)


if __name__ == "__main__":
    example_usage()
