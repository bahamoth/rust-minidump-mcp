"""Symbol preparation prompts for FastMCP."""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class SymbolPreparationProvider:
    """Provider for symbol preparation prompts."""

    def __init__(self) -> None:
        """Initialize the symbol preparation provider."""
        self._prompts_dir = Path(__file__).parent

    async def symbol_transformation_guide(
        self,
        symbol_sources: Optional[List[str]] = None,
        symbol_server_urls: Optional[List[str]] = None,
        executable_paths: Optional[List[str]] = None,
        target_modules: Optional[List[str]] = None,
    ) -> str:
        """
        Guide for transforming native debug symbols (PDB/DWARF) to Breakpad format required by minidump analysis tools.

        This prompt explains why Breakpad format is needed, how to use dump_syms tool,
        and provides troubleshooting for common symbol transformation issues.

        Args:
            symbol_sources: List of paths to symbol files or directories containing PDB/DWARF files
            symbol_server_urls: Optional list of symbol server URLs to fetch symbols from
            executable_paths: Optional paths to executable files for improved unwind quality
            target_modules: Optional specific modules to prioritize for symbol preparation
        """
        # Handle case where prompt is called without parameters (for metadata/listing)
        if symbol_sources is None:
            return self._create_usage_guide()

        try:
            # Runtime validation for robustness (FastMCP might pass invalid data)
            # Check if it's not iterable (strings are iterable but we want to exclude them)
            try:
                iter(symbol_sources)
                is_iterable = True
                is_string = isinstance(symbol_sources, str)
            except TypeError:
                is_iterable = False
                is_string = False

            if not is_iterable or is_string:
                error_msg = f"Invalid symbol_sources type: expected list, got {type(symbol_sources).__name__}"
                logger.error(error_msg)
                return self._create_error_response(
                    "symbol_transformation_guide",
                    error_msg,
                    "The symbol_sources must be a list of paths to symbol files or directories.",
                )

            # Validate list is not empty
            if not symbol_sources:
                error_msg = "symbol_sources list is empty"
                logger.error(error_msg)
                return self._create_error_response(
                    "symbol_transformation_guide",
                    error_msg,
                    "Please provide at least one path to symbol files or directories.",
                )

            # Load the symbol transformation guide template
            template_path = self._prompts_dir / "symbol_transformation_guide.md"
            if not template_path.exists():
                error_msg = f"Template file not found: {template_path}"
                logger.error(error_msg)
                return self._create_error_response(
                    "symbol_transformation_guide",
                    error_msg,
                    "The prompt template file is missing. Please ensure the installation is complete.",
                )

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # Build the complete prompt with input data
            prompt = f"{template}\n\n## Your Symbol Sources\n\n"

            # Add symbol sources
            prompt += "**Available Symbol Files:**\n"
            for source in symbol_sources:
                prompt += f"- {source}\n"
            prompt += "\n"

            # Add optional parameters if provided
            if symbol_server_urls:
                prompt += "**Symbol Server URLs:**\n"
                for url in symbol_server_urls:
                    prompt += f"- {url}\n"
                prompt += "\n"

            if executable_paths:
                prompt += "**Executable Files:**\n"
                for path in executable_paths:
                    prompt += f"- {path}\n"
                prompt += "\n"

            if target_modules:
                prompt += "**Priority Modules:**\n"
                for module in target_modules:
                    prompt += f"- {module}\n"
                prompt += "\n"

            prompt += (
                "Please provide guidance on transforming these symbols to Breakpad format, "
                "including specific commands and troubleshooting steps."
            )

            return prompt

        except Exception as e:
            error_msg = f"Unexpected error in symbol_transformation_guide: {str(e)}"
            logger.exception(error_msg)
            return self._create_error_response(
                "symbol_transformation_guide",
                error_msg,
                "An unexpected error occurred. Please check the server logs for details.",
            )

    def _create_usage_guide(self) -> str:
        """
        Create a usage guide for when prompt is called without parameters.

        Returns:
            Usage guide as a formatted message
        """
        return """## Symbol Transformation Guide

This prompt provides guidance for transforming native debug symbols (PDB/DWARF) to Breakpad format
required by minidump analysis tools.

### Required Parameters
- `symbol_sources`: List of paths to symbol files or directories containing PDB/DWARF files

### Optional Parameters
- `symbol_server_urls`: List of symbol server URLs to fetch symbols from
- `executable_paths`: Paths to executable files for improved unwind quality
- `target_modules`: Specific modules to prioritize for symbol preparation

### Usage Example
Provide paths to your symbol files (PDB on Windows, DWARF on Linux/macOS) to get detailed guidance on:
- Why Breakpad format is needed for minidump analysis
- How to use the `extract_symbols` tool (which uses dump_syms internally)
- Expected output structure (MODULE/GUID/MODULE.sym)
- Common troubleshooting steps

### What This Prompt Provides
- Step-by-step transformation instructions
- Command examples for your specific symbols
- Directory structure expectations
- Troubleshooting for common issues
"""

    def _create_error_response(self, prompt_name: str, error: str, guidance: str) -> str:
        """
        Create a user-friendly error response.

        Args:
            prompt_name: Name of the prompt that failed
            error: Technical error message
            guidance: User-friendly guidance

        Returns:
            Formatted error message as a prompt
        """
        return f"""## Error in {prompt_name}

**Error:** {error}

**Guidance:** {guidance}

### Required Parameters

This prompt requires the following parameters:
- `symbol_sources` (required): List of paths to symbol files or directories containing PDB/DWARF files
- `symbol_server_urls` (optional): List of symbol server URLs to fetch symbols from
- `executable_paths` (optional): Paths to executable files for improved unwind quality
- `target_modules` (optional): Specific modules to prioritize for symbol preparation

### Example Usage

To use this prompt correctly, provide at least one symbol source:
1. Paths to PDB files (Windows symbols)
2. Paths to DWARF files (Linux/macOS symbols)
3. Directories containing symbol files

If you're experiencing issues, please check:
- That you have provided valid paths to symbol files
- That the paths exist and are accessible
- That all required template files are present
"""
