"""
MCP Client Library

A comprehensive Model Context Protocol (MCP) client library with support for
Streamable HTTP and SSE transports, multiple authentication methods, and
connection management.
"""

from typing import Dict, Optional, Any, Union, Protocol
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport, SSETransport
from fastmcp.client.auth import BearerAuth
import logging
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import base64
import json
from datetime import datetime, timedelta
import secrets

logger = logging.getLogger(__name__)


# ============================================================================
# Core Types and Enums
# ============================================================================

class TransportType(Enum):
    """Available transport types for MCP client"""
    STREAMABLE_HTTP = "streamable_http"
    SSE = "sse"


# ============================================================================
# Exceptions
# ============================================================================

class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    pass


class MCPConnectionError(MCPClientError):
    """Exception raised when connection to MCP server fails"""
    pass


class MCPAuthenticationError(MCPClientError):
    """Exception raised when authentication fails"""
    pass


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class MCPConfig:
    """Configuration for MCP client connection"""
    url: str
    transport_type: TransportType = TransportType.STREAMABLE_HTTP
    headers: Optional[Dict[str, str]] = None
    bearer_token: Optional[str] = None
    timeout: Optional[float] = 30.0
    retry_attempts: int = 3


# ============================================================================
# Authentication System
# ============================================================================

class AuthProvider(Protocol):
    """Protocol for authentication providers"""
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        ...
    
    def is_valid(self) -> bool:
        """Check if authentication is valid"""
        ...


@dataclass
class AuthToken:
    """Represents an authentication token with metadata"""
    token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not empty and not expired)"""
        return bool(self.token) and not self.is_expired


class BearerAuthProvider:
    """Bearer token authentication provider"""
    
    def __init__(self, token: str, token_type: str = "Bearer"):
        self.auth_token = AuthToken(token=token, token_type=token_type)
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers with bearer token"""
        if not self.auth_token.is_valid:
            raise ValueError("Invalid or expired token")
        
        return {
            "Authorization": f"{self.auth_token.token_type} {self.auth_token.token}"
        }
    
    def is_valid(self) -> bool:
        """Check if authentication is valid"""
        return self.auth_token.is_valid


class APIKeyAuthProvider:
    """API Key authentication provider"""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers with API key"""
        if not self.api_key:
            raise ValueError("API key is required")
        
        return {self.header_name: self.api_key}
    
    def is_valid(self) -> bool:
        """Check if authentication is valid"""
        return bool(self.api_key)


class BasicAuthProvider:
    """Basic authentication provider"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers with basic auth"""
        if not self.username or not self.password:
            raise ValueError("Username and password are required")
        
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}"
        }
    
    def is_valid(self) -> bool:
        """Check if authentication is valid"""
        return bool(self.username) and bool(self.password)


class CustomHeaderAuthProvider:
    """Custom header authentication provider"""
    
    def __init__(self, headers: Dict[str, str]):
        self.auth_headers = headers
    
    def get_headers(self) -> Dict[str, str]:
        """Get custom authentication headers"""
        if not self.auth_headers:
            raise ValueError("Authentication headers are required")
        
        return self.auth_headers.copy()
    
    def is_valid(self) -> bool:
        """Check if authentication is valid"""
        return bool(self.auth_headers)


class AuthManager:
    """Authentication manager for MCP clients"""
    
    def __init__(self, auth_provider: AuthProvider):
        self.auth_provider = auth_provider
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers from provider"""
        if not self.auth_provider.is_valid():
            raise ValueError("Authentication provider is not valid")
        
        return self.auth_provider.get_headers()
    
    def validate_auth(self) -> bool:
        """Validate current authentication"""
        try:
            return self.auth_provider.is_valid()
        except Exception as e:
            logger.error(f"Authentication validation failed: {e}")
            return False


# ============================================================================
# Main MCP Client
# ============================================================================

class MCPClient:
    """
    Enhanced MCP Client with support for both Streamable HTTP and SSE transports
    """
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self._client: Optional[Client] = None
        self._transport = None
        
    def _create_transport(self) -> Union[StreamableHttpTransport, SSETransport]:
        """Create transport based on configuration"""
        headers = self.config.headers or {}
        
        logger.info(f"Creating transport with URL: {self.config.url}")
        logger.info(f"Transport type: {self.config.transport_type}")
        logger.info(f"Headers: {headers}")
        
        # Add bearer token to headers if provided
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
        
        try:
            if self.config.transport_type == TransportType.STREAMABLE_HTTP:
                logger.info(f"Creating StreamableHttpTransport with URL: {self.config.url}")
                return StreamableHttpTransport(
                    url=self.config.url,
                    headers=headers
                )
            elif self.config.transport_type == TransportType.SSE:
                logger.info(f"Creating SSETransport with URL: {self.config.url}")
                return SSETransport(
                    url=self.config.url,
                    headers=headers
                )
            else:
                raise MCPClientError(f"Unsupported transport type: {self.config.transport_type}")
        except Exception as e:
            logger.error(f"Failed to create transport: {e}")
            logger.error(f"URL that failed: {self.config.url}")
            logger.error(f"Transport type that failed: {self.config.transport_type}")
            raise MCPConnectionError(f"Failed to create transport: {e}")
    
    async def connect(self) -> None:
        """Establish connection to MCP server"""
        try:
            self._transport = self._create_transport()
            self._client = Client(self._transport)
            
            # Test connection
            await self._client.__aenter__()
            logger.info(f"Successfully connected to MCP server at {self.config.url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            if "auth" in str(e).lower() or "unauthorized" in str(e).lower():
                raise MCPAuthenticationError(f"Authentication failed: {e}")
            raise MCPConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._client = None
                self._transport = None
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to server"""
        return self._client is not None
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources from MCP server"""
        if not self.is_connected:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            result = await self._client.list_resources()
            return result
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            raise MCPConnectionError(f"Failed to list resources: {e}")
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from MCP server"""
        if not self.is_connected:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            result = await self._client.list_tools()
            return result
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise MCPConnectionError(f"Failed to list tools: {e}")
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.is_connected:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            result = await self._client.call_tool(name, arguments or {})
            return result
        except Exception as e:
            logger.error(f"Failed to call tool '{name}': {e}")
            raise MCPConnectionError(f"Failed to call tool '{name}': {e}")
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from MCP server"""
        if not self.is_connected:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            result = await self._client.read_resource(uri)
            return result
        except Exception as e:
            logger.error(f"Failed to read resource '{uri}': {e}")
            raise MCPConnectionError(f"Failed to read resource '{uri}': {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# ============================================================================
# Factory and Service Functions
# ============================================================================

class MCPService:
    """Service class for managing MCP client connections"""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._default_client: Optional[MCPClient] = None
    
    def create_default_client(self) -> MCPClient:
        """Create default MCP client using application settings"""
        # Import settings fresh each time to avoid caching issues
        import importlib
        config_module = importlib.import_module("app.config")
        settings = config_module.settings
        
        logger.info(f"Creating MCP client with URL: {settings.mcp_server_url}")
        logger.info(f"Transport type: {settings.mcp_transport_type}")
        logger.info(f"Bearer token present: {bool(settings.mcp_bearer_token)}")
        
        if not settings.mcp_server_url:
            raise ValueError("MCP server URL is not configured")
        
        transport_type = (
            TransportType.STREAMABLE_HTTP 
            if settings.mcp_transport_type == "streamable_http" 
            else TransportType.SSE
        )
        
        config = MCPConfig(
            url=settings.mcp_server_url,
            transport_type=transport_type,
            bearer_token=settings.mcp_bearer_token if settings.mcp_bearer_token else None,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts
        )
        
        logger.info(f"MCPConfig created with URL: {config.url}")
        
        client = MCPClient(config)
        self._default_client = client
        return client
    
    def create_client_with_bearer_token(
        self,
        url: str,
        token: str,
        transport_type: str = "streamable_http"
    ) -> MCPClient:
        """Create MCP client with bearer token authentication"""
        from ..config import settings
        
        transport_enum = (
            TransportType.STREAMABLE_HTTP 
            if transport_type == "streamable_http" 
            else TransportType.SSE
        )
        
        config = MCPConfig(
            url=url,
            transport_type=transport_enum,
            bearer_token=token,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts
        )
        
        return MCPClient(config)
    
    def create_client_with_api_key(
        self,
        url: str,
        api_key: str,
        header_name: str = "X-API-Key",
        transport_type: str = "streamable_http"
    ) -> MCPClient:
        """Create MCP client with API key authentication"""
        from ..config import settings
        
        auth_provider = APIKeyAuthProvider(api_key, header_name)
        auth_manager = AuthManager(auth_provider)
        auth_headers = auth_manager.get_auth_headers()
        
        transport_enum = (
            TransportType.STREAMABLE_HTTP 
            if transport_type == "streamable_http" 
            else TransportType.SSE
        )
        
        config = MCPConfig(
            url=url,
            transport_type=transport_enum,
            headers=auth_headers,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts
        )
        
        return MCPClient(config)
    
    def create_client_with_basic_auth(
        self,
        url: str,
        username: str,
        password: str,
        transport_type: str = "streamable_http"
    ) -> MCPClient:
        """Create MCP client with basic authentication"""
        from ..config import settings
        
        auth_provider = BasicAuthProvider(username, password)
        auth_manager = AuthManager(auth_provider)
        auth_headers = auth_manager.get_auth_headers()
        
        transport_enum = (
            TransportType.STREAMABLE_HTTP 
            if transport_type == "streamable_http" 
            else TransportType.SSE
        )
        
        config = MCPConfig(
            url=url,
            transport_type=transport_enum,
            headers=auth_headers,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts
        )
        
        return MCPClient(config)
    
    def create_client_with_custom_headers(
        self,
        url: str,
        headers: Dict[str, str],
        transport_type: str = "streamable_http"
    ) -> MCPClient:
        """Create MCP client with custom headers"""
        from ..config import settings
        
        transport_enum = (
            TransportType.STREAMABLE_HTTP 
            if transport_type == "streamable_http" 
            else TransportType.SSE
        )
        
        config = MCPConfig(
            url=url,
            transport_type=transport_enum,
            headers=headers,
            timeout=settings.mcp_timeout,
            retry_attempts=settings.mcp_retry_attempts
        )
        
        return MCPClient(config)
    
    def register_client(self, name: str, client: MCPClient) -> None:
        """Register a client with a name for later retrieval"""
        self._clients[name] = client
        logger.info(f"Registered MCP client '{name}'")
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get registered client by name"""
        return self._clients.get(name)
    
    def get_default_client(self) -> Optional[MCPClient]:
        """Get default client"""
        return self._default_client
    
    def remove_client(self, name: str) -> bool:
        """Remove registered client"""
        if name in self._clients:
            del self._clients[name]
            logger.info(f"Removed MCP client '{name}'")
            return True
        return False
    
    async def disconnect_all(self) -> None:
        """Disconnect all registered clients"""
        for name, client in self._clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected client '{name}'")
            except Exception as e:
                logger.error(f"Error disconnecting client '{name}': {e}")
        
        if self._default_client:
            try:
                await self._default_client.disconnect()
                logger.info("Disconnected default client")
            except Exception as e:
                logger.error(f"Error disconnecting default client: {e}")
    
    def list_clients(self) -> Dict[str, bool]:
        """List all registered clients and their connection status"""
        status = {}
        for name, client in self._clients.items():
            status[name] = client.is_connected
        
        if self._default_client:
            status["default"] = self._default_client.is_connected
        
        return status


# ============================================================================
# Global Service Instance and Convenience Functions
# ============================================================================

# Global MCP service instance
mcp_service = MCPService()


def get_default_mcp_client() -> MCPClient:
    """Get or create default MCP client"""
    # Always create fresh client to avoid caching issues
    client = mcp_service.create_default_client()
    return client


def create_mcp_client_from_config(
    url: Optional[str] = None,
    bearer_token: Optional[str] = None,
    transport_type: Optional[str] = None
) -> MCPClient:
    """Create MCP client using configuration with optional overrides"""
    from ..config import settings
    
    server_url = url or settings.mcp_server_url
    token = bearer_token or settings.mcp_bearer_token
    transport = transport_type or settings.mcp_transport_type
    
    if not server_url:
        raise ValueError("MCP server URL is required")
    
    transport_enum = (
        TransportType.STREAMABLE_HTTP 
        if transport == "streamable_http" 
        else TransportType.SSE
    )
    
    config = MCPConfig(
        url=server_url,
        transport_type=transport_enum,
        bearer_token=token if token else None,
        timeout=settings.mcp_timeout,
        retry_attempts=settings.mcp_retry_attempts
    )
    
    return MCPClient(config)


def create_streamable_http_client(
    url: str,
    bearer_token: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> MCPClient:
    """Create MCP client with Streamable HTTP transport"""
    from ..config import settings
    
    config = MCPConfig(
        url=url,
        transport_type=TransportType.STREAMABLE_HTTP,
        bearer_token=bearer_token,
        headers=headers,
        timeout=settings.mcp_timeout,
        retry_attempts=settings.mcp_retry_attempts
    )
    
    return MCPClient(config)


def create_sse_client(
    url: str,
    bearer_token: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> MCPClient:
    """Create MCP client with SSE transport"""
    from ..config import settings
    
    config = MCPConfig(
        url=url,
        transport_type=TransportType.SSE,
        bearer_token=bearer_token,
        headers=headers,
        timeout=settings.mcp_timeout,
        retry_attempts=settings.mcp_retry_attempts
    )
    
    return MCPClient(config)


# Context manager for temporary MCP client
class TemporaryMCPClient:
    """Context manager for temporary MCP client connections"""
    
    def __init__(self, client: MCPClient):
        self.client = client
    
    async def __aenter__(self) -> MCPClient:
        """Enter context and connect client"""
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and disconnect client"""
        await self.client.disconnect()


def temporary_mcp_client(
    url: str,
    bearer_token: Optional[str] = None,
    transport_type: str = "streamable_http",
    headers: Optional[Dict[str, str]] = None
) -> TemporaryMCPClient:
    """Create temporary MCP client context manager"""
    from ..config import settings
    
    transport_enum = (
        TransportType.STREAMABLE_HTTP 
        if transport_type == "streamable_http" 
        else TransportType.SSE
    )
    
    config = MCPConfig(
        url=url,
        transport_type=transport_enum,
        bearer_token=bearer_token,
        headers=headers,
        timeout=settings.mcp_timeout,
        retry_attempts=settings.mcp_retry_attempts
    )
    
    client = MCPClient(config)
    return TemporaryMCPClient(client)


# ============================================================================
# Authentication Helper Functions
# ============================================================================

def create_bearer_auth(token: str) -> BearerAuthProvider:
    """Create bearer token authentication provider"""
    return BearerAuthProvider(token)


def create_api_key_auth(api_key: str, header_name: str = "X-API-Key") -> APIKeyAuthProvider:
    """Create API key authentication provider"""
    return APIKeyAuthProvider(api_key, header_name)


def create_basic_auth(username: str, password: str) -> BasicAuthProvider:
    """Create basic authentication provider"""
    return BasicAuthProvider(username, password)


def create_custom_header_auth(headers: Dict[str, str]) -> CustomHeaderAuthProvider:
    """Create custom header authentication provider"""
    return CustomHeaderAuthProvider(headers)


def create_auth_manager(auth_type: str, **kwargs) -> AuthManager:
    """Create authentication manager with specified type"""
    if auth_type == "bearer":
        if "token" not in kwargs:
            raise ValueError("Bearer token is required")
        provider = create_bearer_auth(kwargs["token"])
        
    elif auth_type == "api_key":
        if "api_key" not in kwargs:
            raise ValueError("API key is required")
        header_name = kwargs.get("header_name", "X-API-Key")
        provider = create_api_key_auth(kwargs["api_key"], header_name)
        
    elif auth_type == "basic":
        if "username" not in kwargs or "password" not in kwargs:
            raise ValueError("Username and password are required")
        provider = create_basic_auth(kwargs["username"], kwargs["password"])
        
    elif auth_type == "custom":
        if "headers" not in kwargs:
            raise ValueError("Custom headers are required")
        provider = create_custom_header_auth(kwargs["headers"])
        
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")
    
    return AuthManager(provider)