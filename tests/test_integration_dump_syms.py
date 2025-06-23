"""Integration tests for dump_syms tool."""

import tempfile
from pathlib import Path

import pytest

from minidumpmcp.tools.dump_syms import DumpSymsTool, _get_dump_syms_path


@pytest.mark.integration
class TestDumpSymsIntegration:
    """Integration tests for DumpSymsTool with real binary."""

    @pytest.mark.asyncio
    async def test_extract_symbols_from_real_binary(self):
        """Test extracting symbols from the minidump-stackwalk binary itself."""
        # Use minidump-stackwalk binary as test file
        stackwalk_path = Path(__file__).parent.parent / "minidumpmcp" / "tools" / "bin" / "minidump-stackwalk-macos"

        if not stackwalk_path.exists():
            pytest.skip(f"Test binary not found at {stackwalk_path}")

        dump_syms_path = _get_dump_syms_path()
        if not dump_syms_path.exists():
            pytest.skip(f"dump_syms not found at {dump_syms_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            dump_syms_tool = DumpSymsTool()
            result = await dump_syms_tool.extract_symbols(str(stackwalk_path), str(tmpdir))

            # Check that operation succeeded
            if not result["success"]:
                print(f"Error: {result.get('error', 'Unknown error')}")
            assert result["success"] is True
            assert "symbol_file" in result
            assert "module_info" in result

            # Check that symbol file was created
            symbol_file = Path(result["symbol_file"])
            assert symbol_file.exists()
            assert symbol_file.stat().st_size > 0

            # Check module info
            module_info = result["module_info"]
            assert "name" in module_info
            assert "id" in module_info
            assert "os" in module_info
            assert "arch" in module_info

            # Verify Breakpad directory structure
            # Should be: <tmpdir>/<module_name>/<module_id>/<module_name>.sym
            parts = symbol_file.parts
            assert parts[-3] == module_info["name"]  # module name directory
            assert parts[-2] == module_info["id"]  # module id directory
            assert parts[-1] == f"{module_info['name']}.sym"  # symbol file

            # Read and verify symbol file content
            content = symbol_file.read_text()
            lines = content.strip().split("\n")

            # First line should be MODULE header
            assert lines[0].startswith("MODULE")
            assert module_info["os"] in lines[0]
            assert module_info["arch"] in lines[0]
            assert module_info["id"] in lines[0]
            assert module_info["name"] in lines[0]

    @pytest.mark.asyncio
    async def test_extract_symbols_invalid_binary(self, tmp_path):
        """Test error handling with invalid binary file."""
        # Create a text file that's not a valid binary
        invalid_binary = tmp_path / "not_a_binary.txt"
        invalid_binary.write_text("This is not a binary file")

        dump_syms_path = _get_dump_syms_path()
        if not dump_syms_path.exists():
            pytest.skip(f"dump_syms not found at {dump_syms_path}")

        dump_syms_tool = DumpSymsTool()
        result = await dump_syms_tool.extract_symbols(str(invalid_binary))

        # Should fail but handle gracefully
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_symbol_extraction(self):
        """Test concurrent symbol extraction from same binary."""
        import asyncio

        stackwalk_path = Path(__file__).parent.parent / "minidumpmcp" / "tools" / "bin" / "minidump-stackwalk-macos"

        if not stackwalk_path.exists():
            pytest.skip(f"Test binary not found at {stackwalk_path}")

        dump_syms_path = _get_dump_syms_path()
        if not dump_syms_path.exists():
            pytest.skip(f"dump_syms not found at {dump_syms_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            dump_syms_tool = DumpSymsTool()

            # Run multiple extractions concurrently
            tasks = []
            for i in range(3):
                output_dir = Path(tmpdir) / f"symbols_{i}"
                output_dir.mkdir()
                tasks.append(dump_syms_tool.extract_symbols(str(stackwalk_path), str(output_dir)))

            results = await asyncio.gather(*tasks)

            # All should succeed
            for result in results:
                assert result["success"] is True
                assert Path(result["symbol_file"]).exists()

            # All should have same module info
            module_infos = [r["module_info"] for r in results]
            assert all(info == module_infos[0] for info in module_infos)
