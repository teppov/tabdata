"""Tests for the database connection module."""

import os
import sqlite3
import pytest

from varman.db.connection import DatabaseManager, get_db_manager, get_connection


def test_database_manager_init_default():
    """Test that DatabaseManager initializes with default path."""
    manager = DatabaseManager()
    assert manager.db_path.endswith("varman.db")
    assert manager.connection is None


def test_database_manager_init_custom_path():
    """Test that DatabaseManager initializes with custom path."""
    manager = DatabaseManager("/tmp/test.db")
    assert manager.db_path == "/tmp/test.db"
    assert manager.connection is None


def test_database_manager_connect(temp_db_path):
    """Test that DatabaseManager can connect to a database."""
    manager = DatabaseManager(temp_db_path)
    connection = manager.connect()
    assert isinstance(connection, sqlite3.Connection)
    assert manager.connection is connection
    manager.close()


def test_database_manager_close(temp_db_path):
    """Test that DatabaseManager can close a connection."""
    manager = DatabaseManager(temp_db_path)
    connection = manager.connect()
    manager.close()
    assert manager.connection is None
    # Verify the connection is closed by trying to execute a query
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_database_manager_context_manager(temp_db_path):
    """Test that DatabaseManager works as a context manager."""
    manager = DatabaseManager(temp_db_path)
    with manager as connection:
        assert isinstance(connection, sqlite3.Connection)
        assert manager.connection is connection
    assert manager.connection is None


def test_get_db_manager():
    """Test that get_db_manager returns a singleton instance."""
    manager1 = get_db_manager()
    manager2 = get_db_manager()
    assert manager1 is manager2


def test_get_connection(db_manager):
    """Test that get_connection returns a connection."""
    connection = get_connection()
    assert isinstance(connection, sqlite3.Connection)
    connection.close()