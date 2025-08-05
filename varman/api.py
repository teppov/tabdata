"""
varman.api - High-level API for the varman package.
"""

from typing import List, Dict, Any, Optional, Tuple
from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.models.category import Category

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

# Bulk operations for variables

def bulk_create_variables(variables_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[Variable], List[Dict[str, Any]]]:
    """Create multiple variables in a single transaction.
    
    Args:
        variables_data: List of dictionaries containing variable data.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of created Variable instances
            - A list of dictionaries containing error details and original data
    """
    return Variable.bulk_create_with_validation(variables_data, stop_on_error=stop_on_error)

def bulk_create_categorical_variables(variables_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[Variable], List[Dict[str, Any]]]:
    """Create multiple categorical variables with new category sets in a single transaction.
    
    Args:
        variables_data: List of dictionaries containing variable data with category_names.
                       Each dictionary should contain:
                       - name: The name of the variable
                       - data_type: The data type (must be "nominal" or "ordinal")
                       - category_names: A list of category names
                       - description (optional): A description of the variable
                       - reference (optional): A reference for the variable
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of created Variable instances
            - A list of dictionaries containing error details and original data
    """
    return Variable.bulk_create_categorical(variables_data, stop_on_error=stop_on_error)

def bulk_update_variables(variables_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[Variable], List[Dict[str, Any]]]:
    """Update multiple variables in a single transaction.
    
    Args:
        variables_data: List of dictionaries containing variable data with ID.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of updated Variable instances
            - A list of dictionaries containing error details and original data
    """
    return Variable.bulk_update(variables_data, stop_on_error=stop_on_error)

def bulk_delete_variables(variable_ids: List[int], stop_on_error: bool = False) -> Tuple[List[int], List[Dict[str, Any]]]:
    """Delete multiple variables in a single transaction.
    
    Args:
        variable_ids: List of variable IDs to delete.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of successfully deleted variable IDs
            - A list of dictionaries containing error details and original data
    """
    return Variable.bulk_delete(variable_ids, stop_on_error=stop_on_error)

# Bulk operations for category sets

def bulk_create_category_sets(category_sets_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[CategorySet], List[Dict[str, Any]]]:
    """Create multiple category sets with categories in a single transaction.
    
    Args:
        category_sets_data: List of dictionaries containing category set data.
                           Each dictionary should contain:
                           - name: The name of the category set
                           - category_names: A list of category names
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of created CategorySet instances
            - A list of dictionaries containing error details and original data
    """
    return CategorySet.bulk_create_with_categories(category_sets_data, stop_on_error=stop_on_error)

def bulk_update_category_sets(category_sets_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[CategorySet], List[Dict[str, Any]]]:
    """Update multiple category sets in a single transaction.
    
    Args:
        category_sets_data: List of dictionaries containing category set data with ID.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of updated CategorySet instances
            - A list of dictionaries containing error details and original data
    """
    return CategorySet.bulk_update(category_sets_data, stop_on_error=stop_on_error)

def bulk_delete_category_sets(category_set_ids: List[int], stop_on_error: bool = False) -> Tuple[List[int], List[Dict[str, Any]]]:
    """Delete multiple category sets in a single transaction.
    
    Args:
        category_set_ids: List of category set IDs to delete.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of successfully deleted category set IDs
            - A list of dictionaries containing error details and original data
    """
    return CategorySet.bulk_delete(category_set_ids, stop_on_error=stop_on_error)

# Bulk operations for categories

def bulk_create_categories(categories_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[Category], List[Dict[str, Any]]]:
    """Create multiple categories with labels in a single transaction.
    
    Args:
        categories_data: List of dictionaries containing category data with optional labels.
                       Each dictionary should contain:
                       - name: The name of the category
                       - category_set_id: The ID of the category set
                       - labels (optional): A list of label dictionaries
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of created Category instances
            - A list of dictionaries containing error details and original data
    """
    return Category.bulk_create_with_labels(categories_data, stop_on_error=stop_on_error)

def bulk_update_categories(categories_data: List[Dict[str, Any]], stop_on_error: bool = False) -> Tuple[List[Category], List[Dict[str, Any]]]:
    """Update multiple categories in a single transaction.
    
    Args:
        categories_data: List of dictionaries containing category data with ID.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of updated Category instances
            - A list of dictionaries containing error details and original data
    """
    return Category.bulk_update(categories_data, stop_on_error=stop_on_error)

def bulk_delete_categories(category_ids: List[int], stop_on_error: bool = False) -> Tuple[List[int], List[Dict[str, Any]]]:
    """Delete multiple categories in a single transaction.
    
    Args:
        category_ids: List of category IDs to delete.
        stop_on_error: If True, stop processing and rollback on first error.
                      If False, continue processing remaining items (default: False).
        
    Returns:
        A tuple containing:
            - A list of successfully deleted category IDs
            - A list of dictionaries containing error details and original data
    """
    return Category.bulk_delete(category_ids, stop_on_error=stop_on_error)
