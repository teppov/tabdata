"""Tests for the constraints framework."""

import pytest
import sqlite3

from varman.utils.constraints import (
    Constraint, MinValueConstraint, MaxValueConstraint,
    EmailConstraint, UrlConstraint, RegexConstraint,
    create_constraint, constraint_from_dict, register_constraint_type
)
from varman.models.variable import Variable


def test_min_value_constraint():
    """Test the MinValueConstraint."""
    constraint = MinValueConstraint(10)
    
    # Test validation
    assert constraint.validate(10) is True
    assert constraint.validate(11) is True
    assert constraint.validate(9) is False
    assert constraint.validate("10") is True
    assert constraint.validate("9") is False
    assert constraint.validate("abc") is False
    
    # Test to_dict and from_dict
    constraint_dict = constraint.to_dict()
    assert constraint_dict["type"] == "min_value"
    assert constraint_dict["min_value"] == 10
    
    new_constraint = MinValueConstraint.from_dict(constraint_dict)
    assert new_constraint.min_value == 10


def test_max_value_constraint():
    """Test the MaxValueConstraint."""
    constraint = MaxValueConstraint(10)
    
    # Test validation
    assert constraint.validate(10) is True
    assert constraint.validate(9) is True
    assert constraint.validate(11) is False
    assert constraint.validate("10") is True
    assert constraint.validate("11") is False
    assert constraint.validate("abc") is False
    
    # Test to_dict and from_dict
    constraint_dict = constraint.to_dict()
    assert constraint_dict["type"] == "max_value"
    assert constraint_dict["max_value"] == 10
    
    new_constraint = MaxValueConstraint.from_dict(constraint_dict)
    assert new_constraint.max_value == 10


def test_email_constraint():
    """Test the EmailConstraint."""
    constraint = EmailConstraint()
    
    # Test validation
    assert constraint.validate("user@example.com") is True
    assert constraint.validate("user.name@example.co.uk") is True
    assert constraint.validate("user@") is False
    assert constraint.validate("user@.com") is False
    assert constraint.validate("@example.com") is False
    assert constraint.validate("not an email") is False
    assert constraint.validate(123) is False
    
    # Test to_dict and from_dict
    constraint_dict = constraint.to_dict()
    assert constraint_dict["type"] == "email"
    
    new_constraint = EmailConstraint.from_dict(constraint_dict)
    assert isinstance(new_constraint, EmailConstraint)


def test_url_constraint():
    """Test the UrlConstraint."""
    constraint = UrlConstraint()
    
    # Test validation
    assert constraint.validate("http://example.com") is True
    assert constraint.validate("https://example.com/path") is True
    assert constraint.validate("ftp://example.com") is True
    assert constraint.validate("example.com") is False
    assert constraint.validate("not a url") is False
    assert constraint.validate(123) is False
    
    # Test to_dict and from_dict
    constraint_dict = constraint.to_dict()
    assert constraint_dict["type"] == "url"
    
    new_constraint = UrlConstraint.from_dict(constraint_dict)
    assert isinstance(new_constraint, UrlConstraint)


def test_regex_constraint():
    """Test the RegexConstraint."""
    constraint = RegexConstraint(r"^\d{3}-\d{2}-\d{4}$")
    
    # Test validation
    assert constraint.validate("123-45-6789") is True
    assert constraint.validate("123-456-789") is False
    assert constraint.validate("abc-de-fghi") is False
    assert constraint.validate(123) is False
    
    # Test to_dict and from_dict
    constraint_dict = constraint.to_dict()
    assert constraint_dict["type"] == "regex"
    assert constraint_dict["pattern"] == r"^\d{3}-\d{2}-\d{4}$"
    
    new_constraint = RegexConstraint.from_dict(constraint_dict)
    assert new_constraint.pattern == r"^\d{3}-\d{2}-\d{4}$"


def test_create_constraint():
    """Test the create_constraint function."""
    min_constraint = create_constraint("min_value", min_value=10)
    assert isinstance(min_constraint, MinValueConstraint)
    assert min_constraint.min_value == 10
    
    max_constraint = create_constraint("max_value", max_value=20)
    assert isinstance(max_constraint, MaxValueConstraint)
    assert max_constraint.max_value == 20
    
    email_constraint = create_constraint("email")
    assert isinstance(email_constraint, EmailConstraint)
    
    url_constraint = create_constraint("url")
    assert isinstance(url_constraint, UrlConstraint)
    
    regex_constraint = create_constraint("regex", pattern=r"\d+")
    assert isinstance(regex_constraint, RegexConstraint)
    assert regex_constraint.pattern == r"\d+"
    
    with pytest.raises(ValueError):
        create_constraint("unknown_type")


def test_constraint_from_dict():
    """Test the constraint_from_dict function."""
    min_dict = {"type": "min_value", "min_value": 10}
    min_constraint = constraint_from_dict(min_dict)
    assert isinstance(min_constraint, MinValueConstraint)
    assert min_constraint.min_value == 10
    
    max_dict = {"type": "max_value", "max_value": 20}
    max_constraint = constraint_from_dict(max_dict)
    assert isinstance(max_constraint, MaxValueConstraint)
    assert max_constraint.max_value == 20
    
    email_dict = {"type": "email"}
    email_constraint = constraint_from_dict(email_dict)
    assert isinstance(email_constraint, EmailConstraint)
    
    url_dict = {"type": "url"}
    url_constraint = constraint_from_dict(url_dict)
    assert isinstance(url_constraint, UrlConstraint)
    
    regex_dict = {"type": "regex", "pattern": r"\d+"}
    regex_constraint = constraint_from_dict(regex_dict)
    assert isinstance(regex_constraint, RegexConstraint)
    assert regex_constraint.pattern == r"\d+"
    
    with pytest.raises(ValueError):
        constraint_from_dict({"type": "unknown_type"})


def test_register_constraint_type():
    """Test the register_constraint_type function."""
    # Create a custom constraint class
    class CustomConstraint(Constraint):
        def __init__(self, value):
            self.value = value
        
        def validate(self, value):
            return value == self.value
        
        def to_dict(self):
            return {"type": "custom", "value": self.value}
        
        @staticmethod
        def from_dict(data):
            return CustomConstraint(data["value"])
    
    # Register the custom constraint type
    register_constraint_type("custom", CustomConstraint)
    
    # Create a custom constraint
    custom_constraint = create_constraint("custom", value="test")
    assert isinstance(custom_constraint, CustomConstraint)
    assert custom_constraint.value == "test"
    
    # Test validation
    assert custom_constraint.validate("test") is True
    assert custom_constraint.validate("other") is False
    
    # Test to_dict and from_dict
    custom_dict = custom_constraint.to_dict()
    assert custom_dict["type"] == "custom"
    assert custom_dict["value"] == "test"
    
    new_custom_constraint = constraint_from_dict(custom_dict)
    assert isinstance(new_custom_constraint, CustomConstraint)
    assert new_custom_constraint.value == "test"


@pytest.fixture
def variable(db_connection):
    """Create a test variable."""
    return Variable.create_with_validation(
        name="test_constraints",
        data_type="discrete",
        description="A test variable for constraints",
        connection=db_connection
    )[0]  # the 2nd element is a list of validation errors


def test_variable_add_constraint(variable, db_connection):
    """Test adding a constraint to a variable."""
    # Add a min value constraint
    min_constraint = MinValueConstraint(10)
    variable.add_constraint(min_constraint, db_connection)
    
    # Verify the constraint was added
    constraints = variable.constraints
    assert len(constraints) == 1
    assert isinstance(constraints[0], MinValueConstraint)
    assert constraints[0].min_value == 10
    
    # Add a max value constraint
    max_constraint = MaxValueConstraint(20)
    variable.add_constraint(max_constraint, db_connection)
    
    # Refresh constraints
    variable._constraints = None
    constraints = variable.constraints
    
    # Verify both constraints are present
    assert len(constraints) == 2
    constraint_types = [c.to_dict()["type"] for c in constraints]
    assert "min_value" in constraint_types
    assert "max_value" in constraint_types


def test_variable_remove_constraint(variable, db_connection):
    """Test removing a constraint from a variable."""
    # Add constraints
    variable.add_constraint(MinValueConstraint(10), db_connection)
    variable.add_constraint(MaxValueConstraint(20), db_connection)
    
    # Verify constraints were added
    variable._constraints = None
    constraints = variable.constraints
    assert len(constraints) == 2
    
    # Remove min value constraint
    variable.remove_constraint("min_value", db_connection)
    
    # Verify min value constraint was removed
    variable._constraints = None
    constraints = variable.constraints
    assert len(constraints) == 1
    assert constraints[0].to_dict()["type"] == "max_value"
    
    # Remove max value constraint
    variable.remove_constraint("max_value", db_connection)
    
    # Verify all constraints were removed
    variable._constraints = None
    constraints = variable.constraints
    assert len(constraints) == 0


def test_variable_to_dict_with_constraints(variable, db_connection):
    """Test that constraints are included in the variable's dictionary representation."""
    # Add constraints
    variable.add_constraint(MinValueConstraint(10), db_connection)
    variable.add_constraint(MaxValueConstraint(20), db_connection)
    
    # Get dictionary representation
    var_dict = variable.to_dict()
    
    # Verify constraints are included
    assert "constraints" in var_dict
    assert len(var_dict["constraints"]) == 2
    
    constraint_types = [c["type"] for c in var_dict["constraints"]]
    assert "min_value" in constraint_types
    assert "max_value" in constraint_types
    
    min_constraint = next(c for c in var_dict["constraints"] if c["type"] == "min_value")
    assert min_constraint["min_value"] == 10
    
    max_constraint = next(c for c in var_dict["constraints"] if c["type"] == "max_value")
    assert max_constraint["max_value"] == 20