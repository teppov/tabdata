"""Base model class for varman."""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from varman.db.connection import get_connection
from varman.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

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
        logger.debug(f"Creating new {cls.__name__} with data: {data}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {cls.__name__}.create")

        columns = [col for col in data.keys() if col in cls.columns]
        values = [data[col] for col in columns]

        placeholders = ", ".join(["?"] * len(columns))
        columns_str = ", ".join(columns)

        cursor = connection.cursor()
        query = f"INSERT INTO {cls.table_name} ({columns_str}) VALUES ({placeholders})"
        logger.debug(f"Executing query: {query} with values: {values}")
        
        try:
            cursor.execute(query, values)
            connection.commit()
            
            # Get the ID of the inserted row
            row_id = cursor.lastrowid
            logger.info(f"Created {cls.__name__} with ID: {row_id}")
            
            # Create and return a new instance with the ID
            instance_data = {**data, cls.id_column: row_id}
            return cls(**instance_data)
        except Exception as e:
            logger.error(f"Error creating {cls.__name__}: {str(e)}")
            raise

    @classmethod
    def get(cls: Type[T], id_value: int, connection: Optional[sqlite3.Connection] = None) -> Optional[T]:
        """Get a record by ID.

        Args:
            id_value: The ID of the record to get.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The model instance, or None if not found.
        """
        logger.debug(f"Getting {cls.__name__} with ID: {id_value}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {cls.__name__}.get")

        cursor = connection.cursor()
        query = f"SELECT * FROM {cls.table_name} WHERE {cls.id_column} = ?"
        logger.debug(f"Executing query: {query} with ID: {id_value}")
        
        try:
            cursor.execute(query, (id_value,))
            row = cursor.fetchone()
            
            if row is None:
                logger.info(f"{cls.__name__} with ID {id_value} not found")
                return None

            logger.debug(f"Found {cls.__name__} with ID: {id_value}")
            return cls(**dict(row))
        except Exception as e:
            logger.error(f"Error getting {cls.__name__} with ID {id_value}: {str(e)}")
            raise

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
        logger.debug(f"Getting {cls.__name__} with {column} = {value}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {cls.__name__}.get_by")

        cursor = connection.cursor()
        query = f"SELECT * FROM {cls.table_name} WHERE {column} = ?"
        logger.debug(f"Executing query: {query} with value: {value}")
        
        try:
            cursor.execute(query, (value,))
            row = cursor.fetchone()
            
            if row is None:
                logger.info(f"{cls.__name__} with {column} = {value} not found")
                return None

            logger.debug(f"Found {cls.__name__} with {column} = {value}")
            return cls(**dict(row))
        except Exception as e:
            logger.error(f"Error getting {cls.__name__} with {column} = {value}: {str(e)}")
            raise

    @classmethod
    def get_all(cls: Type[T], connection: Optional[sqlite3.Connection] = None) -> List[T]:
        """Get all records.

        Args:
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A list of model instances.
        """
        logger.debug(f"Getting all {cls.__name__} records")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {cls.__name__}.get_all")

        cursor = connection.cursor()
        query = f"SELECT * FROM {cls.table_name}"
        logger.debug(f"Executing query: {query}")
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            count = len(rows)
            logger.info(f"Retrieved {count} {cls.__name__} records")
            
            return [cls(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all {cls.__name__} records: {str(e)}")
            raise

    @classmethod
    def filter(cls: Type[T], conditions: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> List[T]:
        """Filter records by conditions.

        Args:
            conditions: Dictionary of column-value pairs to filter by.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A list of model instances.
        """
        logger.debug(f"Filtering {cls.__name__} records with conditions: {conditions}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {cls.__name__}.filter")

        where_clauses = []
        values = []

        for column, value in conditions.items():
            where_clauses.append(f"{column} = ?")
            values.append(value)

        where_clause = " AND ".join(where_clauses)
        
        cursor = connection.cursor()
        query = f"SELECT * FROM {cls.table_name} WHERE {where_clause}"
        logger.debug(f"Executing query: {query} with values: {values}")
        
        try:
            cursor.execute(query, values)
            rows = cursor.fetchall()
            
            count = len(rows)
            logger.info(f"Filtered {count} {cls.__name__} records matching conditions: {conditions}")
            
            return [cls(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error filtering {cls.__name__} records: {str(e)}")
            raise
        
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
        logger.debug(f"Getting paginated {cls.__name__} records: page={page}, page_size={page_size}, "
                    f"filters={filters}, sort_by={sort_by}, sort_order={sort_order}")
        
        try:
            # Validate parameters
            if page < 1:
                msg = "Page number must be >= 1"
                logger.error(f"Pagination error: {msg}")
                raise ValueError(msg)
            if page_size <= 0:
                msg = "Page size must be > 0"
                logger.error(f"Pagination error: {msg}")
                raise ValueError(msg)
            if page_size > 1000:
                msg = "Page size must be <= 1000"
                logger.error(f"Pagination error: {msg}")
                raise ValueError(msg)
            if sort_by is not None and sort_by not in cls.columns and sort_by != cls.id_column:
                msg = f"Sort column '{sort_by}' is not a valid column"
                logger.error(f"Pagination error: {msg}")
                raise ValueError(msg)
            if sort_order.lower() not in ["asc", "desc"]:
                msg = "Sort order must be 'asc' or 'desc'"
                logger.error(f"Pagination error: {msg}")
                raise ValueError(msg)
                
            # Get connection
            if connection is None:
                connection = get_connection()
                logger.debug(f"Created new database connection for {cls.__name__}.get_paginated")
                
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
            logger.debug(f"Executing count query: {count_query} with values: {values}")
            
            cursor = connection.cursor()
            cursor.execute(count_query, values)
            total_count = cursor.fetchone()[0]
            logger.debug(f"Total count: {total_count}")
            
            # If no results, return empty list and total count
            if total_count == 0:
                logger.info(f"No {cls.__name__} records found matching filters: {filters}")
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
            logger.debug(f"Executing pagination query: {query} with values: {values}")
            
            cursor.execute(query, values)
            
            # Convert rows to model instances
            results = [cls(**dict(row)) for row in cursor.fetchall()]
            
            logger.info(f"Retrieved page {page} of {cls.__name__} records: {len(results)} of {total_count} total records")
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error in get_paginated for {cls.__name__}: {str(e)}")
            raise

    def update(self, data: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> None:
        """Update this record in the database.

        Args:
            data: Data to update.
            connection: SQLite connection. If None, a new connection is created.
        """
        logger.debug(f"Updating {self.__class__.__name__} with ID {self.id}, data: {data}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {self.__class__.__name__}.update")

        try:
            if self.id is None:
                msg = "Cannot update a model without an ID"
                logger.error(f"Update error: {msg}")
                raise ValueError(msg)

            set_clauses = []
            values = []

            for column, value in data.items():
                if column in self.columns:
                    set_clauses.append(f"{column} = ?")
                    values.append(value)
                    setattr(self, column, value)

            if not set_clauses:
                logger.info(f"No valid columns to update for {self.__class__.__name__} with ID {self.id}")
                return

            set_clause = ", ".join(set_clauses)
            values.append(self.id)

            cursor = connection.cursor()
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_column} = ?"
            logger.debug(f"Executing query: {query} with values: {values}")
            
            cursor.execute(query, values)
            connection.commit()
            
            rows_affected = cursor.rowcount
            logger.info(f"Updated {self.__class__.__name__} with ID {self.id}: {rows_affected} rows affected")
        except Exception as e:
            logger.error(f"Error updating {self.__class__.__name__} with ID {self.id}: {str(e)}")
            raise

    def delete(self, connection: Optional[sqlite3.Connection] = None) -> None:
        """Delete this record from the database.

        Args:
            connection: SQLite connection. If None, a new connection is created.
        """
        logger.debug(f"Deleting {self.__class__.__name__} with ID {self.id}")
        
        if connection is None:
            connection = get_connection()
            logger.debug(f"Created new database connection for {self.__class__.__name__}.delete")

        try:
            if self.id is None:
                msg = "Cannot delete a model without an ID"
                logger.error(f"Delete error: {msg}")
                raise ValueError(msg)

            cursor = connection.cursor()
            query = f"DELETE FROM {self.table_name} WHERE {self.id_column} = ?"
            logger.debug(f"Executing query: {query} with ID: {self.id}")
            
            cursor.execute(query, (self.id,))
            connection.commit()
            
            rows_affected = cursor.rowcount
            logger.info(f"Deleted {self.__class__.__name__} with ID {self.id}: {rows_affected} rows affected")
        except Exception as e:
            logger.error(f"Error deleting {self.__class__.__name__} with ID {self.id}: {str(e)}")
            raise

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
        logger.debug(f"Bulk creating {len(items_data)} {cls.__name__} items, validate={validate}, stop_on_error={stop_on_error}")
        
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
            logger.debug(f"Created new database connection for {cls.__name__}.bulk_create")
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            logger.debug(f"Created copy of provided connection for {cls.__name__}.bulk_create")
            
        successful_items = []
        errors = []
        
        try:
            # Start transaction
            logger.debug(f"Starting transaction for bulk create of {cls.__name__}")
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for i, item_data in enumerate(items_data):
                try:
                    logger.debug(f"Processing item {i+1}/{len(items_data)} for bulk create: {item_data}")
                    
                    # Validate data if required
                    if validate and hasattr(cls, 'validate_data'):
                        logger.debug(f"Validating item {i+1}: {item_data}")
                        validation_result = cls.validate_data(item_data)
                        if not validation_result.is_valid:
                            error = {
                                "data": item_data,
                                "errors": validation_result.errors
                            }
                            errors.append(error)
                            logger.warning(f"Validation failed for item {i+1}: {validation_result.errors}")
                            if stop_on_error:
                                msg = f"Validation failed: {validation_result.errors}"
                                logger.error(f"Stopping bulk create due to validation error: {msg}")
                                raise ValueError(msg)
                            continue
                    
                    # Create the item
                    item = cls.create(item_data, connection)
                    successful_items.append(item)
                    logger.debug(f"Successfully created item {i+1} with ID: {item.id}")
                    
                except Exception as e:
                    error = {
                        "data": item_data,
                        "error": str(e)
                    }
                    errors.append(error)
                    logger.warning(f"Error creating item {i+1}: {str(e)}")
                    if stop_on_error:
                        logger.error(f"Stopping bulk create due to error: {str(e)}")
                        raise
            
            # Commit transaction if no errors or stop_on_error is False
            logger.debug(f"Committing transaction for bulk create of {cls.__name__}")
            connection.commit()
            logger.info(f"Bulk created {len(successful_items)} {cls.__name__} items successfully, {len(errors)} errors")
            
        except Exception as e:
            # Rollback transaction on error if stop_on_error is True
            try:
                logger.warning(f"Rolling back transaction for bulk create of {cls.__name__}")
                connection.rollback()
            except Exception as rollback_error:
                logger.error(f"Error rolling back transaction: {str(rollback_error)}")
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
                logger.error(f"Bulk create failed with error: {str(e)}")
        finally:
            if close_connection:
                try:
                    logger.debug(f"Closing connection for bulk create of {cls.__name__}")
                    connection.close()
                except Exception as close_error:
                    logger.error(f"Error closing connection: {str(close_error)}")
                
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
        logger.debug(f"Bulk updating {len(items_data)} {cls.__name__} items, validate={validate}, stop_on_error={stop_on_error}")
        
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
            logger.debug(f"Created new database connection for {cls.__name__}.bulk_update")
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            logger.debug(f"Created copy of provided connection for {cls.__name__}.bulk_update")
            
        successful_items = []
        errors = []
        
        try:
            # Start transaction
            logger.debug(f"Starting transaction for bulk update of {cls.__name__}")
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for i, item_data in enumerate(items_data):
                try:
                    logger.debug(f"Processing item {i+1}/{len(items_data)} for bulk update: {item_data}")
                    
                    # Check if ID is provided
                    if cls.id_column not in item_data or item_data[cls.id_column] is None:
                        msg = f"{cls.id_column} is required for update operations"
                        error = {
                            "data": item_data,
                            "error": msg
                        }
                        errors.append(error)
                        logger.warning(f"Missing ID for item {i+1}: {msg}")
                        if stop_on_error:
                            logger.error(f"Stopping bulk update due to missing ID: {msg}")
                            raise ValueError(msg)
                        continue
                    
                    # Get the existing item
                    item_id = item_data[cls.id_column]
                    logger.debug(f"Getting existing item with ID {item_id}")
                    item = cls.get(item_id, connection)
                    if item is None:
                        msg = f"Item with {cls.id_column}={item_id} not found"
                        error = {
                            "data": item_data,
                            "error": msg
                        }
                        errors.append(error)
                        logger.warning(f"Item not found for update: {msg}")
                        if stop_on_error:
                            logger.error(f"Stopping bulk update due to item not found: {msg}")
                            raise ValueError(msg)
                        continue
                    
                    # Create a copy of the data without the ID for validation
                    update_data = {k: v for k, v in item_data.items() if k != cls.id_column}
                    logger.debug(f"Update data for item {i+1}: {update_data}")
                    
                    # Validate data if required
                    if validate and hasattr(cls, 'validate_data'):
                        logger.debug(f"Validating update data for item {i+1}")
                        # Get current data to merge with update data for validation
                        current_data = item.to_dict()
                        # Remove ID from current data
                        if cls.id_column in current_data:
                            del current_data[cls.id_column]
                        
                        # Merge current data with update data for validation
                        validation_data = {**current_data, **update_data}
                        logger.debug(f"Validation data for item {i+1}: {validation_data}")

                        validation_result = cls.validate_data(validation_data)
                        if not validation_result.is_valid:
                            error = {
                                "data": item_data,
                                "errors": validation_result.errors
                            }
                            errors.append(error)
                            logger.warning(f"Validation failed for item {i+1}: {validation_result.errors}")
                            if stop_on_error:
                                msg = f"Validation failed: {validation_result.errors}"
                                logger.error(f"Stopping bulk update due to validation error: {msg}")
                                raise ValueError(msg)
                            continue
                    
                    # Update the item
                    logger.debug(f"Updating item {i+1} with ID {item_id}")
                    item.update(update_data, connection)
                    successful_items.append(item)
                    logger.debug(f"Successfully updated item {i+1} with ID {item_id}")
                    
                except Exception as e:
                    error = {
                        "data": item_data,
                        "error": str(e)
                    }
                    errors.append(error)
                    logger.warning(f"Error updating item {i+1}: {str(e)}")
                    if stop_on_error:
                        logger.error(f"Stopping bulk update due to error: {str(e)}")
                        raise
            
            # Commit transaction if no errors or stop_on_error is False
            logger.debug(f"Committing transaction for bulk update of {cls.__name__}")
            connection.commit()
            logger.info(f"Bulk updated {len(successful_items)} {cls.__name__} items successfully, {len(errors)} errors")
            
        except Exception as e:
            # Rollback transaction on error if stop_on_error is True
            try:
                logger.warning(f"Rolling back transaction for bulk update of {cls.__name__}")
                connection.rollback()
            except Exception as rollback_error:
                logger.error(f"Error rolling back transaction: {str(rollback_error)}")
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
                logger.error(f"Bulk update failed with error: {str(e)}")
        finally:
            if close_connection:
                try:
                    logger.debug(f"Closing connection for bulk update of {cls.__name__}")
                    connection.close()
                except Exception as close_error:
                    logger.error(f"Error closing connection: {str(close_error)}")
                
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
        logger.debug(f"Bulk deleting {len(item_ids)} {cls.__name__} items, stop_on_error={stop_on_error}")
        
        # Always create a new connection for bulk operations to avoid locking issues
        if connection is None:
            connection = get_connection()
            close_connection = True
            logger.debug(f"Created new database connection for {cls.__name__}.bulk_delete")
        else:
            # Make a copy of the connection to avoid sharing
            new_connection = get_connection()
            # Copy the state of the provided connection
            for pragma in ["foreign_keys"]:
                value = connection.execute(f"PRAGMA {pragma}").fetchone()[0]
                new_connection.execute(f"PRAGMA {pragma}={value}")
            connection = new_connection
            close_connection = True
            logger.debug(f"Created copy of provided connection for {cls.__name__}.bulk_delete")
            
        successful_ids = []
        errors = []
        
        try:
            # Start transaction
            logger.debug(f"Starting transaction for bulk delete of {cls.__name__}")
            connection.execute("BEGIN IMMEDIATE TRANSACTION")
            
            for i, item_id in enumerate(item_ids):
                try:
                    logger.debug(f"Processing item {i+1}/{len(item_ids)} for bulk delete: ID={item_id}")
                    
                    # Get the item to delete
                    item = cls.get(item_id, connection)
                    if item is None:
                        msg = f"Item with {cls.id_column}={item_id} not found"
                        error = {
                            "data": {"id": item_id},
                            "error": msg
                        }
                        errors.append(error)
                        logger.warning(f"Item not found for delete: {msg}")
                        if stop_on_error:
                            logger.error(f"Stopping bulk delete due to item not found: {msg}")
                            raise ValueError(msg)
                        continue
                    
                    # Delete the item
                    logger.debug(f"Deleting item {i+1} with ID {item_id}")
                    item.delete(connection)
                    successful_ids.append(item_id)
                    logger.debug(f"Successfully deleted item {i+1} with ID {item_id}")
                    
                except Exception as e:
                    error = {
                        "data": {"id": item_id},
                        "error": str(e)
                    }
                    errors.append(error)
                    logger.warning(f"Error deleting item {i+1} with ID {item_id}: {str(e)}")
                    if stop_on_error:
                        logger.error(f"Stopping bulk delete due to error: {str(e)}")
                        raise
            
            # Commit transaction if no errors or stop_on_error is False
            logger.debug(f"Committing transaction for bulk delete of {cls.__name__}")
            connection.commit()
            logger.info(f"Bulk deleted {len(successful_ids)} {cls.__name__} items successfully, {len(errors)} errors")
            
        except Exception as e:
            # Rollback transaction on error if stop_on_error is True
            try:
                logger.warning(f"Rolling back transaction for bulk delete of {cls.__name__}")
                connection.rollback()
            except Exception as rollback_error:
                logger.error(f"Error rolling back transaction: {str(rollback_error)}")
                
            if not errors:  # Add the error if it's not already in the errors list
                errors.append({
                    "data": None,
                    "error": str(e)
                })
                logger.error(f"Bulk delete failed with error: {str(e)}")
        finally:
            if close_connection:
                try:
                    logger.debug(f"Closing connection for bulk delete of {cls.__name__}")
                    connection.close()
                except Exception as close_error:
                    logger.error(f"Error closing connection: {str(close_error)}")
                
        return successful_ids, errors
