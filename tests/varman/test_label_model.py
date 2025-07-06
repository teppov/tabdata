"""Tests for the Label model."""

import pytest
import sqlite3
from typing import Dict, Optional, Any

from varman.models.label import Label
from varman.models.variable import Variable
from varman.models.category import Category


def test_label_init(db_connection):
    """Test initializing a Label instance."""
    # Create a label
    label = Label(
        entity_type="variable",
        entity_id=1,
        language_code="en",
        language="English",
        text="Test Label",
        purpose="Short"
    )
    
    # Check attributes
    assert label.entity_type == "variable"
    assert label.entity_id == 1
    assert label.language_code == "en"
    assert label.language == "English"
    assert label.text == "Test Label"
    assert label.purpose == "Short"


def test_label_create_for_entity(db_connection):
    """Test creating a label for an entity."""
    # Create a variable to use as the entity
    variable, validation_errors = Variable.create_with_validation(
        name="test_var",
        data_type="discrete",
        connection=db_connection
    )
    
    # Create a label for the variable
    label = Label.create_for_entity(
        entity_type="variable",
        entity_id=variable.id,
        text="Test Label",
        language_code="en",
        purpose="Short",
        connection=db_connection
    )
    
    # Check that the label was created correctly
    assert label.entity_type == "variable"
    assert label.entity_id == variable.id
    assert label.language_code == "en"
    assert label.text == "Test Label"
    assert label.purpose == "Short"
    
    # Verify the label was saved to the database
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM labels WHERE id = ?", (label.id,))
    row = cursor.fetchone()
    assert row is not None
    assert row["entity_type"] == "variable"
    assert row["entity_id"] == variable.id
    assert row["language_code"] == "en"
    assert row["text"] == "Test Label"
    assert row["purpose"] == "Short"


def test_label_create_for_entity_with_language(db_connection):
    """Test creating a label for an entity with language name instead of code."""
    # Create a variable to use as the entity
    variable, validation_errors = Variable.create_with_validation(
        name="test_var2",
        data_type="discrete",
        connection=db_connection
    )
    
    # Create a label for the variable
    label = Label.create_for_entity(
        entity_type="variable",
        entity_id=variable.id,
        text="Test Label",
        language="English",
        purpose="Short",
        connection=db_connection
    )
    
    # Check that the label was created correctly
    assert label.entity_type == "variable"
    assert label.entity_id == variable.id
    assert label.language == "English"
    assert label.text == "Test Label"
    assert label.purpose == "Short"


def test_label_create_for_entity_missing_language(db_connection):
    """Test creating a label without specifying a language."""
    # Create a variable to use as the entity
    variable, validation_errors = Variable.create_with_validation(
        name="test_var3",
        data_type="discrete",
        connection=db_connection
    )
    
    # Try to create a label without a language
    with pytest.raises(ValueError, match="Either language_code or language must be provided"):
        Label.create_for_entity(
            entity_type="variable",
            entity_id=variable.id,
            text="Test Label",
            purpose="Short",
            connection=db_connection
        )


def test_label_entity_variable(db_connection):
    """Test getting the entity for a variable label."""
    # Create a variable
    variable, validation_errors = Variable.create_with_validation(
        name="test_var_entity",
        data_type="discrete",
        connection=db_connection
    )
    
    # Create a label for the variable
    label = Label.create_for_entity(
        entity_type="variable",
        entity_id=variable.id,
        text="Test Label",
        language_code="en",
        connection=db_connection
    )
    
    # Get the entity
    entity = label.entity
    
    # Check that the entity is the variable
    assert entity is not None
    assert entity.id == variable.id
    assert entity.name == "test_var_entity"


def test_label_entity_category(db_connection):
    """Test getting the entity for a category label."""
    # Create a category set
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
    db_connection.commit()
    
    cursor.execute("SELECT id FROM category_sets WHERE name = 'test_set'")
    category_set_id = cursor.fetchone()[0]
    
    # Create a category
    cursor.execute(
        "INSERT INTO categories (name, category_set_id) VALUES (?, ?)",
        ("test_category", category_set_id)
    )
    db_connection.commit()
    
    cursor.execute("SELECT id FROM categories WHERE name = 'test_category'")
    category_id = cursor.fetchone()[0]
    
    # Create a label for the category
    label = Label.create_for_entity(
        entity_type="category",
        entity_id=category_id,
        text="Test Category Label",
        language_code="en",
        connection=db_connection
    )
    
    # Get the entity
    entity = label.entity
    
    # Check that the entity is the category
    assert entity is not None
    assert entity.id == category_id
    assert entity.name == "test_category"


def test_label_entity_unknown(db_connection):
    """Test getting the entity for a label with an unknown entity type."""
    # Create a label with an unknown entity type
    label = Label.create({
        "entity_type": "unknown",
        "entity_id": 1,
        "language_code": "en",
        "text": "Test Label"
    }, db_connection)
    
    # Get the entity
    entity = label.entity
    
    # Check that the entity is None
    assert entity is None


def test_label_to_dict(db_connection):
    """Test converting a label to a dictionary."""
    # Create a label
    label = Label.create({
        "entity_type": "variable",
        "entity_id": 1,
        "language_code": "en",
        "language": "English",
        "text": "Test Label",
        "purpose": "Short"
    }, db_connection)
    
    # Convert to dictionary
    label_dict = label.to_dict()
    
    # Check dictionary
    assert label_dict["entity_type"] == "variable"
    assert label_dict["entity_id"] == 1
    assert label_dict["language_code"] == "en"
    assert label_dict["language"] == "English"
    assert label_dict["text"] == "Test Label"
    assert label_dict["purpose"] == "Short"