"""Category model for varman."""

import sqlite3
from typing import Dict, List, Optional, Any

from varman.db.connection import get_connection
from varman.models.base import BaseModel
from varman.utils.validation import ValidationResult, validate_name


class Category(BaseModel):
    """Model for categories."""

    table_name = "categories"
    columns = ["name", "category_set_id"]

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate category data.

        Args:
            data: Dictionary containing category data.

        Returns:
            A ValidationResult object containing any errors or warnings.
        """
        result = ValidationResult()

        # Validate required fields
        if "name" not in data or not data["name"]:
            result.add_error("name", "Name is required")
        elif not validate_name(data["name"]):
            result.add_error("name", "Name must be a valid Python identifier and lowercase")

        if "category_set_id" not in data or not data["category_set_id"]:
            result.add_error("category_set_id", "Category set ID is required")

        # Validate labels if present
        if "labels" in data and data["labels"]:
            if not isinstance(data["labels"], list):
                result.add_error("labels", "Labels must be a list")
            else:
                for i, label in enumerate(data["labels"]):
                    if not isinstance(label, dict):
                        result.add_error(f"labels[{i}]", "Label must be a dictionary")
                        continue

                    if "text" not in label or not label["text"]:
                        result.add_error(f"labels[{i}].text", "Label text is required")

                    if "language_code" not in label and "language" not in label:
                        result.add_error(f"labels[{i}].language", "Either language_code or language is required")

        return result

    def __init__(self, **kwargs):
        """Initialize a Category instance.

        Args:
            **kwargs: Model attributes.
        """
        super().__init__(**kwargs)
        self._labels = None

    @property
    def category_set(self):
        """Get the category set for this category.

        Returns:
            The CategorySet instance, or None if not found.
        """
        from varman.models.category_set import CategorySet

        if self.category_set_id is None:
            return None

        return CategorySet.get(self.category_set_id)

    @property
    def labels(self):
        """Get the labels for this category.

        Returns:
            A list of Label instances.
        """
        from varman.models.label import Label

        if self._labels is None:
            if self.id is not None:
                self._labels = Label.filter({
                    "entity_type": "category",
                    "entity_id": self.id
                })
            else:
                self._labels = []

        return self._labels

    def add_label(self, text: str, language_code: Optional[str] = None, language: Optional[str] = None,
                 purpose: Optional[str] = None, connection: Optional[sqlite3.Connection] = None) -> 'Label':
        """Add a label to this category.

        Args:
            text: The label text.
            language_code: The language code (ISO 639).
            language: The language name.
            purpose: The purpose of the label (e.g., "short", "long").
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The created Label instance.
        """
        from varman.models.label import Label

        if self.id is None:
            raise ValueError("Cannot add a label to a category without an ID")

        if language_code is None and language is None:
            raise ValueError("Either language_code or language must be provided")

        label = Label.create({
            "entity_type": "category",
            "entity_id": self.id,
            "language_code": language_code,
            "language": language,
            "text": text,
            "purpose": purpose
        }, connection)

        if self._labels is not None:
            self._labels.append(label)

        return label

    def remove_label(self, label_id: int, connection: Optional[sqlite3.Connection] = None) -> None:
        """Remove a label from this category.

        Args:
            label_id: The ID of the label to remove.
            connection: SQLite connection. If None, a new connection is created.
        """
        from varman.models.label import Label

        if self.id is None:
            raise ValueError("Cannot remove a label from a category without an ID")

        label = Label.get(label_id, connection)
        if label is None:
            return

        if label.entity_type != "category" or label.entity_id != self.id:
            raise ValueError("Label does not belong to this category")

        label.delete(connection)

        if self._labels is not None:
            self._labels = [l for l in self._labels if l.id != label_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the category to a dictionary.

        Returns:
            A dictionary representation of the category.
        """
        result = super().to_dict()
        result["labels"] = [label.to_dict() for label in self.labels]
        return result
