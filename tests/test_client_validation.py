"""Tests for client parameter validation."""

from typing import Any, Dict, List
from unittest.mock import Mock

import pytest
from mcp.types import Prompt, PromptArgument

# Import functions to test
from minidumpmcp.client_validators.validators import ArgumentValidator, ParameterConverter


class TestSchemaExtraction:
    """Test JSON schema extraction from descriptions."""

    def test_extract_schema_with_colon(self):
        """Test extraction with 'schema: {...}' pattern."""
        desc = 'This is a description with schema: {"type": "string", "enum": ["a", "b", "c"]}'
        schema = ArgumentValidator.parse_schema_from_description(desc)
        assert schema is not None
        assert schema["type"] == "string"
        assert schema["enum"] == ["a", "b", "c"]

    def test_extract_schema_with_following(self):
        """Test extraction with 'following schema: {...}' pattern."""
        desc = (
            "Provide as a JSON string matching the following schema: "
            '{"enum":["registers","memory","stack_frames","all"],"type":"string"}'
        )
        schema = ArgumentValidator.parse_schema_from_description(desc)
        assert schema is not None
        assert schema["type"] == "string"
        assert schema["enum"] == ["registers", "memory", "stack_frames", "all"]

    def test_extract_schema_invalid_json(self):
        """Test handling of invalid JSON in schema."""
        desc = "This has invalid schema: {invalid json}"
        schema = ArgumentValidator.parse_schema_from_description(desc)
        assert schema is None

    def test_extract_schema_no_match(self):
        """Test when no schema pattern is found."""
        desc = "This is just a regular description without any schema"
        schema = ArgumentValidator.parse_schema_from_description(desc)
        assert schema is None

    def test_extract_schema_empty_description(self):
        """Test with empty or None description."""
        assert ArgumentValidator.parse_schema_from_description("") is None
        assert ArgumentValidator.parse_schema_from_description(None) is None  # type: ignore


class TestEnumExtraction:
    """Test enum value extraction from schema."""

    def test_extract_direct_enum(self):
        """Test extraction from direct enum field."""
        schema = {"enum": ["value1", "value2", "value3"], "type": "string"}
        values = ArgumentValidator.extract_enum_values(schema)
        assert values == ["value1", "value2", "value3"]

    def test_extract_anyof_enum(self):
        """Test extraction from anyOf with enum."""
        schema = {"anyOf": [{"type": "string"}, {"enum": ["a", "b", "c"], "type": "string"}, {"type": "null"}]}
        values = ArgumentValidator.extract_enum_values(schema)
        assert values == ["a", "b", "c"]

    def test_extract_no_enum(self):
        """Test schema without enum values."""
        schema = {"type": "string", "minLength": 1}
        values = ArgumentValidator.extract_enum_values(schema)
        assert values is None

    def test_extract_empty_schema(self):
        """Test with empty or None schema."""
        assert ArgumentValidator.extract_enum_values({}) is None
        assert ArgumentValidator.extract_enum_values(None) is None  # type: ignore


class TestArgumentValidation:
    """Test argument value validation."""

    def test_validate_enum_valid(self):
        """Test validation with valid enum value."""
        schema = {"enum": ["registers", "memory", "all"], "type": "string"}
        error = ArgumentValidator.validate_argument_value("focus", "memory", schema)
        assert error is None

    def test_validate_enum_invalid(self):
        """Test validation with invalid enum value."""
        schema = {"enum": ["registers", "memory", "all"], "type": "string"}
        error = ArgumentValidator.validate_argument_value("focus", "invalid", schema)
        assert error is not None
        assert "Invalid value for 'focus'" in error
        assert "Must be one of" in error
        assert "['registers', 'memory', 'all']" in error

    def test_validate_no_schema(self):
        """Test validation without schema."""
        error = ArgumentValidator.validate_argument_value("param", "any_value", None)  # type: ignore
        assert error is None

    def test_validate_no_enum_in_schema(self):
        """Test validation with schema but no enum."""
        schema = {"type": "string", "minLength": 1}
        error = ArgumentValidator.validate_argument_value("param", "any_value", schema)
        assert error is None


class TestParameterConversion:
    """Test parameter conversion for MCP protocol."""

    def test_convert_string_value(self):
        """Test that string values remain unchanged."""
        arguments = {"key1": "value1", "key2": "value2"}
        converted = ParameterConverter.convert_to_mcp_format(arguments)
        assert converted == {"key1": "value1", "key2": "value2"}

    def test_convert_dict_to_json_string(self):
        """Test that dict values are converted to JSON strings."""
        arguments = {"config": {"nested": "value"}}
        converted = ParameterConverter.convert_to_mcp_format(arguments)
        assert converted == {"config": '{"nested": "value"}'}

    def test_convert_list_to_json_string(self):
        """Test that list values are converted to JSON strings."""
        arguments = {"items": ["a", "b", "c"]}
        converted = ParameterConverter.convert_to_mcp_format(arguments)
        assert converted == {"items": '["a", "b", "c"]'}

    def test_convert_mixed_types(self):
        """Test conversion of mixed types."""
        arguments = {"string": "value", "dict": {"key": "val"}, "list": [1, 2, 3], "bool": True, "number": 42}
        converted = ParameterConverter.convert_to_mcp_format(arguments)
        assert converted["string"] == "value"
        assert converted["dict"] == '{"key": "val"}'
        assert converted["list"] == "[1, 2, 3]"
        assert converted["bool"] == "true"
        assert converted["number"] == "42"

    def test_parse_json_arguments_valid(self):
        """Test parsing valid JSON arguments."""
        args_str = '{"key": "value", "number": 42}'
        parsed = ParameterConverter.parse_json_arguments(args_str)
        assert parsed == {"key": "value", "number": 42}

    def test_parse_json_arguments_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="Invalid JSON"):
            ParameterConverter.parse_json_arguments("not json")

    def test_parse_json_arguments_not_object(self):
        """Test parsing non-object JSON raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="Arguments must be a JSON object"):
            ParameterConverter.parse_json_arguments('["array", "not", "object"]')


class TestPromptValidation:
    """Test full prompt validation flow."""

    def create_mock_prompt(self, arguments: List[Dict[str, Any]]) -> Prompt:
        """Create a mock prompt with given arguments."""
        prompt = Mock(spec=Prompt)
        prompt.name = "test_prompt"
        prompt.description = "Test prompt"

        prompt_args = []
        for arg_data in arguments:
            arg = Mock(spec=PromptArgument)
            arg.name = arg_data["name"]
            arg.required = arg_data.get("required", False)
            arg.description = arg_data.get("description", "")
            prompt_args.append(arg)

        prompt.arguments = prompt_args
        return prompt

    def test_validate_unknown_arguments(self):
        """Test detection of unknown arguments."""
        prompt = self.create_mock_prompt([{"name": "valid_arg", "required": False}])

        arguments = {"valid_arg": "value", "unknown_arg": "value"}
        errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
        assert len(errors) == 1
        assert "Unknown arguments: {'unknown_arg'}" in errors[0]

    def test_validate_missing_required(self):
        """Test detection of missing required arguments."""
        prompt = self.create_mock_prompt(
            [{"name": "required_arg", "required": True}, {"name": "optional_arg", "required": False}]
        )

        arguments = {"optional_arg": "value"}
        errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
        assert len(errors) == 1
        assert "Missing required arguments: {'required_arg'}" in errors[0]

    def test_validate_enum_in_prompt(self):
        """Test enum validation in prompt context."""
        prompt = self.create_mock_prompt(
            [
                {
                    "name": "technical_focus",
                    "required": False,
                    "description": (
                        "Provide as a JSON string matching the following schema: "
                        '{"enum":["registers","memory","all"],"type":"string"}'
                    ),
                }
            ]
        )

        # Valid enum value
        arguments = {"technical_focus": "memory"}
        errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
        assert len(errors) == 0

        # Invalid enum value
        arguments = {"technical_focus": "invalid"}
        errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
        assert len(errors) == 1
        assert "Invalid value for 'technical_focus'" in errors[0]
        assert "Must be one of: ['registers', 'memory', 'all']" in errors[0]

    def test_validate_all_errors_together(self):
        """Test multiple validation errors are collected."""
        prompt = self.create_mock_prompt(
            [
                {"name": "required_arg", "required": True},
                {"name": "enum_arg", "required": False, "description": 'schema: {"enum":["a", "b"], "type":"string"}'},
            ]
        )

        arguments = {"unknown_arg": "value", "enum_arg": "invalid"}
        errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
        assert len(errors) == 3
        # Should have: unknown args, missing required, invalid enum
        error_str = "\n".join(errors)
        assert "Unknown arguments" in error_str
        assert "Missing required arguments" in error_str
        assert "Invalid value for 'enum_arg'" in error_str


# Integration tests would go here but require more setup
# They would test the full flow with actual client calls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
