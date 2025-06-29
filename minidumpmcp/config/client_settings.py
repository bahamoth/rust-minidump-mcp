"""Client configuration settings using Pydantic Settings."""

from typing import Any, Literal, Tuple, Type

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


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
        default="stdio",
        description="Transport type to use",
    )
    timeout: float = Field(
        default=30.0,
        ge=0.1,
        description="Request timeout in seconds",
    )

    @property
    def config_dict(self) -> dict[str, dict[str, Any]]:
        """Get configuration dictionary for FastMCP Client.

        Returns:
            Configuration dictionary with server name as key.
        """
        if self.transport == "stdio":
            return {
                "RustMinidumpMcp": {
                    "command": "python",
                    "args": ["-m", "minidumpmcp", "server", "--transport", "stdio"],
                    "transport": "stdio",
                }
            }
        else:  # streamable-http, sse
            return {
                "RustMinidumpMcp": {
                    "url": self.url,
                    "transport": self.transport,
                }
            }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources priority.

        Priority order (highest to lowest):
        1. init_settings: Arguments passed to the constructor
        2. env_settings: Environment variables
        3. dotenv_settings: .env file

        This allows CLI arguments to override environment variables and .env files.
        """
        return (init_settings, env_settings, dotenv_settings)
