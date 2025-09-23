"""
Utility modules for the application.
"""

from .typescript_formatter import (
    TypeScriptFormatter,
    get_formatter,
    format_typescript_code,
    format_test_case_code,
    format_fixture_code,
    format_typescript_file
)

# MCP Client Library (all-in-one)
from .mcp_client import (
    # Core client and config
    MCPClient,
    MCPConfig,
    TransportType,
    MCPClientError,
    MCPConnectionError,
    MCPAuthenticationError,
    
    # Authentication providers
    AuthManager,
    BearerAuthProvider,
    APIKeyAuthProvider,
    BasicAuthProvider,
    CustomHeaderAuthProvider,
    create_bearer_auth,
    create_api_key_auth,
    create_basic_auth,
    create_custom_header_auth,
    create_auth_manager,
    
    # Service and factory functions
    MCPService,
    mcp_service,
    get_default_mcp_client,
    create_mcp_client_from_config,
    create_streamable_http_client,
    create_sse_client,
    temporary_mcp_client,
    TemporaryMCPClient
)

# AI Provider Library
from .ai_provider import (
    # Core types and enums
    AIProviderType,
    MessageRole,
    
    # Exceptions
    AIProviderError,
    AIProviderConnectionError,
    AIProviderAuthenticationError,
    AIProviderRateLimitError,
    AIProviderQuotaExceededError,
    AIProviderModelNotFoundError,
    
    # Data models
    AIMessage,
    AIUsage,
    AIResponse,
    AIModel,
    
    # Providers
    BaseAIProvider,
    OpenAIProvider,
    
    # Service
    AIService,
    ai_service,
    
    # Convenience functions
    get_default_ai_provider,
    create_openai_provider,
    chat_completion,
    temporary_openai_provider,
    TemporaryAIProvider,
    
    # Helper functions
    create_system_message,
    create_user_message,
    create_assistant_message,
    create_conversation,
    quick_chat
)

__all__ = [
    # TypeScript formatter
    'TypeScriptFormatter',
    'get_formatter', 
    'format_typescript_code',
    'format_test_case_code',
    'format_fixture_code',
    'format_typescript_file',
    
    # MCP Client core
    'MCPClient',
    'MCPConfig',
    'TransportType',
    'MCPClientError',
    'MCPConnectionError',
    'MCPAuthenticationError',
    
    # MCP Authentication
    'AuthManager',
    'BearerAuthProvider',
    'APIKeyAuthProvider',
    'BasicAuthProvider',
    'CustomHeaderAuthProvider',
    'create_bearer_auth',
    'create_api_key_auth',
    'create_basic_auth',
    'create_custom_header_auth',
    'create_auth_manager',
    
    # MCP Factory and Service
    'MCPService',
    'mcp_service',
    'get_default_mcp_client',
    'create_mcp_client_from_config',
    'create_streamable_http_client',
    'create_sse_client',
    'temporary_mcp_client',
    'TemporaryMCPClient',
    
    # AI Provider system
    'AIProviderType',
    'MessageRole',
    'AIProviderError',
    'AIProviderConnectionError',
    'AIProviderAuthenticationError',
    'AIProviderRateLimitError',
    'AIProviderQuotaExceededError',
    'AIProviderModelNotFoundError',
    'AIMessage',
    'AIUsage',
    'AIResponse',
    'AIModel',
    'BaseAIProvider',
    'OpenAIProvider',
    'AIService',
    'ai_service',
    'get_default_ai_provider',
    'create_openai_provider',
    'chat_completion',
    'temporary_openai_provider',
    'TemporaryAIProvider',
    'create_system_message',
    'create_user_message',
    'create_assistant_message',
    'create_conversation',
    'quick_chat',

]
