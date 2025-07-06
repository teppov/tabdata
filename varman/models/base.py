"""Base model class for varman."""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

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
