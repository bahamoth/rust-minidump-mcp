"""Tests for client configuration."""

import os
from unittest.mock import patch

import pytest

from minidumpmcp.config.client_settings import ClientSettings


class TestClientSettings:
    """Test client settings configuration."""

    def test_default_settings(self) -> None:
        """Test default client settings."""
        settings = ClientSettings()
        assert settings.url == "http://localhost:8000/mcp"
        assert settings.transport == "stdio"
        assert settings.timeout == 30.0

    def test_env_var_override(self) -> None:
        """Test environment variable overrides."""
        with patch.dict(
            os.environ,
            {
                "MINIDUMP_MCP_CLIENT_URL": "http://custom:9000/api",
                "MINIDUMP_MCP_CLIENT_TRANSPORT": "sse",
                "MINIDUMP_MCP_CLIENT_TIMEOUT": "60",
            },
        ):
            settings = ClientSettings()
            assert settings.url == "http://custom:9000/api"
            assert settings.transport == "sse"
            assert settings.timeout == 60.0

    def test_direct_instantiation(self) -> None:
        """Test direct instantiation with parameters."""
        settings = ClientSettings(
            url="http://test:8080/mcp",
            transport="stdio",
            timeout=45.0,
        )
        assert settings.url == "http://test:8080/mcp"
        assert settings.transport == "stdio"
        assert settings.timeout == 45.0

    def test_config_dict_property(self) -> None:
        """Test config_dict property for FastMCP Client."""
        settings = ClientSettings(
            url="http://example.com/mcp",
            transport="streamable-http",
        )
        config = settings.config_dict
        assert "RustMinidumpMcp" in config
        assert config["RustMinidumpMcp"]["url"] == "http://example.com/mcp"
        assert config["RustMinidumpMcp"]["transport"] == "streamable-http"

    def test_invalid_transport(self) -> None:
        """Test invalid transport type raises error."""
        with pytest.raises(ValueError, match="Input should be"):
            ClientSettings(transport="invalid")  # type: ignore[arg-type]

    def test_invalid_timeout(self) -> None:
        """Test invalid timeout value."""
        with pytest.raises(ValueError, match="Input should be greater than or equal to 0.1"):
            ClientSettings(timeout=0.05)

    def test_mixed_config_sources(self) -> None:
        """Test configuration priority: direct > env > default."""
        with patch.dict(
            os.environ,
            {
                "MINIDUMP_MCP_CLIENT_URL": "http://env:8000/mcp",
                "MINIDUMP_MCP_CLIENT_TIMEOUT": "45",
            },
        ):
            # Direct parameter should override env var
            settings = ClientSettings(url="http://direct:9000/api")
            assert settings.url == "http://direct:9000/api"  # Direct override
            assert settings.timeout == 45.0  # From env var
            assert settings.transport == "stdio"  # Default
