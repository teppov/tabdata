"""CategorySet model for varman."""

import sqlite3
from typing import Dict, List, Optional, Any, Tuple

from varman.db.connection import get_connection
from varman.models.base import BaseModel
from varman.utils.validation import ValidationResult, validate_name


class CategorySet(BaseModel):
    """Model for category sets."""

    table_name = "category_sets"
    columns = ["name"]

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate category set data.

        Args:
            data: Dictionary containing category set data.

        Returns:
            A ValidationResult object containing any errors or warnings.
        """
        result = ValidationResult()

        # Validate required fields
        if "name" not in data or not data["name"]:
            result.add_error("name", "Name is required")
        elif not validate_name(data["name"]):
            result.add_error("name", "Name must be a valid Python identifier and lowercase")

        # Validate categories if present
        if "categories" in data and data["categories"]:
            if not isinstance(data["categories"], list):
                result.add_error("categories", "Categories must be a list")
            else:
                for i, category in enumerate(data["categories"]):
                    if not isinstance(category, dict):
                        result.add_error(f"categories[{i}]", "Category must be a dictionary")
                        continue

                    if "name" not in category or not category["name"]:
                        result.add_error(f"categories[{i}].name", "Category name is required")
                    elif not validate_name(category["name"]):
                        result.add_error(f"categories[{i}].name", "Category name must be a valid Python identifier and lowercase")

                    # Validate category labels
                    if "labels" in category and category["labels"]:
                        if not isinstance(category["labels"], list):
                            result.add_error(f"categories[{i}].labels", "Labels must be a list")
                        else:
                            for j, label in enumerate(category["labels"]):
                                if not isinstance(label, dict):
                                    result.add_error(f"categories[{i}].labels[{j}]", "Label must be a dictionary")
                                    continue

                                if "text" not in label or not label["text"]:
                                    result.add_error(f"categories[{i}].labels[{j}].text", "Label text is required")

                                if "language_code" not in label and "language" not in label:
                                    result.add_error(f"categories[{i}].labels[{j}].language", "Either language_code or language is required")

        return result

    def __init__(self, **kwargs):
        """Initialize a CategorySet instance.

        Args:
            **kwargs: Model attributes.
        """
        super().__init__(**kwargs)
        self._categories = None

    @property
    def categories(self):
        """Get the categories for this category set.

        Returns:
            A list of Category instances.
        """
        from varman.models.category import Category

        if self._categories is None:
            if self.id is not None:
                self._categories = Category.filter({"category_set_id": self.id})
            else:
                self._categories = []

        return self._categories

    @classmethod
    def create_with_categories(cls, name: str, category_names: List[str], connection: Optional[sqlite3.Connection] = None) -> 'CategorySet':
        """Create a category set with categories.

        Args:
            name: The name of the category set.
            category_names: A list of category names.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The created CategorySet instance.
        """
        if connection is None:
            connection = get_connection()

        # Create the category set
        category_set = cls.create({"name": name}, connection)

        # Create the categories
        from varman.models.category import Category

        for category_name in category_names:
            Category.create({
                "name": category_name,
                "category_set_id": category_set.id
            }, connection)

        return category_set

    def add_category(self, name: str, connection: Optional[sqlite3.Connection] = None) -> 'Category':
        """Add a category to this category set.

        Args:
            name: The name of the category.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The created Category instance.
        """
        from varman.models.category import Category

        if self.id is None:
            raise ValueError("Cannot add a category to a category set without an ID")

        category = Category.create({
            "name": name,
            "category_set_id": self.id
        }, connection)

        if self._categories is not None:
            self._categories.append(category)

        return category

    def remove_category(self, category_id: int, connection: Optional[sqlite3.Connection] = None) -> None:
        """Remove a category from this category set.

        Args:
            category_id: The ID of the category to remove.
            connection: SQLite connection. If None, a new connection is created.
        """
        from varman.models.category import Category

        if self.id is None:
            raise ValueError("Cannot remove a category from a category set without an ID")

        category = Category.get(category_id, connection)
        if category is None:
            return

        if category.category_set_id != self.id:
            raise ValueError("Category does not belong to this category set")

        category.delete(connection)

        if self._categories is not None:
            self._categories = [c for c in self._categories if c.id != category_id]

    def get_category_by_name(self, name: str):
        """Get a category by name.

        Args:
            name: The name of the category.

        Returns:
            The Category instance, or None if not found.
        """
        for category in self.categories:
            if category.name == name:
                return category
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the category set to a dictionary.

        Returns:
            A dictionary representation of the category set.
        """
        result = super().to_dict()
        result["categories"] = [category.to_dict() for category in self.categories]
        return result
        
    @classmethod
    def bulk_create_with_categories(cls, 
                                  items_data: List[Dict[str, Any]],
                                  stop_on_error: bool = False,
                                  connection: Optional[sqlite3.Connection] = None) -> Tuple[List['CategorySet'], List[Dict[str, Any]]]:
        """Create multiple category sets with categories in a single transaction.
        
        Args:
            items_data: List of dictionaries containing category set data.
                       Each dictionary should contain:
                       - name: The name of the category set
                       - category_names: A list of category names
            stop_on_error: If True, stop processing and rollback on first error.
                          If False, continue processing remaining items (default: False).
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of created CategorySet instances
                - A list of dictionaries containing error details and original data
                
        Example:
            >>> data = [
            ...     {
            ...         "name": "gender", 
            ...         "category_names": ["male", "female", "other"]
            ...     },
            ...     {
            ...         "name": "education", 
            ...         "category_names": ["primary", "secondary", "tertiary"]
            ...     }
            ... ]
            >>> successful, errors = CategorySet.bulk_create_with_categories(data)
        """
        
        if connection is None:
            connection = get_connection()
            close_connection = True
        else:
            close_connection = False
            
        successful_items = []
        errors = []
        
        # Start transaction
        connection.execute("BEGIN TRANSACTION")
        
        try:
            for item_data in items_data:
                try:
                    # Check required fields
                    if "name" not in item_data or not item_data["name"]:
                        error = {
                            "data": item_data,
                            "error": "Name is required"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError("Name is required")
                        continue
                        
                    if "category_names" not in item_data or not item_data["category_names"]:
                        error = {
                            "data": item_data,
                            "error": "Category names are required"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError("Category names are required")
                        continue
                    
                    # Validate name
                    if not validate_name(item_data["name"]):
                        error = {
                            "data": item_data,
                            "error": "Name must be a valid Python identifier and lowercase"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError("Name must be a valid Python identifier and lowercase")
                        continue
                    
                    # Create the category set with categories
                    category_set = cls.create_with_categories(
                        name=item_data["name"],
                        category_names=item_data["category_names"],
                        connection=connection
                    )
                    
                    successful_items.append(category_set)
                    
                except Exception as e:
                    error = {
                        "data": item_data,
                        "error": str(e)
                    }
                    errors.append(error)
                    if stop_on_error:
                        raise
            
            # Commit transaction if no errors or stop_on_error is False
            connection.commit()
            
        except Exception as e:
            # Rollback transaction on error if stop_on_error is True
            connection.rollback()
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
        finally:
            if close_connection:
                connection.close()
                
        return successful_items, errors
