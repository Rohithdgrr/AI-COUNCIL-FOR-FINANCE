"""
User Data Connector for MCP
Allows users to connect their own data sources to the platform
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, validator
import httpx
import json

logger = logging.getLogger(__name__)


class DataSourceConfig(BaseModel):
    """Configuration for a user data source"""
    id: str
    name: str
    type: str  # 'api', 'webhook', 'database', 'file'
    description: Optional[str] = None
    enabled: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    # API configuration
    api_url: Optional[HttpUrl] = None
    api_method: Optional[str] = "GET"
    api_headers: Optional[Dict[str, str]] = None
    api_auth_type: Optional[str] = None  # 'bearer', 'basic', 'api_key'
    api_auth_value: Optional[str] = None
    
    # Webhook configuration
    webhook_secret: Optional[str] = None
    
    # Database configuration
    db_type: Optional[str] = None  # 'postgresql', 'mysql', 'mongodb'
    db_connection_string: Optional[str] = None
    db_query: Optional[str] = None
    
    # File configuration
    file_path: Optional[str] = None
    file_format: Optional[str] = None  # 'json', 'csv', 'xml'
    
    # Data mapping
    data_mapping: Optional[Dict[str, str]] = None
    
    # Refresh settings
    refresh_interval: Optional[int] = 3600  # seconds
    last_refresh: Optional[datetime] = None
    
    # RAG integration
    enable_rag: bool = True
    rag_collection: Optional[str] = None
    
    # MCP tool generation
    generate_mcp_tool: bool = True
    mcp_tool_name: Optional[str] = None
    mcp_tool_description: Optional[str] = None
    
    @validator('api_method')
    def validate_method(cls, v):
        if v and v.upper() not in ['GET', 'POST', 'PUT', 'DELETE']:
            raise ValueError('Invalid HTTP method')
        return v.upper() if v else 'GET'


class UserDataConnector:
    """Manages user data source connections"""
    
    def __init__(self):
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self.cache: Dict[str, Any] = {}
    
    async def add_data_source(self, config: DataSourceConfig) -> Dict[str, Any]:
        """Add a new data source"""
        try:
            # Validate connection
            if config.type == 'api':
                await self._validate_api_connection(config)
            elif config.type == 'database':
                await self._validate_db_connection(config)
            
            # Store configuration
            self.data_sources[config.id] = config
            
            # Generate MCP tool if requested
            if config.generate_mcp_tool:
                await self._generate_mcp_tool(config)
            
            # Initial data fetch
            data = await self.fetch_data(config.id)
            
            # Index in RAG if enabled
            if config.enable_rag and data:
                await self._index_in_rag(config, data)
            
            logger.info(f"Added data source: {config.name} ({config.id})")
            
            return {
                "success": True,
                "data_source_id": config.id,
                "message": f"Data source '{config.name}' connected successfully",
                "records_fetched": len(data) if isinstance(data, list) else 1,
            }
            
        except Exception as e:
            logger.error(f"Failed to add data source {config.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def fetch_data(self, source_id: str) -> Any:
        """Fetch data from a source"""
        config = self.data_sources.get(source_id)
        if not config or not config.enabled:
            return None
        
        try:
            if config.type == 'api':
                data = await self._fetch_from_api(config)
            elif config.type == 'database':
                data = await self._fetch_from_database(config)
            elif config.type == 'file':
                data = await self._fetch_from_file(config)
            else:
                data = None
            
            # Update cache and last refresh
            if data:
                self.cache[source_id] = data
                config.last_refresh = datetime.now()
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch data from {config.name}: {e}")
            return None
    
    async def _fetch_from_api(self, config: DataSourceConfig) -> Any:
        """Fetch data from API endpoint"""
        headers = config.api_headers or {}
        
        # Add authentication
        if config.api_auth_type == 'bearer' and config.api_auth_value:
            headers['Authorization'] = f'Bearer {config.api_auth_value}'
        elif config.api_auth_type == 'api_key' and config.api_auth_value:
            headers['X-API-Key'] = config.api_auth_value
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=config.api_method,
                url=str(config.api_url),
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Apply data mapping if configured
            if config.data_mapping:
                data = self._apply_mapping(data, config.data_mapping)
            
            return data
    
    async def _fetch_from_database(self, config: DataSourceConfig) -> Any:
        """Fetch data from database"""
        # This would require database-specific libraries
        # For now, return placeholder
        logger.warning(f"Database fetching not yet implemented for {config.db_type}")
        return None
    
    async def _fetch_from_file(self, config: DataSourceConfig) -> Any:
        """Fetch data from file"""
        import os
        
        if not config.file_path or not os.path.exists(config.file_path):
            raise FileNotFoundError(f"File not found: {config.file_path}")
        
        with open(config.file_path, 'r') as f:
            if config.file_format == 'json':
                return json.load(f)
            elif config.file_format == 'csv':
                import csv
                return list(csv.DictReader(f))
            else:
                return f.read()
    
    def _apply_mapping(self, data: Any, mapping: Dict[str, str]) -> Any:
        """Apply field mapping to data"""
        if isinstance(data, dict):
            return {mapping.get(k, k): v for k, v in data.items()}
        elif isinstance(data, list):
            return [self._apply_mapping(item, mapping) for item in data]
        return data
    
    async def _validate_api_connection(self, config: DataSourceConfig):
        """Validate API connection"""
        if not config.api_url:
            raise ValueError("API URL is required")
        
        # Test connection
        headers = config.api_headers or {}
        if config.api_auth_type == 'bearer' and config.api_auth_value:
            headers['Authorization'] = f'Bearer {config.api_auth_value}'
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                method=config.api_method,
                url=str(config.api_url),
                headers=headers
            )
            response.raise_for_status()
    
    async def _validate_db_connection(self, config: DataSourceConfig):
        """Validate database connection"""
        if not config.db_connection_string:
            raise ValueError("Database connection string is required")
        # Add actual validation logic here
    
    async def _generate_mcp_tool(self, config: DataSourceConfig):
        """Generate MCP tool for this data source"""
        tool_name = config.mcp_tool_name or f"user_data_{config.id}"
        tool_description = config.mcp_tool_description or f"Fetch data from {config.name}"
        
        # Register as MCP tool
        from backend.mcp.registry import mcp_registry
        
        async def tool_function(**kwargs):
            return await self.fetch_data(config.id)
        
        mcp_registry.register_tool(
            name=tool_name,
            description=tool_description,
            category="user_data",
            agents=["risk", "supply", "logistics", "market", "finance", "brand", "moderator"],
            function=tool_function
        )
        
        logger.info(f"Generated MCP tool: {tool_name}")
    
    async def _index_in_rag(self, config: DataSourceConfig, data: Any):
        """Index data in RAG system"""
        try:
            from backend.rag.loader import DocumentLoader
            from backend.rag.vectorstore import get_vectorstore
            
            # Convert data to text
            if isinstance(data, dict):
                text = json.dumps(data, indent=2)
            elif isinstance(data, list):
                text = "\n\n".join([json.dumps(item, indent=2) for item in data])
            else:
                text = str(data)
            
            # Create document
            doc = {
                "content": text,
                "metadata": {
                    "source": config.name,
                    "source_id": config.id,
                    "type": config.type,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Index in vectorstore
            collection_name = config.rag_collection or f"user_data_{config.id}"
            vectorstore = await get_vectorstore(collection_name)
            await vectorstore.add_documents([doc])
            
            logger.info(f"Indexed data from {config.name} in RAG")
            
        except Exception as e:
            logger.error(f"Failed to index in RAG: {e}")
    
    async def remove_data_source(self, source_id: str) -> bool:
        """Remove a data source"""
        if source_id in self.data_sources:
            config = self.data_sources[source_id]
            
            # Remove from cache
            self.cache.pop(source_id, None)
            
            # Remove MCP tool if generated
            if config.generate_mcp_tool:
                from backend.mcp.registry import mcp_registry
                tool_name = config.mcp_tool_name or f"user_data_{config.id}"
                mcp_registry.unregister_tool(tool_name)
            
            # Remove from data sources
            del self.data_sources[source_id]
            
            logger.info(f"Removed data source: {config.name}")
            return True
        
        return False
    
    async def list_data_sources(self) -> List[Dict[str, Any]]:
        """List all data sources"""
        return [
            {
                "id": config.id,
                "name": config.name,
                "type": config.type,
                "description": config.description,
                "enabled": config.enabled,
                "last_refresh": config.last_refresh.isoformat() if config.last_refresh else None,
                "records_cached": len(self.cache.get(config.id, [])) if isinstance(self.cache.get(config.id), list) else 1 if config.id in self.cache else 0,
            }
            for config in self.data_sources.values()
        ]
    
    async def refresh_all(self):
        """Refresh all data sources"""
        for source_id in list(self.data_sources.keys()):
            await self.fetch_data(source_id)


# Global instance
user_data_connector = UserDataConnector()
