"""Test fixtures for varman tests."""

import os
import pytest
import tempfile
import sqlite3

from varman.db.connection import DatabaseManager, get_db_manager
from varman.db.schema import init_db, reset_db


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def db_manager(temp_db_path):
    """Get a database manager with a temporary database."""
    # Override the global db_manager with our test instance
    manager = DatabaseManager(temp_db_path)
    
    # Store the original manager to restore later
    import varman.db.connection
    original_manager = varman.db.connection._db_manager
    varman.db.connection._db_manager = manager
    
    # Initialize the database
    with manager.connect() as conn:
        init_db(conn)
    
    yield manager
    
    # Restore the original manager
    varman.db.connection._db_manager = original_manager


@pytest.fixture
def db_connection(db_manager):
    """Get a database connection."""
    with db_manager.connect() as conn:
        yield conn


@pytest.fixture
def empty_db(db_connection):
    """Reset the database to an empty state."""
    reset_db(db_connection)
    return db_connection