"""
Real-Time Executive Dashboard for Phase 4: Collaborative Boardroom

Professional Streamlit dashboard with voice input, live visualizations,
audio briefings, and critical alert monitoring.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import os
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.voice_briefer import create_voice_briefer_agent, SpeechTaskBuilder, generate_voice_brief
from src.agents.crewai_manager import DataOpsManager
from src.rag.vector_store import VectorStoreManager
from src.agents.librarian import LibrarianAgent
from src.config import GROQ_API_KEY
from langchain_groq import ChatGroq

# Audio libraries (graceful degradation if not installed)
try:
    from gtts import gTTS
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    st.warning("Audio features require: pip install gtts pygame")

# Voice input library (optional)
try:
    from streamlit_mic_recorder import mic_recorder
    VOICE_INPUT_AVAILABLE = True
except ImportError:
    VOICE_INPUT_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Executive Boardroom | DataGenie AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Executive Dark Mode Theme
DARK_THEME = {
    "background": "#0E1117",
    "secondary_bg": "#1E2128",
    "text": "#FAFAFA",
    "accent": "#FF4B4B",
    "success": "#00CC88",
    "warning": "#FFB800",
    "critical": "#FF4B4B",
    "border": "#262730"
}

# Custom CSS for Executive Dark Mode
st.markdown(f"""
<style>
    /* Global Dark Mode */
    .stApp {{
        background-color: {DARK_THEME['background']};
        color: {DARK_THEME['text']};
    }}
    
    /* Header Styling */
    .boardroom-header {{
        background: linear-gradient(135deg, #1E2128 0%, #2D3142 100%);
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid {DARK_THEME['accent']};
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    .boardroom-title {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {DARK_THEME['text']};
        margin: 0;
        letter-spacing: -0.5px;
    }}
    
    .boardroom-subtitle {{
        font-size: 1rem;
        color: #8B92A8;
        margin-top: 0.5rem;
    }}
    
    /* Live Connection Status */
    .status-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0.5rem 1rem;
        background: {DARK_THEME['secondary_bg']};
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }}
    
    .status-dot {{
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }}
    
    .status-live {{
        background: {DARK_THEME['success']};
    }}
    
    .status-offline {{
        background: #666;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    /* Visual Stage */
    .visual-stage {{
        background: {DARK_THEME['secondary_bg']};
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid {DARK_THEME['border']};
        min-height: 400px;
    }}
    
    /* Critical Alert Cards */
    .alert-card {{
        background: {DARK_THEME['secondary_bg']};
        border-left: 4px solid {DARK_THEME['critical']};
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    
    .alert-card.warning {{
        border-left-color: {DARK_THEME['warning']};
    }}
    
    .alert-card.info {{
        border-left-color: {DARK_THEME['success']};
    }}
    
    .alert-priority {{
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: {DARK_THEME['critical']};
    }}
    
    /* Metric Cards */
    .metric-card {{
        background: {DARK_THEME['secondary_bg']};
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid {DARK_THEME['border']};
        text-align: center;
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {DARK_THEME['accent']};
    }}
    
    .metric-label {{
        font-size: 0.9rem;
        color: #8B92A8;
        margin-top: 0.5rem;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {DARK_THEME['accent']} 0%, #CC3939 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 75, 75, 0.3);
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# AUDIO FUNCTIONS
# ============================================================================

def speak_script(text: str, lang: str = 'en', slow: bool = False) -> bool:
    """
    Convert text to speech and play it automatically.
    
    Uses gTTS (Google Text-to-Speech) and pygame for playback.
    
    Args:
        text: Speech script to convert
        lang: Language code (default 'en')
        slow: Slow speech rate (default False)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not AUDIO_AVAILABLE:
        st.warning("Audio features not available. Install: pip install gtts pygame")
        return False
    
    try:
        # Generate TTS audio
        tts = gTTS(text=text, lang=lang, slow=slow)
        
        # Save to temporary file
        audio_file = Path("temp_briefing.mp3")
        tts.save(str(audio_file))
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load and play audio
        pygame.mixer.music.load(str(audio_file))
        pygame.mixer.music.play()
        
        # Wait for playback to complete
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Cleanup
        pygame.mixer.quit()
        if audio_file.exists():
            audio_file.unlink()
        
        logger.info(f"Played audio briefing: {len(text)} chars")
        return True
        
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")
        st.error(f"Audio playback error: {e}")
        return False


def display_audio_player(text: str):
    """
    Display an audio player widget for manual playback.
    
    Fallback option if automatic playback fails.
    
    Args:
        text: Speech script to convert
    """
    if not AUDIO_AVAILABLE:
        st.info("📢 **Voice Briefing** (Audio not available):")
        st.markdown(f"*{text}*")
        return
    
    try:
        # Generate TTS audio
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        audio_file = Path("temp_briefing.mp3")
        tts.save(str(audio_file))
        
        # Display Streamlit audio player
        st.audio(str(audio_file), format='audio/mp3')
        
        # Cleanup
        if audio_file.exists():
            audio_file.unlink()
    
    except Exception as e:
        logger.error(f"Audio player generation failed: {e}")
        st.error(f"Could not generate audio: {e}")


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_metric_cards(metrics: List[Dict[str, Any]]):
    """
    Create visual metric cards for key KPIs.
    
    Args:
        metrics: List of dicts with 'label', 'value', 'delta' (optional)
    """
    cols = st.columns(len(metrics))
    
    for col, metric in zip(cols, metrics):
        with col:
            value = metric.get('value', 'N/A')
            label = metric.get('label', 'Metric')
            delta = metric.get('delta', None)
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if delta is not None:
                delta_color = DARK_THEME['success'] if delta >= 0 else DARK_THEME['critical']
                st.markdown(f"<div style='text-align: center; color: {delta_color}; font-size: 0.9rem;'>{delta:+.1%}</div>", unsafe_allow_html=True)


def create_placeholder_chart(chart_type: str = "bar") -> go.Figure:
    """
    Create a placeholder chart for the Visual Stage.
    
    Args:
        chart_type: Type of chart ('bar', 'line', 'scatter')
    
    Returns:
        go.Figure: Plotly figure
    """
    # Sample data
    df = pd.DataFrame({
        'Category': ['Q1', 'Q2', 'Q3', 'Q4'],
        'Value': [100, 120, 95, 140]
    })
    
    if chart_type == "bar":
        fig = px.bar(
            df, x='Category', y='Value',
            title='Quarterly Performance',
            color_discrete_sequence=[DARK_THEME['accent']]
        )
    elif chart_type == "line":
        fig = px.line(
            df, x='Category', y='Value',
            title='Trend Analysis',
            markers=True,
            color_discrete_sequence=[DARK_THEME['accent']]
        )
    else:
        fig = px.scatter(
            df, x='Category', y='Value',
            title='Distribution View',
            size='Value',
            color_discrete_sequence=[DARK_THEME['accent']]
        )
    
    # Dark theme styling
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor=DARK_THEME['secondary_bg'],
        paper_bgcolor=DARK_THEME['secondary_bg'],
        font=dict(color=DARK_THEME['text']),
        title_font_size=18,
        height=400
    )
    
    return fig


def render_visual_stage(query_results: Optional[Dict] = None):
    """
    Render the central Visual Stage with dynamic charts.
    
    Args:
        query_results: Results from CrewAI pipeline execution
    """
    st.markdown('<div class="visual-stage">', unsafe_allow_html=True)
    
    if query_results is None:
        # Placeholder state
        st.markdown("### 📊 Visual Stage")
        st.info("Run a query to generate visualizations from the ScientistAgent")
        
        # Show example chart
        fig = create_placeholder_chart("bar")
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Dynamic visualization from query results
        st.markdown("### 📊 Analysis Results")
        
        # Check if results contain chart data
        charts = query_results.get('charts', [])
        if charts:
            for chart_data in charts:
                fig = render_dynamic_chart(chart_data)
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback to table view
            if 'data' in query_results:
                df = pd.DataFrame(query_results['data'])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No visualization data available")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_dynamic_chart(chart_data: Dict[str, Any]) -> go.Figure:
    """
    Render a dynamic chart from chart data dictionary.
    
    Args:
        chart_data: Dictionary with 'type', 'data', 'title', 'labels'
    
    Returns:
        go.Figure: Plotly figure
    """
    chart_type = chart_data.get('type', 'bar')
    data = chart_data.get('data', {})
    title = chart_data.get('title', 'Analysis Chart')
    
    df = pd.DataFrame(data)
    
    if chart_type == "bar":
        x_col = chart_data.get('x', df.columns[0])
        y_col = chart_data.get('y', df.columns[1])
        fig = px.bar(df, x=x_col, y=y_col, title=title, color_discrete_sequence=[DARK_THEME['accent']])
    elif chart_type == "line":
        x_col = chart_data.get('x', df.columns[0])
        y_col = chart_data.get('y', df.columns[1])
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True, color_discrete_sequence=[DARK_THEME['accent']])
    elif chart_type == "scatter":
        x_col = chart_data.get('x', df.columns[0])
        y_col = chart_data.get('y', df.columns[1])
        fig = px.scatter(df, x=x_col, y=y_col, title=title, color_discrete_sequence=[DARK_THEME['accent']])
    elif chart_type == "histogram":
        fig = px.histogram(df, title=title, color_discrete_sequence=[DARK_THEME['accent']])
    else:
        # Default to table
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns)),
            cells=dict(values=[df[col] for col in df.columns])
        )])
    
    # Apply dark theme
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor=DARK_THEME['secondary_bg'],
        paper_bgcolor=DARK_THEME['secondary_bg'],
        font=dict(color=DARK_THEME['text']),
        title_font_size=18,
        height=400
    )
    
    return fig


# ============================================================================
# ALERT FUNCTIONS
# ============================================================================

def render_critical_alerts(alerts: List[Dict[str, Any]]):
    """
    Render critical alerts sidebar from Phase 3 Executive Agent.
    
    Args:
        alerts: List of alert dictionaries with 'priority', 'message', 'timestamp'
    """
    st.sidebar.markdown("### 🚨 Critical Alerts")
    
    if not alerts:
        st.sidebar.info("No critical alerts")
        return
    
    for alert in alerts[:5]:  # Top 5 alerts
        priority = alert.get('priority', 'medium').lower()
        message = alert.get('message', 'No details')
        timestamp = alert.get('timestamp', datetime.now().strftime('%H:%M'))
        
        # Determine alert class
        alert_class = "alert-card"
        if priority in ['critical', 'p1', 'high']:
            alert_class += " critical"
            emoji = "🔴"
        elif priority in ['warning', 'p2', 'medium']:
            alert_class += " warning"
            emoji = "⚠️"
        else:
            alert_class += " info"
            emoji = "ℹ️"
        
        st.sidebar.markdown(f"""
        <div class="{alert_class}">
            <div class="alert-priority">{emoji} {priority.upper()}</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">{message}</div>
            <div style="font-size: 0.75rem; color: #8B92A8; margin-top: 0.5rem;">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application for Executive Boardroom."""
    
    # ========================================================================
    # HEADER
    # ========================================================================
    
    st.markdown("""
    <div class="boardroom-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="boardroom-title">🎯 Executive Boardroom</h1>
                <p class="boardroom-subtitle">Voice-Powered Business Intelligence Dashboard</p>
            </div>
            <div class="status-indicator">
                <div class="status-dot status-live"></div>
                <span>Live Connection</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # SIDEBAR: ALERTS & CONFIG
    # ========================================================================
    
    st.sidebar.title("⚙️ Configuration")
    
    # Voice input toggle
    use_voice = st.sidebar.checkbox("Enable Voice Input", value=False, disabled=not VOICE_INPUT_AVAILABLE)
    if not VOICE_INPUT_AVAILABLE and use_voice:
        st.sidebar.warning("Voice input requires: pip install streamlit-mic-recorder")
    
    # Audio output toggle
    enable_audio = st.sidebar.checkbox("Enable Audio Briefing", value=AUDIO_AVAILABLE)
    
    # Briefing duration
    briefing_duration = st.sidebar.slider("Briefing Duration (seconds)", 30, 90, 45, 5)
    
    st.sidebar.divider()
    
    # Critical Alerts Section (Phase 3 integration)
    sample_alerts = [
        {"priority": "Critical", "message": "Revenue down 15% in EMEA region", "timestamp": "10:23"},
        {"priority": "High", "message": "Customer churn rate increased 8%", "timestamp": "09:45"},
        {"priority": "Medium", "message": "Supply chain delays detected", "timestamp": "08:12"}
    ]
    
    render_critical_alerts(sample_alerts)
    
    # ========================================================================
    # MAIN LAYOUT: QUERY INPUT
    # ========================================================================
    
    st.markdown("### 💬 Query Input")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if use_voice and VOICE_INPUT_AVAILABLE:
            # Voice input using mic_recorder
            st.info("🎤 Click microphone to record voice query")
            audio_data = mic_recorder(
                start_prompt="Start Recording",
                stop_prompt="Stop Recording",
                key="voice_recorder"
            )
            
            if audio_data:
                st.success("Voice recorded! (Voice-to-text not yet implemented - use text input below)")
                query = st.text_input("Or type your query:", placeholder="What are the Q3 revenue trends by region?")
            else:
                query = st.text_input("Or type your query:", placeholder="What are the Q3 revenue trends by region?")
        else:
            query = st.text_input("Enter your business intelligence query:", 
                                  placeholder="What are the Q3 revenue trends by region?")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        run_query = st.button("🚀 Execute", use_container_width=True)
    
    # ========================================================================
    # VISUAL STAGE
    # ========================================================================
    
    st.divider()
    
    # Initialize session state for results
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None
    if 'voice_script' not in st.session_state:
        st.session_state.voice_script = None
    
    # Execute query workflow
    if run_query and query:
        with st.spinner("🔄 Running CrewAI pipeline..."):
            try:
                # Initialize components
                llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)
                
                # Simulated query execution (replace with actual DataOpsManager call)
                st.info("📊 Executing multi-agent workflow...")
                
                # Phase 1-3 would run here via DataOpsManager
                # For now, simulate results
                query_results = {
                    'query': query,
                    'data': [
                        {'Region': 'NA', 'Q3_Revenue': 125000, 'Change': 0.08},
                        {'Region': 'EMEA', 'Q3_Revenue': 98000, 'Change': -0.15},
                        {'Region': 'APAC', 'Q3_Revenue': 110000, 'Change': 0.12}
                    ],
                    'charts': [{
                        'type': 'bar',
                        'data': {
                            'Region': ['NA', 'EMEA', 'APAC'],
                            'Revenue': [125000, 98000, 110000]
                        },
                        'title': 'Q3 Revenue by Region',
                        'x': 'Region',
                        'y': 'Revenue'
                    }],
                    'key_metrics': [125000, 98000, 110000]
                }
                
                st.session_state.query_results = query_results
                
                # Generate voice briefing (Phase 4)
                st.info("🎙️ Generating executive voice briefing...")
                
                briefing_context = {
                    'query': query,
                    'sql_results': {'rows': query_results['data']},
                    'key_metrics': query_results['key_metrics'],
                    'insights': "EMEA region shows significant decline of 15% requiring immediate attention. NA and APAC performing above expectations."
                }
                
                voice_script = generate_voice_brief(llm, briefing_context, duration=briefing_duration)
                st.session_state.voice_script = voice_script
                
                st.success("✅ Workflow complete!")
                
            except Exception as e:
                st.error(f"Error executing workflow: {e}")
                logger.error(f"Workflow execution error: {e}")
    
    # Render Visual Stage
    render_visual_stage(st.session_state.query_results)
    
    # ========================================================================
    # METRICS & AUDIO OUTPUT
    # ========================================================================
    
    if st.session_state.query_results:
        st.divider()
        
        # Key Metrics
        st.markdown("### 📈 Key Metrics")
        metrics = [
            {'label': 'NA Revenue', 'value': '$125K', 'delta': 0.08},
            {'label': 'EMEA Revenue', 'value': '$98K', 'delta': -0.15},
            {'label': 'APAC Revenue', 'value': '$110K', 'delta': 0.12}
        ]
        create_metric_cards(metrics)
    
    if st.session_state.voice_script:
        st.divider()
        
        # Voice Briefing Section
        st.markdown("### 🎙️ Executive Voice Briefing")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Script** ({briefing_duration}s target):")
            st.markdown(f"*{st.session_state.voice_script}*")
        
        with col2:
            if enable_audio and AUDIO_AVAILABLE:
                if st.button("▶️ Play Briefing", use_container_width=True):
                    with st.spinner("Playing audio..."):
                        speak_script(st.session_state.voice_script)
            else:
                st.info("Audio disabled or unavailable")
        
        # Audio player widget (always available)
        if AUDIO_AVAILABLE:
            display_audio_player(st.session_state.voice_script)
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    
    st.divider()
    st.markdown(f"""
    <div style="text-align: center; color: #8B92A8; font-size: 0.85rem;">
        DataGenie AI | Executive Boardroom v4.0 | Phase 4: Collaborative Boardroom<br>
        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
