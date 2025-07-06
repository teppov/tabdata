"""Variable model for varman."""

import json
import os
import sqlite3
from typing import Dict, List, Optional, Any, Union, Tuple

from varman.db.connection import get_connection
from varman.models.base import BaseModel
from varman.utils.constraints import Constraint, constraint_from_dict
from varman.utils.validation import ValidationResult, validate_name, validate_data_type


class Variable(BaseModel):
    """Model for variables."""

    table_name = "variables"
    columns = ["name", "data_type", "category_set_id", "description", "reference"]

    # Valid data types
    DATA_TYPES = ["discrete", "continuous", "nominal", "ordinal", "text"]

    # Data types that require a category set
    CATEGORICAL_TYPES = ["nominal", "ordinal"]

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate variable data.

        Args:
            data: Dictionary containing variable data.

        Returns:
            A ValidationResult object containing any errors or warnings.
        """
        result = ValidationResult()

        # Validate required fields
        if "name" not in data or not data["name"]:
            result.add_error("name", "Name is required")
        elif not validate_name(data["name"]):
            result.add_error("name", "Name must be a valid Python identifier and lowercase")

        if "data_type" not in data or not data["data_type"]:
            result.add_error("data_type", "Data type is required")
        elif not validate_data_type(data["data_type"], cls.DATA_TYPES):
            result.add_error("data_type", f"Data type must be one of {cls.DATA_TYPES}")

        # Validate category set requirements
        if "data_type" in data and data["data_type"]:
            data_type = data["data_type"]
            category_set_id = data.get("category_set_id")
            category_set = data.get("category_set")

            if data_type in cls.CATEGORICAL_TYPES and not category_set_id and not category_set:
                result.add_error("category_set", f"Category set is required for {data_type} variables")
            elif data_type not in cls.CATEGORICAL_TYPES and (category_set_id or category_set):
                result.add_warning("category_set", f"Category set is not needed for {data_type} variables")

        # Validate category set if present
        if "category_set" in data and data["category_set"]:
            category_set = data["category_set"]

            if not isinstance(category_set, dict):
                result.add_error("category_set", "Category set must be a dictionary")
            else:
                # Validate category set name
                if "name" not in category_set or not category_set["name"]:
                    result.add_error("category_set.name", "Category set name is required")
                elif not validate_name(category_set["name"]):
                    result.add_error("category_set.name", "Category set name must be a valid Python identifier and lowercase")

                # Validate categories
                if "categories" not in category_set or not category_set["categories"]:
                    result.add_error("category_set.categories", "Categories are required for a category set")
                elif not isinstance(category_set["categories"], list):
                    result.add_error("category_set.categories", "Categories must be a list")
                else:
                    for i, category in enumerate(category_set["categories"]):
                        if not isinstance(category, dict):
                            result.add_error(f"category_set.categories[{i}]", "Category must be a dictionary")
                            continue

                        if "name" not in category or not category["name"]:
                            result.add_error(f"category_set.categories[{i}].name", "Category name is required")
                        elif not validate_name(category["name"]):
                            result.add_error(f"category_set.categories[{i}].name", "Category name must be a valid Python identifier and lowercase")

                        # Validate category labels
                        if "labels" in category and category["labels"]:
                            if not isinstance(category["labels"], list):
                                result.add_error(f"category_set.categories[{i}].labels", "Labels must be a list")
                            else:
                                for j, label in enumerate(category["labels"]):
                                    if not isinstance(label, dict):
                                        result.add_error(f"category_set.categories[{i}].labels[{j}]", "Label must be a dictionary")
                                        continue

                                    if "text" not in label or not label["text"]:
                                        result.add_error(f"category_set.categories[{i}].labels[{j}].text", "Label text is required")

                                    if "language_code" not in label and "language" not in label:
                                        result.add_error(f"category_set.categories[{i}].labels[{j}].language", "Either language_code or language is required")

        # Validate labels
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

        # Validate constraints
        if "constraints" in data and data["constraints"]:
            if not isinstance(data["constraints"], list):
                result.add_error("constraints", "Constraints must be a list")
            else:
                for i, constraint in enumerate(data["constraints"]):
                    if not isinstance(constraint, dict):
                        result.add_error(f"constraints[{i}]", "Constraint must be a dictionary")
                        continue

                    if "type" not in constraint or not constraint["type"]:
                        result.add_error(f"constraints[{i}].type", "Constraint type is required")

                    # Validate constraint parameters based on type
                    constraint_type = constraint.get("type")
                    if constraint_type == "range":
                        if "min" not in constraint and "max" not in constraint:
                            result.add_error(f"constraints[{i}]", "Range constraint must have at least one of 'min' or 'max'")
                    elif constraint_type == "regex":
                        if "pattern" not in constraint or not constraint["pattern"]:
                            result.add_error(f"constraints[{i}].pattern", "Regex constraint must have a pattern")
                    elif constraint_type == "enum":
                        if "values" not in constraint or not constraint["values"]:
                            result.add_error(f"constraints[{i}].values", "Enum constraint must have values")
                        elif not isinstance(constraint["values"], list):
                            result.add_error(f"constraints[{i}].values", "Enum constraint values must be a list")
                    elif constraint_type:
                        result.add_warning(f"constraints[{i}].type", f"Unknown constraint type: {constraint_type}")

        return result

    def __init__(self, **kwargs):
        """Initialize a Variable instance.

        Args:
            **kwargs: Model attributes.
        """
        super().__init__(**kwargs)
        self._labels = None
        self._constraints = None

    @property
    def category_set(self):
        """Get the category set for this variable.

        Returns:
            The CategorySet instance, or None if not found.
        """
        from varman.models.category_set import CategorySet

        if self.category_set_id is None:
            return None

        return CategorySet.get(self.category_set_id)

    @property
    def labels(self):
        """Get the labels for this variable.

        Returns:
            A list of Label instances.
        """
        from varman.models.label import Label

        if self._labels is None:
            if self.id is not None:
                self._labels = Label.filter({
                    "entity_type": "variable",
                    "entity_id": self.id
                })
            else:
                self._labels = []

        return self._labels

    @property
    def constraints(self):
        """Get the constraints for this variable.

        Returns:
            A list of Constraint instances.
        """
        if self._constraints is None:
            if self.id is not None:
                self._constraints = self._load_constraints()
            else:
                self._constraints = []

        return self._constraints

    def _load_constraints(self, connection: Optional[sqlite3.Connection] = None):
        """Load constraints from the database.

        Args:
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A list of Constraint instances.
        """
        if connection is None:
            connection = get_connection()

        cursor = connection.cursor()
        cursor.execute(
            "SELECT constraint_data FROM variable_constraints WHERE variable_id = ?",
            (self.id,)
        )

        constraints = []
        for row in cursor.fetchall():
            constraint_data = json.loads(row["constraint_data"])
            constraints.append(constraint_from_dict(constraint_data))

        return constraints

    @classmethod
    def create_with_validation(cls, name: str, data_type: str, category_set_id: Optional[int] = None,
                              description: Optional[str] = None, reference: Optional[str] = None,
                              connection: Optional[sqlite3.Connection] = None) -> Union[Tuple['Variable', List], Tuple[None, List]]:
        """Create a variable with validation.

        Args:
            name: The name of the variable.
            data_type: The data type of the variable.
            category_set_id: The ID of the category set (required for nominal and ordinal data types).
            description: A description of the variable.
            reference: A reference for the variable.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A tuple containing:
                - The created Variable instance, or None if validation failed
                - A list of validation errors

        Raises:
            ValueError: If the data type is invalid or if a category set is required but not provided.
                        This is for backward compatibility.
        """
        # Create data dictionary for validation
        data = {
            "name": name,
            "data_type": data_type,
            "category_set_id": category_set_id,
            "description": description,
            "reference": reference
        }

        # Validate data
        validation_result = cls.validate_data(data)

        # For backward compatibility, raise ValueError for critical errors
        if not validation_result.is_valid:
            for error in validation_result.errors:
                if error["field"] == "data_type":
                    raise ValueError(error["message"])
                elif error["field"] == "category_set" and "required" in error["message"]:
                    raise ValueError(error["message"])

        # Return errors if validation failed
        if not validation_result.is_valid:
            return None, validation_result.errors

        # Create variable if validation passed
        variable = cls.create(data, connection)

        return variable, []

    @classmethod
    def create_categorical(cls, name: str, data_type: str, category_names: List[str],
                          description: Optional[str] = None, reference: Optional[str] = None,
                          connection: Optional[sqlite3.Connection] = None) -> Union[Tuple['Variable', List], Tuple[None, List]]:
        """Create a categorical variable with a new category set.

        Args:
            name: The name of the variable.
            data_type: The data type of the variable (must be "nominal" or "ordinal").
            category_names: A list of category names.
            description: A description of the variable.
            reference: A reference for the variable.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A tuple containing:
                - The created Variable instance, or None if validation failed
                - A list of validation errors

        Raises:
            ValueError: If the data type is not "nominal" or "ordinal".
        """
        if data_type not in cls.CATEGORICAL_TYPES:
            raise ValueError(f"Data type must be one of {cls.CATEGORICAL_TYPES}, got {data_type}")

        if connection is None:
            connection = get_connection()

        # Create a category set with the same name as the variable
        from varman.models.category_set import CategorySet

        category_set = CategorySet.create_with_categories(name, category_names, connection)

        # Create the variable
        variable, errors = cls.create_with_validation(
            name=name,
            data_type=data_type,
            category_set_id=category_set.id,
            description=description,
            reference=reference,
            connection=connection
        )

        return variable, errors

    def add_label(self, text: str, language_code: Optional[str] = None, language: Optional[str] = None,
                 purpose: Optional[str] = None, connection: Optional[sqlite3.Connection] = None) -> 'Label':
        """Add a label to this variable.

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
            raise ValueError("Cannot add a label to a variable without an ID")

        if language_code is None and language is None:
            raise ValueError("Either language_code or language must be provided")

        label = Label.create({
            "entity_type": "variable",
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
        """Remove a label from this variable.

        Args:
            label_id: The ID of the label to remove.
            connection: SQLite connection. If None, a new connection is created.
        """
        from varman.models.label import Label

        if self.id is None:
            raise ValueError("Cannot remove a label from a variable without an ID")

        label = Label.get(label_id, connection)
        if label is None:
            return

        if label.entity_type != "variable" or label.entity_id != self.id:
            raise ValueError("Label does not belong to this variable")

        label.delete(connection)

        if self._labels is not None:
            self._labels = [l for l in self._labels if l.id != label_id]

    def add_constraint(self, constraint: Constraint, connection: Optional[sqlite3.Connection] = None) -> None:
        """Add a constraint to this variable.

        Args:
            constraint: The constraint to add.
            connection: SQLite connection. If None, a new connection is created.

        Raises:
            ValueError: If the variable has no ID.
        """
        if self.id is None:
            raise ValueError("Cannot add a constraint to a variable without an ID")

        if connection is None:
            connection = get_connection()

        # Convert constraint to JSON
        constraint_data = json.dumps(constraint.to_dict())

        # Insert into database
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO variable_constraints (variable_id, constraint_data) VALUES (?, ?)",
            (self.id, constraint_data)
        )
        connection.commit()

        # Update cache
        if self._constraints is not None:
            self._constraints.append(constraint)

    def remove_constraint(self, constraint_type: str, connection: Optional[sqlite3.Connection] = None) -> None:
        """Remove constraints of a specific type from this variable.

        Args:
            constraint_type: The type of constraint to remove.
            connection: SQLite connection. If None, a new connection is created.

        Raises:
            ValueError: If the variable has no ID.
        """
        if self.id is None:
            raise ValueError("Cannot remove constraints from a variable without an ID")

        if connection is None:
            connection = get_connection()

        # Find constraints of the specified type
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, constraint_data FROM variable_constraints WHERE variable_id = ?",
            (self.id,)
        )

        # Collect IDs of constraints to remove
        constraint_ids = []
        for row in cursor.fetchall():
            constraint_data = json.loads(row["constraint_data"])
            if constraint_data.get("type") == constraint_type:
                constraint_ids.append(row["id"])

        # Remove from database
        if constraint_ids:
            placeholders = ", ".join("?" for _ in constraint_ids)
            cursor.execute(
                f"DELETE FROM variable_constraints WHERE id IN ({placeholders})",
                constraint_ids
            )
            connection.commit()

        # Update cache
        if self._constraints is not None:
            self._constraints = [c for c in self._constraints if c.to_dict().get("type") != constraint_type]

    def update(self, data: Dict[str, Any], connection: Optional[sqlite3.Connection] = None) -> Union[Tuple[bool, List], Tuple[bool, None]]:
        """Update this variable with validation.

        Args:
            data: Data to update.
            connection: SQLite connection. If None, a new connection is created.

        Returns:
            A tuple containing:
                - True if the update was successful, False otherwise
                - A list of validation errors, or None if validation passed
        """
        # For partial updates, we don't need to validate required fields that aren't being updated
        # We'll only validate the fields that are being updated
        validation_errors = []

        # Validate name if it's being updated
        if "name" in data:
            if not data["name"]:
                validation_errors.append({"field": "name", "message": "Name is required"})
            elif not validate_name(data["name"]):
                validation_errors.append({"field": "name", "message": "Name must be a valid Python identifier and lowercase"})

        # Validate data_type if it's being updated
        if "data_type" in data:
            if not data["data_type"]:
                validation_errors.append({"field": "data_type", "message": "Data type is required"})
            elif not validate_data_type(data["data_type"], self.__class__.DATA_TYPES):
                validation_errors.append({"field": "data_type", "message": f"Data type must be one of {self.__class__.DATA_TYPES}"})

        # Return errors if validation failed
        if validation_errors:
            return False, validation_errors

        # Update if validation passed
        super().update(data, connection)

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the variable to a dictionary.

        Returns:
            A dictionary representation of the variable.
        """
        result = super().to_dict()
        result["labels"] = [label.to_dict() for label in self.labels]
        result["constraints"] = [constraint.to_dict() for constraint in self.constraints]

        if self.category_set_id is not None:
            result["category_set"] = self.category_set.to_dict()

        return result

    @classmethod
    def export_to_json(cls, variables: List['Variable'], file_path: str) -> None:
        """Export variables to a JSON file.

        Args:
            variables: List of Variable instances to export.
            file_path: Path to the output JSON file.

        Raises:
            ValueError: If the file path is invalid.
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        # Convert variables to a dictionary with variable names as keys
        variables_data = {}
        for var in variables:
            variables_data[var.name] = var.to_dict()

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Write to file
        with open(file_path, 'w') as f:
            json.dump(variables_data, f, indent=2)

    @classmethod
    def import_from_json(cls, file_path: str, overwrite: bool = False) -> Tuple[List['Variable'], List[Dict[str, Any]], List[str]]:
        """Import variables from a JSON file.

        Args:
            file_path: Path to the input JSON file.
            overwrite: Whether to overwrite existing variables with the same name.

        Returns:
            A tuple containing:
                - List of imported Variable instances
                - List of validation errors for variables that couldn't be imported
                - List of names of variables that were overwritten (if overwrite=True)

        Raises:
            ValueError: If the file path is invalid or the file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Read from file
        with open(file_path, 'r') as f:
            variables_data = json.load(f)

        imported_variables = []
        all_errors = []
        overwritten_variables = []

        # Handle both dictionary and list formats for backward compatibility
        if isinstance(variables_data, dict):
            # Dictionary format with variable names as keys
            for var_name, var_data in variables_data.items():
                # Ensure the name in the data matches the key
                if "name" not in var_data:
                    var_data["name"] = var_name
                elif var_data["name"] != var_name:
                    var_data["name"] = var_name

                # Check if variable already exists
                existing_var = cls.get_by("name", var_name)

                if existing_var and not overwrite:
                    all_errors.append({
                        "variable": var_name,
                        "errors": [{"field": "name", "message": f"Variable '{var_name}' already exists. Use overwrite option to replace it."}]
                    })
                    continue

                if existing_var and overwrite:
                    # Delete existing variable
                    existing_var.delete()
                    overwritten_variables.append(var_name)

                # Validate variable data
                validation_result = cls.validate_data(var_data)

                if not validation_result.is_valid:
                    all_errors.append({
                        "variable": var_name,
                        "errors": validation_result.errors
                    })
                    continue

                try:
                    # Create new variable
                    variable = cls._import_variable_from_dict(var_data)
                    imported_variables.append(variable)
                except Exception as e:
                    all_errors.append({
                        "variable": var_name,
                        "errors": [{"field": "general", "message": str(e)}]
                    })
        else:
            # Legacy list format
            for var_data in variables_data:
                var_name = var_data.get("name")
                if not var_name:
                    all_errors.append({
                        "variable": "unknown",
                        "errors": [{"field": "name", "message": "Variable name is required"}]
                    })
                    continue

                # Check if variable already exists
                existing_var = cls.get_by("name", var_name)

                if existing_var and not overwrite:
                    all_errors.append({
                        "variable": var_name,
                        "errors": [{"field": "name", "message": f"Variable '{var_name}' already exists. Use overwrite option to replace it."}]
                    })
                    continue

                if existing_var and overwrite:
                    # Delete existing variable
                    existing_var.delete()
                    overwritten_variables.append(var_name)

                # Validate variable data
                validation_result = cls.validate_data(var_data)

                if not validation_result.is_valid:
                    all_errors.append({
                        "variable": var_name,
                        "errors": validation_result.errors
                    })
                    continue

                try:
                    # Create new variable
                    variable = cls._import_variable_from_dict(var_data)
                    imported_variables.append(variable)
                except Exception as e:
                    all_errors.append({
                        "variable": var_name,
                        "errors": [{"field": "general", "message": str(e)}]
                    })

        return imported_variables, all_errors, overwritten_variables

    @classmethod
    def _import_variable_from_dict(cls, var_data: Dict[str, Any]) -> 'Variable':
        """Import a single variable from a dictionary.

        Args:
            var_data: Dictionary containing variable data.

        Returns:
            The imported Variable instance.

        Raises:
            ValueError: If the variable data is invalid.
        """
        from varman.models.category_set import CategorySet

        # Extract basic variable data
        name = var_data.get("name")
        data_type = var_data.get("data_type")
        description = var_data.get("description")
        reference = var_data.get("reference")

        if not name or not data_type:
            raise ValueError("Variable must have a name and data type")

        # Handle category set
        category_set_id = None
        if "category_set" in var_data and var_data["category_set"]:
            category_set_data = var_data["category_set"]
            category_set_name = category_set_data.get("name")

            # Check if category set already exists
            category_set = CategorySet.get_by("name", category_set_name)

            if not category_set:
                # Create new category set
                category_names = [cat.get("name") for cat in category_set_data.get("categories", [])]
                category_set = CategorySet.create_with_categories(category_set_name, category_names)

                # Add labels to categories if present
                for cat_data in category_set_data.get("categories", []):
                    category = category_set.get_category_by_name(cat_data.get("name"))
                    if category and "labels" in cat_data:
                        for label_data in cat_data.get("labels", []):
                            category.add_label(
                                text=label_data.get("text"),
                                language_code=label_data.get("language_code"),
                                language=label_data.get("language"),
                                purpose=label_data.get("purpose")
                            )

            category_set_id = category_set.id

        # Create variable
        if data_type in cls.CATEGORICAL_TYPES and category_set_id is None:
            raise ValueError(f"Category set is required for {data_type} variables")

        variable, errors = cls.create_with_validation(
            name=name,
            data_type=data_type,
            category_set_id=category_set_id,
            description=description,
            reference=reference
        )

        if not variable:
            error_messages = "; ".join([f"{e['field']}: {e['message']}" for e in errors])
            raise ValueError(f"Failed to create variable: {error_messages}")

        # Add labels
        for label_data in var_data.get("labels", []):
            variable.add_label(
                text=label_data.get("text"),
                language_code=label_data.get("language_code"),
                language=label_data.get("language"),
                purpose=label_data.get("purpose")
            )

        # Add constraints
        for constraint_data in var_data.get("constraints", []):
            constraint = constraint_from_dict(constraint_data)
            variable.add_constraint(constraint)

        return variable
