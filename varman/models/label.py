"""Label model for varman."""

import sqlite3
from typing import Dict, Optional, Any

from varman.db.connection import get_connection
from varman.models.base import BaseModel


class Label(BaseModel):
    """Model for labels."""

    table_name = "labels"
    columns = ["entity_type", "entity_id", "language_code", "language", "text", "purpose"]

    def __init__(self, **kwargs):
        """Initialize a Label instance.

        Args:
            **kwargs: Model attributes.
        """
        super().__init__(**kwargs)
    
    @property
    def entity(self):
        """Get the entity (variable or category) for this label.

        Returns:
            The entity instance, or None if not found.
        """
        if self.entity_type == "variable":
            from varman.models.variable import Variable
            return Variable.get(self.entity_id)
        elif self.entity_type == "category":
            from varman.models.category import Category
            return Category.get(self.entity_id)
        else:
            return None
    
    @classmethod
    def create_for_entity(cls, entity_type: str, entity_id: int, text: str,
                         language_code: Optional[str] = None, language: Optional[str] = None,
                         purpose: Optional[str] = None, connection: Optional[sqlite3.Connection] = None) -> 'Label':
        """Create a label for an entity.

        Args:
            entity_type: The type of entity ("variable" or "category").
            entity_id: The ID of the entity.
            text: The label text.
            language_code: The language code (ISO 639).
            language: The language name.
            purpose: The purpose of the label (e.g., "short", "long").
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            The created Label instance.
        """
        if language_code is None and language is None:
            raise ValueError("Either language_code or language must be provided")
        
        return cls.create({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "language_code": language_code,
            "language": language,
            "text": text,
            "purpose": purpose
        }, connection)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the label to a dictionary.

        Returns:
            A dictionary representation of the label.
        """
        return super().to_dict()