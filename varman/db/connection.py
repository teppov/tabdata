"""Database connection management for varman."""

import os
import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manages the SQLite database connection."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        if db_path is None:
            # Default to a .varman directory in the user's home directory
            home_dir = Path.home()
            data_dir = home_dir / ".varman"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "varman.db")
        else:
            self.db_path = db_path
        
        self.connection = None
    
    def connect(self):
        """Connect to the SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")
        # Return rows as dictionaries
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton instance for global use
_db_manager = None


def get_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """Get the database manager singleton instance.

    Args:
        db_path: Path to the SQLite database file. If None, uses the default path.

    Returns:
        The database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_connection():
    """Get a database connection.

    Returns:
        A SQLite connection object.
    """
    return get_db_manager().connect()