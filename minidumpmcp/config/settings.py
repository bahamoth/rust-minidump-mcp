"""Server configuration settings using Pydantic Settings."""

from typing import Any, Literal, Tuple, Type, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class BaseTransportConfig(BaseModel):
    """Base configuration for all transport types."""

    timeout: float = Field(default=30.0, description="Request timeout in seconds")


class StdioTransportConfig(BaseTransportConfig):
    """Configuration for STDIO transport.

    STDIO transport requires minimal configuration as it uses
    standard input/output streams for communication.
    """


class HttpTransportConfig(BaseTransportConfig):
    """Base configuration for HTTP-based transports."""

    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, ge=1, le=65535, description="Port to bind to")
    path: str = Field(default="/mcp", description="HTTP endpoint path")
    cors_enabled: bool = Field(default=True, description="Enable CORS")


class StreamableHttpConfig(HttpTransportConfig):
    """Configuration for Streamable HTTP transport."""

    json_response: bool = Field(default=False, description="Use JSON response format")
    stateless_http: bool = Field(default=False, description="Enable stateless HTTP mode")


class SseTransportConfig(HttpTransportConfig):
    """Configuration for Server-Sent Events (SSE) transport."""

    message_path: str = Field(default="/message", description="Message endpoint path")
    sse_path: str = Field(default="/sse", description="SSE endpoint path")


# Union type for all transport configurations
TransportConfig = Union[StdioTransportConfig, StreamableHttpConfig, SseTransportConfig]


class ServerSettings(BaseSettings):
    """Main server configuration with environment variable support.

    Supports configuration through:
    - Environment variables with MINIDUMP_MCP_ prefix
    - .env files
    - Direct instantiation with parameters

    Environment variable examples:
    - MINIDUMP_MCP_NAME=my-server
    - MINIDUMP_MCP_TRANSPORT=streamable-http
    - MINIDUMP_MCP_STREAMABLE_HTTP__HOST=0.0.0.0
    - MINIDUMP_MCP_STREAMABLE_HTTP__PORT=8080
    """

    model_config = SettingsConfigDict(
        env_prefix="MINIDUMP_MCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Core server settings
    name: str = Field(default="rust-minidump-mcp", description="Server name")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", description="Logging level")

    # Transport selection
    transport: Literal["stdio", "streamable-http", "sse"] = Field(default="stdio", description="Transport type to use")

    # Transport-specific configurations
    stdio: StdioTransportConfig = Field(default_factory=StdioTransportConfig)
    streamable_http: StreamableHttpConfig = Field(default_factory=StreamableHttpConfig)
    sse: SseTransportConfig = Field(default_factory=SseTransportConfig)

    @property
    def transport_config(self) -> TransportConfig:
        """Get the configuration for the currently selected transport.

        Returns:
            The configuration object for the selected transport type.

        Raises:
            ValueError: If an unknown transport type is configured.
        """
        match self.transport:
            case "stdio":
                return self.stdio
            case "streamable-http":
                return self.streamable_http
            case "sse":
                return self.sse
            case _:
                raise ValueError(f"Unknown transport: {self.transport}")

    @field_validator("transport", mode="before")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate that the transport type is supported."""
        v = v.lower()  # Normalize to lowercase
        valid_transports = {"stdio", "streamable-http", "sse"}
        if v not in valid_transports:
            raise ValueError(f"Invalid transport '{v}'. Must be one of: {valid_transports}")
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize log level to uppercase."""
        return v.upper()

    def model_post_init(self, context: Any, /) -> None:
        """Perform additional validation after model initialization."""
        # Validate HTTP transport configurations
        match self.transport:
            case "streamable-http" | "sse":
                config = self.transport_config
                if isinstance(config, HttpTransportConfig):
                    if config.port < 1 or config.port > 65535:
                        raise ValueError(f"Invalid port: {config.port}. Must be between 1 and 65535")
                    if not config.host:
                        raise ValueError("Host cannot be empty for HTTP-based transports")

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
