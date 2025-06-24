"""Tests for custom exception classes."""

from pathlib import Path

from minidumpmcp.exceptions import (
    ConfigurationError,
    ConnectionError,
    FileValidationError,
    MinidumpAnalysisError,
    MinidumpMCPError,
    PathTraversalError,
    SymbolExtractionError,
    ToolExecutionError,
    ToolNotFoundError,
)


class TestMinidumpMCPError:
    """Test base exception class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = MinidumpMCPError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}
        assert error.suggestion is None
        assert error.error_code is None

    def test_error_with_context(self) -> None:
        """Test error with context."""
        error = MinidumpMCPError("Test error", context={"file": "test.dmp", "size": 1024})
        assert "Context: file=test.dmp, size=1024" in str(error)

    def test_error_with_suggestion(self) -> None:
        """Test error with suggestion."""
        error = MinidumpMCPError("Test error", suggestion="Try this solution")
        assert "Suggestion: Try this solution" in str(error)

    def test_error_with_all_fields(self) -> None:
        """Test error with all fields."""
        error = MinidumpMCPError(
            "Test error",
            context={"key": "value"},
            suggestion="Do this",
            error_code="TEST_ERROR",
        )
        assert "Test error" in str(error)
        assert "Context: key=value" in str(error)
        assert "Suggestion: Do this" in str(error)
        assert error.error_code == "TEST_ERROR"


class TestToolErrors:
    """Test tool-related errors."""

    def test_tool_not_found_error(self) -> None:
        """Test ToolNotFoundError."""
        error = ToolNotFoundError("minidump-stackwalk", [Path("/usr/bin"), Path("/usr/local/bin")])
        assert "Required tool 'minidump-stackwalk' not found" in str(error)
        assert "Run 'just install-tools'" in str(error)
        assert error.error_code == "TOOL_NOT_FOUND"

    def test_tool_execution_error(self) -> None:
        """Test ToolExecutionError."""
        error = ToolExecutionError(
            "dump_syms",
            ["dump_syms", "test.exe"],
            1,
            "Permission denied",
        )
        assert "Tool 'dump_syms' failed with exit code 1" in str(error)
        assert "Check file permissions" in str(error)
        assert error.error_code == "TOOL_EXECUTION_FAILED"

    def test_tool_execution_error_timeout(self) -> None:
        """Test ToolExecutionError with timeout suggestion."""
        error = ToolExecutionError(
            "minidump-stackwalk",
            ["minidump-stackwalk", "large.dmp"],
            -1,
            "Operation timeout",
        )
        assert "Try increasing the timeout" in str(error)


class TestFileErrors:
    """Test file-related errors."""

    def test_file_validation_error(self) -> None:
        """Test FileValidationError."""
        error = FileValidationError(Path("/tmp/test.dmp"), "File not found")
        assert "File validation failed for '/tmp/test.dmp'" in str(error)
        assert "Check the file path" in str(error)
        assert error.error_code == "FILE_VALIDATION_FAILED"

    def test_file_validation_too_large(self) -> None:
        """Test FileValidationError for large files."""
        error = FileValidationError(Path("huge.dmp"), "File too large (2GB)")
        assert "Try processing a smaller file" in str(error)

    def test_path_traversal_error(self) -> None:
        """Test PathTraversalError."""
        error = PathTraversalError("../../../etc/passwd")
        assert "Potential path traversal attack detected" in str(error)
        assert "Use absolute paths" in str(error)
        assert error.error_code == "PATH_TRAVERSAL_DETECTED"


class TestAnalysisErrors:
    """Test analysis-related errors."""

    def test_minidump_analysis_error(self) -> None:
        """Test MinidumpAnalysisError."""
        error = MinidumpAnalysisError(
            Path("crash.dmp"),
            "Minidump is corrupted",
            {"offset": "0x1000", "expected": "MDMP"},
        )
        assert "Failed to analyze minidump 'crash.dmp'" in str(error)
        assert "may be corrupted" in str(error)
        assert error.error_code == "MINIDUMP_ANALYSIS_FAILED"

    def test_symbol_extraction_error(self) -> None:
        """Test SymbolExtractionError."""
        error = SymbolExtractionError(
            Path("app.exe"),
            "Unsupported format: ARM64",
        )
        assert "Failed to extract symbols from 'app.exe'" in str(error)
        assert "Ensure the binary is a supported format" in str(error)
        assert error.error_code == "SYMBOL_EXTRACTION_FAILED"


class TestConfigurationErrors:
    """Test configuration errors."""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        error = ConfigurationError("transport", "invalid-transport", "Unknown transport type")
        assert "Invalid configuration for 'transport'" in str(error)
        assert "Valid transports are: stdio, streamable-http, sse" in str(error)
        assert error.error_code == "CONFIGURATION_ERROR"

    def test_configuration_error_port(self) -> None:
        """Test ConfigurationError for port."""
        error = ConfigurationError("port", 99999, "Port out of range")
        assert "Port must be between 1 and 65535" in str(error)


class TestNetworkErrors:
    """Test network-related errors."""

    def test_connection_error(self) -> None:
        """Test ConnectionError."""
        error = ConnectionError(
            "http://localhost:8000/mcp",
            "Connection refused",
            "streamable-http",
        )
        assert "Failed to connect to server" in str(error)
        assert "may not be running" in str(error)
        assert error.error_code == "CONNECTION_ERROR"

    def test_connection_error_timeout(self) -> None:
        """Test ConnectionError with timeout."""
        error = ConnectionError(
            "http://remote:8080/api",
            "Request timeout after 30s",
        )
        assert "not responding" in str(error)
        assert "increase timeout" in str(error)
