"""Constraints framework for varman variables."""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union


class Constraint(ABC):
    """Base class for all constraints."""

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value is valid, False otherwise.
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: Dict[str, Any]) -> 'Constraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new constraint instance.
        """
        pass


class MinValueConstraint(Constraint):
    """Constraint for minimum value."""

    def __init__(self, min_value: Union[int, float]):
        """Initialize a MinValueConstraint.

        Args:
            min_value: The minimum allowed value.
        """
        self.min_value = min_value

    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value is greater than or equal to the minimum value, False otherwise.
        """
        try:
            return float(value) >= self.min_value
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        return {
            "type": "min_value",
            "min_value": self.min_value
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MinValueConstraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new MinValueConstraint instance.
        """
        return MinValueConstraint(data["min_value"])


class MaxValueConstraint(Constraint):
    """Constraint for maximum value."""

    def __init__(self, max_value: Union[int, float]):
        """Initialize a MaxValueConstraint.

        Args:
            max_value: The maximum allowed value.
        """
        self.max_value = max_value

    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value is less than or equal to the maximum value, False otherwise.
        """
        try:
            return float(value) <= self.max_value
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        return {
            "type": "max_value",
            "max_value": self.max_value
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MaxValueConstraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new MaxValueConstraint instance.
        """
        return MaxValueConstraint(data["max_value"])


class EmailConstraint(Constraint):
    """Constraint for email validation."""

    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value is a valid email address, False otherwise.
        """
        if not isinstance(value, str):
            return False
        
        # Simple email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        return {
            "type": "email"
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EmailConstraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new EmailConstraint instance.
        """
        return EmailConstraint()


class UrlConstraint(Constraint):
    """Constraint for URL validation."""

    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value is a valid URL, False otherwise.
        """
        if not isinstance(value, str):
            return False
        
        # Simple URL validation regex
        url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        return {
            "type": "url"
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UrlConstraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new UrlConstraint instance.
        """
        return UrlConstraint()


class RegexConstraint(Constraint):
    """Constraint for regex pattern matching."""

    def __init__(self, pattern: str):
        """Initialize a RegexConstraint.

        Args:
            pattern: The regex pattern to match against.
        """
        self.pattern = pattern
        self.compiled_pattern = re.compile(pattern)

    def validate(self, value: Any) -> bool:
        """Validate a value against this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value matches the regex pattern, False otherwise.
        """
        if not isinstance(value, str):
            return False
        
        return bool(self.compiled_pattern.match(value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the constraint to a dictionary.

        Returns:
            A dictionary representation of the constraint.
        """
        return {
            "type": "regex",
            "pattern": self.pattern
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'RegexConstraint':
        """Create a constraint from a dictionary.

        Args:
            data: The dictionary representation of the constraint.

        Returns:
            A new RegexConstraint instance.
        """
        return RegexConstraint(data["pattern"])


# Registry of constraint types
CONSTRAINT_TYPES: Dict[str, Type[Constraint]] = {
    "min_value": MinValueConstraint,
    "max_value": MaxValueConstraint,
    "email": EmailConstraint,
    "url": UrlConstraint,
    "regex": RegexConstraint
}


def create_constraint(constraint_type: str, **kwargs) -> Constraint:
    """Create a constraint of the specified type.

    Args:
        constraint_type: The type of constraint to create.
        **kwargs: Additional arguments for the constraint.

    Returns:
        A new constraint instance.

    Raises:
        ValueError: If the constraint type is not recognized.
    """
    if constraint_type not in CONSTRAINT_TYPES:
        raise ValueError(f"Unknown constraint type: {constraint_type}")
    
    constraint_class = CONSTRAINT_TYPES[constraint_type]
    return constraint_class(**kwargs)


def constraint_from_dict(data: Dict[str, Any]) -> Constraint:
    """Create a constraint from a dictionary.

    Args:
        data: The dictionary representation of the constraint.

    Returns:
        A new constraint instance.

    Raises:
        ValueError: If the constraint type is not recognized.
    """
    constraint_type = data.get("type")
    if constraint_type not in CONSTRAINT_TYPES:
        raise ValueError(f"Unknown constraint type: {constraint_type}")
    
    constraint_class = CONSTRAINT_TYPES[constraint_type]
    return constraint_class.from_dict(data)


def register_constraint_type(constraint_type: str, constraint_class: Type[Constraint]) -> None:
    """Register a new constraint type.

    Args:
        constraint_type: The type name for the constraint.
        constraint_class: The constraint class.
    """
    CONSTRAINT_TYPES[constraint_type] = constraint_class