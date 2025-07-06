"""Validation utilities for varman."""

import re
from typing import Tuple, Optional, List, Dict, Any


class ValidationError(Exception):
    """Exception raised for validation errors."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ValidationResult:
    """Result of a validation operation."""
    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, field: str, message: str):
        """Add an error to the validation result.

        Args:
            field: The field that has the error.
            message: The error message.
        """
        self.errors.append({"field": field, "message": message})

    def add_warning(self, field: str, message: str):
        """Add a warning to the validation result.

        Args:
            field: The field that has the warning.
            message: The warning message.
        """
        self.warnings.append({"field": field, "message": message})

    @property
    def is_valid(self):
        """Check if the validation result is valid.

        Returns:
            True if there are no errors, False otherwise.
        """
        return len(self.errors) == 0

    def __str__(self):
        """Get a string representation of the validation result.

        Returns:
            A string representation.
        """
        result = []
        if self.errors:
            result.append("Errors:")
            for error in self.errors:
                result.append(f"  {error['field']}: {error['message']}")
        if self.warnings:
            result.append("Warnings:")
            for warning in self.warnings:
                result.append(f"  {warning['field']}: {warning['message']}")
        if not result:
            result.append("Valid")
        return "\n".join(result)


def validate_name(name: str) -> bool:
    """Validate a name.

    Args:
        name: The name to validate.

    Returns:
        True if the name is valid, False otherwise.
    """
    # Name must be a valid Python identifier and lowercase
    return name.isidentifier() and name.islower()


def parse_label(label_str: str) -> Tuple[str, Optional[str], str]:
    """Parse a label string.

    Args:
        label_str: The label string in format 'language:text' or 'language:purpose:text'.

    Returns:
        A tuple of (language, purpose, text).

    Raises:
        ValueError: If the label string is invalid.
    """
    parts = label_str.split(":", 2)
    if len(parts) == 2:
        language, text = parts
        purpose = None
    elif len(parts) == 3:
        language, purpose, text = parts
    else:
        raise ValueError(f"Invalid label format: {label_str}")

    return language, purpose, text


def is_language_code(language: str) -> bool:
    """Check if a string is a language code.

    Args:
        language: The string to check.

    Returns:
        True if the string is a language code, False otherwise.
    """
    # Language code is a two-letter ISO 639 code
    return len(language) == 2 and language.isalpha()


def validate_data_type(data_type: str, valid_types: list) -> bool:
    """Validate a data type.

    Args:
        data_type: The data type to validate.
        valid_types: A list of valid data types.

    Returns:
        True if the data type is valid, False otherwise.
    """
    return data_type in valid_types
