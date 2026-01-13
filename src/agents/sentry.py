"""
Anomaly Sentry Agent for Autonomous Multi-Agent Business Intelligence System Phase 4
==============================================

Background monitoring service that continuously checks key database metrics
and triggers proactive alerts when anomalies are detected.

Features:
- Scheduled metric monitoring (APScheduler)
- 7-day rolling average baseline computation
- >20% deviation detection
- WebSocket alert broadcasting
- Root Cause Analysis task triggering
- Configurable metrics and thresholds

Author: Sabarish-29
Version: 2.0.4
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
from sqlalchemy import create_engine, text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricDefinition:
    """Defines a monitored metric"""
    name: str
    query: str
    description: str
    threshold_percent: float = 20.0  # Default 20% deviation
    rolling_window_days: int = 7


@dataclass
class AnomalyAlert:
    """Represents a detected anomaly"""
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_percent: float
    severity: AlertSeverity
    timestamp: datetime
    description: str
    root_cause_analysis: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat()
        }


class AnomalySentryAgent:
    """
    Background monitoring agent that detects anomalies in database metrics
    and triggers proactive alerts.
    """

    def __init__(
        self,
        database_uri: str = "sqlite:///data/sample/sales_db.sqlite",
        check_interval_minutes: int = 5,
        alert_callback: Optional[Callable] = None
    ):
        """
        Initialize the Sentry Agent.

        Args:
            database_uri: Database connection string
            check_interval_minutes: How often to check metrics
            alert_callback: Async function to call when alert is detected
        """
        self.database_uri = database_uri
        self.check_interval = check_interval_minutes
        self.alert_callback = alert_callback
        self.engine = create_engine(database_uri)
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

        # Define key metrics to monitor
        self.metrics = self._define_default_metrics()

        # Alert history
        self.alert_history: List[AnomalyAlert] = []

        logger.info(f"🔍 Anomaly Sentry initialized with {len(self.metrics)} metrics")

    def _define_default_metrics(self) -> List[MetricDefinition]:
        """
        Define the 3-5 key metrics to monitor.
        These can be customized based on business needs.
        """
        return [
            MetricDefinition(
                name="daily_revenue",
                query="""
                    SELECT DATE(sale_date) as date, SUM(revenue) as value
                    FROM sales
                    WHERE sale_date >= DATE('now', '-14 days')
                    GROUP BY DATE(sale_date)
                    ORDER BY date DESC
                """,
                description="Total daily revenue from sales transactions"
            ),
            MetricDefinition(
                name="sales_count",
                query="""
                    SELECT DATE(sale_date) as date, COUNT(*) as value
                    FROM sales
                    WHERE sale_date >= DATE('now', '-14 days')
                    GROUP BY DATE(sale_date)
                    ORDER BY date DESC
                """,
                description="Number of sales transactions per day"
            ),
            MetricDefinition(
                name="average_transaction_value",
                query="""
                    SELECT DATE(sale_date) as date, AVG(revenue) as value
                    FROM sales
                    WHERE sale_date >= DATE('now', '-14 days')
                    GROUP BY DATE(sale_date)
                    ORDER BY date DESC
                """,
                description="Average revenue per sales transaction"
            ),
            MetricDefinition(
                name="new_customers",
                query="""
                    SELECT DATE(created_date) as date, COUNT(*) as value
                    FROM customers
                    WHERE created_date >= DATE('now', '-14 days')
                    GROUP BY DATE(created_date)
                    ORDER BY date DESC
                """,
                description="Number of new customer registrations per day",
                threshold_percent=30.0  # More volatile, higher threshold
            ),
            MetricDefinition(
                name="units_sold",
                query="""
                    SELECT DATE(sale_date) as date, SUM(quantity) as value
                    FROM sales
                    WHERE sale_date >= DATE('now', '-14 days')
                    GROUP BY DATE(sale_date)
                    ORDER BY date DESC
                """,
                description="Total units sold per day"
            )
        ]

    async def start(self):
        """Start the background monitoring service"""
        if self.is_running:
            logger.warning("⚠️ Sentry is already running")
            return

        logger.info(f"🚀 Starting Anomaly Sentry (checking every {self.check_interval} minutes)")

        # Schedule periodic checks
        self.scheduler.add_job(
            self._check_all_metrics,
            trigger=IntervalTrigger(minutes=self.check_interval),
            id='metric_check',
            name='Check all metrics for anomalies',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        # Run initial check
        await self._check_all_metrics()

    async def stop(self):
        """Stop the monitoring service"""
        if not self.is_running:
            return

        logger.info("🛑 Stopping Anomaly Sentry")
        self.scheduler.shutdown(wait=False)
        self.is_running = False

    async def _check_all_metrics(self):
        """Check all defined metrics for anomalies"""
        logger.info("🔍 Checking all metrics for anomalies...")

        for metric in self.metrics:
            try:
                alert = await self._check_metric(metric)
                if alert:
                    await self._handle_alert(alert)
            except Exception as e:
                logger.error(f"❌ Error checking metric '{metric.name}': {e}")

    async def _check_metric(self, metric: MetricDefinition) -> Optional[AnomalyAlert]:
        """
        Check a single metric for anomalies.

        Args:
            metric: Metric definition to check

        Returns:
            AnomalyAlert if anomaly detected, None otherwise
        """
        try:
            # Execute query
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(metric.query), conn)

            if df.empty or len(df) < metric.rolling_window_days:
                logger.debug(f"⏭️ Insufficient data for '{metric.name}' (need {metric.rolling_window_days} days)")
                return None

            # Get current value (most recent day)
            current_value = float(df.iloc[0]['value'])

            # Calculate baseline (7-day rolling average, excluding today)
            baseline_values = df.iloc[1:metric.rolling_window_days + 1]['value']
            baseline_avg = float(baseline_values.mean())

            # Calculate deviation
            if baseline_avg == 0:
                deviation_percent = 0.0
            else:
                deviation_percent = ((current_value - baseline_avg) / baseline_avg) * 100

            # Check if deviation exceeds threshold
            if abs(deviation_percent) > metric.threshold_percent:
                severity = self._determine_severity(abs(deviation_percent))

                alert = AnomalyAlert(
                    metric_name=metric.name,
                    current_value=current_value,
                    baseline_value=baseline_avg,
                    deviation_percent=deviation_percent,
                    severity=severity,
                    timestamp=datetime.now(),
                    description=f"{metric.description}: {deviation_percent:+.1f}% deviation detected"
                )

                logger.warning(
                    f"🚨 ANOMALY DETECTED in '{metric.name}': "
                    f"Current={current_value:.2f}, Baseline={baseline_avg:.2f}, "
                    f"Deviation={deviation_percent:+.1f}%"
                )

                return alert

            logger.debug(f"✅ '{metric.name}' is within normal range ({deviation_percent:+.1f}%)")
            return None

        except Exception as e:
            logger.error(f"❌ Error checking metric '{metric.name}': {e}")
            return None

    def _determine_severity(self, deviation_percent: float) -> AlertSeverity:
        """Determine alert severity based on deviation magnitude"""
        if deviation_percent > 50:
            return AlertSeverity.CRITICAL
        elif deviation_percent > 30:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    async def _handle_alert(self, alert: AnomalyAlert):
        """
        Handle a detected anomaly alert.

        Actions:
        1. Store in alert history
        2. Trigger root cause analysis (if critical)
        3. Call alert callback (broadcast to UI via WebSocket)
        """
        # Store in history
        self.alert_history.append(alert)

        # Trigger root cause analysis for critical alerts
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.WARNING]:
            logger.info(f"🔬 Triggering root cause analysis for '{alert.metric_name}'...")
            root_cause = await self._perform_root_cause_analysis(alert)
            alert.root_cause_analysis = root_cause

        # Broadcast alert via callback (WebSocket)
        if self.alert_callback:
            try:
                await self.alert_callback(alert)
            except Exception as e:
                logger.error(f"❌ Error calling alert callback: {e}")

    async def _perform_root_cause_analysis(self, alert: AnomalyAlert) -> str:
        """
        Perform automated root cause analysis for an anomaly.

        This is a simplified version. In a full implementation, this would:
        1. Query related metrics
        2. Check for correlations
        3. Use the CrewAI Manager to generate insights
        4. Potentially trigger the Researcher Agent for external context

        Args:
            alert: The anomaly alert to analyze

        Returns:
            Root cause analysis summary
        """
        # Placeholder implementation
        # TODO: Integrate with CrewAI Manager for deep analysis

        analysis_parts = [
            f"Detected {alert.deviation_percent:+.1f}% deviation in {alert.metric_name}.",
            f"Current value: {alert.current_value:.2f}",
            f"7-day baseline: {alert.baseline_value:.2f}"
        ]

        # Simple heuristics
        if alert.deviation_percent < 0:
            analysis_parts.append("⚠️ Metric is trending DOWN. Possible causes: decreased demand, operational issues, or seasonal effects.")
        else:
            analysis_parts.append("📈 Metric is trending UP. Possible causes: successful campaign, seasonal spike, or data quality issue.")

        return " | ".join(analysis_parts)

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts for UI display"""
        recent = sorted(self.alert_history, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [alert.to_dict() for alert in recent]

    def add_custom_metric(self, metric: MetricDefinition):
        """Add a custom metric to monitor"""
        self.metrics.append(metric)
        logger.info(f"➕ Added custom metric: {metric.name}")

    async def manual_check(self, metric_name: str) -> Optional[AnomalyAlert]:
        """Manually trigger a check for a specific metric"""
        metric = next((m for m in self.metrics if m.name == metric_name), None)
        if not metric:
            logger.error(f"❌ Metric '{metric_name}' not found")
            return None

        return await self._check_metric(metric)


# ============================================================================
# CrewAI Integration Functions
# ============================================================================

def create_sentry_monitoring_task(sentry: AnomalySentryAgent, metric_name: str):
    """
    Factory function to create CrewAI tasks for manual metric checks.

    This allows the Manager Agent to explicitly request metric checks
    when users ask questions like "Are there any anomalies in revenue?"
    """
    from crewai import Task

    description = f"""
    Check the '{metric_name}' metric for anomalies using the Anomaly Sentry Agent.

    The Sentry will:
    1. Query the last 14 days of data for {metric_name}
    2. Calculate the 7-day rolling average baseline
    3. Compare current value to baseline
    4. Report any deviations >20%

    If an anomaly is detected, provide:
    - Current value vs. baseline
    - Percentage deviation
    - Severity level
    - Initial root cause hypothesis
    """

    expected_output = f"""
    A detailed anomaly report for {metric_name} including:
    - Status: NORMAL or ANOMALY
    - Current metric value
    - Baseline (7-day average)
    - Deviation percentage
    - Severity if anomaly detected
    - Root cause analysis if critical
    """

    return Task(
        description=description,
        expected_output=expected_output,
        agent=None  # Will be assigned by Manager
    )


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """Example of using the Anomaly Sentry Agent"""

    # Define alert callback
    async def alert_handler(alert: AnomalyAlert):
        print(f"\n🚨 ALERT RECEIVED:")
        print(f"   Metric: {alert.metric_name}")
        print(f"   Severity: {alert.severity.value.upper()}")
        print(f"   Deviation: {alert.deviation_percent:+.1f}%")
        print(f"   Analysis: {alert.root_cause_analysis}")

    # Initialize sentry
    sentry = AnomalySentryAgent(
        database_uri="sqlite:///data/sample/sample.db",
        check_interval_minutes=5,
        alert_callback=alert_handler
    )

    # Start monitoring
    await sentry.start()

    # Keep running (in production, this would be in the main event loop)
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        await sentry.stop()


if __name__ == "__main__":
    asyncio.run(example_usage())
