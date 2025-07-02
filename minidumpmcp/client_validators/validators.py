"""Validators for MCP client arguments."""

import json
import re
from typing import Any, Dict, List, Optional

from mcp.types import Prompt


class ArgumentValidator:
    """Validates arguments for MCP prompts and tools."""

    @staticmethod
    def parse_schema_from_description(description: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON schema from prompt argument description.

        Args:
            description: The argument description that may contain JSON schema

        Returns:
            Parsed JSON schema dict or None if not found/invalid
        """
        if not description:
            return None

        # Look for JSON schema in the description
        # Try both patterns: "schema: {}" and "following schema: {}"
        patterns = [r"schema:\s*({.*})", r"following schema:\s*({.*?})(?:\s|$)"]

        for pattern in patterns:
            match = re.search(pattern, description, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1))
                    return result  # type: ignore
                except json.JSONDecodeError:
                    pass
        return None

    @staticmethod
    def extract_enum_values(schema: Dict[str, Any]) -> Optional[List[str]]:
        """
        Extract enum values from a JSON schema.

        Args:
            schema: JSON schema dict

        Returns:
            List of enum values or None if not found
        """
        if not schema:
            return None

        # Direct enum
        if "enum" in schema:
            return schema["enum"]  # type: ignore

        # anyOf with enum
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if "enum" in option:
                    return option["enum"]  # type: ignore

        return None

    @staticmethod
    def validate_argument_value(name: str, value: str, schema: Dict[str, Any]) -> Optional[str]:
        """
        Validate an argument value against its schema.

        Args:
            name: Argument name
            value: Argument value
            schema: JSON schema to validate against

        Returns:
            Error message if invalid, None if valid
        """
        if not schema:
            return None

        # Check enum values
        enum_values = ArgumentValidator.extract_enum_values(schema)
        if enum_values and value not in enum_values:
            return f"Invalid value for '{name}': '{value}'. Must be one of: {enum_values}"

        return None

    @staticmethod
    def validate_prompt_arguments(prompt: Prompt, arguments: Dict[str, Any]) -> List[str]:
        """
        Validate all arguments for a prompt.

        Args:
            prompt: The prompt definition
            arguments: Arguments to validate

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        if not prompt.arguments:
            # No arguments defined, so any provided arguments are invalid
            if arguments:
                errors.append(f"Prompt '{prompt.name}' does not accept any arguments")
            return errors

        # Check for unknown arguments
        valid_args = {arg.name for arg in prompt.arguments}
        provided_args = set(arguments.keys())
        unknown_args = provided_args - valid_args

        if unknown_args:
            errors.append(f"Unknown arguments: {unknown_args}")

        # Check for missing required arguments
        required_args = {arg.name for arg in prompt.arguments if arg.required}
        missing_args = required_args - provided_args

        if missing_args:
            errors.append(f"Missing required arguments: {missing_args}")

        # Validate argument values
        for arg in prompt.arguments:
            if arg.name in arguments and arg.description:
                schema = ArgumentValidator.parse_schema_from_description(arg.description)
                if schema:
                    error = ArgumentValidator.validate_argument_value(arg.name, arguments[arg.name], schema)
                    if error:
                        errors.append(error)

        return errors


class ParameterConverter:
    """Converts parameters to MCP-compliant format."""

    @staticmethod
    def convert_to_mcp_format(arguments: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert arguments to MCP protocol format (dict[str, str]).

        Args:
            arguments: Arguments with any value types

        Returns:
            Arguments with all values converted to strings
        """
        converted = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                converted[key] = value
            else:
                # Convert non-string values to JSON strings
                converted[key] = json.dumps(value)
        return converted

    @staticmethod
    def parse_json_arguments(args_string: str) -> Dict[str, Any]:
        """
        Parse JSON arguments string.

        Args:
            args_string: JSON string of arguments

        Returns:
            Parsed arguments dict

        Raises:
            ValueError: If JSON is invalid or not an object
        """
        try:
            parsed = json.loads(args_string)
            if not isinstance(parsed, dict):
                raise ValueError("Arguments must be a JSON object")
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
