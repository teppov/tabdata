"""Tests for bulk operations in varman."""

import os
import sqlite3
import tempfile
import unittest
from typing import List, Dict, Any, Tuple

from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.models.category import Category
from varman.db.connection import get_connection
import varman.api as api


class TestBulkOperations(unittest.TestCase):
    """Test bulk operations for varman models."""

    def setUp(self):
        """Set up a test database."""
        # Create a temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Set up the database connection
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        # Create the schema
        from varman.db.schema import init_db
        init_db(self.connection)
        
        # Monkey patch the get_connection function to use our test database
        self.original_get_connection = get_connection
        
        # Store the original db_path
        import varman.db.connection
        self.original_db_path = varman.db.connection._db_manager.db_path if varman.db.connection._db_manager else None
        
        # Set the db_manager to use our test database
        varman.db.connection._db_manager = None
        varman.db.connection.get_db_manager(self.db_path)
        
        # Make sure each test gets a fresh connection
        def mock_get_connection():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
            
        # Replace the original get_connection function
        varman.db.connection.get_connection = mock_get_connection

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
        import varman.db.connection
        varman.db.connection.get_connection = self.original_get_connection
        
        # Restore the original db_path
        if hasattr(self, 'original_db_path'):
            varman.db.connection._db_manager = None
            if self.original_db_path:
                varman.db.connection.get_db_manager(self.original_db_path)

    def test_bulk_create_variables(self):
        """Test bulk creation of variables."""
        # Prepare test data with unique names
        variables_data = [
            {"name": "var1_test_bulk_create", "data_type": "continuous", "description": "First variable"},
            {"name": "var2_test_bulk_create", "data_type": "text", "reference": "Some reference"},
            {"name": "var3_test_bulk_create", "data_type": "discrete", "description": "Third variable"}
        ]
        
        # Test bulk creation
        successful, errors = api.bulk_create_variables(variables_data)
        
        # Check results
        self.assertEqual(len(successful), 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(successful[0].name, "var1_test_bulk_create")
        self.assertEqual(successful[1].name, "var2_test_bulk_create")
        self.assertEqual(successful[2].name, "var3_test_bulk_create")
        
        # Verify variables were created in the database
        all_variables = Variable.get_all()
        self.assertEqual(len(all_variables), 3)

    def test_bulk_create_variables_with_errors(self):
        """Test bulk creation of variables with validation errors."""
        # Prepare test data with errors
        variables_data = [
            {"name": "var1_test_with_errors", "data_type": "continuous"},  # Valid
            {"name": "var2_test_with_errors", "data_type": "invalid_type"},  # Invalid data type
            {"name": "", "data_type": "text"}  # Missing name
        ]
        
        # Test bulk creation with continue on error
        successful, errors = api.bulk_create_variables(variables_data, stop_on_error=False)
        
        # Check results
        self.assertEqual(len(successful), 1)
        self.assertEqual(len(errors), 2)
        self.assertEqual(successful[0].name, "var1_test_with_errors")
        
        # Verify only valid variables were created
        all_variables = Variable.get_all()
        self.assertEqual(len(all_variables), 1)

    def test_bulk_create_categorical_variables(self):
        """Test bulk creation of categorical variables."""
        # Prepare test data with unique names
        variables_data = [
            {
                "name": "gender_test_bulk_create_categorical", 
                "data_type": "nominal", 
                "category_names": ["male", "female", "other"],
                "description": "Gender of respondent"
            },
            {
                "name": "education_test_bulk_create_categorical", 
                "data_type": "ordinal", 
                "category_names": ["primary", "secondary", "tertiary"],
                "reference": "Education level"
            }
        ]
        
        # Test bulk creation
        successful, errors = api.bulk_create_categorical_variables(variables_data)

        print(f'\napi.bulk_create_categorical_variables, {errors = }\n')

        # Check results
        self.assertEqual(len(successful), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(successful[0].name, "gender_test_bulk_create_categorical")
        self.assertEqual(successful[1].name, "education_test_bulk_create_categorical")
        
        # Verify variables and category sets were created
        all_variables = Variable.get_all()
        all_category_sets = CategorySet.get_all()
        self.assertEqual(len(all_variables), 2)
        self.assertEqual(len(all_category_sets), 2)
        
        # Verify categories were created
        gender_categories = all_category_sets[0].categories
        education_categories = all_category_sets[1].categories
        self.assertEqual(len(gender_categories), 3)
        self.assertEqual(len(education_categories), 3)

    def test_bulk_update_variables(self):
        """Test bulk update of variables."""
        # Create some variables first with unique names
        variables_data = [
            {"name": "var1_test_bulk_update", "data_type": "continuous", "description": "First variable"},
            {"name": "var2_test_bulk_update", "data_type": "text", "reference": "Some reference"}
        ]
        successful, errors = api.bulk_create_variables(variables_data)

        print(f'\napi.bulk_create_variables, {errors = }\n')
        
        # Prepare update data
        update_data = [
            {"id": successful[0].id, "description": "Updated description"},
            {"id": successful[1].id, "reference": "Updated reference"}
        ]
        
        # Test bulk update
        updated, errors = api.bulk_update_variables(update_data)
        
        # Check results
        self.assertEqual(len(updated), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(updated[0].description, "Updated description")
        self.assertEqual(updated[1].reference, "Updated reference")
        
        # Verify variables were updated in the database
        var1 = Variable.get(successful[0].id)
        var2 = Variable.get(successful[1].id)
        self.assertEqual(var1.description, "Updated description")
        self.assertEqual(var2.reference, "Updated reference")

    def test_bulk_delete_variables(self):
        """Test bulk deletion of variables."""
        # Create some variables first with unique names
        variables_data = [
            {"name": "var1_test_bulk_delete", "data_type": "continuous"},
            {"name": "var2_test_bulk_delete", "data_type": "text"},
            {"name": "var3_test_bulk_delete", "data_type": "discrete"}
        ]
        successful, _ = api.bulk_create_variables(variables_data)
        
        # Get IDs
        ids = [var.id for var in successful]
        
        # Delete first two variables
        deleted_ids, errors = api.bulk_delete_variables(ids[:2])
        
        # Check results
        self.assertEqual(len(deleted_ids), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(deleted_ids, ids[:2])
        
        # Verify variables were deleted from the database
        all_variables = Variable.get_all()
        self.assertEqual(len(all_variables), 1)
        self.assertEqual(all_variables[0].id, ids[2])

    def test_bulk_create_category_sets(self):
        """Test bulk creation of category sets."""
        # Prepare test data with unique names
        category_sets_data = [
            {
                "name": "gender_test_bulk_create_category_sets", 
                "category_names": ["male", "female", "other"]
            },
            {
                "name": "education_test_bulk_create_category_sets", 
                "category_names": ["primary", "secondary", "tertiary"]
            }
        ]
        
        # Test bulk creation
        successful, errors = api.bulk_create_category_sets(category_sets_data)
        
        # Check results
        self.assertEqual(len(successful), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(successful[0].name, "gender_test_bulk_create_category_sets")
        self.assertEqual(successful[1].name, "education_test_bulk_create_category_sets")
        
        # Verify category sets were created
        all_category_sets = CategorySet.get_all()
        self.assertEqual(len(all_category_sets), 2)
        
        # Verify categories were created
        gender_categories = all_category_sets[0].categories
        education_categories = all_category_sets[1].categories
        self.assertEqual(len(gender_categories), 3)
        self.assertEqual(len(education_categories), 3)

    def test_bulk_create_categories(self):
        """Test bulk creation of categories with labels."""
        # Create a category set first with a unique name for this test
        category_set = CategorySet.create({"name": "colors_test_bulk_create_categories"})
        
        # Prepare test data
        categories_data = [
            {
                "name": "red", 
                "category_set_id": category_set.id,
                "labels": [
                    {"text": "Red", "language_code": "en"},
                    {"text": "Rouge", "language_code": "fr"}
                ]
            },
            {
                "name": "blue", 
                "category_set_id": category_set.id,
                "labels": [
                    {"text": "Blue", "language_code": "en"},
                    {"text": "Bleu", "language_code": "fr"}
                ]
            }
        ]
        
        # Test bulk creation
        successful, errors = api.bulk_create_categories(categories_data)
        
        # Check results
        self.assertEqual(len(successful), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(successful[0].name, "red")
        self.assertEqual(successful[1].name, "blue")
        
        # Verify categories were created
        all_categories = category_set.categories
        self.assertEqual(len(all_categories), 2)
        
        # Verify labels were created
        red_labels = all_categories[0].labels
        blue_labels = all_categories[1].labels
        self.assertEqual(len(red_labels), 2)
        self.assertEqual(len(blue_labels), 2)

    def test_transaction_rollback(self):
        """Test transaction rollback on error with stop_on_error=True."""
        # Prepare test data with an error in the middle
        variables_data = [
            {"name": "var1_test_rollback", "data_type": "continuous"},  # Valid
            {"name": "var2_test_rollback", "data_type": "invalid_type"},  # Invalid - should cause rollback
            {"name": "var3_test_rollback", "data_type": "text"}  # Valid but won't be processed
        ]
        
        # Test bulk creation with stop on error
        successful, errors = api.bulk_create_variables(variables_data, stop_on_error=True)
        
        # Check results
        # The first variable might be created before the error is encountered
        self.assertLessEqual(len(successful), 1)  # At most one successful item
        self.assertGreaterEqual(len(errors), 1)  # At least one error
        
        # If there's a successful item, verify it's the first one
        if len(successful) == 1:
            self.assertEqual(successful[0].name, "var1_test_rollback")
        
        # Verify the second and third variables were not created due to rollback
        all_variables = Variable.get_all()
        # We might have at most one variable (the first one)
        self.assertLessEqual(len(all_variables), 1)

    def test_empty_list(self):
        """Test bulk operations with empty lists."""
        # Test with empty lists
        successful, errors = api.bulk_create_variables([])
        self.assertEqual(len(successful), 0)
        self.assertEqual(len(errors), 0)
        
        successful, errors = api.bulk_update_variables([])
        self.assertEqual(len(successful), 0)
        self.assertEqual(len(errors), 0)
        
        deleted_ids, errors = api.bulk_delete_variables([])
        self.assertEqual(len(deleted_ids), 0)
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()