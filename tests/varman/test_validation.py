"""Tests for the validation utilities."""

import pytest
from varman.utils.validation import (
    validate_name, parse_label, is_language_code, validate_data_type,
    ValidationError, ValidationResult
)
from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.models.category import Category


def test_validate_name():
    """Test the validate_name function."""
    # Valid names
    assert validate_name("name") is True
    assert validate_name("variable_name") is True
    assert validate_name("name123") is True

    # Invalid names
    assert validate_name("Name") is False  # Not lowercase
    assert validate_name("123name") is False  # Starts with a number
    assert validate_name("name-with-hyphens") is False  # Contains invalid characters
    assert validate_name("name with spaces") is False  # Contains spaces
    assert validate_name("") is False  # Empty string


def test_parse_label():
    """Test the parse_label function."""
    # Test with two parts (language:text)
    language, purpose, text = parse_label("en:English text")
    assert language == "en"
    assert purpose is None
    assert text == "English text"

    # Test with three parts (language:purpose:text)
    language, purpose, text = parse_label("en:short:Short text")
    assert language == "en"
    assert purpose == "short"
    assert text == "Short text"

    # Test with invalid format
    with pytest.raises(ValueError):
        parse_label("invalid_format")

    # Test with more than 2 colons (extra colons should be part of the text)
    language, purpose, text = parse_label("too:many:colons:in:string")
    assert language == "too"
    assert purpose == "many"
    assert text == "colons:in:string"


def test_is_language_code():
    """Test the is_language_code function."""
    # Valid language codes
    assert is_language_code("en") is True
    assert is_language_code("fi") is True
    assert is_language_code("de") is True

    # Invalid language codes
    assert is_language_code("eng") is False  # Too long
    assert is_language_code("e") is False  # Too short
    assert is_language_code("12") is False  # Not alphabetic
    assert is_language_code("e1") is False  # Not alphabetic
    assert is_language_code("") is False  # Empty string


def test_validate_data_type():
    """Test the validate_data_type function."""
    valid_types = ["discrete", "continuous", "nominal", "ordinal", "text"]

    # Valid data types
    assert validate_data_type("discrete", valid_types) is True
    assert validate_data_type("continuous", valid_types) is True
    assert validate_data_type("nominal", valid_types) is True
    assert validate_data_type("ordinal", valid_types) is True
    assert validate_data_type("text", valid_types) is True

    # Invalid data types
    assert validate_data_type("invalid_type", valid_types) is False
    assert validate_data_type("", valid_types) is False
    assert validate_data_type("DISCRETE", valid_types) is False  # Case sensitive

    # Test with different valid_types list
    custom_types = ["type1", "type2"]
    assert validate_data_type("type1", custom_types) is True
    assert validate_data_type("type2", custom_types) is True
    assert validate_data_type("discrete", custom_types) is False


def test_validation_error():
    """Test the ValidationError class."""
    error = ValidationError("name", "Name is required")
    assert error.field == "name"
    assert error.message == "Name is required"
    assert str(error) == "name: Name is required"


def test_validation_result():
    """Test the ValidationResult class."""
    result = ValidationResult()

    # Test initial state
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0

    # Test adding errors
    result.add_error("name", "Name is required")
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0]["field"] == "name"
    assert result.errors[0]["message"] == "Name is required"

    # Test adding warnings
    result.add_warning("data_type", "Data type is deprecated")
    assert len(result.warnings) == 1
    assert result.warnings[0]["field"] == "data_type"
    assert result.warnings[0]["message"] == "Data type is deprecated"

    # Test string representation
    assert "Errors:" in str(result)
    assert "name: Name is required" in str(result)
    assert "Warnings:" in str(result)
    assert "data_type: Data type is deprecated" in str(result)


def test_variable_validate_data():
    """Test the Variable.validate_data method."""
    # Test valid data
    data = {
        "name": "variable",
        "data_type": "discrete"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is True

    # Test missing name
    data = {
        "data_type": "discrete"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test invalid name
    data = {
        "name": "Invalid Name",
        "data_type": "discrete"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test missing data type
    data = {
        "name": "variable"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "data_type" for e in result.errors)

    # Test invalid data type
    data = {
        "name": "variable",
        "data_type": "invalid_type"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "data_type" for e in result.errors)

    # Test categorical variable without category set
    data = {
        "name": "variable",
        "data_type": "nominal"
    }
    result = Variable.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "category_set" for e in result.errors)

    # Test non-categorical variable with category set
    data = {
        "name": "variable",
        "data_type": "discrete",
        "category_set_id": 1
    }
    result = Variable.validate_data(data)
    assert result.is_valid is True  # This is a warning, not an error
    assert any(w["field"] == "category_set" for w in result.warnings)


def test_category_set_validate_data():
    """Test the CategorySet.validate_data method."""
    # Test valid data
    data = {
        "name": "category_set"
    }
    result = CategorySet.validate_data(data)
    assert result.is_valid is True

    # Test missing name
    data = {}
    result = CategorySet.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test invalid name
    data = {
        "name": "Invalid Name"
    }
    result = CategorySet.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test with categories
    data = {
        "name": "category_set",
        "categories": [
            {"name": "category1"},
            {"name": "category2"}
        ]
    }
    result = CategorySet.validate_data(data)
    assert result.is_valid is True

    # Test with invalid categories
    data = {
        "name": "category_set",
        "categories": "not_a_list"
    }
    result = CategorySet.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "categories" for e in result.errors)

    # Test with invalid category name
    data = {
        "name": "category_set",
        "categories": [
            {"name": "Invalid Name"}
        ]
    }
    result = CategorySet.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"].startswith("categories[0].name") for e in result.errors)


def test_category_validate_data():
    """Test the Category.validate_data method."""
    # Test valid data
    data = {
        "name": "category",
        "category_set_id": 1
    }
    result = Category.validate_data(data)
    assert result.is_valid is True

    # Test missing name
    data = {
        "category_set_id": 1
    }
    result = Category.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test invalid name
    data = {
        "name": "Invalid Name",
        "category_set_id": 1
    }
    result = Category.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "name" for e in result.errors)

    # Test missing category set ID
    data = {
        "name": "category"
    }
    result = Category.validate_data(data)
    assert result.is_valid is False
    assert any(e["field"] == "category_set_id" for e in result.errors)
