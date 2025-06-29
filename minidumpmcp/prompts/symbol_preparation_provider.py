"""Symbol preparation prompts for FastMCP."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field


class SymbolPreparationProvider:
    """Provider for symbol preparation prompts."""

    def __init__(self) -> None:
        """Initialize the symbol preparation provider."""
        self._prompts_dir = Path(__file__).parent

    async def prepare_symbols_for_analysis(
        self,
        symbol_sources: List[str] = Field(
            description="List of paths to symbol files or directories containing PDB/DWARF files"
        ),
        symbol_server_urls: Optional[List[str]] = Field(
            default=None, description="List of symbol server URLs to fetch symbols from"
        ),
        executable_paths: Optional[List[str]] = Field(
            default=None, description="Paths to executable files for improved unwind quality"
        ),
        target_modules: Optional[List[str]] = Field(
            default=None, description="Specific modules to prioritize for symbol preparation"
        ),
    ) -> str:
        """
        Guide symbol preparation from native formats (PDB/DWARF) to Breakpad format.

        This prompt helps users convert debug symbols for use with minidump analysis tools,
        providing step-by-step guidance and automation suggestions.
        """
        # Load the prepare symbols template
        template_path = self._prompts_dir / "prepare_symbols_for_analysis.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Build the complete prompt with input data
        prompt = f"{template}\n\n## Analysis Task\n\n"

        # Add symbol sources
        prompt += "**Symbol Sources:**\n"
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
            prompt += "**Executable Paths:**\n"
            for path in executable_paths:
                prompt += f"- {path}\n"
            prompt += "\n"

        if target_modules:
            prompt += "**Target Modules:**\n"
            for module in target_modules:
                prompt += f"- {module}\n"
            prompt += "\n"

        prompt += (
            "Please analyze these symbol sources and provide a comprehensive preparation guide "
            "according to the JSON format specified above."
        )

        return prompt
