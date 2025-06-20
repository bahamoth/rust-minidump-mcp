"""Crash analysis prompts for FastMCP."""

import json
from pathlib import Path
from typing import Any, Dict, Literal

from pydantic import Field


class CrashAnalysisProvider:
    """Provider for crash analysis prompts."""

    def __init__(self) -> None:
        """Initialize the crash analysis provider."""
        self._prompts_dir = Path(__file__).parent

    async def crash_analyzer(
        self,
        analysis_data: Dict[str, Any] = Field(description="Complete JSON output from stackwalk_minidump tool"),
        analysis_depth: Literal["basic", "detailed", "comprehensive"] = Field(
            default="detailed", description="Analysis depth level"
        ),
        focus_area: Literal["memory", "threading", "logic", "all"] = Field(
            default="all", description="Specific focus area for analysis"
        ),
    ) -> str:
        """
        Analyze crash dump data and provide comprehensive insights about software crashes.

        This prompt acts as an expert crash analysis specialist with deep knowledge
        of Windows minidump analysis, stack traces, and debugging techniques.
        """
        # Load the crash analyzer template
        template_path = self._prompts_dir / "crash_analyzer.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Build the complete prompt with analysis data
        prompt = f"{template}\n\n## Analysis Task\n\n"
        prompt += f"**Analysis Data:**\n```json\n{json.dumps(analysis_data, indent=2)}\n```\n\n"
        prompt += f"**Analysis Depth:** {analysis_depth}\n"
        prompt += f"**Focus Area:** {focus_area}\n\n"
        prompt += (
            "Please analyze this crash dump data and provide your structured JSON response "
            "according to the format specified above."
        )

        return prompt

    async def stack_interpreter(
        self,
        analysis_data: Dict[str, Any] = Field(description="Complete JSON output from stackwalk_minidump tool"),
        frame_limit: int = Field(default=20, description="Maximum number of frames to analyze (max: 50)"),
        focus_thread: Literal["crashing", "all"] = Field(default="crashing", description="Which thread to analyze"),
    ) -> str:
        """
        Analyze stack trace frames and interpret call patterns, execution flow, and function sequences.

        This prompt specializes in understanding how programs execute and where they fail,
        with expertise in call stack analysis and frame interpretation.
        """
        # Load the stack interpreter template
        template_path = self._prompts_dir / "stack_interpreter.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Extract and limit stack frames
        crashing_thread = analysis_data.get("crashing_thread", {})
        stack_frames = crashing_thread.get("frames", [])
        limited_frames = stack_frames[: min(frame_limit, 50)]

        # Build the complete prompt
        prompt = f"{template}\n\n## Analysis Task\n\n"
        prompt += f"**Stack Frames:**\n```json\n{json.dumps(limited_frames, indent=2)}\n```\n\n"
        prompt += f"**Frame Limit:** {frame_limit}\n"
        prompt += f"**Focus Thread:** {focus_thread}\n\n"
        prompt += "Please analyze these stack frames and provide your structured JSON response."

        return prompt

    async def exception_decoder(
        self,
        analysis_data: Dict[str, Any] = Field(description="Complete JSON output from stackwalk_minidump tool"),
        focus_type: Literal["address_pattern", "exception_type", "all"] = Field(
            default="all", description="Focus on specific exception aspect"
        ),
    ) -> str:
        """
        Decode exception information and provide targeted analysis of crash exception types and memory addresses.

        This prompt specializes in Windows exception analysis with deep expertise in
        interpreting crash exception types, memory addresses, and system-level crash patterns.
        """
        # Load the exception decoder template
        template_path = self._prompts_dir / "exception_decoder.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Extract exception information
        crash_info = analysis_data.get("crash_info", {})
        system_info = analysis_data.get("system_info", {})

        exception_type = crash_info.get("type", "UNKNOWN")
        exception_address = crash_info.get("address", "0x00000000")

        # Build the complete prompt
        prompt = f"{template}\n\n## Analysis Task\n\n"
        prompt += f"**Exception Type:** {exception_type}\n"
        prompt += f"**Exception Address:** {exception_address}\n"
        prompt += f"**System Context:**\n```json\n{json.dumps(system_info, indent=2)}\n```\n\n"
        prompt += f"**Focus Type:** {focus_type}\n\n"
        prompt += "Please analyze this exception information and provide your structured JSON response."

        return prompt

    async def symbol_advisor(
        self,
        analysis_data: Dict[str, Any] = Field(description="Complete JSON output from stackwalk_minidump tool"),
        focus_area: Literal["application_modules", "system_modules", "all"] = Field(
            default="all", description="Focus on specific symbol aspect"
        ),
    ) -> str:
        """
        Evaluate symbol information quality and provide guidance for improving crash analysis accuracy.

        This prompt specializes in debugging symbol analysis with expertise in understanding
        how symbol information affects crash analysis and how to optimize symbol availability.
        """
        # Load the symbol advisor template
        template_path = self._prompts_dir / "symbol_advisor.md"
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        # Extract modules information
        modules_info = analysis_data.get("modules", [])

        # Build the complete prompt
        prompt = f"{template}\n\n## Analysis Task\n\n"
        prompt += f"**Modules Information:**\n```json\n{json.dumps(modules_info, indent=2)}\n```\n\n"
        prompt += f"**Focus Area:** {focus_area}\n\n"
        prompt += "Please analyze the symbol information and provide your structured JSON response."

        return prompt
