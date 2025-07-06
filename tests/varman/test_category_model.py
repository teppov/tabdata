"""Tests for the Category model."""

import pytest
import sqlite3
from typing import Dict, List, Optional, Any

from varman.models.category import Category
from varman.models.category_set import CategorySet
from varman.models.label import Label


def test_category_init(db_connection):
    """Test initializing a Category instance."""
    # Create a category
    category = Category(
        name="test_category",
        category_set_id=1
    )
    
    # Check attributes
    assert category.name == "test_category"
    assert category.category_set_id == 1
    assert category._labels is None


def test_category_set_property(db_connection):
    """Test the category_set property."""
    # Create a category set
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    
    # Create a category
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Get the category set
    retrieved_set = category.category_set
    
    # Check that the category set is correct
    assert retrieved_set is not None
    assert retrieved_set.id == category_set.id
    assert retrieved_set.name == "test_set"


def test_category_set_property_none(db_connection):
    """Test the category_set property when category_set_id is None."""
    # Create a category without a category set
    category = Category(name="test_category")
    
    # Get the category set
    retrieved_set = category.category_set
    
    # Check that the category set is None
    assert retrieved_set is None


def test_labels_property(db_connection):
    """Test the labels property."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Add some labels
    label1 = Label.create_for_entity(
        entity_type="category",
        entity_id=category.id,
        text="Label 1",
        language_code="en",
        connection=db_connection
    )
    
    label2 = Label.create_for_entity(
        entity_type="category",
        entity_id=category.id,
        text="Label 2",
        language_code="fi",
        connection=db_connection
    )
    
    # Get the labels
    labels = category.labels
    
    # Check that the labels are correct
    assert len(labels) == 2
    label_texts = [label.text for label in labels]
    assert "Label 1" in label_texts
    assert "Label 2" in label_texts


def test_labels_property_no_id(db_connection):
    """Test the labels property when the category has no ID."""
    # Create a category without saving it
    category = Category(name="test_category")
    
    # Get the labels
    labels = category.labels
    
    # Check that the labels list is empty
    assert labels == []


def test_add_label(db_connection):
    """Test adding a label to a category."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Add a label
    label = category.add_label(
        text="Test Label",
        language_code="en",
        purpose="Short",
        connection=db_connection
    )
    
    # Check that the label was created correctly
    assert label.entity_type == "category"
    assert label.entity_id == category.id
    assert label.language_code == "en"
    assert label.text == "Test Label"
    assert label.purpose == "Short"
    
    # Check that the label is in the category's labels
    assert label in category.labels


def test_add_label_no_id(db_connection):
    """Test adding a label to a category without an ID."""
    # Create a category without saving it
    category = Category(name="test_category")
    
    # Try to add a label
    with pytest.raises(ValueError, match="Cannot add a label to a category without an ID"):
        category.add_label(
            text="Test Label",
            language_code="en",
            connection=db_connection
        )


def test_add_label_no_language(db_connection):
    """Test adding a label without specifying a language."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Try to add a label without a language
    with pytest.raises(ValueError, match="Either language_code or language must be provided"):
        category.add_label(
            text="Test Label",
            connection=db_connection
        )


def test_remove_label(db_connection):
    """Test removing a label from a category."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Add a label
    label = category.add_label(
        text="Test Label",
        language_code="en",
        connection=db_connection
    )
    
    # Check that the label is in the category's labels
    assert label in category.labels
    
    # Remove the label
    category.remove_label(label.id, db_connection)
    
    # Check that the label is no longer in the category's labels
    assert label not in category.labels


def test_remove_label_no_id(db_connection):
    """Test removing a label from a category without an ID."""
    # Create a category without saving it
    category = Category(name="test_category")
    
    # Try to remove a label
    with pytest.raises(ValueError, match="Cannot remove a label from a category without an ID"):
        category.remove_label(1, db_connection)


def test_remove_label_not_found(db_connection):
    """Test removing a label that doesn't exist."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Remove a non-existent label (should not raise an error)
    category.remove_label(999, db_connection)


def test_remove_label_wrong_category(db_connection):
    """Test removing a label that belongs to a different category."""
    # Create two categories
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category1 = Category.create({
        "name": "category1",
        "category_set_id": category_set.id
    }, db_connection)
    
    category2 = Category.create({
        "name": "category2",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Add a label to category1
    label = category1.add_label(
        text="Test Label",
        language_code="en",
        connection=db_connection
    )
    
    # Try to remove the label from category2
    with pytest.raises(ValueError, match="Label does not belong to this category"):
        category2.remove_label(label.id, db_connection)


def test_to_dict(db_connection):
    """Test converting a category to a dictionary."""
    # Create a category set and category
    category_set = CategorySet.create({"name": "test_set"}, db_connection)
    category = Category.create({
        "name": "test_category",
        "category_set_id": category_set.id
    }, db_connection)
    
    # Add a label
    label = category.add_label(
        text="Test Label",
        language_code="en",
        connection=db_connection
    )
    
    # Convert to dictionary
    category_dict = category.to_dict()
    
    # Check dictionary
    assert category_dict["name"] == "test_category"
    assert category_dict["category_set_id"] == category_set.id
    assert "labels" in category_dict
    assert len(category_dict["labels"]) == 1
    assert category_dict["labels"][0]["text"] == "Test Label"