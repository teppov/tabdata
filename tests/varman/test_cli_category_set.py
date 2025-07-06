"""Tests for the CLI category set commands."""

import os
import pytest
from unittest.mock import patch, MagicMock

from varman.cli.main import cli
from varman.cli.category_set import (
    create_category_set_command, list_category_sets_command, show_category_set_command,
    add_category_command, remove_category_command, add_label_command,
    remove_label_command, delete_category_set_command
)
from varman.models.category_set import CategorySet
from varman.models.category import Category


def test_create_category_set_command(db_connection, capsys):
    """Test creating a category set."""
    # Mock args
    args = MagicMock()
    args.name = "test_set"
    args.categories = ["cat1", "cat2", "cat3"]
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        create_category_set_command(args)
    
    # Check that the category set was created
    category_set = CategorySet.get_by("name", "test_set")
    assert category_set is not None
    
    # Check that the categories were created
    assert len(category_set.categories) == 3
    category_names = [cat.name for cat in category_set.categories]
    assert "cat1" in category_names
    assert "cat2" in category_names
    assert "cat3" in category_names
    
    # Check output
    captured = capsys.readouterr()
    assert "Category set 'test_set' created with 3 categories" in captured.out


def test_create_category_set_invalid_name(db_connection, capsys):
    """Test creating a category set with an invalid name."""
    # Mock args
    args = MagicMock()
    args.name = "Invalid-Name"  # Contains hyphens and uppercase
    args.categories = ["cat1", "cat2"]
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        create_category_set_command(args)
    
    # Check that the category set was not created
    category_set = CategorySet.get_by("name", "Invalid-Name")
    assert category_set is None
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Name must be a valid Python identifier and lowercase" in captured.out


def test_create_category_set_already_exists(db_connection, capsys):
    """Test creating a category set that already exists."""
    # Create a category set
    CategorySet.create_with_categories("existing_set", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "existing_set"
    args.categories = ["cat2", "cat3"]
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        create_category_set_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'existing_set' already exists" in captured.out


def test_list_category_sets_command(db_connection, capsys):
    """Test listing category sets."""
    # Create some category sets
    CategorySet.create_with_categories("set1", ["cat1", "cat2"])
    CategorySet.create_with_categories("set2", ["cat3"])
    
    # Mock args
    args = MagicMock()
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        list_category_sets_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Category sets:" in captured.out
    assert "set1 (2 categories)" in captured.out
    assert "set2 (1 categories)" in captured.out


def test_list_category_sets_empty(db_connection, capsys):
    """Test listing category sets when none exist."""
    # Mock args
    args = MagicMock()
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        list_category_sets_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "No category sets found" in captured.out


def test_show_category_set_command(db_connection, capsys):
    """Test showing a category set."""
    # Create a category set with categories
    category_set = CategorySet.create_with_categories("show_set", ["cat1", "cat2"])
    
    # Add a label to a category
    category = category_set.categories[0]
    category.add_label(text="Category 1", language_code="en", purpose="Short")
    
    # Mock args
    args = MagicMock()
    args.name = "show_set"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        show_category_set_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Name: show_set" in captured.out
    assert "Categories:" in captured.out
    assert "cat1" in captured.out
    assert "cat2" in captured.out
    assert "en (Short): Category 1" in captured.out


def test_show_category_set_nonexistent(db_connection, capsys):
    """Test showing a category set that doesn't exist."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        show_category_set_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_add_category_command(db_connection, capsys):
    """Test adding a category to a category set."""
    # Create a category set
    category_set = CategorySet.create_with_categories("add_set", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "add_set"
    args.category_name = "cat2"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_category_command(args)
    
    # Check that the category was added
    updated_set = CategorySet.get_by("name", "add_set")
    assert len(updated_set.categories) == 2
    category_names = [cat.name for cat in updated_set.categories]
    assert "cat1" in category_names
    assert "cat2" in category_names
    
    # Check output
    captured = capsys.readouterr()
    assert "Category 'cat2' added to category set 'add_set'" in captured.out


def test_add_category_nonexistent_set(db_connection, capsys):
    """Test adding a category to a nonexistent category set."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    args.category_name = "cat1"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_category_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_add_category_already_exists(db_connection, capsys):
    """Test adding a category that already exists in the category set."""
    # Create a category set with a category
    category_set = CategorySet.create_with_categories("duplicate_set", ["existing_cat"])
    
    # Mock args
    args = MagicMock()
    args.name = "duplicate_set"
    args.category_name = "existing_cat"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_category_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category 'existing_cat' already exists in this category set" in captured.out


def test_remove_category_command(db_connection, capsys):
    """Test removing a category from a category set."""
    # Create a category set with categories
    category_set = CategorySet.create_with_categories("remove_set", ["cat1", "cat2"])
    
    # Mock args
    args = MagicMock()
    args.name = "remove_set"
    args.category_name = "cat1"
    args.yes = True  # Skip confirmation
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_category_command(args)
    
    # Check that the category was removed
    updated_set = CategorySet.get_by("name", "remove_set")
    assert len(updated_set.categories) == 1
    assert updated_set.categories[0].name == "cat2"
    
    # Check output
    captured = capsys.readouterr()
    assert "Category 'cat1' removed from category set 'remove_set'" in captured.out


def test_remove_category_nonexistent_set(db_connection, capsys):
    """Test removing a category from a nonexistent category set."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    args.category_name = "cat1"
    args.yes = True
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_category_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_remove_category_nonexistent_category(db_connection, capsys):
    """Test removing a nonexistent category from a category set."""
    # Create a category set
    category_set = CategorySet.create_with_categories("set_with_cats", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "set_with_cats"
    args.category_name = "nonexistent_cat"
    args.yes = True
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_category_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category 'nonexistent_cat' does not exist in this category set" in captured.out


def test_add_label_command(db_connection, capsys):
    """Test adding a label to a category."""
    # Create a category set with a category
    category_set = CategorySet.create_with_categories("label_set", ["label_cat"])
    
    # Mock args
    args = MagicMock()
    args.name = "label_set"
    args.category_name = "label_cat"
    args.label_str = "en:Short:Test Label"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_label_command(args)
    
    # Check that the label was added
    updated_set = CategorySet.get_by("name", "label_set")
    category = next(cat for cat in updated_set.categories if cat.name == "label_cat")
    assert len(category.labels) == 1
    assert category.labels[0].text == "Test Label"
    assert category.labels[0].language_code == "en"
    assert category.labels[0].purpose == "Short"
    
    # Check output
    captured = capsys.readouterr()
    assert "Label added to category 'label_cat' in category set 'label_set'" in captured.out


def test_add_label_nonexistent_set(db_connection, capsys):
    """Test adding a label to a category in a nonexistent category set."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    args.category_name = "cat1"
    args.label_str = "en:Test Label"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_label_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_add_label_nonexistent_category(db_connection, capsys):
    """Test adding a label to a nonexistent category."""
    # Create a category set
    category_set = CategorySet.create_with_categories("set_for_label", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "set_for_label"
    args.category_name = "nonexistent_cat"
    args.label_str = "en:Test Label"
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_label_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category 'nonexistent_cat' does not exist in this category set" in captured.out


def test_add_label_invalid_format(db_connection, capsys):
    """Test adding a label with an invalid format."""
    # Create a category set with a category
    category_set = CategorySet.create_with_categories("invalid_label_set", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "invalid_label_set"
    args.category_name = "cat1"
    args.label_str = "invalid_format"  # Missing colon
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        add_label_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Invalid label format: invalid_format" in captured.out


def test_remove_label_command(db_connection, capsys):
    """Test removing a label from a category."""
    # Create a category set with a category
    category_set = CategorySet.create_with_categories("remove_label_set", ["cat_with_label"])
    
    # Add a label to the category
    category = next(cat for cat in category_set.categories if cat.name == "cat_with_label")
    category.add_label(text="Label to remove", language_code="en")
    
    # Get the label ID
    label_id = category.labels[0].id
    
    # Mock args
    args = MagicMock()
    args.name = "remove_label_set"
    args.category_name = "cat_with_label"
    args.label_id = label_id
    args.yes = True  # Skip confirmation
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_label_command(args)
    
    # Check that the label was removed
    updated_set = CategorySet.get_by("name", "remove_label_set")
    category = next(cat for cat in updated_set.categories if cat.name == "cat_with_label")
    assert len(category.labels) == 0
    
    # Check output
    captured = capsys.readouterr()
    assert "Label removed from category 'cat_with_label' in category set 'remove_label_set'" in captured.out


def test_remove_label_nonexistent_set(db_connection, capsys):
    """Test removing a label from a category in a nonexistent category set."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    args.category_name = "cat1"
    args.label_id = 1
    args.yes = True
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_label_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_remove_label_nonexistent_category(db_connection, capsys):
    """Test removing a label from a nonexistent category."""
    # Create a category set
    category_set = CategorySet.create_with_categories("set_for_remove_label", ["cat1"])
    
    # Mock args
    args = MagicMock()
    args.name = "set_for_remove_label"
    args.category_name = "nonexistent_cat"
    args.label_id = 1
    args.yes = True
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        remove_label_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category 'nonexistent_cat' does not exist in this category set" in captured.out


def test_delete_category_set_command(db_connection, capsys):
    """Test deleting a category set."""
    # Create a category set
    CategorySet.create_with_categories("delete_set", ["cat1", "cat2"])
    
    # Mock args
    args = MagicMock()
    args.name = "delete_set"
    args.yes = True  # Skip confirmation
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        delete_category_set_command(args)
    
    # Check that the category set was deleted
    assert CategorySet.get_by("name", "delete_set") is None
    
    # Check output
    captured = capsys.readouterr()
    assert "Category set 'delete_set' deleted" in captured.out


def test_delete_category_set_nonexistent(db_connection, capsys):
    """Test deleting a nonexistent category set."""
    # Mock args
    args = MagicMock()
    args.name = "nonexistent_set"
    args.yes = True
    
    # Call the command
    with patch("varman.db.connection.get_connection", return_value=db_connection):
        delete_category_set_command(args)
    
    # Check output
    captured = capsys.readouterr()
    assert "Error: Category set 'nonexistent_set' does not exist" in captured.out


def test_cli_category_set_list_integration(db_connection):
    """Test the category-set list command through the CLI."""
    # Create some category sets
    CategorySet.create_with_categories("cli_list_set1", ["cat1"])
    CategorySet.create_with_categories("cli_list_set2", ["cat2"])
    
    # Mock sys.argv
    with patch("sys.argv", ["varman", "category-set", "list"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()
    
    # The test passes if no exception is raised


def test_cli_category_set_show_integration(db_connection):
    """Test the category-set show command through the CLI."""
    # Create a category set
    CategorySet.create_with_categories("cli_show_set", ["cat1", "cat2"])
    
    # Mock sys.argv
    with patch("sys.argv", ["varman", "category-set", "show", "cli_show_set"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()
    
    # The test passes if no exception is raised


def test_cli_category_set_add_category_integration(db_connection):
    """Test the category-set add-category command through the CLI."""
    # Create a category set
    CategorySet.create_with_categories("cli_add_cat_set", ["cat1"])
    
    # Mock sys.argv
    with patch("sys.argv", [
        "varman", "category-set", "add-category", "cli_add_cat_set",
        "--category", "cat2"
    ]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()
    
    # Check that the category was added
    category_set = CategorySet.get_by("name", "cli_add_cat_set")
    category_names = [cat.name for cat in category_set.categories]
    assert "cat2" in category_names


def test_cli_category_set_delete_integration(db_connection):
    """Test the category-set delete command through the CLI."""
    # Create a category set
    CategorySet.create_with_categories("cli_delete_set", ["cat1"])
    
    # Mock sys.argv
    with patch("sys.argv", ["varman", "category-set", "delete", "cli_delete_set", "--yes"]):
        with patch("varman.db.connection.get_connection", return_value=db_connection):
            cli()
    
    # Check that the category set was deleted
    assert CategorySet.get_by("name", "cli_delete_set") is None