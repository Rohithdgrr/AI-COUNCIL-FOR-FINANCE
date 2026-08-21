from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import os

API_KEYS = os.getenv("API_KEYS", "dev-key").split(",")
MCP_API_KEYS = os.getenv("MCP_API_KEY", "dev-mcp-key").split(",")
PUBLIC_ENDPOINTS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/test", "/metrics", "/market/ticker", "/market/risk-dashboard", "/market/brand-intel", "/market/forex-rates", "/market/commodity-prices", "/market/supply-chain-stocks", "/market/global-news", "/council/v2/stream", "/council/stream", "/council/analyze", "/council/query", "/astra/swarm", "/astra/run", "/astra/chat"}
PUBLIC_PREFIXES = ("/market/company/", "/council/", "/astra/", "/api/council/", "/api/astra/", "/ws", "/graphql", "/mcp/", "/api/mcp/")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_ENDPOINTS or request.method == "OPTIONS" or any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        if request.url.path.startswith("/mcp/"):
            key = request.headers.get("X-MCP-API-Key", "") or request.query_params.get("mcp_key", "")
            if key not in MCP_API_KEYS:
                return JSONResponse(status_code=401, content={"detail": "Invalid MCP API key"})
            return await call_next(request)

        key = request.headers.get("X-API-Key", "") or request.query_params.get("api_key", "")
        if key not in API_KEYS:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

        return await call_next(request)
