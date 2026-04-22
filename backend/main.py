from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from contextlib import asynccontextmanager
import logging
import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

# LangSmith env must be set before any langchain imports
from backend.observability.langsmith_config import configure_langsmith_env
configure_langsmith_env()

from backend.config import settings
from backend.middleware.auth import AuthMiddleware
from backend.middleware.error_handler import ErrorHandlerMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.security import SecurityMiddleware
from backend.middleware.logging import RequestLoggingMiddleware, setup_json_logging
from backend.middleware.rate_limiter import RedisRateLimitMiddleware
from backend.routes.health import router as health_router
from backend.routes.models import router as models_router
from backend.routes.council import router as council_router
from backend.routes.risk import router as risk_router
from backend.routes.ingest import router as ingest_router
from backend.routes.optimize import router as optimize_router
from backend.routes.settings import router as settings_router
from backend.rag.api import router as rag_router
from backend.routes.market import router as market_router
from backend.routes.observability import router as observability_router
from backend.routes.council_v2 import router as council_v2_router
from backend.routes.mcp_manifest import router as mcp_manifest_router
from backend.routes.astra import router as astra_router
from backend.routes.data_sources import router as data_sources_router
from backend.routes.quota import router as quota_router
from backend.routes.webhooks import router as webhooks_router
from backend.routes.batch import router as batch_router
from backend.ws.server import websocket_endpoint
from backend.ws.dashboard_stream import run_dashboard_stream
from backend.tasks import start_scheduler, stop_scheduler

# Setup structured JSON logging
setup_json_logging()
logger = logging.getLogger(__name__)

# Track app start time for uptime
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = time.time()
    logger.info("Starting SupplyChainGPT Council API...", extra={"session_id": "startup"})

    dashboard_stream_task = asyncio.create_task(run_dashboard_stream())
    
    # Start background task scheduler for continuous data ingestion
    try:
        await start_scheduler()
        logger.info("Background task scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start task scheduler: {e}")

    try:
        from backend.db.neon import init_db
        await init_db()
        logger.info("Neon PostgreSQL initialized")
    except Exception as e:
        logger.warning(f"Neon PG not available: {e}")

    try:
        from backend.db.redis_client import init_redis
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    try:
        from backend.db.neo4j_client import init_neo4j_schema
        await init_neo4j_schema()
        logger.info("Neo4j initialized with sample data")
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")

    try:
        from backend.mcp.registry import register_all_tools
        register_all_tools()
        logger.info("MCP tools registered")
    except Exception as e:
        logger.warning(f"MCP tools registration failed: {e}")

    try:
        from backend.mcp.mcp_toolkit import init_all_mcp_clients
        init_all_mcp_clients()
        logger.info("MCP clients initialized for all agents")
    except Exception as e:
        logger.warning(f"MCP client initialization failed: {e}")

    try:
        from backend.api.webhooks import webhook_manager
        await webhook_manager.load_subscriptions()
        # Start webhook delivery worker in background
        asyncio.create_task(webhook_manager.start_delivery_worker())
        logger.info("Webhook system initialized")
    except Exception as e:
        logger.warning(f"Webhook system initialization failed: {e}")

    yield
    
    # Cleanup on shutdown
    dashboard_stream_task.cancel()
    try:
        await dashboard_stream_task
    except asyncio.CancelledError:
        pass
    
    # Stop background task scheduler
    try:
        await stop_scheduler()
        logger.info("Background task scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping task scheduler: {e}")
    
    logger.info("Shutting down SupplyChainGPT Council API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# Middleware order matters: added LAST runs FIRST
# Execution order: CORS -> RedisRateLimit -> Security -> RequestLogging -> RateLimit -> Auth -> ErrorHandler
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RedisRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP sub-app
from backend.mcp.server import mcp_app
app.mount("/mcp", mcp_app)

# API Routes
app.include_router(health_router, tags=["Health"])
app.include_router(models_router, prefix="/models", tags=["Models"])
app.include_router(council_router, prefix="/council", tags=["Council"])
app.include_router(council_v2_router, prefix="/council/v2", tags=["Council V2"])
app.include_router(risk_router, prefix="/risk", tags=["Risk"])
app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])
app.include_router(optimize_router, prefix="/optimize", tags=["Optimize"])
app.include_router(settings_router, prefix="/settings", tags=["Settings"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(market_router, tags=["Market"])
app.include_router(observability_router, prefix="/observability", tags=["Observability"])
app.include_router(mcp_manifest_router, prefix="/mcp", tags=["MCP Manifest"])
app.include_router(astra_router, prefix="/astra", tags=["Astra ⭐"])
app.include_router(data_sources_router, tags=["Data Sources"])
app.include_router(quota_router, tags=["Quota & Usage"])
app.include_router(webhooks_router, tags=["Webhooks"])
app.include_router(batch_router, prefix="/api/v1", tags=["Batch Operations"])

# Task scheduler API
from backend.routes.tasks import router as tasks_router
app.include_router(tasks_router, tags=["Task Scheduler"])

# Viewport optimization API
from backend.routes.viewport import router as viewport_router
app.include_router(viewport_router, tags=["Viewport Optimization"])

# WebSocket
app.websocket("/ws")(websocket_endpoint)

# GraphQL
from strawberry.fastapi import GraphQLRouter
from backend.graphql.schema import schema

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    from backend.observability.langsmith_config import generate_prometheus_metrics
    return generate_prometheus_metrics()


@app.get("/health")
async def health_detailed():
    """Detailed health check with uptime and component status."""
    from backend.db.redis_client import get_redis
    from backend.db.neon import get_pool

    checks = {}
    uptime = time.time() - _start_time if _start_time else 0

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["neon_postgres"] = "ok"
    except Exception:
        checks["neon_postgres"] = "error"

    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    try:
        from backend.mcp.registry import list_tools
        tool_count = len(list_tools())
        checks["mcp_tools"] = "ok" if tool_count > 0 else "error"
    except Exception:
        checks["mcp_tools"] = "error"

    try:
        from backend.rag.embedder import get_embeddings
        get_embeddings()
        checks["rag_embedder"] = "ok"
    except Exception:
        checks["rag_embedder"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "success": True,
        "data": {
            "status": "ok" if all_ok else "degraded",
            "version": settings.version,
            "uptime_seconds": round(uptime, 1),
            "langsmith_tracing": settings.langchain_tracing_v2,
            "human_in_loop": settings.human_in_loop,
            "checks": checks,
        },
        "error": None,
    }


@app.get("/test")
async def test_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "test.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
