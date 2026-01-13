"""
Autonomous Multi-Agent Business Intelligence System - Phase 4 API with WebSocket Alerts

This file demonstrates how to integrate:
- CrewAI hierarchical multi-agent system
- Anomaly Sentry with proactive alerts
- Researcher Agent for external context
- WebSocket real-time alert broadcasting
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any
import math
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from src.agents.librarian import LibrarianAgent
from src.agents.crewai_manager import DataOpsManager, BusinessGlossary
from src.agents.sentry import AnomalySentryAgent, AnomalyAlert

# Load environment variables (use repo-root .env regardless of process CWD)
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Autonomous Multi-Agent Business Intelligence System - Phase 4",
    description="Hierarchical Multi-Agent SQL Generation with Proactive Monitoring & Research",
    version="2.0.4"
)

# Global instances (initialized on startup)
librarian_agent: Optional[LibrarianAgent] = None
business_glossary: Optional[BusinessGlossary] = None
dataops_manager: Optional[DataOpsManager] = None
sentry_agent: Optional[AnomalySentryAgent] = None

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for alert broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_alert(self, alert: AnomalyAlert):
        """Broadcast alert to all connected clients"""
        message = alert.to_dict()
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send alert to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

manager = ConnectionManager()


class QueryRequest(BaseModel):
    """Request model for SQL generation."""
    query: str
    database: str = "default"
    use_crewai: bool = True
    enable_research: bool = False  # Phase 4: Enable external research


class AnalyticsRequest(BaseModel):
    """Request model for analytics workflow."""
    query: str
    database: str = "default"


class ResearchRequest(BaseModel):
    """Request model for unified research workflow."""
    query: str
    database: str = "default"
    force_research: bool = False


class QueryResponse(BaseModel):
    """Response model for SQL generation."""
    sql: str
    confidence: float
    method: str
    explanation: Optional[str] = None
    agents_involved: Optional[list] = None
    # Back-compat / E2E fields
    context: Optional[str] = None
    schema_context: Optional[str] = None
    attempts: Optional[int] = None
    pii_detected: Optional[bool] = None
    pii_risk_level: Optional[str] = None
    pii_info: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """
    Initialize all components on application startup.
    """
    global librarian_agent, business_glossary, dataops_manager, sentry_agent
    
    logger.info("Initializing Autonomous Multi-Agent Business Intelligence System Phase 4...")
    
    # 1. Initialize Librarian Agent
    try:
        librarian_agent = LibrarianAgent(
            db_path="./data/schema_library",
            use_chroma=(os.getenv("DATAGENIE_TEST_MODE") != "1"),
        )
        logger.info("✅ Librarian Agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Librarian Agent: {e}")
        librarian_agent = None
    
    # 2. Initialize Business Glossary
    try:
        business_glossary = BusinessGlossary(glossary_path="./configs/business_glossary.yaml")
        logger.info("✅ Business Glossary loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load Business Glossary: {e}")
        business_glossary = None
    
    # 3. Initialize DataOps Manager (CrewAI)
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        if librarian_agent and business_glossary:
            # Default to a smaller/cheaper model to avoid Groq TPD exhaustion in demos.
            # Opt into the bigger model via env when you have the quota.
            use_large = os.getenv("DATAGENIE_USE_LARGE_GROQ_MODEL") == "1"
            default_model = "llama-3.3-70b-versatile" if use_large else "llama-3.1-8b-instant"
            dataops_manager = DataOpsManager(
                llm_api_key=groq_api_key,
                librarian_agent=librarian_agent,
                business_glossary=business_glossary,
                model_name=os.getenv("GROQ_MODEL", default_model),
                reasoning_provider=os.getenv("CREWAI_REASONING_PROVIDER", "auto"),
                reasoning_model=os.getenv("OPENAI_REASONING_MODEL", "o1"),
            )
            logger.info("✅ DataOps Manager (CrewAI) initialized")
        else:
            logger.warning("⚠️ Skipping DataOps Manager - dependencies not initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize DataOps Manager: {e}")
        dataops_manager = None
    
    # 4. Initialize Anomaly Sentry (Phase 4)
    try:
        async def alert_callback(alert: AnomalyAlert):
            """Callback to broadcast alerts via WebSocket"""
            logger.warning(f"🚨 Broadcasting alert: {alert.metric_name}")
            await manager.broadcast_alert(alert)
        
        sentry_agent = AnomalySentryAgent(
            database_uri=(
                os.getenv("SQLALCHEMY_DB_URL")
                or os.getenv("DATABASE_URL")
                or "sqlite:///data/sample/sales_db.sqlite"
            ),
            check_interval_minutes=5,  # Check every 5 minutes
            alert_callback=alert_callback
        )
        
        # Start background monitoring
        await sentry_agent.start()
        logger.info("✅ Anomaly Sentry Agent started (monitoring every 5 minutes)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry Agent: {e}")
        sentry_agent = None
    
    logger.info("🚀 Autonomous Multi-Agent Business Intelligence System Phase 4 startup complete!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global sentry_agent
    
    if sentry_agent:
        await sentry_agent.stop()
        logger.info("Anomaly Sentry stopped")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Autonomous Multi-Agent Business Intelligence System - Phase 4",
        "version": "2.0.4",
        "features": [
            "Hierarchical Multi-Agent System (CrewAI)",
            "Semantic Schema Retrieval (Librarian Agent)",
            "Business Glossary Integration",
            "Self-Healing SQL Loop (Critic Agent)",
            "Python Analytics Sandbox (Data Scientist)",
            "Proactive Anomaly Monitoring (Sentry Agent)",
            "External Research Integration (Tavily API)",
            "Real-time WebSocket Alerts"
        ]
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint showing status of all components.
    """
    return {
        "status": "healthy",
        "components": {
            "librarian_agent": librarian_agent is not None,
            "business_glossary": business_glossary is not None,
            "dataops_manager": dataops_manager is not None,
            "sentry_agent": sentry_agent is not None and sentry_agent.is_running,
            "websocket_connections": len(manager.active_connections)
        },
        "version": "2.0.4",
        "monitoring": {
            "metrics_tracked": len(sentry_agent.metrics) if sentry_agent else 0,
            "recent_alerts": len(sentry_agent.alert_history) if sentry_agent else 0
        }
    }


@app.post("/query", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    """
    Generate SQL from natural language query using CrewAI hierarchical process.
    
    Args:
        request: Query request with natural language query and options
        
    Returns:
        Generated SQL with metadata
    """
    try:
        if not dataops_manager:
            raise HTTPException(
                status_code=503,
                detail="DataOps Manager not initialized. Check logs for startup errors."
            )
        
        logger.info(f"Received query: {request.query}")
        
        # Generate SQL using CrewAI hierarchical process
        result = dataops_manager.generate_sql_hierarchical(
            user_query=request.query,
            database=request.database
        )
        
        if result.get('error'):
            if result.get("error_type") == "rate_limit":
                retry_after = result.get("retry_after_seconds")
                headers = {}
                if isinstance(retry_after, (int, float)) and retry_after > 0:
                    headers["Retry-After"] = str(int(math.ceil(float(retry_after))))
                raise HTTPException(
                    status_code=429,
                    detail=f"LLM rate-limited. {result['error']}",
                    headers=headers or None,
                )

            raise HTTPException(
                status_code=500,
                detail=f"SQL generation failed: {result['error']}"
            )
        
        return QueryResponse(
            sql=result.get('sql', ''),
            confidence=result.get('confidence', 0.0),
            method=result.get('method', 'crewai_hierarchical'),
            explanation=result.get('enriched_context'),
            agents_involved=result.get('agents_involved', []),
            # E2E/back-compat fields
            context=result.get('schema_context') or result.get('enriched_context'),
            schema_context=result.get('schema_context'),
            attempts=result.get('attempts'),
            pii_detected=result.get('pii_detected'),
            pii_risk_level=result.get('pii_risk_level'),
            pii_info={
                'pii_types': result.get('detections') or [],
                'risk_level': result.get('risk_level') or result.get('pii_risk_level'),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schema/index")
async def index_schema(
    table_name: str,
    schema_definition: str,
    columns: list,
    metadata: Optional[dict] = None
):
    """
    Index a new table schema into the Librarian's knowledge base.
    
    Args:
        table_name: Name of the table
        schema_definition: CREATE TABLE statement or description
        columns: List of column definitions
        metadata: Optional metadata
        
    Returns:
        Success status
    """
    try:
        if not librarian_agent:
            raise HTTPException(
                status_code=503,
                detail="Librarian Agent not initialized"
            )
        
        success = librarian_agent.index_table_schema(
            table_name=table_name,
            schema_definition=schema_definition,
            columns=columns,
            metadata=metadata
        )
        
        if success:
            return {"status": "success", "message": f"Schema indexed for table: {table_name}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to index schema")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema/tables")
async def list_tables():
    """
    List all tables indexed in the Librarian's knowledge base.
    
    Returns:
        List of table names
    """
    try:
        if not librarian_agent:
            raise HTTPException(
                status_code=503,
                detail="Librarian Agent not initialized"
            )
        
        tables = librarian_agent.list_all_tables()
        return {"tables": tables, "count": len(tables)}
        
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/glossary/term/{term}")
async def get_business_term(term: str):
    """
    Get definition for a specific business term.
    
    Args:
        term: Business term name
        
    Returns:
        Term definition and SQL logic
    """
    try:
        if not business_glossary:
            raise HTTPException(
                status_code=503,
                detail="Business Glossary not initialized"
            )
        
        definition = business_glossary.get_term_definition(term)
        
        if definition:
            return {
                "term": term,
                "definition": definition.get('description'),
                "sql_logic": definition.get('sql_logic'),
                "related_tables": definition.get('related_tables', []),
                "related_columns": definition.get('related_columns', [])
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Business term '{term}' not found in glossary"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving business term: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/analytics")
async def query_with_analytics(request: QueryRequest):
    """
    Process natural language query with analytics capabilities (Phase 3).
    
    Automatically detects analytics intent and performs:
    - SQL generation & validation (Phase 1+2)
    - SQL execution
    - Statistical analysis (forecast, correlation, anomaly, summary)
    - Visualization generation (Plotly JSON)
    
    Args:
        request: QueryRequest with query and database
        
    Returns:
        Complete analytics result with SQL, data, analysis, and visualization
    """
    try:
        if not dataops_manager:
            raise HTTPException(
                status_code=503,
                detail="DataOps Manager not initialized. Check logs for startup errors."
            )
        
        logger.info(f"Analytics query received: {request.query}")
        
        # Generate SQL with analytics
        result = dataops_manager.generate_with_analytics(
            query=request.query,
            database=request.database if request.database != "default" else "sqlite:///data/sample/sample.db"
        )
        
        if result.get('error'):
            raise HTTPException(
                status_code=500,
                detail=f"Analytics workflow failed: {result['error']}"
            )
        
        return {
            "sql": result.get('sql'),
            "confidence": result.get('confidence'),
            "data": result.get('data'),
            "analytics_performed": result.get('analytics_performed', False),
            "analytics_type": result.get('analytics_type'),
            "analysis_result": result.get('analysis_result'),
            "visualization": result.get('visualization'),  # Plotly JSON
            "method": result.get('method'),
            "validation": result.get('validation')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing analytics query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 4 ENDPOINTS: Sentry Alerts & Research Integration
# ============================================================================

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for receiving real-time anomaly alerts.
    
    Clients connect to this endpoint to receive proactive alerts when the
    Anomaly Sentry detects unusual patterns in key business metrics.
    
    Message Format:
    {
        "metric_name": "daily_revenue",
        "current_value": 15000.0,
        "baseline_value": 10000.0,
        "deviation_percent": 50.0,
        "severity": "warning",
        "timestamp": "2024-01-11T10:30:00",
        "description": "...",
        "root_cause_analysis": "..."
    }
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to Autonomous Multi-Agent Business Intelligence System Alert System",
            "monitoring": {
                "metrics": len(sentry_agent.metrics) if sentry_agent else 0,
                "check_interval_minutes": sentry_agent.check_interval if sentry_agent else 0
            }
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()
                
                # Echo back for heartbeat
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@app.get("/alerts/recent")
async def get_recent_alerts(limit: int = 10):
    """
    Get recent anomaly alerts.
    
    Args:
        limit: Maximum number of alerts to return (default 10)
        
    Returns:
        List of recent alerts with details
    """
    try:
        if not sentry_agent:
            raise HTTPException(
                status_code=503,
                detail="Sentry Agent not initialized"
            )
        
        alerts = sentry_agent.get_recent_alerts(limit=limit)
        
        return {
            "count": len(alerts),
            "alerts": alerts,
            "monitoring_status": {
                "is_running": sentry_agent.is_running,
                "metrics_tracked": len(sentry_agent.metrics),
                "check_interval_minutes": sentry_agent.check_interval
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/check/{metric_name}")
async def manual_metric_check(metric_name: str):
    """
    Manually trigger a check for a specific metric.
    
    Args:
        metric_name: Name of the metric to check (e.g., "daily_revenue")
        
    Returns:
        Alert if anomaly detected, or status message
    """
    try:
        if not sentry_agent:
            raise HTTPException(
                status_code=503,
                detail="Sentry Agent not initialized"
            )
        
        logger.info(f"Manual check requested for metric: {metric_name}")
        
        alert = await sentry_agent.manual_check(metric_name)
        
        if alert:
            # Broadcast to WebSocket clients
            await manager.broadcast_alert(alert)
            
            return {
                "status": "anomaly_detected",
                "alert": alert.to_dict()
            }
        else:
            return {
                "status": "normal",
                "message": f"Metric '{metric_name}' is within normal range",
                "metric": metric_name
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/research")
async def query_with_research(request: ResearchRequest):
    """
    PHASE 4: Process query with unified internal + external research.
    
    This endpoint:
    1. Analyzes internal database (SQL generation & execution)
    2. Optionally fetches external market data via Tavily Search
    3. Synthesizes unified insights combining both sources
    
    Use when you need to:
    - Compare internal metrics to market benchmarks
    - Understand external factors affecting business
    - Validate internal findings with industry data
    
    Args:
        request: ResearchRequest with query and options
        
    Returns:
        Unified report with SQL results, external research, and combined insights
    """
    try:
        if not dataops_manager:
            raise HTTPException(
                status_code=503,
                detail="DataOps Manager not initialized"
            )
        
        logger.info(f"Research query received: {request.query}")
        
        # Check if Tavily API key is configured
        if not os.getenv("TAVILY_API_KEY"):
            logger.warning("TAVILY_API_KEY not set - research will be limited")
        
        # Generate SQL with optional external research
        result = dataops_manager.generate_with_research(
            query=request.query,
            database=request.database if request.database != "default" else "sqlite:///data/sample/sample.db",
            force_research=request.force_research
        )
        
        if result.get('error'):
            raise HTTPException(
                status_code=500,
                detail=f"Research workflow failed: {result['error']}"
            )
        
        return {
            "sql": result.get('sql'),
            "data": result.get('data'),
            "internal_findings": result.get('internal_findings'),
            "external_research": result.get('external_research'),
            "unified_insights": result.get('unified_insights'),
            "research_performed": result.get('research_performed', False),
            "method": result.get('method'),
            # E2E/back-compat alias fields
            "research": result.get('external_research'),
            "insights": result.get('unified_insights'),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing research query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 6: Report Generation Endpoints
# ============================================================================

class ReportRequest(BaseModel):
    """Request model for report generation"""
    query: str
    sql_result: Dict[str, Any]
    analytics_result: Optional[Dict[str, Any]] = None
    research_result: Optional[Dict[str, Any]] = None
    formats: List[str] = ["pdf", "pptx"]


@app.post("/reports/generate")
def generate_reports(request: ReportRequest):
    """
    Generate professional reports (PDF and/or PPTX)
    
    Phase 6 endpoint that uses the Reporter Agent to create
    comprehensive reports from query results.
    
    Returns:
        Dictionary mapping format to file path
    """
    try:
        if not dataops_manager:
            raise HTTPException(
                status_code=503,
                detail="DataOps Manager not initialized"
            )
        
        logger.info(f"Report generation requested for formats: {request.formats}")
        
        # Generate reports using CrewAI Manager
        report_paths = dataops_manager.download_report(
            query=request.query,
            sql_result=request.sql_result,
            analytics_result=request.analytics_result,
            research_result=request.research_result,
            formats=request.formats
        )
        
        if report_paths.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Report generation failed: {report_paths['error']}"
            )
        
        return report_paths
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/guardrails/summary")
def get_guardrails_summary():
    """
    Get PII protection summary
    
    Phase 6 endpoint that returns statistics about PII detection
    and redaction activity.
    """
    try:
        if not dataops_manager:
            raise HTTPException(
                status_code=503,
                detail="DataOps Manager not initialized"
            )
        
        summary = dataops_manager.guardrails.get_guardrails_summary()
        return {
            "status": "active",
            "summary": summary,
            "pii_protection": "enabled"
        }
        
    except Exception as e:
        logger.error(f"Error getting guardrails summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
