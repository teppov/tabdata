"""Tests for the database schema module."""

import sqlite3
import pytest

from varman.db.schema import init_db, reset_db


def test_init_db(db_connection):
    """Test that init_db creates the expected tables."""
    # Get the list of tables
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Check that all expected tables exist
    assert "category_sets" in tables
    assert "categories" in tables
    assert "variables" in tables
    assert "labels" in tables


def test_init_db_idempotent(db_connection):
    """Test that init_db is idempotent (can be called multiple times)."""
    # Call init_db again
    init_db(db_connection)
    
    # Get the list of tables
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Check that all expected tables exist
    assert "category_sets" in tables
    assert "categories" in tables
    assert "variables" in tables
    assert "labels" in tables


def test_reset_db(db_connection):
    """Test that reset_db drops and recreates all tables."""
    # Insert some data
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
    db_connection.commit()
    
    # Get the category set ID
    cursor.execute("SELECT id FROM category_sets WHERE name = 'test_set'")
    category_set_id = cursor.fetchone()[0]
    
    # Insert a category
    cursor.execute(
        "INSERT INTO categories (name, category_set_id) VALUES (?, ?)",
        ("test_category", category_set_id)
    )
    db_connection.commit()
    
    # Reset the database
    reset_db(db_connection)
    
    # Check that the tables exist but are empty
    cursor.execute("SELECT COUNT(*) FROM category_sets")
    assert cursor.fetchone()[0] == 0
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    assert cursor.fetchone()[0] == 0


def test_table_constraints(db_connection):
    """Test that table constraints are enforced."""
    cursor = db_connection.cursor()
    
    # Test unique constraint on category_sets.name
    cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
    db_connection.commit()
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO category_sets (name) VALUES ('test_set')")
        db_connection.commit()
    
    # Test foreign key constraint on categories.category_set_id
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO categories (name, category_set_id) VALUES (?, ?)",
            ("test_category", 999)  # Non-existent category_set_id
        )
        db_connection.commit()
    
    # Test check constraint on variables.data_type
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO variables (name, data_type) VALUES (?, ?)",
            ("test_variable", "invalid_type")  # Invalid data_type
        )
        db_connection.commit()
    
    # Test check constraint on variables (categorical variables must have category_set_id)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO variables (name, data_type, category_set_id) VALUES (?, ?, ?)",
            ("test_variable", "nominal", None)  # Nominal without category_set_id
        )
        db_connection.commit()