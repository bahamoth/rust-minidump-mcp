"""Custom exceptions for minidump-mcp with detailed error messages and recovery suggestions."""

from pathlib import Path
from typing import Any, Optional


class MinidumpMCPError(Exception):
    """Base exception for all minidump-mcp errors.

    Provides structured error information with context and recovery suggestions.
    """

    def __init__(
        self,
        message: str,
        *,
        context: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize error with detailed information.

        Args:
            message: Primary error message
            context: Additional context about the error (e.g., file paths, commands)
            suggestion: Actionable suggestion for resolving the error
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestion = suggestion
        self.error_code = error_code

    def __str__(self) -> str:
        """Format error message with context and suggestion."""
        parts = [self.message]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts)


# Tool-related errors
class ToolNotFoundError(MinidumpMCPError):
    """Raised when a required tool binary is not found."""

    def __init__(self, tool_name: str, searched_paths: Optional[list[Path]] = None) -> None:
        """Initialize tool not found error."""
        message = f"Required tool '{tool_name}' not found"
        context: dict[str, Any] = {"tool": tool_name}
        if searched_paths:
            context["searched_paths"] = [str(p) for p in searched_paths]

        suggestion = f"Run 'just install-tools' to install {tool_name}, or ensure it's available on your PATH"

        super().__init__(message, context=context, suggestion=suggestion, error_code="TOOL_NOT_FOUND")


class ToolExecutionError(MinidumpMCPError):
    """Raised when a tool execution fails."""

    def __init__(
        self,
        tool_name: str,
        command: list[str],
        exit_code: int,
        stderr: Optional[str] = None,
    ) -> None:
        """Initialize tool execution error."""
        message = f"Tool '{tool_name}' failed with exit code {exit_code}"
        context = {
            "tool": tool_name,
            "command": " ".join(command),
            "exit_code": exit_code,
        }
        if stderr:
            context["stderr"] = stderr.strip()

        # Provide specific suggestions based on common error patterns
        suggestion = "Check the command output for details"
        if stderr:
            if "permission denied" in stderr.lower():
                suggestion = f"Check file permissions for {tool_name}"
            elif "not found" in stderr.lower():
                suggestion = "Ensure all required files exist and paths are correct"
            elif "timeout" in stderr.lower():
                suggestion = "Try increasing the timeout or processing smaller files"

        super().__init__(message, context=context, suggestion=suggestion, error_code="TOOL_EXECUTION_FAILED")


# File-related errors
class FileValidationError(MinidumpMCPError):
    """Raised when file validation fails."""

    def __init__(self, path: Path, reason: str) -> None:
        """Initialize file validation error."""
        message = f"File validation failed for '{path}': {reason}"
        context = {"path": str(path), "reason": reason}

        suggestion = None
        if "not found" in reason.lower():
            suggestion = "Check the file path and ensure the file exists"
        elif "not a file" in reason.lower():
            suggestion = "Ensure the path points to a file, not a directory"
        elif "too large" in reason.lower():
            suggestion = "Try processing a smaller file or increase the size limit"
        elif "invalid format" in reason.lower():
            suggestion = "Ensure the file is a valid minidump (.dmp) or symbol file"

        super().__init__(message, context=context, suggestion=suggestion, error_code="FILE_VALIDATION_FAILED")


class PathTraversalError(MinidumpMCPError):
    """Raised when a potential path traversal attack is detected."""

    def __init__(self, path: str) -> None:
        """Initialize path traversal error."""
        message = "Potential path traversal attack detected"
        context = {"path": path}
        suggestion = "Use absolute paths or paths relative to the current directory"

        super().__init__(message, context=context, suggestion=suggestion, error_code="PATH_TRAVERSAL_DETECTED")


# Analysis-related errors
class MinidumpAnalysisError(MinidumpMCPError):
    """Raised when minidump analysis fails."""

    def __init__(self, minidump_path: Path, reason: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize minidump analysis error."""
        message = f"Failed to analyze minidump '{minidump_path.name}': {reason}"
        context = {"minidump": str(minidump_path), "reason": reason}
        if details:
            context.update(details)

        suggestion = None
        if "corrupt" in reason.lower():
            suggestion = "The minidump file may be corrupted. Try obtaining a fresh copy"
        elif "unsupported" in reason.lower():
            suggestion = "This minidump format may not be supported. Check the minidump version"
        elif "symbols" in reason.lower():
            suggestion = "Provide symbol files for better analysis results"

        super().__init__(message, context=context, suggestion=suggestion, error_code="MINIDUMP_ANALYSIS_FAILED")


class SymbolExtractionError(MinidumpMCPError):
    """Raised when symbol extraction fails."""

    def __init__(self, binary_path: Path, reason: str) -> None:
        """Initialize symbol extraction error."""
        message = f"Failed to extract symbols from '{binary_path.name}': {reason}"
        context = {"binary": str(binary_path), "reason": reason}

        suggestion = None
        if "unsupported format" in reason.lower():
            suggestion = "Ensure the binary is a supported format (PDB, DWARF)"
        elif "no debug info" in reason.lower():
            suggestion = "The binary may not contain debug information"

        super().__init__(message, context=context, suggestion=suggestion, error_code="SYMBOL_EXTRACTION_FAILED")


# Configuration errors
class ConfigurationError(MinidumpMCPError):
    """Raised when configuration is invalid."""

    def __init__(self, setting: str, value: Any, reason: str) -> None:
        """Initialize configuration error."""
        message = f"Invalid configuration for '{setting}': {reason}"
        context = {"setting": setting, "value": str(value), "reason": reason}

        suggestion = f"Check the documentation for valid values of '{setting}'"
        if "transport" in setting.lower():
            suggestion = "Valid transports are: stdio, streamable-http, sse"
        elif "port" in setting.lower():
            suggestion = "Port must be between 1 and 65535"
        elif "timeout" in setting.lower():
            suggestion = "Timeout must be a positive number (in seconds)"

        super().__init__(message, context=context, suggestion=suggestion, error_code="CONFIGURATION_ERROR")


# Network errors
class ConnectionError(MinidumpMCPError):
    """Raised when connection to server fails."""

    def __init__(self, url: str, reason: str, transport: Optional[str] = None) -> None:
        """Initialize connection error."""
        message = f"Failed to connect to server at '{url}': {reason}"
        context = {"url": url, "reason": reason}
        if transport:
            context["transport"] = transport

        suggestion = "Ensure the server is running and accessible at the specified URL"
        if "refused" in reason.lower():
            suggestion = "The server may not be running. Start it with 'minidump-mcp server'"
        elif "timeout" in reason.lower():
            suggestion = "The server is not responding. Check if it's overloaded or increase timeout"
        elif "not found" in reason.lower():
            suggestion = "Check the URL path. For HTTP transport, the default path is '/mcp'"

        super().__init__(message, context=context, suggestion=suggestion, error_code="CONNECTION_ERROR")
