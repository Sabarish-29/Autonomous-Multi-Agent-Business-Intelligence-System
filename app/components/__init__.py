"""
Autonomous Multi-Agent Business Intelligence System - UI Components Package
======================================

Reusable Streamlit components for the Autonomous Multi-Agent Business Intelligence System dashboard.
"""

from .agent_trace import AgentTraceViewer
from .monitoring_dashboard import MonitoringDashboard

__all__ = [
    'AgentTraceViewer',
    'MonitoringDashboard'
]

__version__ = '2.0.4'
