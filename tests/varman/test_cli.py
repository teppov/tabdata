"""Tests for the CLI functionality."""

import os
import subprocess
import sys
import pytest
from unittest.mock import patch, MagicMock

from varman.cli.main import cli, setup_parser
from varman.db.schema import reset_db


def test_setup_parser():
    """Test that the argument parser is set up correctly."""
    parser = setup_parser()

    # Test that the parser has the expected commands
    subparsers = parser._subparsers._group_actions[0]
    commands = [action.dest for action in subparsers._choices_actions]

    assert "reset" in commands
    assert "variable" in commands
    assert "category-set" in commands


def test_cli_help(capsys):
    """Test that the CLI help command works."""
    # Mock sys.argv
    with patch("sys.argv", ["varman", "--help"]):
        # Call cli() and catch the SystemExit
        with pytest.raises(SystemExit):
            cli()

    # Check that help text was printed
    captured = capsys.readouterr()
    assert "Manage variables for a tabular dataset" in captured.out


def test_cli_reset(db_connection, capsys):
    """Test the reset command."""
    # Insert some data to be reset
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
    db_connection.commit()

    # Mock sys.argv and confirm_action
    with patch("sys.argv", ["varman", "reset", "--yes"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # Check that the database was reset
    cursor.execute("SELECT COUNT(*) FROM category_sets")
    assert cursor.fetchone()[0] == 0

    # Check that a message was printed
    captured = capsys.readouterr()
    assert "Database reset" in captured.out


def test_cli_variable_list(db_connection, capsys):
    """Test the variable list command."""
    # Create a variable
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO variables (name, data_type, description) VALUES (?, ?, ?)",
        ("test_var", "discrete", "Test variable")
    )
    db_connection.commit()

    # Mock sys.argv
    with patch("sys.argv", ["varman", "variable", "list"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # Check that the variable was listed
    captured = capsys.readouterr()
    assert "test_var" in captured.out
    assert "discrete" in captured.out


def test_cli_variable_create(db_connection, capsys):
    """Test the variable create command."""
    # Mock sys.argv
    with patch("sys.argv", [
        "varman", "variable", "create", "new_var",
        "--type", "discrete",
        "--description", "New variable"
    ]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
                cli()

    # Check that the variable was created
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM variables WHERE name = 'new_var'")
    row = cursor.fetchone()
    assert row is not None
    assert row["data_type"] == "discrete"
    assert row["description"] == "New variable"

    # Check that a message was printed
    captured = capsys.readouterr()
    assert "Variable 'new_var' created" in captured.out


def test_cli_category_set_create(db_connection, capsys):
    """Test the category-set create command."""
    # Mock sys.argv
    with patch("sys.argv", [
        "varman", "category-set", "create", "new_set",
        "--category", "cat1",
        "--category", "cat2"
    ]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()

    # Check that the category set was created
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM category_sets WHERE name = 'new_set'")
    row = cursor.fetchone()
    assert row is not None

    # Check that the categories were created
    cursor.execute(
        "SELECT * FROM categories WHERE category_set_id = ?",
        (row["id"],)
    )
    categories = cursor.fetchall()
    assert len(categories) == 2
    category_names = [cat["name"] for cat in categories]
    assert "cat1" in category_names
    assert "cat2" in category_names

    # Check that a message was printed
    captured = capsys.readouterr()
    assert "Category set 'new_set' created" in captured.out


def test_cli_integration():
    """Test the CLI with actual subprocess calls."""
    # Use a temporary database file
    db_path = os.path.join(os.path.dirname(__file__), "test_cli.db")

    try:
        # Set the database path environment variable
        os.environ["VARMAN_DB_PATH"] = db_path

        # Reset the database
        result = subprocess.run(
            [sys.executable, "-m", "varman.cli.main", "reset", "--yes"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Database reset" in result.stdout

        # Create a variable
        result = subprocess.run(
            [
                sys.executable, "-m", "varman.cli.main", "variable", "create", "test_var",
                "--type", "discrete",
                "--description", "Test variable"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Variable 'test_var' created" in result.stdout

        # List variables
        result = subprocess.run(
            [sys.executable, "-m", "varman.cli.main", "variable", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "test_var" in result.stdout
        assert "discrete" in result.stdout

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)
        if "VARMAN_DB_PATH" in os.environ:
            del os.environ["VARMAN_DB_PATH"]
