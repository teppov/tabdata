"""
varman.api - High-level API for the varman package.
"""

from typing import List, Dict, Any, Optional, Tuple
from varman.models.variable import Variable
from varman.models.category_set import CategorySet

def create_variable(name: str, data_type: str, **kwargs) -> Variable:
    """Create a variable with the given name and data type."""
    return Variable.create_with_validation(name=name, data_type=data_type, **kwargs)

def create_categorical_variable(name: str, data_type: str, categories: List[str], **kwargs) -> Variable:
    """Create a categorical variable with the given name, data type, and categories."""
    return Variable.create_categorical(name=name, data_type=data_type, category_names=categories, **kwargs)

def get_variable(name: str) -> Optional[Variable]:
    """Get a variable by name."""
    return Variable.get_by("name", name)

def list_variables() -> List[Variable]:
    """List all variables."""
    return Variable.get_all()

def import_variables(file_path: str, overwrite: bool = False) -> Tuple[List[Variable], List[str], List[str]]:
    """Import variables from a JSON file."""
    return Variable.import_from_json(file_path, overwrite)

def export_variables(file_path: str, variables: Optional[List[Variable]] = None) -> None:
    """Export variables to a JSON file."""
    if variables is None:
        variables = Variable.get_all()
    Variable.export_to_json(variables, file_path)
