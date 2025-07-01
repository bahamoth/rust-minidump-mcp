"""Crash analysis prompts for FastMCP."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

logger = logging.getLogger(__name__)


class CrashAnalysisProvider:
    """Provider for crash analysis prompts."""

    def __init__(self) -> None:
        """Initialize the crash analysis provider."""
        self._prompts_dir = Path(__file__).parent

    async def analyze_crash_with_expertise(
        self,
        stackwalk_output: Optional[Union[str, Dict[str, Any]]] = None,
        focus_areas: Optional[List[Literal["root_cause", "prevention", "improvements"]]] = None,
    ) -> str:
        """
        Analyze crash dump as an expert with 20 years of experience.

        Provides root cause analysis and concrete improvement suggestions.
        This prompt gives the LLM a crash analysis expert role to identify programming languages,
        detect crash patterns, and recommend prevention strategies.

        Args:
            stackwalk_output: Complete JSON output from stackwalk_minidump tool (as JSON string or dict)
            focus_areas: Optional list of specific areas to focus the analysis on
                        (root_cause, prevention, improvements)
        """
        # Handle case where prompt is called without parameters (for metadata/listing)
        if stackwalk_output is None:
            return self._create_usage_guide("analyze_crash_with_expertise")

        try:
            # Parse JSON if string is provided
            if isinstance(stackwalk_output, str):
                try:
                    stackwalk_data = json.loads(stackwalk_output)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON in stackwalk_output: {str(e)}"
                    logger.error(error_msg)
                    return self._create_error_response(
                        "analyze_crash_with_expertise",
                        error_msg,
                        "The stackwalk_output must be valid JSON string or dictionary.",
                    )
            else:
                # If it's already a dict, use it as is
                stackwalk_data = stackwalk_output

            # Runtime validation for robustness
            if not isinstance(stackwalk_data, dict):
                error_msg = (
                    f"Invalid stackwalk_output type after parsing: expected dict, got {type(stackwalk_data).__name__}"
                )
                logger.error(error_msg)
                return self._create_error_response(
                    "analyze_crash_with_expertise",
                    error_msg,
                    "The stackwalk_output must be a dictionary containing the crash analysis data.",
                )

            # Load the analyze crash with expertise template
            template_path = self._prompts_dir / "analyze_crash_with_expertise.md"
            if not template_path.exists():
                error_msg = f"Template file not found: {template_path}"
                logger.error(error_msg)
                return self._create_error_response(
                    "analyze_crash_with_expertise",
                    error_msg,
                    "The prompt template file is missing. Please ensure the installation is complete.",
                )

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # Build the complete prompt with analysis data
            prompt = f"{template}\n\n## Stackwalk Output\n\n"
            prompt += f"```json\n{json.dumps(stackwalk_data, indent=2)}\n```\n\n"

            if focus_areas and isinstance(focus_areas, list):
                prompt += f"**Focus Areas:** {', '.join(focus_areas)}\n\n"

            prompt += (
                "Please analyze this crash dump and provide your expert analysis "
                "following the response format specified above."
            )

            return prompt

        except Exception as e:
            error_msg = f"Unexpected error in analyze_crash_with_expertise: {str(e)}"
            logger.exception(error_msg)
            return self._create_error_response(
                "analyze_crash_with_expertise",
                error_msg,
                "An unexpected error occurred. Please check the server logs for details.",
            )

    async def analyze_technical_details(
        self,
        stackwalk_output: Optional[Union[str, Dict[str, Any]]] = None,
        technical_focus: Literal["registers", "memory", "stack_frames", "all"] = "all",
    ) -> str:
        """
        Perform deep technical analysis of crash dump focusing on registers, memory patterns, and stack frames.

        This prompt guides detailed low-level analysis of CPU state, memory access patterns,
        and stack frame interpretation for understanding the exact failure mechanism.

        Args:
            stackwalk_output: Complete JSON output from stackwalk_minidump tool (as JSON string or dict)
            technical_focus: Specific technical aspect to analyze in depth
                           (registers, memory, stack_frames, all). Defaults to "all"
        """
        # Handle case where prompt is called without parameters (for metadata/listing)
        if stackwalk_output is None:
            return self._create_usage_guide("analyze_technical_details")

        try:
            # Parse JSON if string is provided
            if isinstance(stackwalk_output, str):
                try:
                    stackwalk_data = json.loads(stackwalk_output)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON in stackwalk_output: {str(e)}"
                    logger.error(error_msg)
                    return self._create_error_response(
                        "analyze_technical_details",
                        error_msg,
                        "The stackwalk_output must be valid JSON string or dictionary.",
                    )
            else:
                # If it's already a dict, use it as is
                stackwalk_data = stackwalk_output

            # Runtime validation for robustness
            if not isinstance(stackwalk_data, dict):
                error_msg = (
                    f"Invalid stackwalk_output type after parsing: expected dict, got {type(stackwalk_data).__name__}"
                )
                logger.error(error_msg)
                return self._create_error_response(
                    "analyze_technical_details",
                    error_msg,
                    "The stackwalk_output must be a dictionary containing the crash analysis data.",
                )

            # Load the technical details template
            template_path = self._prompts_dir / "analyze_technical_details.md"
            if not template_path.exists():
                error_msg = f"Template file not found: {template_path}"
                logger.error(error_msg)
                return self._create_error_response(
                    "analyze_technical_details",
                    error_msg,
                    "The prompt template file is missing. Please ensure the installation is complete.",
                )

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # Build the complete prompt
            prompt = f"{template}\n\n## Stackwalk Output\n\n"
            prompt += f"```json\n{json.dumps(stackwalk_data, indent=2)}\n```\n\n"
            prompt += f"**Technical Focus:** {technical_focus}\n\n"
            prompt += (
                "Please perform a deep technical analysis of this crash dump "
                "following the response format specified above."
            )

            return prompt

        except Exception as e:
            error_msg = f"Unexpected error in analyze_technical_details: {str(e)}"
            logger.exception(error_msg)
            return self._create_error_response(
                "analyze_technical_details",
                error_msg,
                "An unexpected error occurred. Please check the server logs for details.",
            )

    def _create_usage_guide(self, prompt_name: str) -> str:
        """
        Create a usage guide for when prompt is called without parameters.

        Args:
            prompt_name: Name of the prompt

        Returns:
            Usage guide as a formatted message
        """
        if prompt_name == "analyze_crash_with_expertise":
            return """## Crash Analysis with Expertise

This prompt analyzes crash dumps with expert-level insights, providing root cause analysis
and concrete improvement suggestions.

### Required Parameters
- `stackwalk_output`: Complete JSON output from the stackwalk_minidump tool

### Optional Parameters
- `focus_areas`: List of specific areas to focus on (root_cause, prevention, improvements)

### Usage Example
1. First, analyze a minidump file using the `stackwalk_minidump` tool
2. Pass the resulting JSON output to this prompt for expert analysis

The analysis will include:
- Programming language detection from modules/symbols
- Crash pattern recognition
- Prevention strategies and code improvements
- Expert recommendations based on 20 years of debugging experience
"""
        elif prompt_name == "analyze_technical_details":
            return """## Technical Details Analysis

This prompt performs deep technical analysis of crash dumps, focusing on registers, memory patterns, and stack frames.

### Required Parameters
- `stackwalk_output`: Complete JSON output from the stackwalk_minidump tool

### Optional Parameters
- `technical_focus`: Specific aspect to analyze (registers, memory, stack_frames, all)

### Usage Example
1. First, analyze a minidump file using the `stackwalk_minidump` tool
2. Pass the resulting JSON output to this prompt for technical analysis

The analysis will include:
- Register state interpretation
- Memory access pattern analysis
- Stack frame pattern recognition
- Symbol-less frame estimation methods
"""
        else:
            return f"Usage guide for {prompt_name} - Please provide required parameters to use this prompt."

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
- `stackwalk_output` (required): Complete JSON output from the stackwalk_minidump tool
- `focus_areas` (optional): List of specific areas to focus on (for analyze_crash_with_expertise)
- `technical_focus` (optional): Specific technical aspect to analyze (for analyze_technical_details)

### Example Usage

To use this prompt correctly, first run the stackwalk_minidump tool on a crash dump file:
1. Use the `stackwalk_minidump` tool with your .dmp file
2. Pass the resulting JSON output to this prompt

If you're experiencing issues, please check:
- That you have valid stackwalk output data
- That the data is in the correct JSON format
- That all required template files are present
"""
