"""
API Versioning Strategy for SupplyChainGPT

Provides backward compatibility and gradual migration path.
Zero breaking changes for existing clients.
"""

from fastapi import Request, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Version Configuration
# ============================================================================

SUPPORTED_VERSIONS = ["v1", "v2", "v3"]
DEFAULT_VERSION = "v2"
DEPRECATED_VERSIONS = ["v1"]  # Still supported but deprecated

VERSION_DEPRECATION_DATES = {
    "v1": "2027-01-01",  # Will be removed after this date
}

VERSION_FEATURES = {
    "v1": {
        "description": "Legacy API (deprecated)",
        "features": [
            "Basic council debates",
            "Simple risk assessment",
            "Limited agent support",
        ],
        "limitations": [
            "No GraphQL support",
            "No webhooks",
            "No batch operations",
        ],
    },
    "v2": {
        "description": "Current stable API",
        "features": [
            "Full council debates with Astra",
            "Advanced risk assessment",
            "All 7 specialized agents",
            "GraphQL support",
            "Webhook notifications",
            "Batch operations",
            "RAG pipeline",
            "99+ MCP tools",
        ],
        "limitations": [],
    },
    "v3": {
        "description": "Beta API (new features)",
        "features": [
            "All v2 features",
            "Real-time collaboration",
            "Advanced analytics",
            "Custom agent creation",
            "Multi-tenant support",
        ],
        "limitations": [
            "Beta - may have breaking changes",
            "Not recommended for production",
        ],
    },
}


# ============================================================================
# Version Detection
# ============================================================================

def get_api_version(request: Request) -> str:
    """
    Extract API version from request.
    
    Priority:
    1. Path prefix (/api/v2/...)
    2. Header (X-API-Version: v2)
    3. Query parameter (?version=v2)
    4. Default version
    """
    # Check path
    path = request.url.path
    for version in SUPPORTED_VERSIONS:
        if path.startswith(f"/api/{version}/"):
            return version
    
    # Check header
    version_header = request.headers.get("X-API-Version")
    if version_header and version_header in SUPPORTED_VERSIONS:
        return version_header
    
    # Check query parameter
    version_param = request.query_params.get("version")
    if version_param and version_param in SUPPORTED_VERSIONS:
        return version_param
    
    # Default
    return DEFAULT_VERSION


def validate_api_version(version: str) -> bool:
    """Check if API version is supported."""
    return version in SUPPORTED_VERSIONS


def is_deprecated(version: str) -> bool:
    """Check if API version is deprecated."""
    return version in DEPRECATED_VERSIONS


def get_deprecation_warning(version: str) -> Optional[str]:
    """Get deprecation warning message."""
    if version in DEPRECATED_VERSIONS:
        deprecation_date = VERSION_DEPRECATION_DATES.get(version, "unknown")
        return (
            f"API version {version} is deprecated and will be removed after "
            f"{deprecation_date}. Please migrate to {DEFAULT_VERSION}."
        )
    return None


# ============================================================================
# Version Middleware
# ============================================================================

class APIVersionMiddleware:
    """Middleware to handle API versioning."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Get version
            version = get_api_version(request)
            
            # Validate version
            if not validate_api_version(version):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported API version: {version}. "
                           f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
                )
            
            # Add version to request state
            scope["state"] = {"api_version": version}
            
            # Log deprecation warning
            if is_deprecated(version):
                warning = get_deprecation_warning(version)
                logger.warning(f"Deprecated API version used: {warning}")
            
            # Add deprecation header to response
            async def send_with_deprecation(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    
                    # Add version header
                    headers.append((b"X-API-Version", version.encode()))
                    
                    # Add deprecation warning if applicable
                    if is_deprecated(version):
                        warning = get_deprecation_warning(version)
                        headers.append((b"X-API-Deprecation", warning.encode()))
                    
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_with_deprecation)
        else:
            await self.app(scope, receive, send)


# ============================================================================
# Version-Specific Response Transformers
# ============================================================================

def transform_response_for_version(data: dict, version: str) -> dict:
    """
    Transform response data based on API version.
    
    Ensures backward compatibility by adapting response format.
    """
    if version == "v1":
        # V1 format: simpler structure
        return _transform_to_v1(data)
    elif version == "v2":
        # V2 format: current structure
        return data
    elif version == "v3":
        # V3 format: enhanced structure
        return _transform_to_v3(data)
    else:
        return data


def _transform_to_v1(data: dict) -> dict:
    """Transform to v1 format (legacy)."""
    # Remove v2+ fields
    if "astra_results" in data:
        del data["astra_results"]
    
    if "webhook_events" in data:
        del data["webhook_events"]
    
    # Simplify agent results
    if "agents" in data:
        for agent in data["agents"]:
            # Remove advanced fields
            agent.pop("citations", None)
            agent.pop("model_used", None)
            agent.pop("provider", None)
    
    return data


def _transform_to_v3(data: dict) -> dict:
    """Transform to v3 format (enhanced)."""
    # Add v3 enhancements
    data["api_version"] = "v3"
    
    # Add metadata
    if "agents" in data:
        data["agent_count"] = len(data["agents"])
    
    if "citations" in data:
        data["citation_count"] = len(data["citations"])
    
    return data


# ============================================================================
# Version Info Endpoint
# ============================================================================

def get_version_info() -> dict:
    """Get information about all API versions."""
    return {
        "supported_versions": SUPPORTED_VERSIONS,
        "default_version": DEFAULT_VERSION,
        "deprecated_versions": DEPRECATED_VERSIONS,
        "versions": VERSION_FEATURES,
        "deprecation_dates": VERSION_DEPRECATION_DATES,
    }


# Example usage:
"""
from backend.api.versioning import get_api_version, transform_response_for_version

# In route handler
@app.get("/api/v2/debates/{debate_id}")
async def get_debate(debate_id: str, request: Request):
    version = get_api_version(request)
    
    # Get data
    data = await fetch_debate(debate_id)
    
    # Transform for version
    response = transform_response_for_version(data, version)
    
    return response
"""
