"""Tests for dump_syms tool."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from minidumpmcp.tools.dump_syms import DumpSymsTool, _get_dump_syms_path


@pytest.fixture
def dump_syms_tool():
    """Create a DumpSymsTool instance."""
    return DumpSymsTool()


class TestDumpSymsTool:
    """Test cases for DumpSymsTool."""

    def test_get_dump_syms_path_darwin(self):
        """Test getting dump_syms binary on macOS."""
        with patch("platform.system", return_value="Darwin"):
            binary_path = _get_dump_syms_path()
            assert binary_path.name == "dump-syms-macos"

    def test_get_dump_syms_path_linux(self):
        """Test getting dump_syms binary on Linux."""
        with patch("platform.system", return_value="Linux"):
            binary_path = _get_dump_syms_path()
            assert binary_path.name == "dump-syms-linux"

    def test_get_dump_syms_path_windows(self):
        """Test getting dump_syms binary on Windows."""
        with patch("platform.system", return_value="Windows"):
            binary_path = _get_dump_syms_path()
            assert binary_path.name == "dump-syms-windows.exe"

    @pytest.mark.asyncio
    async def test_extract_symbols_success(self, dump_syms_tool, tmp_path):
        """Test successful symbol extraction."""
        # Create a fake binary file
        binary_file = tmp_path / "test.exe"
        binary_file.write_text("fake binary content")

        # Mock dump_syms output
        mock_stdout = b"MODULE windows x86_64 1234567890ABCDEF test.exe\nPUBLIC 1000 0 main\n"
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(mock_stdout, b""))
        mock_process.returncode = 0

        with patch("minidumpmcp.tools.dump_syms._get_dump_syms_path") as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path

            with patch("minidumpmcp.tools.dump_syms.run_subprocess") as mock_run:
                mock_run.return_value = mock_stdout.decode()

                result = await dump_syms_tool.extract_symbols(str(binary_file), str(tmp_path / "symbols"))

                # Check that operation succeeded
                assert result["success"] is True
                assert "symbol_file" in result
                assert "module_info" in result

                # Check module info
                assert result["module_info"]["name"] == "test.exe"
                assert result["module_info"]["id"] == "1234567890ABCDEF"
                assert result["module_info"]["os"] == "windows"
                assert result["module_info"]["arch"] == "x86_64"

                # Check that symbol file was created in correct structure
                expected_path = tmp_path / "symbols" / "test.exe" / "1234567890ABCDEF" / "test.exe.sym"
                assert result["symbol_file"] == str(expected_path)
                assert Path(result["symbol_file"]).exists()
                assert Path(result["symbol_file"]).read_text() == mock_stdout.decode()

    @pytest.mark.asyncio
    async def test_extract_symbols_binary_not_found(self, dump_syms_tool):
        """Test error when binary file doesn't exist."""
        result = await dump_syms_tool.extract_symbols("/nonexistent/file.exe")
        assert result["success"] is False
        assert "Binary file not found" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_symbols_dump_syms_fails(self, dump_syms_tool, tmp_path):
        """Test error when dump_syms execution fails."""
        binary_file = tmp_path / "test.exe"
        binary_file.write_text("fake binary content")

        with patch("minidumpmcp.tools.dump_syms._get_dump_syms_path") as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path

            with patch("minidumpmcp.tools.dump_syms.run_subprocess") as mock_run:
                from minidumpmcp.tools._common import ToolExecutionError

                mock_run.side_effect = ToolExecutionError("Error: Invalid file format")

                result = await dump_syms_tool.extract_symbols(str(binary_file))
                assert result["success"] is False
                assert "dump_syms execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_symbols_invalid_output(self, dump_syms_tool, tmp_path):
        """Test error when dump_syms produces invalid output."""
        binary_file = tmp_path / "test.exe"
        binary_file.write_text("fake binary content")

        # Invalid header format
        mock_stdout = "INVALID HEADER FORMAT\n"

        with patch("minidumpmcp.tools.dump_syms._get_dump_syms_path") as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path

            with patch("minidumpmcp.tools.dump_syms.run_subprocess") as mock_run:
                mock_run.return_value = mock_stdout

                result = await dump_syms_tool.extract_symbols(str(binary_file))
                assert result["success"] is False
                assert "Invalid symbol header" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_symbols_empty_output(self, dump_syms_tool, tmp_path):
        """Test error when dump_syms produces no output."""
        binary_file = tmp_path / "test.exe"
        binary_file.write_text("fake binary content")

        with patch("minidumpmcp.tools.dump_syms._get_dump_syms_path") as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path

            with patch("minidumpmcp.tools.dump_syms.run_subprocess") as mock_run:
                mock_run.return_value = ""

                result = await dump_syms_tool.extract_symbols(str(binary_file))
                assert result["success"] is False
                assert "dump_syms produced no output" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_symbols_default_output_dir(self, dump_syms_tool, tmp_path):
        """Test symbol extraction with default output directory."""
        binary_file = tmp_path / "test.dll"
        binary_file.write_text("fake binary content")

        mock_stdout = "MODULE linux x86 ABCDEF123456 test.dll\nPUBLIC 2000 0 function\n"

        with patch("minidumpmcp.tools.dump_syms._get_dump_syms_path") as mock_get_path:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_get_path.return_value = mock_path

            with patch("minidumpmcp.tools.dump_syms.run_subprocess") as mock_run:
                mock_run.return_value = mock_stdout

                with patch("pathlib.Path.cwd", return_value=tmp_path):
                    result = await dump_syms_tool.extract_symbols(str(binary_file))

                    # Check that operation succeeded
                    assert result["success"] is True

                    # Check that symbol file was created in default location
                    expected_path = tmp_path / "symbols" / "test.dll" / "ABCDEF123456" / "test.dll.sym"
                    assert result["symbol_file"] == str(expected_path)
                    assert Path(result["symbol_file"]).exists()
