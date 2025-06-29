"""End-to-end crash analysis workflow prompts for FastMCP."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field


class CrashWorkflowProvider:
    """Provider for comprehensive crash analysis workflow prompts."""

    def __init__(self) -> None:
        """Initialize the crash workflow provider."""
        self._prompts_dir = Path(__file__).parent

    async def analyze_crash_end_to_end(
        self,
        dump_path: str = Field(description="Path to the minidump (.dmp) file"),
        symbol_sources: Optional[List[str]] = Field(
            default=None, description="Paths to PDB/DWARF files or directories, or Breakpad symbol directories"
        ),
        symbol_server_urls: Optional[List[str]] = Field(
            default=None, description="URLs of symbol servers (e.g., Microsoft, internal servers)"
        ),
        executable_path: Optional[str] = Field(
            default=None, description="Path to the crashed executable for enhanced unwind information"
        ),
        analysis_options: Optional[Dict[str, Any]] = Field(
            default=None, description="Configuration for analysis depth and focus areas"
        ),
    ) -> str:
        """
        Guide users through complete crash analysis from raw dump to actionable insights.

        This comprehensive prompt orchestrates the entire workflow including symbol
        preparation, minidump analysis, result interpretation, and recommendations.
        """
        # Load the end-to-end analysis template
        template_path = self._prompts_dir / "analyze_crash_end_to_end.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Build the complete prompt with input data
        prompt = f"{template}\n\n## Analysis Task\n\n"

        # Add required dump path
        prompt += f"**Dump File:** `{dump_path}`\n\n"

        # Add symbol sources if provided
        if symbol_sources:
            prompt += "**Symbol Sources:**\n"
            for source in symbol_sources:
                prompt += f"- `{source}`\n"
            prompt += "\n"
        else:
            prompt += "**Symbol Sources:** None provided (will attempt analysis without symbols)\n\n"

        # Add symbol server URLs if provided
        if symbol_server_urls:
            prompt += "**Symbol Server URLs:**\n"
            for url in symbol_server_urls:
                prompt += f"- {url}\n"
            prompt += "\n"

        # Add executable path if provided
        if executable_path:
            prompt += f"**Executable Path:** `{executable_path}`\n\n"

        # Add analysis options if provided
        if analysis_options:
            prompt += f"**Analysis Options:**\n```json\n{json.dumps(analysis_options, indent=2)}\n```\n\n"

        prompt += (
            "Please provide a complete workflow guide for analyzing this crash dump, "
            "including all necessary steps from symbol preparation through final recommendations, "
            "formatted according to the JSON structure specified above."
        )

        return prompt
