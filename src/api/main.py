"""
Autonomous Multi-Agent Business Intelligence System - FastAPI Application

Main API entry point with all endpoints.
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..config import settings
from ..llm.router import get_llm_router, LLMRouter
from ..nlp.ner_extractor import NERExtractor
from ..nlp.intent_classifier import IntentClassifier
from ..rag.vector_store import VectorStore
from ..text_to_sql.generator import TextToSQLGenerator

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str = Field(..., description="Natural language query")
    database: str = Field(default="default", description="Target database")
    use_rag: bool = Field(default=True, description="Use RAG for context")
    validate_sql: bool = Field(default=True, description="Validate generated SQL")
    agentic: bool = Field(default=False, description="Enable agentic orchestration pipeline")


class QueryResponse(BaseModel):
    """Response model for query processing."""
    sql: str
    confidence: float
    explanation: str
    complexity: str
    entities: List[Dict[str, Any]]
    intent: Dict[str, Any]
    cost_estimate: float
    provider: str
    validation_status: str
    validation_errors: List[str]
    plan: Optional[Dict[str, Any]] = None
    insights: Optional[Dict[str, Any]] = None
    agent_trace: Optional[List[str]] = None
    attempts: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_status: Dict[str, Any]
    vector_store_stats: Dict[str, Any]


class ExampleResponse(BaseModel):
    """Example queries response."""
    examples: List[str]
    categories: Dict[str, List[str]]


# -----------------------------------------------------------------------------
# Application Lifecycle
# -----------------------------------------------------------------------------

# Global service instances
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Autonomous Multi-Agent Business Intelligence System...")
    
    try:
        services["llm_router"] = get_llm_router()
        services["ner_extractor"] = NERExtractor()
        services["intent_classifier"] = IntentClassifier(use_transformers=False)
        try:
            services["vector_store"] = VectorStore()
        except Exception as ve:
            logger.warning(f"Vector store initialization failed (non-critical): {ve}")
            services["vector_store"] = None
        services["sql_generator"] = TextToSQLGenerator(
            llm_router=services["llm_router"],
            rag_retriever=None,
            ner_extractor=services["ner_extractor"],
            intent_classifier=services["intent_classifier"]
        )
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Autonomous Multi-Agent Business Intelligence System...")
    services.clear()


# -----------------------------------------------------------------------------
# FastAPI Application
# -----------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered BI Assistant with Natural Language Queries",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Dependency Injection
# -----------------------------------------------------------------------------

def get_sql_generator() -> TextToSQLGenerator:
    """Get SQL generator service."""
    if "sql_generator" not in services:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return services["sql_generator"]


def get_vector_store() -> VectorStore:
    """Get vector store service."""
    if "vector_store" not in services:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return services["vector_store"]


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    llm_router = services.get("llm_router")
    vector_store = services.get("vector_store")

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        llm_status=llm_router.get_status() if llm_router else {"error": "not initialized"},
        vector_store_stats=vector_store.get_stats() if vector_store else {"error": "not initialized"}
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(
    request: QueryRequest,
    sql_generator: TextToSQLGenerator = Depends(get_sql_generator)
):
    """
    Process natural language query and generate SQL.
    
    Example:
    ```json
    {
        "query": "Show me total revenue by region for last quarter",
        "database": "default",
        "use_rag": true
    }
    ```
    """
    try:
        logger.info(f"Processing query: {request.query[:50]}...")

        # If request.use_rag is True and agentic mode is enabled,
        # use generate_agentic() instead of generate().
        # Return agent_trace, plan, and insights when available.
        # Keep existing response structure backward compatible.

        use_agentic = getattr(request, "agentic", False)
        agentic_result: Optional[Dict[str, Any]] = None

        if use_agentic and hasattr(sql_generator, "generate_agentic"):
            try:
                logger.info("Executing agentic pipeline...")
                agentic_result = sql_generator.generate_agentic(
                    query=request.query,
                    database=request.database
                ) or {}
                logger.info(f"Agentic pipeline returned: {list(agentic_result.keys()) if agentic_result else 'None'}")
            except Exception as agentic_err:
                logger.warning(
                    "Agentic pipeline failed, falling back to standard generate()", exc_info=agentic_err
                )
                agentic_result = None

        core_result = sql_generator.generate(
            query=request.query,
            database=request.database,
            use_rag=request.use_rag,
            validate=request.validate_sql
        )

        # If agentic returned a full payload with required keys, prefer it; otherwise fall back to core_result.
        required_keys = {
            "sql",
            "confidence",
            "explanation",
            "complexity",
            "entities",
            "intent",
            "cost_estimate",
            "provider",
            "validation_status",
            "validation_errors",
        }

        payload = None
        if agentic_result and isinstance(agentic_result, dict) and required_keys.issubset(agentic_result.keys()):
            payload = agentic_result
        else:
            payload = {
                "sql": core_result.sql,
                "confidence": core_result.confidence,
                "explanation": core_result.explanation,
                "complexity": core_result.complexity,
                "entities": core_result.entities,
                "intent": core_result.intent,
                "cost_estimate": core_result.cost_estimate,
                "provider": core_result.provider,
                "validation_status": core_result.validation_status,
                "validation_errors": core_result.validation_errors,
            }
            if agentic_result and isinstance(agentic_result, dict):
                payload.update({
                    "plan": agentic_result.get("plan"),
                    "insights": agentic_result.get("insights"),
                    "agent_trace": agentic_result.get("agent_trace"),
                    "attempts": agentic_result.get("attempts"),
                })

        return QueryResponse(
            sql=payload["sql"],
            confidence=payload["confidence"],
            explanation=payload["explanation"],
            complexity=payload["complexity"],
            entities=payload["entities"],
            intent=payload["intent"],
            cost_estimate=payload["cost_estimate"],
            provider=payload["provider"],
            validation_status=payload["validation_status"],
            validation_errors=payload["validation_errors"],
            plan=payload.get("plan"),
            insights=payload.get("insights"),
            agent_trace=payload.get("agent_trace"),
            attempts=payload.get("attempts"),
        )

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/batch", tags=["Query"])
async def process_batch_queries(
    queries: List[str],
    database: str = "default",
    sql_generator: TextToSQLGenerator = Depends(get_sql_generator)
):
    """Process multiple queries in batch."""
    results = []
    
    for query in queries:
        try:
            result = sql_generator.generate_dict(
                query=query,
                database=database
            )
            results.append({"query": query, "result": result, "error": None})
        except Exception as e:
            results.append({"query": query, "result": None, "error": str(e)})

    return {"results": results, "total": len(queries)}


@app.get("/examples", response_model=ExampleResponse, tags=["General"])
async def get_examples():
    """Get example queries by category."""
    return ExampleResponse(
        examples=[
            "Show me total revenue for last quarter",
            "What are the top 10 products by sales?",
            "Compare Q1 and Q2 revenue by region",
            "Show customer count trend over time",
            "Which salespeople exceeded their quota?"
        ],
        categories={
            "aggregation": [
                "What is the total revenue?",
                "How many customers do we have?",
                "What's the average order value?"
            ],
            "ranking": [
                "Top 10 products by sales",
                "Bottom 5 regions by profit",
                "Best performing salespeople"
            ],
            "comparison": [
                "Compare Q1 vs Q2 revenue",
                "Revenue by region comparison",
                "Year over year growth"
            ],
            "trend": [
                "Revenue trend over time",
                "Monthly customer growth",
                "Sales progression by quarter"
            ],
            "filtering": [
                "Sales in California",
                "Orders from Enterprise customers",
                "Products in Software category"
            ]
        }
    )


@app.post("/rag/add-examples", tags=["RAG"])
async def add_query_examples(
    examples: List[Dict[str, str]],
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Add query examples to RAG store.
    
    Example:
    ```json
    [
        {
            "natural_query": "Show total revenue by region",
            "sql_query": "SELECT region, SUM(revenue) FROM sales GROUP BY region"
        }
    ]
    ```
    """
    try:
        count = vector_store.add_query_examples(examples)
        return {"status": "success", "added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/search", tags=["RAG"])
async def search_similar(
    query: str,
    top_k: int = 3,
    vector_store: VectorStore = Depends(get_vector_store)
):
    """Search for similar queries."""
    try:
        results = vector_store.search_similar_queries(query, top_k)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/llm/status", tags=["LLM"])
async def get_llm_status():
    """Get LLM service status."""
    llm_router = services.get("llm_router")
    if not llm_router:
        raise HTTPException(status_code=503, detail="LLM router not initialized")
    
    return llm_router.get_status()


@app.post("/llm/test", tags=["LLM"])
async def test_llm(prompt: str = "Hello, how are you?"):
    """Test LLM connectivity."""
    llm_router = services.get("llm_router")
    if not llm_router:
        raise HTTPException(status_code=503, detail="LLM router not initialized")
    
    try:
        response = llm_router.route_query(
            prompt=prompt,
            task_type="simple_sql",
            max_tokens=100
        )
        return {
            "prompt": prompt,
            "response": response["content"][:200],
            "provider": response.get("provider"),
            "tokens": response.get("tokens")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


# -----------------------------------------------------------------------------
# Run Application
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
