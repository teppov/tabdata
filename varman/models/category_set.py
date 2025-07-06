"""CategorySet model for varman."""

import sqlite3
from typing import Dict, List, Optional, Any

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
