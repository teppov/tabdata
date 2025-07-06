"""Database schema for varman."""

import json
import sqlite3
from typing import Optional

from varman.db.connection import get_connection


def init_db(connection: Optional[sqlite3.Connection] = None):
    """Initialize the database schema.

    Args:
        connection: SQLite connection. If None, a new connection is created.
    """
    if connection is None:
        connection = get_connection()

    cursor = connection.cursor()

    # Create tables

    # Category sets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_set_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_set_id) REFERENCES category_sets (id) ON DELETE CASCADE,
        UNIQUE (name, category_set_id)
    )
    """)

    # Variables table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        data_type TEXT NOT NULL,
        category_set_id INTEGER,
        description TEXT,
        reference TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_set_id) REFERENCES category_sets (id) ON DELETE SET NULL,
        CHECK (
            (data_type IN ('nominal', 'ordinal') AND category_set_id IS NOT NULL) OR
            (data_type IN ('discrete', 'continuous', 'text') AND category_set_id IS NULL)
        )
    )
    """)

    # Labels table (for both variables and categories)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        language_code TEXT,
        language TEXT,
        text TEXT NOT NULL,
        purpose TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CHECK (language_code IS NOT NULL OR language IS NOT NULL),
        UNIQUE (entity_type, entity_id, language_code, language, purpose)
    )
    """)

    # Constraints table for variables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variable_constraints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        variable_id INTEGER NOT NULL,
        constraint_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (variable_id) REFERENCES variables (id) ON DELETE CASCADE
    )
    """)

    # Create triggers for updated_at
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_category_sets_updated_at
    AFTER UPDATE ON category_sets
    FOR EACH ROW
    BEGIN
        UPDATE category_sets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_categories_updated_at
    AFTER UPDATE ON categories
    FOR EACH ROW
    BEGIN
        UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_variables_updated_at
    AFTER UPDATE ON variables
    FOR EACH ROW
    BEGIN
        UPDATE variables SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_labels_updated_at
    AFTER UPDATE ON labels
    FOR EACH ROW
    BEGIN
        UPDATE labels SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_variable_constraints_updated_at
    AFTER UPDATE ON variable_constraints
    FOR EACH ROW
    BEGIN
        UPDATE variable_constraints SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    connection.commit()


def reset_db(connection: Optional[sqlite3.Connection] = None):
    """Reset the database by dropping all tables and recreating them.

    Args:
        connection: SQLite connection. If None, a new connection is created.
    """
    if connection is None:
        connection = get_connection()

    cursor = connection.cursor()

    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS labels")
    cursor.execute("DROP TABLE IF EXISTS variable_constraints")
    cursor.execute("DROP TABLE IF EXISTS variables")
    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute("DROP TABLE IF EXISTS category_sets")

    connection.commit()

    # Recreate tables
    init_db(connection)
