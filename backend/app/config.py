from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict, Any
import secrets
import os
import logging
from pathlib import Path
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

def load_env_file() -> Dict[str, str]:
    """Load .env file and return as dictionary"""
    env_vars = {}
    env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        logger.info(f"Loading .env file from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value
                    # Also set in os.environ for compatibility
                    os.environ[key] = value
        logger.info(f"Loaded {len(env_vars)} environment variables from .env")
    else:
        logger.warning(f".env file not found at: {env_file}")
    
    return env_vars

# Load .env file immediately
_env_vars = load_env_file()

class Settings(BaseSettings):
    # Database settings - individual components for safer handling
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "testmanager_user"
    db_password: str = "testmanager_password"
    db_name: str = "testmanager_db"
    db_driver: str = "postgresql"
    
    # Computed database URL property
    @property
    def database_url(self) -> str:
        """Generate database URL with proper encoding of special characters"""
        # URL encode username and password to handle special characters
        encoded_user = quote_plus(self.db_user)
        encoded_password = quote_plus(self.db_password)
        return f"{self.db_driver}://{encoded_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # App settings
    app_name: str = "AI Test Manager API"
    debug: bool = True
    
    # Security settings
    secret_key: str = secrets.token_urlsafe(32)  # Generate secure key by default
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7  # New setting for refresh token expiration
    
    
    # OpenAI settings
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    
    # Playwright settings
    playwright_projects_path: str = "./playwright_projects"
    
    # MCP settings
    mcp_server_url: str = ""
    mcp_bearer_token: str = ""
    mcp_transport_type: str = "streamable_http"  # streamable_http or sse
    mcp_timeout: float = 30.0
    mcp_retry_attempts: int = 3
    
    # AI Context settings for better planning
    ai_context_include_project_settings: bool = True
    ai_context_include_browser_settings: bool = True
    ai_context_include_environment_info: bool = True
    ai_context_max_length: int = 2000  # Maximum context length to avoid token limits
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="TESTMANAGER_",  # Environment variables should be prefixed with TESTMANAGER_
        # Allow computed properties to work properly
        computed_fields={'database_url'}
    )


# Create settings instance - will automatically use loaded environment variables
settings = Settings()

# Log final configuration for debugging
logger.info(f"✅ Configuration loaded:")
logger.info(f"  MCP Server URL: {repr(settings.mcp_server_url)}")
logger.info(f"  MCP Transport: {repr(settings.mcp_transport_type)}")
logger.info(f"  OpenAI Model: {repr(settings.openai_model)}")
logger.info(f"  Playwright Projects Path: {repr(settings.playwright_projects_path)}")