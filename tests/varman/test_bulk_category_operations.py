import os
import sqlite3
import tempfile
import unittest
from typing import List, Dict, Any, Tuple

from varman.models.category import Category
from varman.models.category_set import CategorySet
import varman.db.connection
from varman.db.connection import get_connection
from varman.db.schema import init_db
import varman.api as api


class TestBulkCategoryOperations(unittest.TestCase):
    """Test bulk operations for categories."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Set up the database connection
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        # Create the schema
        init_db(self.connection)
        
        # Store the original connection function
        self.original_get_connection = varman.db.connection.get_connection
        
        # Store the original db_path
        self.original_db_path = varman.db.connection._db_manager.db_path if varman.db.connection._db_manager else None
        
        # Set the db_manager to use our test database
        varman.db.connection._db_manager = None
        varman.db.connection.get_db_manager(self.db_path)
        
        # Mock the get_connection function to return our test database
        def mock_get_connection():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        
        varman.db.connection.get_connection = mock_get_connection
        
        # Create test data
        self.category_set = CategorySet.create({"name": "test_category_set"})
        self.categories = []
        for i in range(5):
            category = Category.create({
                "name": f"category_{i}",
                "category_set_id": self.category_set.id
            })
            self.categories.append(category)

    def tearDown(self):
        """Clean up after tests."""
        # Close the database connection
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            self.connection = None
        
        # Remove the temporary database
        try:
            os.close(self.db_fd)
            os.unlink(self.db_path)
        except OSError:
            pass
        
        # Restore the original get_connection function and db_manager
        varman.db.connection.get_connection = self.original_get_connection
        
        # Restore the original db_path
        if hasattr(self, 'original_db_path'):
            varman.db.connection._db_manager = None
            if self.original_db_path:
                varman.db.connection.get_db_manager(self.original_db_path)

    def test_bulk_update_categories(self):
        """Test bulk updating categories."""
        # Prepare update data
        update_data = [
            {"id": self.categories[0].id, "name": "updated_category_0"},
            {"id": self.categories[1].id, "name": "updated_category_1"}
        ]
        
        # Update categories
        updated, errors = api.bulk_update_categories(update_data)
        
        # Check results
        self.assertEqual(len(updated), 2)
        self.assertEqual(len(errors), 0)
        
        # Verify updates in database
        for i in range(2):
            category = Category.get_by("id", self.categories[i].id)
            self.assertEqual(category.name, f"updated_category_{i}")
        
        # Verify other categories were not updated
        for i in range(2, 5):
            category = Category.get_by("id", self.categories[i].id)
            self.assertEqual(category.name, f"category_{i}")

    def test_bulk_update_categories_with_errors(self):
        """Test bulk updating categories with errors."""
        # Prepare update data with an invalid ID
        update_data = [
            {"id": self.categories[0].id, "name": "updated_category_0"},
            {"id": 9999, "name": "nonexistent_category"}  # This ID doesn't exist
        ]
        
        # Update categories
        updated, errors = api.bulk_update_categories(update_data)
        
        # Check results
        self.assertEqual(len(updated), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["data"]["id"], 9999)
        
        # Verify the first category was updated
        category = Category.get_by("id", self.categories[0].id)
        self.assertEqual(category.name, "updated_category_0")
        
    def test_bulk_delete_categories(self):
        """Test bulk deleting categories."""
        # Get initial count
        initial_count = len(Category.get_all())
        
        # Prepare delete data
        delete_ids = [self.categories[0].id, self.categories[1].id]
        
        # Delete categories
        deleted_ids, errors = api.bulk_delete_categories(delete_ids)
        
        # Check results
        self.assertEqual(len(deleted_ids), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(set(deleted_ids), set(delete_ids))
        
        # Verify deletions in database
        final_count = len(Category.get_all())
        self.assertEqual(final_count, initial_count - 2)
        
        # Verify specific categories were deleted
        for category_id in delete_ids:
            self.assertIsNone(Category.get_by("id", category_id))
        
        # Verify other categories still exist
        for i in range(2, 5):
            category = Category.get_by("id", self.categories[i].id)
            self.assertIsNotNone(category)
            self.assertEqual(category.name, f"category_{i}")
            
    def test_bulk_delete_categories_with_errors(self):
        """Test bulk deleting categories with errors."""
        # Get initial count
        initial_count = len(Category.get_all())
        
        # Prepare delete data with an invalid ID
        delete_ids = [self.categories[0].id, 9999]  # This ID doesn't exist
        
        # Delete categories
        deleted_ids, errors = api.bulk_delete_categories(delete_ids)
        
        # Check results
        self.assertEqual(len(deleted_ids), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(deleted_ids[0], self.categories[0].id)
        self.assertEqual(errors[0]["data"]["id"], 9999)
        
        # Verify the first category was deleted
        self.assertIsNone(Category.get_by("id", self.categories[0].id))
        
        # Verify final count
        final_count = len(Category.get_all())
        self.assertEqual(final_count, initial_count - 1)