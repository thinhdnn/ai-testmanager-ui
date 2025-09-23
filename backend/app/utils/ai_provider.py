"""
AI Provider Library

A comprehensive AI provider system with support for OpenAI and other AI services.
Provides unified interface for chat completions, model management, and provider configuration.
"""

from typing import Dict, Optional, Any, List, Union, Protocol
from abc import ABC, abstractmethod
import httpx
import logging
from dataclasses import dataclass
from enum import Enum
import json
import asyncio

logger = logging.getLogger(__name__)


# ============================================================================
# Core Types and Enums
# ============================================================================

class AIProviderType(Enum):
    """Available AI provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class MessageRole(Enum):
    """Message roles in AI conversations"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


# ============================================================================
# Exceptions
# ============================================================================

class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass


class AIProviderConnectionError(AIProviderError):
    """Exception raised when AI provider connection fails"""
    pass


class AIProviderAuthenticationError(AIProviderError):
    """Exception raised when AI provider authentication fails"""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Exception raised when AI provider rate limit is exceeded"""
    pass


class AIProviderQuotaExceededError(AIProviderError):
    """Exception raised when AI provider quota is exceeded"""
    pass


class AIProviderModelNotFoundError(AIProviderError):
    """Exception raised when requested model is not found"""
    pass


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AIMessage:
    """Represents a message in AI conversation"""
    role: str  # "system", "user", "assistant", "function", "tool"
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        msg = {"role": self.role, "content": self.content}
        
        if self.name:
            msg["name"] = self.name
        if self.function_call:
            msg["function_call"] = self.function_call
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
            
        return msg
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIMessage':
        """Create AIMessage from dictionary"""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            function_call=data.get("function_call"),
            tool_calls=data.get("tool_calls")
        )
    
    @classmethod
    def system(cls, content: str) -> 'AIMessage':
        """Create system message"""
        return cls(role=MessageRole.SYSTEM.value, content=content)
    
    @classmethod
    def user(cls, content: str, name: Optional[str] = None) -> 'AIMessage':
        """Create user message"""
        return cls(role=MessageRole.USER.value, content=content, name=name)
    
    @classmethod
    def assistant(cls, content: str, name: Optional[str] = None) -> 'AIMessage':
        """Create assistant message"""
        return cls(role=MessageRole.ASSISTANT.value, content=content, name=name)


@dataclass
class AIUsage:
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @classmethod
    def from_openai(cls, usage_data: Dict[str, Any]) -> 'AIUsage':
        """Create from OpenAI usage format"""
        return cls(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )


@dataclass
class AIResponse:
    """Represents AI provider response"""
    content: str
    model: str
    usage: Optional[AIUsage] = None
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_openai_response(cls, response: Dict[str, Any], provider: str = "openai") -> 'AIResponse':
        """Create AIResponse from OpenAI API response"""
        choice = response.get('choices', [{}])[0]
        message = choice.get('message', {})
        
        usage = None
        if response.get('usage'):
            usage = AIUsage.from_openai(response['usage'])
        
        return cls(
            content=message.get('content', ''),
            model=response.get('model', ''),
            usage=usage,
            finish_reason=choice.get('finish_reason'),
            function_call=message.get('function_call'),
            tool_calls=message.get('tool_calls'),
            provider=provider,
            raw_response=response
        )


@dataclass
class AIModel:
    """Represents an AI model"""
    id: str
    name: str
    provider: str
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_functions: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    
    @classmethod
    def from_openai_model(cls, model_data: Dict[str, Any]) -> 'AIModel':
        """Create from OpenAI model format"""
        model_id = model_data.get("id", "")
        
        # Determine capabilities based on model ID
        supports_functions = "gpt-3.5" in model_id or "gpt-4" in model_id
        supports_tools = "gpt-3.5-turbo-1106" in model_id or "gpt-4" in model_id
        supports_vision = "vision" in model_id or "gpt-4-turbo" in model_id
        
        # Estimate context length based on model
        context_length = None
        if "gpt-4-turbo" in model_id:
            context_length = 128000
        elif "gpt-4" in model_id:
            context_length = 8192 if "gpt-4-32k" not in model_id else 32768
        elif "gpt-3.5-turbo" in model_id:
            context_length = 16385 if "16k" in model_id else 4096
        
        return cls(
            id=model_id,
            name=model_data.get("id", model_id),
            provider="openai",
            context_length=context_length,
            supports_functions=supports_functions,
            supports_tools=supports_tools,
            supports_vision=supports_vision
        )


# ============================================================================
# Base AI Provider Interface
# ============================================================================

class BaseAIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client instance"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self._client
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[AIModel]:
        """List available models"""
        pass
    
    async def validate_connection(self) -> bool:
        """Validate provider connection and credentials"""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# ============================================================================
# OpenAI Provider Implementation
# ============================================================================

class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        organization: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        super().__init__(api_key, base_url, timeout, max_retries)
        self.organization = organization
    
    def _get_headers(self) -> Dict[str, str]:
        """Get OpenAI authentication headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-TestManager/1.0"
        }
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        return headers
    
    async def chat_completion(
        self,
        messages: List[AIMessage],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[Union[str, Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate OpenAI chat completion"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature,
            "stream": stream,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if functions:
            payload["functions"] = functions
        if function_call:
            payload["function_call"] = function_call
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        
        try:
            response = await self._make_request_with_retry(url, payload)
            return AIResponse.from_openai_response(response, "openai")
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            raise AIProviderError(f"OpenAI provider error: {e}")
    
    async def list_models(self) -> List[AIModel]:
        """List available OpenAI models"""
        url = f"{self.base_url}/models"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get('data', []):
                try:
                    model = AIModel.from_openai_model(model_data)
                    models.append(model)
                except Exception as e:
                    logger.warning(f"Failed to parse model {model_data.get('id', 'unknown')}: {e}")
            
            return models
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except Exception as e:
            raise AIProviderError(f"OpenAI list models error: {e}")
    
    async def get_model_info(self, model_id: str) -> AIModel:
        """Get specific model information"""
        url = f"{self.base_url}/models/{model_id}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            model_data = response.json()
            return AIModel.from_openai_model(model_data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AIProviderModelNotFoundError(f"Model '{model_id}' not found")
            await self._handle_http_error(e)
        except Exception as e:
            raise AIProviderError(f"OpenAI get model error: {e}")
    
    async def _make_request_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [500, 502, 503, 504] and attempt < self.max_retries:
                    # Retry on server errors
                    wait_time = (2 ** attempt) * 1.0  # Exponential backoff
                    logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    raise e
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1.0
                    logger.warning(f"Connection error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    raise AIProviderConnectionError(f"Connection failed after {self.max_retries} retries: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
    
    async def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors with specific exception types"""
        status_code = error.response.status_code
        
        try:
            error_data = error.response.json()
            error_message = error_data.get('error', {}).get('message', str(error))
            error_code = error_data.get('error', {}).get('code')
        except:
            error_message = str(error)
            error_code = None
        
        if status_code == 401:
            raise AIProviderAuthenticationError(f"OpenAI authentication failed: {error_message}")
        elif status_code == 429:
            if error_code == "insufficient_quota":
                raise AIProviderQuotaExceededError(f"OpenAI quota exceeded: {error_message}")
            else:
                raise AIProviderRateLimitError(f"OpenAI rate limit exceeded: {error_message}")
        elif status_code == 404:
            raise AIProviderModelNotFoundError(f"OpenAI model not found: {error_message}")
        elif status_code >= 500:
            raise AIProviderConnectionError(f"OpenAI server error ({status_code}): {error_message}")
        else:
            raise AIProviderConnectionError(f"OpenAI API error ({status_code}): {error_message}")


# ============================================================================
# AI Service Management
# ============================================================================

class AIService:
    """Service for managing AI providers"""
    
    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider: Optional[BaseAIProvider] = None
        self._default_model: Optional[str] = None
    
    def register_provider(self, name: str, provider: BaseAIProvider) -> None:
        """Register an AI provider"""
        self._providers[name] = provider
        logger.info(f"Registered AI provider '{name}'")
    
    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        """Get registered AI provider by name"""
        return self._providers.get(name)
    
    def set_default_provider(self, provider: BaseAIProvider, model: Optional[str] = None) -> None:
        """Set default AI provider and model"""
        self._default_provider = provider
        self._default_model = model
        logger.info(f"Set default AI provider with model: {model or 'default'}")
    
    def get_default_provider(self) -> Optional[BaseAIProvider]:
        """Get default AI provider"""
        return self._default_provider
    
    def get_default_model(self) -> Optional[str]:
        """Get default model"""
        return self._default_model
    
    def create_openai_provider(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> OpenAIProvider:
        """Create OpenAI provider using configuration"""
        from ..config import settings
        
        # Use provided values or fall back to settings
        key = api_key or settings.openai_api_key
        url = base_url or settings.openai_base_url
        
        if not key:
            raise ValueError("OpenAI API key is required")
        
        provider = OpenAIProvider(
            api_key=key,
            base_url=url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries
        )
        
        return provider
    
    def create_default_openai_provider(self) -> OpenAIProvider:
        """Create default OpenAI provider and set as default"""
        from ..config import settings
        
        provider = self.create_openai_provider()
        self.set_default_provider(provider, settings.openai_model)
        self.register_provider("openai", provider)
        return provider
    
    def remove_provider(self, name: str) -> bool:
        """Remove registered provider"""
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Removed AI provider '{name}'")
            return True
        return False
    
    async def close_all_providers(self) -> None:
        """Close all registered providers"""
        for name, provider in self._providers.items():
            try:
                await provider.close()
                logger.info(f"Closed AI provider '{name}'")
            except Exception as e:
                logger.error(f"Error closing AI provider '{name}': {e}")
        
        if self._default_provider:
            try:
                await self._default_provider.close()
                logger.info("Closed default AI provider")
            except Exception as e:
                logger.error(f"Error closing default AI provider: {e}")
    
    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        providers = list(self._providers.keys())
        if self._default_provider:
            providers.append("default")
        return providers
    
    async def chat_with_default(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Chat using default provider"""
        if not self._default_provider:
            # Try to create default OpenAI provider
            try:
                self.create_default_openai_provider()
            except Exception as e:
                raise AIProviderError(f"No default provider available and failed to create OpenAI provider: {e}")
        
        # Use specified model or default model or fallback
        use_model = model or self._default_model or "gpt-4"
        
        return await self._default_provider.chat_completion(
            messages=messages,
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def get_available_models(self, provider_name: Optional[str] = None) -> Dict[str, List[AIModel]]:
        """Get available models from providers"""
        results = {}
        
        if provider_name:
            # Get models from specific provider
            provider = self.get_provider(provider_name)
            if provider:
                try:
                    models = await provider.list_models()
                    results[provider_name] = models
                except Exception as e:
                    logger.error(f"Failed to get models from {provider_name}: {e}")
                    results[provider_name] = []
        else:
            # Get models from all providers
            for name, provider in self._providers.items():
                try:
                    models = await provider.list_models()
                    results[name] = models
                except Exception as e:
                    logger.error(f"Failed to get models from {name}: {e}")
                    results[name] = []
        
        return results


# ============================================================================
# Global Service Instance and Convenience Functions
# ============================================================================

# Global AI service instance
ai_service = AIService()


def get_default_ai_provider() -> BaseAIProvider:
    """Get or create default AI provider"""
    provider = ai_service.get_default_provider()
    if provider is None:
        provider = ai_service.create_default_openai_provider()
    return provider


def create_openai_provider(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    organization: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3
) -> OpenAIProvider:
    """Create OpenAI provider with optional overrides"""
    return ai_service.create_openai_provider(
        api_key=api_key,
        base_url=base_url,
        organization=organization,
        timeout=timeout,
        max_retries=max_retries
    )


async def chat_completion(
    messages: Union[List[AIMessage], List[Dict[str, str]], str],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    provider: Optional[BaseAIProvider] = None,
    **kwargs
) -> AIResponse:
    """
    Convenient chat completion function
    
    Args:
        messages: Messages as AIMessage list, dict list, or single string
        model: Model name (uses config default if not specified)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        provider: AI provider to use (uses default if not specified)
        **kwargs: Additional provider-specific arguments
    
    Returns:
        AIResponse with generated content
    """
    # Convert messages to AIMessage format
    if isinstance(messages, str):
        ai_messages = [AIMessage.user(messages)]
    elif isinstance(messages, list):
        ai_messages = []
        for msg in messages:
            if isinstance(msg, AIMessage):
                ai_messages.append(msg)
            elif isinstance(msg, dict):
                ai_messages.append(AIMessage.from_dict(msg))
            else:
                raise ValueError(f"Invalid message format: {type(msg)}")
    else:
        raise ValueError(f"Invalid messages format: {type(messages)}")
    
    # Use provided provider or default
    if provider is None:
        return await ai_service.chat_with_default(
            messages=ai_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    else:
        return await provider.chat_completion(
            messages=ai_messages,
            model=model or "gpt-4",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


# Context manager for temporary AI provider
class TemporaryAIProvider:
    """Context manager for temporary AI provider connections"""
    
    def __init__(self, provider: BaseAIProvider):
        self.provider = provider
    
    async def __aenter__(self) -> BaseAIProvider:
        """Enter context"""
        return self.provider
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and close provider"""
        await self.provider.close()


def temporary_openai_provider(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    organization: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3
) -> TemporaryAIProvider:
    """Create temporary OpenAI provider context manager"""
    provider = create_openai_provider(
        api_key=api_key,
        base_url=base_url,
        organization=organization,
        timeout=timeout,
        max_retries=max_retries
    )
    return TemporaryAIProvider(provider)


# ============================================================================
# Helper Functions
# ============================================================================

def create_system_message(content: str) -> AIMessage:
    """Create system message"""
    return AIMessage.system(content)


def create_user_message(content: str, name: Optional[str] = None) -> AIMessage:
    """Create user message"""
    return AIMessage.user(content, name)


def create_assistant_message(content: str, name: Optional[str] = None) -> AIMessage:
    """Create assistant message"""
    return AIMessage.assistant(content, name)


def create_conversation(*messages: Union[str, AIMessage, Dict[str, str]]) -> List[AIMessage]:
    """Create conversation from mixed message types"""
    result = []
    
    for msg in messages:
        if isinstance(msg, str):
            result.append(AIMessage.user(msg))
        elif isinstance(msg, AIMessage):
            result.append(msg)
        elif isinstance(msg, dict):
            result.append(AIMessage.from_dict(msg))
        else:
            raise ValueError(f"Invalid message type: {type(msg)}")
    
    return result


async def quick_chat(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """Quick chat completion with simple prompt"""
    messages = []
    
    if system_prompt:
        messages.append(AIMessage.system(system_prompt))
    
    messages.append(AIMessage.user(prompt))
    
    response = await chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return response.content
