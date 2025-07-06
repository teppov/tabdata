"""Tests for the Variable model."""

import pytest
import sqlite3
import os
import json
import tempfile
from typing import Dict, List, Optional

from varman.models.variable import Variable
from varman.models.category_set import CategorySet


@pytest.fixture
def category_set(db_connection):
    """Create a test category set."""
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
    db_connection.commit()

    cursor.execute("SELECT id FROM category_sets WHERE name = 'test_set'")
    category_set_id = cursor.fetchone()[0]

    # Insert some categories
    categories = ["category1", "category2", "category3"]
    for category in categories:
        cursor.execute(
            "INSERT INTO categories (name, category_set_id) VALUES (?, ?)",
            (category, category_set_id)
        )
    db_connection.commit()

    return category_set_id


def test_variable_create_with_validation(db_connection):
    """Test creating a variable with validation."""
    # Create a discrete variable
    variable, validation_errors = Variable.create_with_validation(
        name="test_discrete",
        data_type="discrete",
        description="A test discrete variable",
        reference="Test reference",
        connection=db_connection
    )

    assert variable.name == "test_discrete"
    assert variable.data_type == "discrete"
    assert variable.description == "A test discrete variable"
    assert variable.reference == "Test reference"
    assert variable.category_set_id is None

    # Verify the variable was saved to the database
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM variables WHERE name = 'test_discrete'")
    row = cursor.fetchone()
    assert row is not None
    assert row["data_type"] == "discrete"


def test_variable_create_with_validation_categorical(db_connection, category_set):
    """Test creating a categorical variable with validation."""
    # Create a nominal variable with a category set
    variable, validation_errors = Variable.create_with_validation(
        name="test_nominal",
        data_type="nominal",
        category_set_id=category_set,
        description="A test nominal variable",
        reference="Test reference",
        connection=db_connection
    )

    assert variable.name == "test_nominal"
    assert variable.data_type == "nominal"
    assert variable.description == "A test nominal variable"
    assert variable.reference == "Test reference"
    assert variable.category_set_id == category_set

    # Verify the variable was saved to the database
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM variables WHERE name = 'test_nominal'")
    row = cursor.fetchone()
    assert row is not None
    assert row["data_type"] == "nominal"
    assert row["category_set_id"] == category_set


def test_variable_create_with_validation_invalid_type(db_connection):
    """Test creating a variable with an invalid data type."""
    with pytest.raises(ValueError):
        variable, validation_errors = Variable.create_with_validation(
            name="test_invalid",
            data_type="invalid_type",
            connection=db_connection
        )


def test_variable_create_categorical(db_connection):
    """Test creating a categorical variable with new categories."""
    # Create a nominal variable with new categories
    variable, validation_errors = Variable.create_categorical(
        name="test_categorical",
        data_type="nominal",
        category_names=["cat1", "cat2", "cat3"],
        description="A test categorical variable",
        reference="Test reference",
        connection=db_connection
    )

    assert variable.name == "test_categorical"
    assert variable.data_type == "nominal"
    assert variable.description == "A test categorical variable"
    assert variable.reference == "Test reference"
    assert variable.category_set_id is not None

    # Verify the categories were created
    cat_set = variable.category_set
    assert cat_set is not None
    assert len(cat_set.categories) == 3
    category_names = [cat.name for cat in cat_set.categories]
    assert "cat1" in category_names
    assert "cat2" in category_names
    assert "cat3" in category_names


def test_variable_add_label(db_connection):
    """Test adding a label to a variable."""
    # Create a variable
    variable, validation_errors = Variable.create_with_validation(
        name="test_label",
        data_type="discrete",
        connection=db_connection
    )

    # Add a label
    variable.add_label(
        text="Test Label",
        language_code="en",
        language="English",
        purpose="Short",
        connection=db_connection
    )

    # Verify the label was added
    labels = variable.labels
    assert len(labels) == 1
    assert labels[0].text == "Test Label"
    assert labels[0].language_code == "en"
    assert labels[0].language == "English"
    assert labels[0].purpose == "Short"


def test_variable_remove_label(db_connection):
    """Test removing a label from a variable."""
    # Create a variable
    variable, validation_errors = Variable.create_with_validation(
        name="test_remove_label",
        data_type="discrete",
        connection=db_connection
    )

    # Add a label
    variable.add_label(
        text="Test Label",
        language_code="en",
        connection=db_connection
    )

    # Get the label ID
    labels = variable.labels
    label_id = labels[0].id

    # Remove the label
    variable.remove_label(label_id, connection=db_connection)

    # Verify the label was removed
    labels = variable.labels
    assert len(labels) == 0


def test_variable_to_dict(db_connection):
    """Test converting a variable to a dictionary."""
    # Create a variable
    variable, validation_errors = Variable.create_with_validation(
        name="test_dict",
        data_type="discrete",
        description="A test variable",
        reference="Test reference",
        connection=db_connection
    )

    # Add a label
    variable.add_label(
        text="Test Label",
        language_code="en",
        connection=db_connection
    )

    # Convert to dictionary
    var_dict = variable.to_dict()

    # Verify the dictionary
    assert var_dict["name"] == "test_dict"
    assert var_dict["data_type"] == "discrete"
    assert var_dict["description"] == "A test variable"
    assert var_dict["reference"] == "Test reference"
    assert "labels" in var_dict
    assert len(var_dict["labels"]) == 1
    assert var_dict["labels"][0]["text"] == "Test Label"


def test_variable_export_to_json(db_connection):
    """Test exporting variables to JSON."""
    # Create variables
    var1, validation_errors = Variable.create_with_validation(
        name="export_var1",
        data_type="discrete",
        description="Variable 1",
        connection=db_connection
    )

    var2, validation_errors = Variable.create_with_validation(
        name="export_var2",
        data_type="continuous",
        description="Variable 2",
        connection=db_connection
    )

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Export variables to JSON
        Variable.export_to_json([var1, var2], temp_path)

        # Verify the file exists
        assert os.path.exists(temp_path)

        # Read the file and verify its contents
        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert "export_var1" in data
        assert "export_var2" in data

        assert data["export_var1"]["name"] == "export_var1"
        assert data["export_var1"]["data_type"] == "discrete"
        assert data["export_var1"]["description"] == "Variable 1"

        assert data["export_var2"]["name"] == "export_var2"
        assert data["export_var2"]["data_type"] == "continuous"
        assert data["export_var2"]["description"] == "Variable 2"

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_variable_import_from_json(db_connection):
    """Test importing variables from JSON."""
    # Create a JSON file with variable data
    variables_data = {
        "import_var1": {
            "name": "import_var1",
            "data_type": "discrete",
            "description": "Imported Variable 1",
            "reference": "Test reference 1",
            "labels": [
                {
                    "text": "Variable 1",
                    "language_code": "en",
                    "purpose": "Short"
                }
            ],
            "constraints": []
        },
        "import_var2": {
            "name": "import_var2",
            "data_type": "continuous",
            "description": "Imported Variable 2",
            "reference": "Test reference 2",
            "labels": [],
            "constraints": []
        }
    }

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(variables_data, temp_file)
        temp_path = temp_file.name

    try:
        # Import variables from JSON
        imported_vars, errors, overwritten = Variable.import_from_json(temp_path)

        # Verify the results
        assert len(imported_vars) == 2
        assert len(errors) == 0
        assert len(overwritten) == 0

        # Verify the variables were created
        var1 = Variable.get_by("name", "import_var1")
        assert var1 is not None
        assert var1.data_type == "discrete"
        assert var1.description == "Imported Variable 1"
        assert var1.reference == "Test reference 1"
        assert len(var1.labels) == 1
        assert var1.labels[0].text == "Variable 1"

        var2 = Variable.get_by("name", "import_var2")
        assert var2 is not None
        assert var2.data_type == "continuous"
        assert var2.description == "Imported Variable 2"
        assert var2.reference == "Test reference 2"

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_variable_import_existing(db_connection):
    """Test importing variables that already exist."""
    # Create an existing variable
    Variable.create_with_validation(
        name="existing_var",
        data_type="discrete",
        description="Existing Variable",
        connection=db_connection
    )

    # Create a JSON file with variable data including the existing one
    variables_data = {
        "existing_var": {
            "name": "existing_var",
            "data_type": "continuous",
            "description": "Updated Variable",
            "labels": [],
            "constraints": []
        },
        "new_var": {
            "name": "new_var",
            "data_type": "text",
            "description": "New Variable",
            "labels": [],
            "constraints": []
        }
    }

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(variables_data, temp_file)
        temp_path = temp_file.name

    try:
        # Import variables from JSON without overwrite
        imported_vars, errors, overwritten = Variable.import_from_json(temp_path)

        # Verify the results
        assert len(imported_vars) == 1  # Only the new variable should be imported
        assert len(errors) == 1  # One error for the existing variable
        assert "already exists" in errors[0]["errors"][0]["message"]
        assert len(overwritten) == 0

        # Verify the existing variable was not changed
        existing_var = Variable.get_by("name", "existing_var")
        assert existing_var.data_type == "discrete"
        assert existing_var.description == "Existing Variable"

        # Verify the new variable was created
        new_var = Variable.get_by("name", "new_var")
        assert new_var is not None
        assert new_var.data_type == "text"
        assert new_var.description == "New Variable"

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_variable_import_overwrite(db_connection):
    """Test overwriting existing variables during import."""
    # Create an existing variable
    Variable.create_with_validation(
        name="overwrite_var",
        data_type="discrete",
        description="Original Variable",
        connection=db_connection
    )

    # Create a JSON file with variable data to overwrite the existing one
    variables_data = {
        "overwrite_var": {
            "name": "overwrite_var",
            "data_type": "continuous",
            "description": "Overwritten Variable",
            "labels": [],
            "constraints": []
        }
    }

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(variables_data, temp_file)
        temp_path = temp_file.name

    try:
        # Import variables from JSON with overwrite
        imported_vars, errors, overwritten = Variable.import_from_json(temp_path, overwrite=True)

        # Verify the results
        assert len(imported_vars) == 1
        assert len(errors) == 0
        assert len(overwritten) == 1
        assert "overwrite_var" in overwritten

        # Verify the variable was overwritten
        var = Variable.get_by("name", "overwrite_var")
        assert var is not None
        assert var.data_type == "continuous"
        assert var.description == "Overwritten Variable"

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
