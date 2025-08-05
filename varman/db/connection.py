"""Database connection management for varman."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from varman.config import get_config
from varman.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class DatabaseManager:
    """Manages the SQLite database connection."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses the config settings.
        """
        if db_path is None:
            # Use the database path from configuration
            config = get_config()
            self.db_path = config.get_database_path()
            logger.debug(f"Using database path from config: {self.db_path}")
            
            # Ensure the directory exists
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            logger.debug(f"Ensured database directory exists: {db_dir}")
        else:
            self.db_path = db_path
            logger.debug(f"Using provided database path: {self.db_path}")
        
        self.connection = None
    
    def connect(self):
        """Connect to the SQLite database."""
        logger.debug(f"Connecting to database: {self.db_path}")
        try:
            self.connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return self.connection
        except Exception as e:
            logger.error(f"Error connecting to database {self.db_path}: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.debug(f"Closed database connection: {self.db_path}")
                self.connection = None
            except Exception as e:
                logger.error(f"Error closing database connection {self.db_path}: {str(e)}")
                raise
    
    def __enter__(self):
        """Context manager entry."""
        logger.debug(f"Entering database context manager for {self.db_path}")
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        logger.debug(f"Exiting database context manager for {self.db_path}")
        self.close()
        if exc_type:
            logger.error(f"Exception in database context manager: {exc_type.__name__}: {exc_val}")


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
        logger.debug("Creating new DatabaseManager singleton instance")
        _db_manager = DatabaseManager(db_path)
    else:
        logger.debug("Using existing DatabaseManager singleton instance")
    return _db_manager


def get_connection():
    """Get a database connection.

    Returns:
        A SQLite connection object.
    """
    logger.debug("Getting new database connection")
    connection = get_db_manager().connect()
    return connection