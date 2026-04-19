"""
API routes for user data source management
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import logging

from backend.mcp.user_data_connector import (
    user_data_connector,
    DataSourceConfig
)

router = APIRouter(prefix="/data-sources", tags=["data-sources"])
logger = logging.getLogger(__name__)


class DataSourceCreateRequest(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    
    # API configuration
    api_url: Optional[str] = None
    api_method: Optional[str] = "GET"
    api_headers: Optional[Dict[str, str]] = None
    api_auth_type: Optional[str] = None
    api_auth_value: Optional[str] = None
    
    # Webhook configuration
    webhook_secret: Optional[str] = None
    
    # Database configuration
    db_type: Optional[str] = None
    db_connection_string: Optional[str] = None
    db_query: Optional[str] = None
    
    # Data mapping
    data_mapping: Optional[Dict[str, str]] = None
    
    # Settings
    refresh_interval: Optional[int] = 3600
    enable_rag: bool = True
    rag_collection: Optional[str] = None
    generate_mcp_tool: bool = True
    mcp_tool_name: Optional[str] = None
    mcp_tool_description: Optional[str] = None


class DataSourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    api_url: Optional[str] = None
    api_headers: Optional[Dict[str, str]] = None
    refresh_interval: Optional[int] = None


@router.post("/")
async def create_data_source(request: DataSourceCreateRequest):
    """Create a new data source connection"""
    try:
        # Generate unique ID
        source_id = str(uuid.uuid4())
        
        # Create configuration
        config = DataSourceConfig(
            id=source_id,
            **request.dict()
        )
        
        # Add data source
        result = await user_data_connector.add_data_source(config)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create data source: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_data_sources():
    """List all data sources"""
    try:
        sources = await user_data_connector.list_data_sources()
        return {
            "success": True,
            "data": sources,
            "count": len(sources)
        }
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}")
async def get_data_source(source_id: str):
    """Get a specific data source"""
    config = user_data_connector.data_sources.get(source_id)
    if not config:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    return {
        "success": True,
        "data": config.dict()
    }


@router.put("/{source_id}")
async def update_data_source(source_id: str, request: DataSourceUpdateRequest):
    """Update a data source"""
    config = user_data_connector.data_sources.get(source_id)
    if not config:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    
    return {
        "success": True,
        "message": "Data source updated successfully"
    }


@router.delete("/{source_id}")
async def delete_data_source(source_id: str):
    """Delete a data source"""
    success = await user_data_connector.remove_data_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    return {
        "success": True,
        "message": "Data source deleted successfully"
    }


@router.post("/{source_id}/refresh")
async def refresh_data_source(source_id: str):
    """Manually refresh a data source"""
    config = user_data_connector.data_sources.get(source_id)
    if not config:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    data = await user_data_connector.fetch_data(source_id)
    
    return {
        "success": True,
        "message": "Data refreshed successfully",
        "records": len(data) if isinstance(data, list) else 1 if data else 0
    }


@router.post("/{source_id}/test")
async def test_data_source(source_id: str):
    """Test a data source connection"""
    config = user_data_connector.data_sources.get(source_id)
    if not config:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    try:
        data = await user_data_connector.fetch_data(source_id)
        return {
            "success": True,
            "message": "Connection successful",
            "sample_data": data[:3] if isinstance(data, list) else data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file_format: str = Form("json"),
    enable_rag: bool = Form(True),
    generate_mcp_tool: bool = Form(True)
):
    """Upload a data file (JSON, CSV, etc.)"""
    try:
        import os
        import tempfile
        
        # Save uploaded file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"user_data_{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create data source
        source_id = str(uuid.uuid4())
        config = DataSourceConfig(
            id=source_id,
            name=name,
            type="file",
            description=description,
            file_path=file_path,
            file_format=file_format,
            enable_rag=enable_rag,
            generate_mcp_tool=generate_mcp_tool,
            mcp_tool_name=f"user_file_{name.lower().replace(' ', '_')}",
            mcp_tool_description=f"Access data from uploaded file: {name}"
        )
        
        result = await user_data_connector.add_data_source(config)
        
        return {
            "success": True,
            "data": result,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook/{source_id}")
async def receive_webhook(source_id: str, payload: Dict[str, Any]):
    """Receive webhook data"""
    config = user_data_connector.data_sources.get(source_id)
    if not config or config.type != "webhook":
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Verify webhook secret if configured
    # (Add proper verification logic here)
    
    # Store webhook data
    user_data_connector.cache[source_id] = payload
    config.last_refresh = datetime.now()
    
    # Index in RAG if enabled
    if config.enable_rag:
        await user_data_connector._index_in_rag(config, payload)
    
    return {
        "success": True,
        "message": "Webhook received successfully"
    }


@router.get("/{source_id}/data")
async def get_data_source_data(source_id: str, limit: int = 100):
    """Get cached data from a source"""
    data = user_data_connector.cache.get(source_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
    # Limit results
    if isinstance(data, list):
        data = data[:limit]
    
    return {
        "success": True,
        "data": data,
        "count": len(data) if isinstance(data, list) else 1
    }


@router.post("/refresh-all")
async def refresh_all_sources():
    """Refresh all data sources"""
    await user_data_connector.refresh_all()
    return {
        "success": True,
        "message": "All data sources refreshed"
    }


# Import datetime
from datetime import datetime
