"""
Monitoring Dashboard Component
===============================

Real-time monitoring dashboard for Autonomous Multi-Agent Business Intelligence System's Anomaly Sentry Agent.

Features:
- Live metric tracking with charts
- Anomaly alert display
- WebSocket connection for real-time updates
- Historical trend visualization
- Manual metric checks
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time
import os


class MonitoringDashboard:
    """Real-time monitoring dashboard component"""
    
    def __init__(self, api_base_url: str | None = None):
        self.api_base_url = (api_base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    
    def render(self):
        """Render the complete monitoring dashboard"""
        
        # Dashboard header with refresh
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("Monitor key business metrics in real-time and receive proactive alerts.")
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # Fetch recent alerts
        alerts = self._get_recent_alerts()
        monitoring_status = self._get_monitoring_status()
        
        # Top metrics row
        self._render_status_metrics(monitoring_status, alerts)
        
        st.markdown("---")
        
        # Alert feed
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🚨 Alert Feed")
            self._render_alert_feed(alerts)
        
        with col2:
            st.subheader("📊 Monitored Metrics")
            self._render_metric_list(monitoring_status)
        
        st.markdown("---")
        
        # Manual metric check
        st.subheader("🔍 Manual Metric Check")
        self._render_manual_check()
        
        st.markdown("---")
        
        # Metric trends (simulated)
        st.subheader("📈 Metric Trends")
        self._render_metric_trends()
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Fetch recent alerts from API"""
        try:
            response = requests.get(f"{self.api_base_url}/alerts/recent?limit=10", timeout=5)
            data = response.json()
            return data.get("alerts", [])
        except Exception as e:
            st.warning(f"Could not fetch alerts: {e}")
            return []
    
    def _get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status from health endpoint"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            data = response.json()
            return data.get("monitoring", {})
        except:
            return {}
    
    def _render_status_metrics(self, status: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """Render top-level status metrics"""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📊 Metrics Tracked",
                value=status.get("metrics_tracked", 0),
                help="Number of metrics being monitored"
            )
        
        with col2:
            total_alerts = len(alerts)
            st.metric(
                label="🚨 Total Alerts",
                value=total_alerts,
                help="Total alerts in history"
            )
        
        with col3:
            # Count critical alerts
            critical_count = sum(1 for a in alerts if a.get("severity") == "critical")
            st.metric(
                label="🔴 Critical",
                value=critical_count,
                delta=None,
                help="Critical severity alerts"
            )
        
        with col4:
            # Last alert time
            if alerts:
                last_alert = alerts[0].get("timestamp", "")
                try:
                    last_time = datetime.fromisoformat(last_alert.replace("Z", "+00:00"))
                    time_ago = (datetime.now() - last_time.replace(tzinfo=None)).seconds // 60
                    st.metric(
                        label="⏰ Last Alert",
                        value=f"{time_ago}m ago",
                        help="Time since last alert"
                    )
                except:
                    st.metric(label="⏰ Last Alert", value="N/A")
            else:
                st.metric(label="⏰ Last Alert", value="None")
    
    def _render_alert_feed(self, alerts: List[Dict[str, Any]]):
        """Render alert feed with details"""
        
        if not alerts:
            st.info("🎉 No anomalies detected! All metrics are within normal range.")
            return
        
        for alert in alerts[:5]:  # Show top 5
            severity = alert.get("severity", "info")
            
            # Severity styling
            severity_config = {
                "critical": {"icon": "🔴", "color": "#dc3545"},
                "warning": {"icon": "🟡", "color": "#ffc107"},
                "info": {"icon": "🔵", "color": "#17a2b8"}
            }
            
            config = severity_config.get(severity, severity_config["info"])
            
            # Alert card
            with st.container():
                st.markdown(f"""
                <div style="
                    background: white;
                    border-left: 4px solid {config['color']};
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin: 0; color: {config['color']};">
                        {config['icon']} {alert.get('metric_name', 'Unknown Metric')}
                    </h4>
                    <p style="margin: 0.5rem 0; color: #666;">
                        <strong>Deviation:</strong> {alert.get('deviation_percent', 0):+.1f}% 
                        | <strong>Current:</strong> {alert.get('current_value', 0):.2f}
                        | <strong>Baseline:</strong> {alert.get('baseline_value', 0):.2f}
                    </p>
                    <p style="margin: 0; font-size: 0.9em; color: #888;">
                        {alert.get('description', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable root cause analysis
                if alert.get("root_cause_analysis"):
                    with st.expander("💡 Root Cause Analysis"):
                        st.write(alert["root_cause_analysis"])
    
    def _render_metric_list(self, status: Dict[str, Any]):
        """Render list of monitored metrics"""
        
        # Default metrics (from Sentry Agent)
        default_metrics = [
            {"name": "daily_revenue", "label": "Daily Revenue", "icon": "💰"},
            {"name": "order_count", "label": "Order Count", "icon": "📦"},
            {"name": "average_order_value", "label": "Avg Order Value", "icon": "💵"},
            {"name": "new_customers", "label": "New Customers", "icon": "👥"},
            {"name": "top_product_sales", "label": "Product Sales", "icon": "🛍️"}
        ]
        
        for metric in default_metrics:
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 0.8rem;
                margin: 0.3rem 0;
                border-radius: 5px;
                border-left: 3px solid #667eea;
            ">
                {metric['icon']} <strong>{metric['label']}</strong><br>
                <small style="color: #666;">{metric['name']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_manual_check(self):
        """Render manual metric check interface"""
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            metric_name = st.selectbox(
                "Select metric to check:",
                ["daily_revenue", "order_count", "average_order_value", "new_customers", "top_product_sales"],
                help="Choose a metric for immediate analysis"
            )
        
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            check_btn = st.button("🔍 Check Now", type="primary", use_container_width=True)
        
        if check_btn:
            with st.spinner(f"Checking {metric_name}..."):
                result = self._trigger_manual_check(metric_name)
                
                if result:
                    if result.get("status") == "anomaly_detected":
                        alert = result.get("alert", {})
                        st.error(f"🚨 Anomaly Detected in {metric_name}!")
                        st.metric(
                            label="Deviation",
                            value=f"{alert.get('deviation_percent', 0):+.1f}%",
                            delta=f"{alert.get('current_value', 0):.2f} vs {alert.get('baseline_value', 0):.2f} baseline"
                        )
                    else:
                        st.success(f"✅ {metric_name} is within normal range")
    
    def _trigger_manual_check(self, metric_name: str) -> Dict[str, Any]:
        """Trigger manual metric check via API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/alerts/check/{metric_name}",
                timeout=10
            )
            return response.json()
        except Exception as e:
            st.error(f"Check failed: {e}")
            return {}
    
    def _render_metric_trends(self):
        """Render metric trend visualizations (simulated data)"""
        
        # Create sample trend data
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14, -1, -1)]
        
        # Simulated data for demo
        revenue_data = [9800, 10200, 9900, 10500, 10800, 11200, 10900, 11500, 12000, 11800, 12200, 12500, 13000, 15000, 14500]
        orders_data = [120, 125, 118, 130, 135, 140, 136, 142, 150, 148, 152, 155, 160, 180, 175]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Daily Revenue Trend", "Order Count Trend"),
            vertical_spacing=0.15
        )
        
        # Revenue chart
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=revenue_data,
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#667eea', width=2),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Add baseline
        baseline_revenue = sum(revenue_data[:-1]) / len(revenue_data[:-1])
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[baseline_revenue] * len(dates),
                mode='lines',
                name='7-day Baseline',
                line=dict(color='#ffc107', width=2, dash='dash')
            ),
            row=1, col=1
        )
        
        # Orders chart
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=orders_data,
                mode='lines+markers',
                name='Orders',
                line=dict(color='#28a745', width=2),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        # Add baseline
        baseline_orders = sum(orders_data[:-1]) / len(orders_data[:-1])
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[baseline_orders] * len(dates),
                mode='lines',
                name='7-day Baseline',
                line=dict(color='#ffc107', width=2, dash='dash')
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Revenue ($)", row=1, col=1)
        fig.update_yaxes(title_text="Orders", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Anomaly indicators
        st.caption("🔴 = Critical | 🟡 = Warning | 🟢 = Normal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue status
            current_rev = revenue_data[-1]
            deviation_rev = ((current_rev - baseline_revenue) / baseline_revenue) * 100
            
            if abs(deviation_rev) > 50:
                st.error(f"🔴 Revenue: {deviation_rev:+.1f}% deviation (CRITICAL)")
            elif abs(deviation_rev) > 20:
                st.warning(f"🟡 Revenue: {deviation_rev:+.1f}% deviation (WARNING)")
            else:
                st.success(f"🟢 Revenue: {deviation_rev:+.1f}% deviation (NORMAL)")
        
        with col2:
            # Orders status
            current_orders = orders_data[-1]
            deviation_orders = ((current_orders - baseline_orders) / baseline_orders) * 100
            
            if abs(deviation_orders) > 50:
                st.error(f"🔴 Orders: {deviation_orders:+.1f}% deviation (CRITICAL)")
            elif abs(deviation_orders) > 20:
                st.warning(f"🟡 Orders: {deviation_orders:+.1f}% deviation (WARNING)")
            else:
                st.success(f"🟢 Orders: {deviation_orders:+.1f}% deviation (NORMAL)")


# ============================================================================
# Standalone Usage Example
# ============================================================================

def example_usage():
    """Example of using MonitoringDashboard"""
    
    st.title("Monitoring Dashboard Example")
    
    dashboard = MonitoringDashboard()
    dashboard.render()


if __name__ == "__main__":
    example_usage()
