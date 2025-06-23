"""Tests for server configuration settings."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from minidumpmcp.config import ServerSettings
from minidumpmcp.config.settings import (
    SseTransportConfig,
    StdioTransportConfig,
    StreamableHttpConfig,
)


class TestServerSettings:
    """Test cases for ServerSettings configuration."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = ServerSettings()

        assert settings.name == "minidump-mcp"
        assert settings.transport == "streamable-http"
        assert settings.log_level == "INFO"
        assert isinstance(settings.transport_config, StreamableHttpConfig)

    def test_programmatic_configuration(self) -> None:
        """Test programmatic configuration of settings."""
        settings = ServerSettings(
            name="test-server",
            transport="stdio",
            log_level="DEBUG",
        )

        assert settings.name == "test-server"
        assert settings.transport == "stdio"
        assert settings.log_level == "DEBUG"
        assert isinstance(settings.transport_config, StdioTransportConfig)

    def test_transport_config_selection(self) -> None:
        """Test that transport_config returns the correct configuration type."""
        # Test STDIO
        stdio_settings = ServerSettings(transport="stdio")
        assert isinstance(stdio_settings.transport_config, StdioTransportConfig)

        # Test Streamable HTTP
        http_settings = ServerSettings(transport="streamable-http")
        assert isinstance(http_settings.transport_config, StreamableHttpConfig)

        # Test SSE
        sse_settings = ServerSettings(transport="sse")
        assert isinstance(sse_settings.transport_config, SseTransportConfig)

    def test_nested_transport_configuration(self) -> None:
        """Test modifying nested transport configurations."""
        settings = ServerSettings(transport="streamable-http")

        # Modify HTTP configuration
        settings.streamable_http.host = "0.0.0.0"
        settings.streamable_http.port = 9000
        settings.streamable_http.path = "/api/mcp"

        config = settings.transport_config
        assert isinstance(config, StreamableHttpConfig)
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.path == "/api/mcp"

    def test_log_level_validation(self) -> None:
        """Test log level validation and normalization."""
        # Valid log levels - test with explicit strings
        settings_debug = ServerSettings(log_level="DEBUG")
        assert settings_debug.log_level == "DEBUG"

        settings_info = ServerSettings(log_level="INFO")
        assert settings_info.log_level == "INFO"

        # Test case normalization - use model_validate for this test
        data_lower = {"log_level": "debug"}
        settings_lower = ServerSettings.model_validate(data_lower)
        assert settings_lower.log_level == "DEBUG"

        # Invalid log level should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            ServerSettings.model_validate({"log_level": "INVALID"})
        assert "literal_error" in str(exc_info.value)

    def test_transport_validation(self) -> None:
        """Test transport type validation."""
        # Valid transports - test explicitly
        stdio_settings = ServerSettings(transport="stdio")
        assert stdio_settings.transport == "stdio"

        http_settings = ServerSettings(transport="streamable-http")
        assert http_settings.transport == "streamable-http"

        sse_settings = ServerSettings(transport="sse")
        assert sse_settings.transport == "sse"

        # Invalid transport should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            ServerSettings.model_validate({"transport": "invalid-transport"})
        assert "value_error" in str(exc_info.value)

    def test_port_validation(self) -> None:
        """Test port range validation for HTTP-based transports."""
        settings = ServerSettings(transport="streamable-http")

        # Valid port ranges
        for port in [1, 8000, 65535]:
            settings.streamable_http.port = port
            # Should not raise any errors during post-init validation
            settings.model_post_init(None)

        # Invalid port ranges should raise validation error
        settings_low = ServerSettings(transport="streamable-http")
        settings_low.streamable_http.port = 0
        with pytest.raises(ValueError, match="Invalid port: 0"):
            settings_low.model_post_init(None)

        settings_high = ServerSettings(transport="streamable-http")
        settings_high.streamable_http.port = 70000
        with pytest.raises(ValueError, match="Invalid port: 70000"):
            settings_high.model_post_init(None)


class TestEnvironmentVariables:
    """Test cases for environment variable configuration."""

    def test_basic_env_vars(self, monkeypatch: MonkeyPatch) -> None:
        """Test basic environment variable configuration."""
        monkeypatch.setenv("MINIDUMP_MCP_NAME", "env-server")
        monkeypatch.setenv("MINIDUMP_MCP_TRANSPORT", "streamable-http")
        monkeypatch.setenv("MINIDUMP_MCP_LOG_LEVEL", "DEBUG")

        settings = ServerSettings()

        assert settings.name == "env-server"
        assert settings.transport == "streamable-http"
        assert settings.log_level == "DEBUG"

    def test_nested_env_vars(self, monkeypatch: MonkeyPatch) -> None:
        """Test nested environment variable configuration."""
        monkeypatch.setenv("MINIDUMP_MCP_TRANSPORT", "streamable-http")
        monkeypatch.setenv("MINIDUMP_MCP_STREAMABLE_HTTP__HOST", "0.0.0.0")
        monkeypatch.setenv("MINIDUMP_MCP_STREAMABLE_HTTP__PORT", "8080")
        monkeypatch.setenv("MINIDUMP_MCP_STREAMABLE_HTTP__PATH", "/api/mcp")
        monkeypatch.setenv("MINIDUMP_MCP_STREAMABLE_HTTP__CORS_ENABLED", "false")

        settings = ServerSettings()

        assert settings.transport == "streamable-http"
        config = settings.transport_config
        assert isinstance(config, StreamableHttpConfig)
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.path == "/api/mcp"
        assert config.cors_enabled is False

    def test_sse_env_vars(self, monkeypatch: MonkeyPatch) -> None:
        """Test SSE-specific environment variables."""
        monkeypatch.setenv("MINIDUMP_MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MINIDUMP_MCP_SSE__HOST", "localhost")
        monkeypatch.setenv("MINIDUMP_MCP_SSE__PORT", "8001")
        monkeypatch.setenv("MINIDUMP_MCP_SSE__MESSAGE_PATH", "/msg")
        monkeypatch.setenv("MINIDUMP_MCP_SSE__SSE_PATH", "/events")

        settings = ServerSettings()

        assert settings.transport == "sse"
        config = settings.transport_config
        assert isinstance(config, SseTransportConfig)
        assert config.host == "localhost"
        assert config.port == 8001
        assert config.message_path == "/msg"
        assert config.sse_path == "/events"

    def test_env_file_loading(self, tmp_path: Path) -> None:
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
MINIDUMP_MCP_NAME=file-server
MINIDUMP_MCP_TRANSPORT=streamable-http
MINIDUMP_MCP_STREAMABLE_HTTP__PORT=9000
        """.strip()
        )

        # Change to the temp directory so .env is found
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            settings = ServerSettings()

            assert settings.name == "file-server"
            assert settings.transport == "streamable-http"
            config = settings.transport_config
            assert isinstance(config, StreamableHttpConfig)
            assert config.port == 9000
        finally:
            os.chdir(original_cwd)


class TestTransportConfigs:
    """Test cases for individual transport configuration classes."""

    def test_stdio_config(self) -> None:
        """Test STDIO transport configuration."""
        config = StdioTransportConfig()
        assert config.timeout == 30.0

    def test_streamable_http_config(self) -> None:
        """Test Streamable HTTP transport configuration."""
        config = StreamableHttpConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.path == "/mcp"
        assert config.cors_enabled is True
        assert config.json_response is False
        assert config.stateless_http is False
        assert config.timeout == 30.0

    def test_sse_config(self) -> None:
        """Test SSE transport configuration."""
        config = SseTransportConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.path == "/mcp"
        assert config.message_path == "/message"
        assert config.sse_path == "/sse"
        assert config.cors_enabled is True
        assert config.timeout == 30.0

    def test_http_config_inheritance(self) -> None:
        """Test that HTTP configs inherit from base classes correctly."""
        # StreamableHttpConfig should inherit from HttpTransportConfig
        config = StreamableHttpConfig(host="test.com", port=9000)
        assert config.host == "test.com"
        assert config.port == 9000
        assert config.timeout == 30.0  # From BaseTransportConfig

        # SseTransportConfig should also inherit from HttpTransportConfig
        sse_config = SseTransportConfig(host="sse.com", port=9001)
        assert sse_config.host == "sse.com"
        assert sse_config.port == 9001
        assert sse_config.timeout == 30.0  # From BaseTransportConfig


class TestValidationEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_host_validation(self) -> None:
        """Test validation of empty host values."""
        settings = ServerSettings(transport="streamable-http")
        settings.streamable_http.host = ""

        with pytest.raises(ValueError, match="Host cannot be empty"):
            settings.model_post_init(None)

    def test_invalid_port_validation(self) -> None:
        """Test validation of invalid port values."""
        settings = ServerSettings(transport="sse")

        # Test port too low
        settings.sse.port = 0
        with pytest.raises(ValueError, match="Invalid port: 0"):
            settings.model_post_init(None)

        # Test port too high
        settings.sse.port = 70000
        with pytest.raises(ValueError, match="Invalid port: 70000"):
            settings.model_post_init(None)

    def test_case_insensitive_env_vars(self, monkeypatch: MonkeyPatch) -> None:
        """Test that environment variables are case insensitive."""
        monkeypatch.setenv("minidump_mcp_log_level", "warning")
        monkeypatch.setenv("MINIDUMP_MCP_TRANSPORT", "sse")

        settings = ServerSettings()

        assert settings.log_level == "WARNING"  # Should be normalized
        assert settings.transport == "sse"  # Should work despite case

    def test_unknown_transport_error(self) -> None:
        """Test error handling for unknown transport in transport_config property."""
        settings = ServerSettings()
        # Manually set an invalid transport to test the property
        settings.__dict__["transport"] = "unknown"

        with pytest.raises(ValueError, match="Unknown transport: unknown"):
            _ = settings.transport_config


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complete_http_configuration(self, monkeypatch: MonkeyPatch) -> None:
        """Test complete HTTP configuration with all options."""
        # Set up comprehensive environment
        env_vars = {
            "MINIDUMP_MCP_NAME": "integration-test",
            "MINIDUMP_MCP_TRANSPORT": "streamable-http",
            "MINIDUMP_MCP_LOG_LEVEL": "DEBUG",
            "MINIDUMP_MCP_STREAMABLE_HTTP__HOST": "0.0.0.0",
            "MINIDUMP_MCP_STREAMABLE_HTTP__PORT": "8080",
            "MINIDUMP_MCP_STREAMABLE_HTTP__PATH": "/api/v1/mcp",
            "MINIDUMP_MCP_STREAMABLE_HTTP__CORS_ENABLED": "true",
            "MINIDUMP_MCP_STREAMABLE_HTTP__JSON_RESPONSE": "true",
            "MINIDUMP_MCP_STREAMABLE_HTTP__STATELESS_HTTP": "true",
            "MINIDUMP_MCP_STREAMABLE_HTTP__TIMEOUT": "60.0",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        settings = ServerSettings()

        # Verify main settings
        assert settings.name == "integration-test"
        assert settings.transport == "streamable-http"
        assert settings.log_level == "DEBUG"

        # Verify transport config
        config = settings.transport_config
        assert isinstance(config, StreamableHttpConfig)
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.path == "/api/v1/mcp"
        assert config.cors_enabled is True
        assert config.json_response is True
        assert config.stateless_http is True
        assert config.timeout == 60.0

    def test_mixed_configuration_sources(self, monkeypatch: MonkeyPatch) -> None:
        """Test mixing programmatic and environment configuration."""
        # Set some environment variables
        monkeypatch.setenv("MINIDUMP_MCP_TRANSPORT", "sse")
        monkeypatch.setenv("MINIDUMP_MCP_SSE__PORT", "8001")

        # Create settings with some programmatic overrides
        settings = ServerSettings(
            name="mixed-config",
            log_level="WARNING",
        )

        # Environment should override defaults, programmatic should override environment
        assert settings.name == "mixed-config"  # Programmatic override
        assert settings.transport == "sse"  # From environment
        assert settings.log_level == "WARNING"  # Programmatic override

        config = settings.transport_config
        assert isinstance(config, SseTransportConfig)
        assert config.port == 8001  # From environment
