"""Client configuration settings using Pydantic Settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    """Client configuration with environment variable support.

    Supports configuration through:
    - Environment variables with MINIDUMP_MCP_CLIENT_ prefix
    - .env files
    - Direct instantiation with parameters
    - CLI arguments

    Environment variable examples:
    - MINIDUMP_MCP_CLIENT_URL=http://localhost:8080/mcp
    - MINIDUMP_MCP_CLIENT_TRANSPORT=streamable-http
    - MINIDUMP_MCP_CLIENT_TIMEOUT=60
    """

    model_config = SettingsConfigDict(
        env_prefix="MINIDUMP_MCP_CLIENT_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Connection settings
    url: str = Field(
        default="http://localhost:8000/mcp",
        description="Server URL for HTTP/SSE transports",
    )
    transport: Literal["stdio", "streamable-http", "sse"] = Field(
        default="streamable-http",
        description="Transport type to use",
    )
    timeout: float = Field(
        default=30.0,
        ge=0.1,
        description="Request timeout in seconds",
    )

    @property
    def config_dict(self) -> dict[str, dict[str, str]]:
        """Get configuration dictionary for FastMCP Client.

        Returns:
            Configuration dictionary with server name as key.
        """
        return {
            "RustMinidumpMcp": {
                "url": self.url,
                "transport": self.transport,
            }
        }
