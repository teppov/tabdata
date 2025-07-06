"""Tests for the example variables JSON file."""

import pytest
import os
import json
import tempfile
from typing import Dict, List, Any

from varman.models.variable import Variable


def test_import_example_variables(db_connection):
    """Test importing variables from the example JSON file."""
    # Get the path to the example JSON file
    example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               "examples", "example_variables.json")

    # Import variables from the example JSON file
    imported_vars, errors, overwritten = Variable.import_from_json(example_path)

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred during import: {errors}"

    # Verify all variables were imported
    with open(example_path, 'r') as f:
        example_data = json.load(f)

    assert len(imported_vars) == len(example_data), "Not all variables were imported"

    # Verify each variable was imported correctly
    for var in imported_vars:
        var_name = var.name
        assert var_name in example_data, f"Variable {var_name} not found in example data"

        var_data = example_data[var_name]
        assert var.data_type == var_data["data_type"]
        assert var.description == var_data["description"]
        assert var.reference == var_data["reference"]

        # Verify labels
        assert len(var.labels) == len(var_data["labels"])

        # Verify constraints
        assert len(var.constraints) == len(var_data["constraints"])

        # Verify category set if applicable
        if "category_set" in var_data:
            assert var.category_set is not None
            assert var.category_set.name == var_data["category_set"]["name"]
            assert len(var.category_set.categories) == len(var_data["category_set"]["categories"])


def test_export_example_variables(db_connection):
    """Test exporting variables and comparing to the example JSON file."""
    # Get the path to the example JSON file
    example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               "examples", "example_variables.json")

    # Import variables from the example JSON file
    imported_vars, errors, overwritten = Variable.import_from_json(example_path)

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred during import: {errors}"

    # Create a temporary file for export
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        temp_path = temp_file.name

    try:
        # Export the imported variables to the temporary file
        Variable.export_to_json(imported_vars, temp_path)

        # Read the original and exported JSON files
        with open(example_path, 'r') as f:
            original_data = json.load(f)

        with open(temp_path, 'r') as f:
            exported_data = json.load(f)

        # Compare the number of variables
        assert len(exported_data) == len(original_data)

        # Compare each variable
        for var_name, original_var in original_data.items():
            assert var_name in exported_data, f"Variable {var_name} not found in exported data"

            exported_var = exported_data[var_name]

            # Compare basic properties
            assert exported_var["name"] == original_var["name"]
            assert exported_var["data_type"] == original_var["data_type"]
            assert exported_var["description"] == original_var["description"]
            assert exported_var["reference"] == original_var["reference"]

            # Compare labels (count only, as order might differ)
            assert len(exported_var["labels"]) == len(original_var["labels"])

            # Compare constraints (count only, as order might differ)
            assert len(exported_var["constraints"]) == len(original_var["constraints"])

            # Compare category set if applicable
            if "category_set" in original_var:
                assert "category_set" in exported_var
                assert exported_var["category_set"]["name"] == original_var["category_set"]["name"]
                assert len(exported_var["category_set"]["categories"]) == len(original_var["category_set"]["categories"])

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
