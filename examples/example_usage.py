#!/usr/bin/env python3
"""Example usage of the varman package."""

import os
import sys
import tempfile

# Add the parent directory to the path so we can import varman
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from varman.db.connection import get_db_manager
from varman.db.schema import init_db
from varman.models.variable import Variable
from varman.models.category_set import CategorySet


def main():
    """Run the example."""
    # Use a temporary database for this example
    with tempfile.NamedTemporaryFile() as temp_file:
        # Initialize the database manager with the temporary file
        db_manager = get_db_manager(temp_file.name)
        
        # Initialize the database schema
        with db_manager.connect() as connection:
            init_db(connection)
        
        # Create a category set
        print("Creating a category set...")
        category_set = CategorySet.create_with_categories(
            name="gender",
            category_names=["male", "female", "other", "unknown"]
        )
        print(f"Created category set: {category_set}")
        
        # Add a label to a category
        print("\nAdding a label to a category...")
        category = category_set.categories[0]  # male
        label = category.add_label(
            text="Male",
            language_code="en",
            purpose="display"
        )
        print(f"Added label: {label}")
        
        # Create a categorical variable
        print("\nCreating a categorical variable...")
        variable = Variable.create_with_validation(
            name="gender_var",
            data_type="nominal",
            category_set_id=category_set.id,
            description="Gender of the participant",
            reference="ISO 5218"
        )
        print(f"Created variable: {variable}")
        
        # Add a label to the variable
        print("\nAdding a label to the variable...")
        label = variable.add_label(
            text="Gender",
            language_code="en",
            purpose="display"
        )
        print(f"Added label: {label}")
        
        # Create a non-categorical variable
        print("\nCreating a non-categorical variable...")
        variable = Variable.create_with_validation(
            name="age",
            data_type="discrete",
            description="Age of the participant in years"
        )
        print(f"Created variable: {variable}")
        
        # List all variables
        print("\nListing all variables...")
        variables = Variable.get_all()
        for variable in variables:
            print(f"- {variable.name} ({variable.data_type})")
        
        # Show details of a variable
        print("\nShowing details of a variable...")
        variable = Variable.get_by("name", "gender_var")
        print(f"Name: {variable.name}")
        print(f"Type: {variable.data_type}")
        print(f"Description: {variable.description}")
        print(f"Reference: {variable.reference}")
        print("Categories:")
        for category in variable.category_set.categories:
            print(f"- {category.name}")
            for label in category.labels:
                print(f"  - {label.language_code or label.language} ({label.purpose}): {label.text}")
        print("Labels:")
        for label in variable.labels:
            print(f"- {label.language_code or label.language} ({label.purpose}): {label.text}")
        
        # Update a variable
        print("\nUpdating a variable...")
        variable.update({
            "description": "Updated description"
        })
        print(f"Updated variable: {variable}")
        
        # Delete a variable
        print("\nDeleting a variable...")
        variable.delete()
        print(f"Deleted variable: {variable.name}")
        
        # List all variables again
        print("\nListing all variables after deletion...")
        variables = Variable.get_all()
        for variable in variables:
            print(f"- {variable.name} ({variable.data_type})")


if __name__ == "__main__":
    main()