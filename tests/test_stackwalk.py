"""Tests for stackwalk tools."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from rust_minidump_mcp.tools.stackwalk import StackwalkProvider


class TestStackwalkProvider:
    """Tests for StackwalkProvider class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.provider = StackwalkProvider()

    def test_minidump_file_not_found(self) -> None:
        """Test handling of non-existent minidump file."""
        result = self.provider.stackwalk_minidump("/nonexistent/file.dmp")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_path_is_not_file(self, tmp_path: Path) -> None:
        """Test handling of directory path instead of file."""
        result = self.provider.stackwalk_minidump(str(tmp_path))

        assert result["success"] is False
        assert "not a file" in result["error"]

    def test_stackwalk_binary_not_found(self, tmp_path: Path) -> None:
        """Test handling of missing minidump-stackwalk binary."""
        # Create a temporary minidump file
        minidump_file = tmp_path / "test.dmp"
        minidump_file.write_bytes(b"fake minidump content")

        result = self.provider.stackwalk_minidump(str(minidump_file))

        assert result["success"] is False
        assert "minidump-stackwalk binary not found" in result["error"]
        assert "uv run just install-tools" in result["error"]

    @patch("rust_minidump_mcp.tools.stackwalk.subprocess.run")
    @patch("rust_minidump_mcp.tools.stackwalk.Path")
    def test_successful_json_output(self, mock_path_class: Mock, mock_subprocess: Mock) -> None:
        """Test successful execution with JSON output."""
        # Mock file system checks
        mock_minidump = Mock()
        mock_minidump.exists.return_value = True
        mock_minidump.is_file.return_value = True
        mock_minidump.absolute.return_value = "/path/to/test.dmp"

        mock_binary = Mock()
        mock_binary.exists.return_value = True

        # Setup Path constructor mock
        def path_side_effect(path: Any) -> Mock:
            if str(path).endswith("test.dmp"):
                return mock_minidump
            elif "minidump-stackwalk" in str(path):
                return mock_binary
            return Mock()

        mock_path_class.side_effect = path_side_effect

        # Mock subprocess output
        mock_result = Mock()
        mock_result.stdout = '{"crash_info": {"type": "EXCEPTION_ACCESS_VIOLATION"}}'
        mock_subprocess.return_value = mock_result

        result = self.provider.stackwalk_minidump("test.dmp")

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["crash_info"]["type"] == "EXCEPTION_ACCESS_VIOLATION"
        assert "command" in result

    @patch("rust_minidump_mcp.tools.stackwalk.subprocess.run")
    @patch("rust_minidump_mcp.tools.stackwalk.Path")
    def test_subprocess_timeout(self, mock_path_class: Mock, mock_subprocess: Mock) -> None:
        """Test handling of subprocess timeout."""
        # Mock file system checks
        mock_minidump = Mock()
        mock_minidump.exists.return_value = True
        mock_minidump.is_file.return_value = True
        mock_minidump.absolute.return_value = "/path/to/test.dmp"

        mock_binary = Mock()
        mock_binary.exists.return_value = True

        def path_side_effect(path: Any) -> Mock:
            if str(path).endswith("test.dmp"):
                return mock_minidump
            elif "minidump-stackwalk" in str(path):
                return mock_binary
            return Mock()

        mock_path_class.side_effect = path_side_effect

        # Mock subprocess timeout
        from subprocess import TimeoutExpired

        mock_subprocess.side_effect = TimeoutExpired("cmd", 30)

        result = self.provider.stackwalk_minidump("test.dmp")

        assert result["success"] is False
        assert "timed out" in result["error"]

    def test_invalid_symbols_path(self, tmp_path: Path) -> None:
        """Test handling of non-existent symbols directory."""
        # Create a temporary minidump file
        minidump_file = tmp_path / "test.dmp"
        minidump_file.write_bytes(b"fake minidump content")

        result = self.provider.stackwalk_minidump(str(minidump_file), symbols_path="/nonexistent/symbols")

        assert result["success"] is False
        assert "Symbols directory not found" in result["error"]
