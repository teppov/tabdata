"""Category model for varman."""

import sqlite3
from typing import Dict, List, Optional, Any, Tuple

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
        
    @classmethod
    def get_paginated(cls, page: int = 1, page_size: int = 20, 
                     filters: Optional[Dict[str, Any]] = None,
                     sort_by: Optional[str] = None,
                     sort_order: str = "asc",
                     search: Optional[str] = None,
                     category_set_id: Optional[int] = None,
                     connection: Optional[sqlite3.Connection] = None) -> Tuple[List['Category'], int]:
        """Get paginated categories with optional filtering, sorting, and text search.
        
        Extends the BaseModel.get_paginated method with additional functionality:
        - Text search in name field
        - Filtering by category_set_id
        
        Args:
            page: Page number (1-based). Must be >= 1.
            page_size: Number of records per page. Must be > 0.
            filters: Dictionary of column-value pairs to filter by.
            sort_by: Column name to sort by. Must be a valid column in the table schema.
            sort_order: Sort order, either "asc" or "desc".
            search: Optional search term to filter by name.
            category_set_id: Optional category set ID to filter by.
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of Category instances for the requested page
                - The total count of records matching the filters and search
                
        Raises:
            ValueError: If page < 1, page_size <= 0, sort_by is not a valid column,
                       or sort_order is not "asc" or "desc".
        """
        if connection is None:
            connection = get_connection()
            
        # Add category_set_id to filters if provided
        if category_set_id is not None:
            if filters is None:
                filters = {}
            filters["category_set_id"] = category_set_id
            
        # Handle text search in name
        if search:
            # Build a custom SQL query with text search
            where_clauses = []
            values = []
            
            # Add search condition for name
            where_clauses.append("name LIKE ?")
            search_term = f"%{search}%"
            values.append(search_term)
            
            # Add filters if provided
            if filters:
                for column, value in filters.items():
                    where_clauses.append(f"{column} = ?")
                    values.append(value)
                    
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM {cls.table_name} WHERE {where_clause}"
            cursor = connection.cursor()
            cursor.execute(count_query, values)
            total_count = cursor.fetchone()[0]
            
            # If no results, return empty list and total count
            if total_count == 0:
                return [], 0
                
            # Build ORDER BY clause if sort_by is provided
            order_clause = ""
            if sort_by:
                order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
                
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build final query with pagination
            query = f"""
                SELECT * FROM {cls.table_name}
                WHERE {where_clause}
                {order_clause}
                LIMIT ? OFFSET ?
            """
            
            # Execute query with pagination
            values.extend([page_size, offset])
            cursor.execute(query, values)
            
            # Convert rows to model instances
            results = [cls(**dict(row)) for row in cursor.fetchall()]
            
            return results, total_count
        else:
            # Use the base implementation for simple filtering
            return super().get_paginated(page, page_size, filters, sort_by, sort_order, connection)
        
    @classmethod
    def bulk_create_with_labels(cls, 
                              items_data: List[Dict[str, Any]],
                              validate: bool = True,
                              stop_on_error: bool = False,
                              connection: Optional[sqlite3.Connection] = None) -> Tuple[List['Category'], List[Dict[str, Any]]]:
        """Create multiple categories with labels in a single transaction.
        
        Args:
            items_data: List of dictionaries containing category data with optional labels.
                       Each dictionary should contain:
                       - name: The name of the category
                       - category_set_id: The ID of the category set
                       - labels (optional): A list of label dictionaries
            validate: Whether to validate data before processing (default: True).
            stop_on_error: If True, stop processing and rollback on first error.
                          If False, continue processing remaining items (default: False).
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of created Category instances
                - A list of dictionaries containing error details and original data
                
        Example:
            >>> data = [
            ...     {
            ...         "name": "male", 
            ...         "category_set_id": 1,
            ...         "labels": [
            ...             {"text": "Male", "language_code": "en"},
            ...             {"text": "Homme", "language_code": "fr"}
            ...         ]
            ...     },
            ...     {
            ...         "name": "female", 
            ...         "category_set_id": 1,
            ...         "labels": [
            ...             {"text": "Female", "language_code": "en"},
            ...             {"text": "Femme", "language_code": "fr"}
            ...         ]
            ...     }
            ... ]
            >>> successful, errors = Category.bulk_create_with_labels(data)
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
                    # Validate data if required
                    if validate:
                        validation_result = cls.validate_data(item_data)
                        if not validation_result.is_valid:
                            error = {
                                "data": item_data,
                                "errors": validation_result.errors
                            }
                            errors.append(error)
                            if stop_on_error:
                                raise ValueError(f"Validation failed: {validation_result.errors}")
                            continue
                    
                    # Extract labels if present
                    labels_data = item_data.pop("labels", []) if "labels" in item_data else []
                    
                    # Create the category
                    category = cls.create(item_data, connection)
                    
                    # Add labels if present
                    for label_data in labels_data:
                        category.add_label(
                            text=label_data["text"],
                            language_code=label_data.get("language_code"),
                            language=label_data.get("language"),
                            purpose=label_data.get("purpose"),
                            connection=connection
                        )
                    
                    successful_items.append(category)
                    
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
