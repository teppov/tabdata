"""Base model class for varman."""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from varman.db.connection import get_connection

T = TypeVar('T', bound='BaseModel')


class BaseModel:
    """Base model class for all models in varman."""

    table_name: str = ""
    id_column: str = "id"
    columns: List[str] = []

    def __init__(self, **kwargs):
        """Initialize a model instance.

        Args:
            **kwargs: Model attributes.
        """
        self.id = kwargs.get(self.id_column)
        for column in self.columns:
            setattr(self, column, kwargs.get(column))

    @classmethod
    def create_table(cls, connection: Optional[sqlite3.Connection] = None) -> None:
        """Create the table for this model.

        Args:
            connection: SQLite connection. If None, a new connection is created.
        """
        raise NotImplementedError("Subclasses must implement create_table")

    @classmethod
    def create(cls: Type[T], data: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> T:
        """Create a new record in the database.

        Args:
            data: Data for the new record.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The created model instance.
        """
        if connection is None:
            connection = get_connection()

        columns = [col for col in data.keys() if col in cls.columns]
        values = [data[col] for col in columns]

        placeholders = ", ".join(["?"] * len(columns))
        columns_str = ", ".join(columns)

        cursor = connection.cursor()
        cursor.execute(
            f"INSERT INTO {cls.table_name} ({columns_str}) VALUES ({placeholders})",
            values
        )
        connection.commit()

        # Get the ID of the inserted row
        row_id = cursor.lastrowid

        # Create and return a new instance with the ID
        instance_data = {**data, cls.id_column: row_id}
        return cls(**instance_data)

    @classmethod
    def get(cls: Type[T], id_value: int, connection: Optional[sqlite3.Connection] = None) -> Optional[T]:
        """Get a record by ID.

        Args:
            id_value: The ID of the record to get.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The model instance, or None if not found.
        """
        if connection is None:
            connection = get_connection()

        cursor = connection.cursor()
        cursor.execute(
            f"SELECT * FROM {cls.table_name} WHERE {cls.id_column} = ?",
            (id_value,)
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return cls(**dict(row))

    @classmethod
    def get_by(cls: Type[T], column: str, value: Any, connection: Optional[sqlite3.Connection] = None) -> Optional[T]:
        """Get a record by a column value.

        Args:
            column: The column to filter by.
            value: The value to filter for.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The model instance, or None if not found.
        """
        if connection is None:
            connection = get_connection()

        cursor = connection.cursor()
        cursor.execute(
            f"SELECT * FROM {cls.table_name} WHERE {column} = ?",
            (value,)
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return cls(**dict(row))

    @classmethod
    def get_all(cls: Type[T], connection: Optional[sqlite3.Connection] = None) -> List[T]:
        """Get all records.

        Args:
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A list of model instances.
        """
        if connection is None:
            connection = get_connection()

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {cls.table_name}")

        return [cls(**dict(row)) for row in cursor.fetchall()]

    @classmethod
    def filter(cls: Type[T], conditions: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> List[T]:
        """Filter records by conditions.

        Args:
            conditions: Dictionary of column-value pairs to filter by.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A list of model instances.
        """
        if connection is None:
            connection = get_connection()

        where_clauses = []
        values = []

        for column, value in conditions.items():
            where_clauses.append(f"{column} = ?")
            values.append(value)

        where_clause = " AND ".join(where_clauses)

        cursor = connection.cursor()
        cursor.execute(
            f"SELECT * FROM {cls.table_name} WHERE {where_clause}",
            values
        )

        return [cls(**dict(row)) for row in cursor.fetchall()]
        
    @classmethod
    def get_paginated(cls: Type[T], page: int = 1, page_size: int = 20, 
                     filters: Optional[Dict[str, Any]] = None,
                     sort_by: Optional[str] = None,
                     sort_order: str = "asc",
                     connection: Optional[sqlite3.Connection] = None) -> Tuple[List[T], int]:
        """Get paginated records with optional filtering and sorting.
        
        Args:
            page: Page number (1-based). Must be >= 1.
            page_size: Number of records per page. Must be > 0.
            filters: Dictionary of column-value pairs to filter by.
            sort_by: Column name to sort by. Must be a valid column in the table schema.
            sort_order: Sort order, either "asc" or "desc".
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of model instances for the requested page
                - The total count of records matching the filters
                
        Raises:
            ValueError: If page < 1, page_size <= 0, sort_by is not a valid column,
                       or sort_order is not "asc" or "desc".
        """
        # Validate parameters
        if page < 1:
            raise ValueError("Page number must be >= 1")
        if page_size <= 0:
            raise ValueError("Page size must be > 0")
        if page_size > 1000:
            raise ValueError("Page size must be <= 1000")
        if sort_by is not None and sort_by not in cls.columns and sort_by != cls.id_column:
            raise ValueError(f"Sort column '{sort_by}' is not a valid column")
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
            
        # Get connection
        if connection is None:
            connection = get_connection()
            
        # Build WHERE clause if filters are provided
        where_clause = ""
        values = []
        
        if filters:
            where_clauses = []
            for column, value in filters.items():
                where_clauses.append(f"{column} = ?")
                values.append(value)
            
            if where_clauses:
                where_clause = f"WHERE {' AND '.join(where_clauses)}"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {cls.table_name} {where_clause}"
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
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """
        
        # Execute query with pagination
        values.extend([page_size, offset])
        cursor.execute(query, values)
        
        # Convert rows to model instances
        results = [cls(**dict(row)) for row in cursor.fetchall()]
        
        return results, total_count

    def update(self, data: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> None:
        """Update this record in the database.

        Args:
            data: Data to update.
            connection: SQLite connection. If None, a new connection is created.
        """
        if connection is None:
            connection = get_connection()

        if self.id is None:
            raise ValueError("Cannot update a model without an ID")

        set_clauses = []
        values = []

        for column, value in data.items():
            if column in self.columns:
                set_clauses.append(f"{column} = ?")
                values.append(value)
                setattr(self, column, value)

        if not set_clauses:
            return

        set_clause = ", ".join(set_clauses)
        values.append(self.id)

        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_column} = ?",
            values
        )
        connection.commit()

    def delete(self, connection: Optional[sqlite3.Connection] = None) -> None:
        """Delete this record from the database.

        Args:
            connection: SQLite connection. If None, a new connection is created.
        """
        if connection is None:
            connection = get_connection()

        if self.id is None:
            raise ValueError("Cannot delete a model without an ID")

        cursor = connection.cursor()
        cursor.execute(
            f"DELETE FROM {self.table_name} WHERE {self.id_column} = ?",
            (self.id,)
        )
        connection.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary.

        Returns:
            A dictionary representation of the model.
        """
        result = {self.id_column: self.id}
        for column in self.columns:
            result[column] = getattr(self, column)
        return result

    def __repr__(self) -> str:
        """Get a string representation of the model.

        Returns:
            A string representation.
        """
        attrs = [f"{self.id_column}={self.id}"]
        for column in self.columns:
            value = getattr(self, column)
            if isinstance(value, str):
                attrs.append(f"{column}='{value}'")
            else:
                attrs.append(f"{column}={value}")

        return f"{self.__class__.__name__}({', '.join(attrs)})"

    def __eq__(self, other) -> bool:
        """Check if this model is equal to another.

        Args:
            other: The other model to compare with.

        Returns:
            True if the models are equal, False otherwise.
        """
        if not isinstance(other, self.__class__):
            return False

        if self.id != other.id:
            return False

        for column in self.columns:
            if getattr(self, column) != getattr(other, column):
                return False

        return True

    def __hash__(self) -> int:
        """Get a hash value for this model.

        Returns:
            A hash value.
        """
        values = [self.id]
        for column in self.columns:
            value = getattr(self, column)
            if isinstance(value, (list, dict, set)):
                # Convert unhashable types to strings for hashing
                values.append(str(value))
            else:
                values.append(value)

        return hash((self.__class__, tuple(values)))

    @classmethod
    def bulk_create(cls: Type[T], 
                   items_data: List[Dict[str, Any]], 
                   validate: bool = True,
                   stop_on_error: bool = False,
                   connection: Optional[sqlite3.Connection] = None) -> Tuple[List[T], List[Dict[str, Any]]]:
        """Create multiple items in a single transaction.
        
        Args:
            items_data: List of dictionaries containing item data.
            validate: Whether to validate data before processing (default: True).
            stop_on_error: If True, stop processing and rollback on first error.
                          If False, continue processing remaining items (default: False).
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of created model instances
                - A list of dictionaries containing error details and original data
                
        Example:
            >>> data = [
            ...     {"name": "var1", "data_type": "numeric"},
            ...     {"name": "var2", "data_type": "text"}
            ... ]
            >>> successful, errors = Variable.bulk_create(data)
        """
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            
        successful_items = []
        errors = []
        
        try:
            # Start transaction
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for item_data in items_data:
                try:
                    # Validate data if required
                    if validate and hasattr(cls, 'validate_data'):
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
                    
                    # Create the item
                    item = cls.create(item_data, connection)
                    successful_items.append(item)
                    
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
            try:
                connection.rollback()
            except:
                pass  # Ignore rollback errors
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
        finally:
            if close_connection:
                try:
                    connection.close()
                except:
                    pass  # Ignore close errors
                
        return successful_items, errors
        
    @classmethod  
    def bulk_update(cls: Type[T], 
                   items_data: List[Dict[str, Any]],
                   validate: bool = True,
                   stop_on_error: bool = False, 
                   connection: Optional[sqlite3.Connection] = None) -> Tuple[List[T], List[Dict[str, Any]]]:
        """Update multiple items in a single transaction.
        
        Args:
            items_data: List of dictionaries containing item data with ID.
            validate: Whether to validate data before processing (default: True).
            stop_on_error: If True, stop processing and rollback on first error.
                          If False, continue processing remaining items (default: False).
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of updated model instances
                - A list of dictionaries containing error details and original data
                
        Example:
            >>> data = [
            ...     {"id": 1, "name": "updated_var1"},
            ...     {"id": 2, "description": "Updated description"}
            ... ]
            >>> successful, errors = Variable.bulk_update(data)
        """
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            
        successful_items = []
        errors = []
        
        try:
            # Start transaction
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for item_data in items_data:
                try:
                    # Check if ID is provided
                    if cls.id_column not in item_data or item_data[cls.id_column] is None:
                        error = {
                            "data": item_data,
                            "error": f"{cls.id_column} is required for update operations"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError(f"{cls.id_column} is required for update operations")
                        continue
                    
                    # Get the existing item
                    item = cls.get(item_data[cls.id_column], connection)
                    if item is None:
                        error = {
                            "data": item_data,
                            "error": f"Item with {cls.id_column}={item_data[cls.id_column]} not found"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError(f"Item with {cls.id_column}={item_data[cls.id_column]} not found")
                        continue
                    
                    # Create a copy of the data without the ID for validation
                    update_data = {k: v for k, v in item_data.items() if k != cls.id_column}
                    
                    # Validate data if required
                    if validate and hasattr(cls, 'validate_data'):
                        # Get current data to merge with update data for validation
                        current_data = item.to_dict()
                        # Remove ID from current data
                        if cls.id_column in current_data:
                            del current_data[cls.id_column]
                        
                        # Merge current data with update data for validation
                        validation_data = {**current_data, **update_data}

                        validation_result = cls.validate_data(validation_data)
                        if not validation_result.is_valid:
                            error = {
                                "data": item_data,
                                "errors": validation_result.errors
                            }
                            errors.append(error)
                            if stop_on_error:
                                raise ValueError(f"Validation failed: {validation_result.errors}")
                            continue
                    
                    # Update the item
                    item.update(update_data, connection)
                    successful_items.append(item)
                    
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
            try:
                connection.rollback()
            except:
                pass  # Ignore rollback errors
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
        finally:
            if close_connection:
                try:
                    connection.close()
                except:
                    pass  # Ignore close errors
                
        return successful_items, errors
        
    @classmethod
    def bulk_delete(cls: Type[T],
                   item_ids: List[int],
                   stop_on_error: bool = False,
                   connection: Optional[sqlite3.Connection] = None) -> Tuple[List[int], List[Dict[str, Any]]]:
        """Delete multiple items in a single transaction.
        
        Args:
            item_ids: List of item IDs to delete.
            stop_on_error: If True, stop processing and rollback on first error.
                          If False, continue processing remaining items (default: False).
            connection: SQLite connection. If None, a new connection is created.
            
        Returns:
            A tuple containing:
                - A list of successfully deleted item IDs
                - A list of dictionaries containing error details and original data
                
        Example:
            >>> ids_to_delete = [1, 2, 3]
            >>> deleted_ids, errors = Variable.bulk_delete(ids_to_delete)
        """
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            
        successful_ids = []
        errors = []
        
        try:
            # Start transaction
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for item_id in item_ids:
                try:
                    # Get the item to delete
                    item = cls.get(item_id, connection)
                    if item is None:
                        error = {
                            "data": {"id": item_id},
                            "error": f"Item with {cls.id_column}={item_id} not found"
                        }
                        errors.append(error)
                        if stop_on_error:
                            raise ValueError(f"Item with {cls.id_column}={item_id} not found")
                        continue
                    
                    # Delete the item
                    item.delete(connection)
                    successful_ids.append(item_id)
                    
                except Exception as e:
                    error = {
                        "data": {"id": item_id},
                        "error": str(e)
                    }
                    errors.append(error)
                    if stop_on_error:
                        raise
            
            # Commit transaction if no errors or stop_on_error is False
            connection.commit()
            
        except Exception as e:
            # Rollback transaction on error if stop_on_error is True
            try:
                connection.rollback()
            except:
                pass  # Ignore rollback errors
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
        finally:
            if close_connection:
                try:
                    connection.close()
                except:
                    pass  # Ignore close errors
                
        return successful_ids, errors
