"""Tests for stackwalk tools."""

from pathlib import Path

import pytest

from minidumpmcp.tools.stackwalk import StackwalkProvider


class TestStackwalkProvider:
    """Tests for StackwalkProvider class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.provider = StackwalkProvider()

    @pytest.mark.asyncio
    async def test_minidump_file_not_found(self) -> None:
        """Test handling of non-existent minidump file."""
        result = await self.provider.stackwalk_minidump("/nonexistent/file.dmp")

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_path_is_not_file(self, tmp_path: Path) -> None:
        """Test handling of directory path instead of file."""
        result = await self.provider.stackwalk_minidump(str(tmp_path))

        assert result["success"] is False
        assert "not a file" in result["error"]

    @pytest.mark.asyncio
    async def test_stackwalk_binary_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of missing minidump-stackwalk binary."""
        # Create a temporary minidump file
        minidump_file = tmp_path / "test.dmp"
        minidump_file.write_bytes(b"fake minidump content")

        # Mock the binary path to not exist by changing the project root
        fake_project_root = tmp_path / "fake_project"
        fake_project_root.mkdir()

        # Patch __file__ to point to a location where the binary doesn't exist
        fake_stackwalk_file = fake_project_root / "minidumpmcp" / "tools" / "stackwalk.py"
        fake_stackwalk_file.parent.mkdir(parents=True)
        fake_stackwalk_file.write_text("# fake file")

        # Mock which to return None (binary not found on PATH)
        monkeypatch.setattr("minidumpmcp.tools.stackwalk.which", lambda x: None)

        # Mock __file__ to use our fake location
        import minidumpmcp.tools.stackwalk as stackwalk_module
        monkeypatch.setattr(stackwalk_module, "__file__", str(fake_stackwalk_file))

        result = await self.provider.stackwalk_minidump(str(minidump_file))

        assert result["success"] is False
        assert "minidump-stackwalk binary not found" in result["error"]
        assert "uv run just install-tools" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_json_output_with_real_minidump(self) -> None:
        """Test successful execution with real minidump file."""
        # Use the real test minidump file
        test_minidump = Path(__file__).parent / "testdata" / "test.dmp"

        if not test_minidump.exists():
            pytest.skip("Test minidump file not found. Run: curl -L -o tests/testdata/test.dmp https://github.com/rust-minidump/rust-minidump/raw/main/testdata/test.dmp")

        result = await self.provider.stackwalk_minidump(str(test_minidump))

        # Assert successful execution
        assert result["success"] is True
        assert "data" in result
        assert "command" in result

        # Verify JSON structure matches expected output from minidump-stackwalk
        data = result["data"]
        assert "crash_info" in data
        assert "system_info" in data
        assert "modules" in data
        assert "threads" in data
        assert "crashing_thread" in data

        # Verify crash info
        crash_info = data["crash_info"]
        assert crash_info["type"] == "EXCEPTION_ACCESS_VIOLATION_WRITE"
        assert crash_info["address"] == "0x00000045"
        assert crash_info["crashing_thread"] == 0

        # Verify system info
        system_info = data["system_info"]
        assert system_info["os"] == "Windows NT"
        assert system_info["cpu_arch"] == "x86"

        # Verify modules are present
        assert len(data["modules"]) > 0
        main_module = data["modules"][0]
        assert main_module["filename"] == "test_app.exe"

        # Verify threads and frames
        assert len(data["threads"]) > 0
        crashing_thread = data["crashing_thread"]
        assert crashing_thread["thread_id"] == 3060
        assert len(crashing_thread["frames"]) == 4

    @pytest.mark.asyncio
    async def test_subprocess_error_handling(self, tmp_path: Path) -> None:
        """Test handling of subprocess execution errors."""
        # Create a fake minidump file
        fake_minidump = tmp_path / "fake.dmp"
        fake_minidump.write_bytes(b"not a real minidump")

        result = await self.provider.stackwalk_minidump(str(fake_minidump))

        # Should fail because it's not a valid minidump
        assert result["success"] is False
        assert "execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_symbols_path(self, tmp_path: Path) -> None:
        """Test handling of non-existent symbols directory."""
        # Create a temporary minidump file
        minidump_file = tmp_path / "test.dmp"
        minidump_file.write_bytes(b"fake minidump content")

        result = await self.provider.stackwalk_minidump(str(minidump_file), symbols_path="/nonexistent/symbols")

        assert result["success"] is False
        assert "Symbols directory not found" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_json_output_with_symbols(self) -> None:
        """Test successful execution with real minidump file and symbols."""
        # Use the real test minidump file and symbols
        test_minidump = Path(__file__).parent / "testdata" / "test.dmp"
        symbols_path = Path(__file__).parent / "testdata" / "symbols"

        if not test_minidump.exists():
            pytest.skip("Test minidump file not found")
        if not symbols_path.exists():
            pytest.skip("Test symbols directory not found")

        result = await self.provider.stackwalk_minidump(str(test_minidump), str(symbols_path))

        # Assert successful execution
        assert result["success"] is True
        assert "data" in result
        assert "command" in result

        # Verify JSON structure
        data = result["data"]
        assert "crash_info" in data
        assert "crashing_thread" in data
        assert "modules" in data

        # With symbols, we should have much more detailed info
        crashing_thread = data["crashing_thread"]
        first_frame = crashing_thread["frames"][0]

        # Verify symbol information is loaded
        assert first_frame["missing_symbols"] is False
        assert first_frame["function"] == "`anonymous namespace'::CrashFunction"
        assert first_frame["file"] == "c:\\test_app.cc"
        assert first_frame["line"] == 58

        # Verify the main module has symbols loaded
        main_module = data["modules"][0]
        assert main_module["filename"] == "test_app.exe"
        assert main_module["loaded_symbols"] is True
        assert main_module["missing_symbols"] is False
