"""Tests for the CLI variable commands."""

import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock

from varman.cli.main import cli
from varman.cli.variable import (
    create_variable_command, list_variables_command, show_variable_command,
    update_variable_command, delete_variable_command, export_variables_command,
    import_variables_command, ArgumentParserError
)
from varman.models.variable import Variable


def test_show_variable_command(db_connection, capsys):
    """Test the show variable command."""
    # Create a variable to show
    variable, validation_errors = Variable.create_with_validation(
        name="test_show",
        data_type="discrete",
        description="Test variable for show command",
        reference="Test reference",
        connection=db_connection
    )

    # Add a label
    variable.add_label(
        text="Test Label",
        language_code="en",
        purpose="Short",
        connection=db_connection
    )

    # Mock args
    args = MagicMock()
    args.name = "test_show"

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        show_variable_command(args)

    # Check output
    captured = capsys.readouterr()
    assert "Name: test_show" in captured.out
    assert "Type: discrete" in captured.out
    assert "Description: Test variable for show command" in captured.out
    assert "Reference: Test reference" in captured.out
    assert "Labels:" in captured.out
    assert "en (Short): Test Label" in captured.out


def test_show_variable_nonexistent(db_connection, capsys):
    """Test showing a variable that doesn't exist."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_var"

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        show_variable_command(args)

    # Check output
    captured = capsys.readouterr()
    assert "Error: Variable 'nonexistent_var' does not exist" in captured.out


def test_update_variable_command(db_connection, capsys):
    """Test updating a variable."""
    # Create a variable to update
    variable, validation_errors = Variable.create_with_validation(
        name="test_update",
        data_type="discrete",
        description="Original description",
        connection=db_connection
    )

    # Mock args
    args = MagicMock()
    args.name = "test_update"
    args.description = "Updated description"
    args.reference = "New reference"
    args.add_label = ["en:New Label"]
    args.remove_label = []
    args.min_value = "10"
    args.max_value = None
    args.email = False
    args.url = False
    args.regex = None
    args.remove_min_value = False
    args.remove_max_value = False
    args.remove_email = False
    args.remove_url = False
    args.remove_regex = False

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        update_variable_command(args)

    # Check that the variable was updated
    updated_var = Variable.get_by("name", "test_update")
    assert updated_var.description == "Updated description"
    assert updated_var.reference == "New reference"

    # Check that the label was added
    assert len(updated_var.labels) == 1
    assert updated_var.labels[0].text == "New Label"

    # Check that the constraint was added
    assert len(updated_var.constraints) == 1
    assert updated_var.constraints[0].to_dict()["type"] == "min_value"
    assert updated_var.constraints[0].to_dict()["min_value"] == 10.0

    # Check output
    captured = capsys.readouterr()
    assert "Variable 'test_update' updated" in captured.out


def test_update_variable_nonexistent(db_connection, capsys):
    """Test updating a variable that doesn't exist."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_var"
    args.description = "Updated description"
    args.reference = None
    args.add_label = []
    args.remove_label = []
    args.min_value = None
    args.max_value = None
    args.email = False
    args.url = False
    args.regex = None
    args.remove_min_value = False
    args.remove_max_value = False
    args.remove_email = False
    args.remove_url = False
    args.remove_regex = False

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        update_variable_command(args)

    # Check output
    captured = capsys.readouterr()
    assert "Error: Variable 'nonexistent_var' does not exist" in captured.out


def test_delete_variable_command(db_connection, capsys):
    """Test deleting a variable."""
    # Create a variable to delete
    variable, validation_errors = Variable.create_with_validation(
        name="test_delete",
        data_type="discrete",
        connection=db_connection
    )

    # Mock args
    args = MagicMock()
    args.name = "test_delete"
    args.yes = True  # Skip confirmation

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        delete_variable_command(args)

    # Check that the variable was deleted
    assert Variable.get_by("name", "test_delete") is None

    # Check output
    captured = capsys.readouterr()
    assert "Variable 'test_delete' deleted" in captured.out


def test_delete_variable_nonexistent(db_connection, capsys):
    """Test deleting a variable that doesn't exist."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_var"
    args.yes = True

    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        delete_variable_command(args)

    # Check output
    captured = capsys.readouterr()
    assert "Error: Variable 'nonexistent_var' does not exist" in captured.out


def test_export_variables_command(db_connection, capsys):
    """Test exporting variables to a JSON file."""
    # Create variables to export
    var1, errors1 = Variable.create_with_validation(
        name="export_var1",
        data_type="discrete",
        description="Variable 1",
        connection=db_connection
    )

    var2, errors2 = Variable.create_with_validation(
        name="export_var2",
        data_type="continuous",
        description="Variable 2",
        connection=db_connection
    )

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Mock args
        args = MagicMock()
        args.file = temp_path
        args.name = None  # Export all variables

        # Call the command
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            export_variables_command(args)

        # Check that the file was created
        assert os.path.exists(temp_path)

        # Check the file contents
        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert "export_var1" in data
        assert "export_var2" in data
        assert data["export_var1"]["description"] == "Variable 1"
        assert data["export_var2"]["description"] == "Variable 2"

        # Check output
        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert temp_path in captured.out

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_export_specific_variables(db_connection, capsys):
    """Test exporting specific variables to a JSON file."""
    # Create variables
    var1, errors1 = Variable.create_with_validation(
        name="specific_var1",
        data_type="discrete",
        connection=db_connection
    )

    var2, errors2 = Variable.create_with_validation(
        name="specific_var2",
        data_type="continuous",
        connection=db_connection
    )

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Mock args
        args = MagicMock()
        args.file = temp_path
        args.name = ["specific_var1"]  # Export only specific_var1

        # Call the command
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            export_variables_command(args)

        # Check the file contents
        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert "specific_var1" in data
        assert "specific_var2" not in data

        # Check output
        captured = capsys.readouterr()
        assert "Exported 1 variable" in captured.out

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_import_variables_command(db_connection, capsys):
    """Test importing variables from a JSON file."""
    # Create a JSON file with variable data
    variables_data = {
        "import_var1": {
            "name": "import_var1",
            "data_type": "discrete",
            "description": "Imported Variable 1",
            "labels": [],
            "constraints": []
        },
        "import_var2": {
            "name": "import_var2",
            "data_type": "continuous",
            "description": "Imported Variable 2",
            "labels": [],
            "constraints": []
        }
    }

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(variables_data, temp_file)
        temp_path = temp_file.name

    try:
        # Mock args
        args = MagicMock()
        args.file = temp_path
        args.overwrite = False

        # Call the command
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            import_variables_command(args)

        # Check that the variables were imported
        var1 = Variable.get_by("name", "import_var1")
        assert var1 is not None
        assert var1.data_type == "discrete"
        assert var1.description == "Imported Variable 1"

        var2 = Variable.get_by("name", "import_var2")
        assert var2 is not None
        assert var2.data_type == "continuous"
        assert var2.description == "Imported Variable 2"

        # Check output
        captured = capsys.readouterr()
        assert "Successfully imported 2 variable" in captured.out

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_import_with_overwrite(db_connection, capsys):
    """Test importing variables with overwrite option."""
    # Create an existing variable
    variable, errors = Variable.create_with_validation(
        name="overwrite_var",
        data_type="discrete",
        description="Original description",
        connection=db_connection
    )

    # Create a JSON file with variable data to overwrite
    variables_data = {
        "overwrite_var": {
            "name": "overwrite_var",
            "data_type": "continuous",
            "description": "Overwritten description",
            "labels": [],
            "constraints": []
        }
    }

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as temp_file:
        json.dump(variables_data, temp_file)
        temp_path = temp_file.name

    try:
        # Mock args
        args = MagicMock()
        args.file = temp_path
        args.overwrite = True

        # Call the command
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            import_variables_command(args)

        # Check that the variable was overwritten
        var = Variable.get_by("name", "overwrite_var")
        assert var is not None
        assert var.data_type == "continuous"
        assert var.description == "Overwritten description"

        # Check output
        captured = capsys.readouterr()
        assert "Successfully imported 1 variable" in captured.out
        assert "Overwritten variables: overwrite_var" in captured.out

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_cli_variable_show_integration(db_connection):
    """Test the variable show command through the CLI."""
    # Create a variable
    variable, errors = Variable.create_with_validation(
        name="show_var",
        data_type="discrete",
        description="Variable to show",
        connection=db_connection
    )

    # Mock sys.argv
    with patch("sys.argv", ["varman", "variable", "show", "show_var"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # The test passes if no exception is raised


def test_cli_variable_update_integration(db_connection):
    """Test the variable update command through the CLI."""
    # Create a variable
    variable, errors = Variable.create_with_validation(
        name="update_var",
        data_type="discrete",
        connection=db_connection
    )

    # Mock sys.argv
    with patch("sys.argv", [
        "varman", "variable", "update", "update_var",
        "--description", "Updated via CLI"
    ]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # Check that the variable was updated
    var = Variable.get_by("name", "update_var")
    assert var.description == "Updated via CLI"


def test_cli_variable_delete_integration(db_connection):
    """Test the variable delete command through the CLI."""
    # Create a variable
    variable, errors = Variable.create_with_validation(
        name="delete_var",
        data_type="discrete",
        connection=db_connection
    )

    # Mock sys.argv
    with patch("sys.argv", ["varman", "variable", "delete", "delete_var", "--yes"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # Check that the variable was deleted
    assert Variable.get_by("name", "delete_var") is None


def test_argument_parser_error():
    """Test the ArgumentParserError class."""
    with pytest.raises(ArgumentParserError):
        raise ArgumentParserError("Test error message")
