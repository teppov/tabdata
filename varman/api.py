"""
varman.api - High-level API for the varman package.
"""

from typing import List, Dict, Any, Optional, Tuple
from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.models.category import Category
from varman.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

def create_variable(name: str, data_type: str, **kwargs) -> Variable:
    """Create a variable with the given name and data type."""
    logger.info(f"Creating variable: name='{name}', data_type='{data_type}', kwargs={kwargs}")
    try:
        variable = Variable.create_with_validation(name=name, data_type=data_type, **kwargs)
        logger.info(f"Created variable: {variable.id} - {variable.name}")
        return variable
    except Exception as e:
        logger.error(f"Error creating variable '{name}': {str(e)}")
        raise

def create_categorical_variable(name: str, data_type: str, categories: List[str], **kwargs) -> Variable:
    """Create a categorical variable with the given name, data type, and categories."""
    logger.info(f"Creating categorical variable: name='{name}', data_type='{data_type}', categories={categories}, kwargs={kwargs}")
    try:
        variable = Variable.create_categorical(name=name, data_type=data_type, category_names=categories, **kwargs)
        logger.info(f"Created categorical variable: {variable.id} - {variable.name} with {len(categories)} categories")
        return variable
    except Exception as e:
        logger.error(f"Error creating categorical variable '{name}': {str(e)}")
        raise

def get_variable(name: str) -> Optional[Variable]:
    """Get a variable by name."""
    logger.debug(f"Getting variable by name: '{name}'")
    try:
        variable = Variable.get_by("name", name)
        if variable:
            logger.debug(f"Found variable: {variable.id} - {variable.name}")
        else:
            logger.debug(f"Variable not found: '{name}'")
        return variable
    except Exception as e:
        logger.error(f"Error getting variable '{name}': {str(e)}")
        raise

def list_variables() -> List[Variable]:
    """List all variables."""
    logger.debug("Listing all variables")
    try:
        variables = Variable.get_all()
        logger.debug(f"Found {len(variables)} variables")
        return variables
    except Exception as e:
        logger.error(f"Error listing variables: {str(e)}")
        raise

def list_variables_paginated(page: int = 1, page_size: int = 20, 
                           filters: Optional[Dict[str, Any]] = None,
                           sort_by: Optional[str] = None,
                           sort_order: str = "asc",
                           search: Optional[str] = None) -> Tuple[List[Variable], int]:
    """List variables with pagination, filtering, sorting, and search.
    
    Args:
        page: Page number (1-based). Must be >= 1.
        page_size: Number of records per page. Must be > 0.
        filters: Dictionary of column-value pairs to filter by.
        sort_by: Column name to sort by. Must be a valid column in the table schema.
        sort_order: Sort order, either "asc" or "desc".
        search: Optional search term to filter by name or description.
        
    Returns:
        A tuple containing:
            - A list of Variable instances for the requested page
            - The total count of records matching the filters and search
            
    Raises:
        ValueError: If page < 1, page_size <= 0, sort_by is not a valid column,
                   or sort_order is not "asc" or "desc".
    """
    logger.debug(f"Listing variables with pagination: page={page}, page_size={page_size}, "
                f"filters={filters}, sort_by={sort_by}, sort_order={sort_order}, search={search}")
    try:
        variables, total = Variable.get_paginated(page, page_size, filters, sort_by, sort_order, search)
        logger.debug(f"Found {len(variables)} variables (page {page} of {(total + page_size - 1) // page_size}), "
                    f"total: {total}")
        return variables, total
    except Exception as e:
        logger.error(f"Error listing variables with pagination: {str(e)}")
        raise

def list_category_sets_paginated(page: int = 1, page_size: int = 20, 
                               filters: Optional[Dict[str, Any]] = None,
                               sort_by: Optional[str] = None,
                               sort_order: str = "asc",
                               search: Optional[str] = None) -> Tuple[List[CategorySet], int]:
    """List category sets with pagination, filtering, sorting, and search.
    
    Args:
        page: Page number (1-based). Must be >= 1.
        page_size: Number of records per page. Must be > 0.
        filters: Dictionary of column-value pairs to filter by.
        sort_by: Column name to sort by. Must be a valid column in the table schema.
        sort_order: Sort order, either "asc" or "desc".
        search: Optional search term to filter by name.
        
    Returns:
        A tuple containing:
            - A list of CategorySet instances for the requested page
            - The total count of records matching the filters and search
            
    Raises:
        ValueError: If page < 1, page_size <= 0, sort_by is not a valid column,
                   or sort_order is not "asc" or "desc".
    """
    logger.debug(f"Listing category sets with pagination: page={page}, page_size={page_size}, "
                f"filters={filters}, sort_by={sort_by}, sort_order={sort_order}, search={search}")
    try:
        category_sets, total = CategorySet.get_paginated(page, page_size, filters, sort_by, sort_order, search)
        logger.debug(f"Found {len(category_sets)} category sets (page {page} of {(total + page_size - 1) // page_size}), "
                    f"total: {total}")
        return category_sets, total
    except Exception as e:
        logger.error(f"Error listing category sets with pagination: {str(e)}")
        raise

def list_categories_paginated(page: int = 1, page_size: int = 20, 
                            filters: Optional[Dict[str, Any]] = None,
                            sort_by: Optional[str] = None,
                            sort_order: str = "asc",
                            search: Optional[str] = None,
                            category_set_id: Optional[int] = None) -> Tuple[List[Category], int]:
    """List categories with pagination, filtering, sorting, and search.
    
    Args:
        page: Page number (1-based). Must be >= 1.
        page_size: Number of records per page. Must be > 0.
        filters: Dictionary of column-value pairs to filter by.
        sort_by: Column name to sort by. Must be a valid column in the table schema.
        sort_order: Sort order, either "asc" or "desc".
        search: Optional search term to filter by name.
        category_set_id: Optional category set ID to filter by.
        
    Returns:
        A tuple containing:
            - A list of Category instances for the requested page
            - The total count of records matching the filters and search
            
    Raises:
        ValueError: If page < 1, page_size <= 0, sort_by is not a valid column,
                   or sort_order is not "asc" or "desc".
    """
    logger.debug(f"Listing categories with pagination: page={page}, page_size={page_size}, "
                f"filters={filters}, sort_by={sort_by}, sort_order={sort_order}, "
                f"search={search}, category_set_id={category_set_id}")
    try:
        categories, total = Category.get_paginated(page, page_size, filters, sort_by, sort_order, search, category_set_id)
        logger.debug(f"Found {len(categories)} categories (page {page} of {(total + page_size - 1) // page_size}), "
                    f"total: {total}")
        return categories, total
    except Exception as e:
        logger.error(f"Error listing categories with pagination: {str(e)}")
        raise

def import_variables(file_path: str, overwrite: bool = False) -> Tuple[List[Variable], List[str], List[str]]:
    """Import variables from a JSON file."""
    logger.info(f"Importing variables from file: {file_path}, overwrite={overwrite}")
    try:
        imported, skipped, errors = Variable.import_from_json(file_path, overwrite)
        logger.info(f"Imported {len(imported)} variables, skipped {len(skipped)}, errors {len(errors)}")
        if errors:
            logger.warning(f"Import errors: {errors}")
        return imported, skipped, errors
    except Exception as e:
        logger.error(f"Error importing variables from {file_path}: {str(e)}")
        raise

def export_variables(file_path: str, variables: Optional[List[Variable]] = None) -> None:
    """Export variables to a JSON file."""
    try:
        if variables is None:
            logger.info(f"Exporting all variables to file: {file_path}")
            variables = Variable.get_all()
        else:
            logger.info(f"Exporting {len(variables)} variables to file: {file_path}")
        
        Variable.export_to_json(variables, file_path)
        logger.info(f"Successfully exported {len(variables)} variables to {file_path}")
    except Exception as e:
        logger.error(f"Error exporting variables to {file_path}: {str(e)}")
        raise

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
    logger.info(f"Bulk creating {len(variables_data)} variables, stop_on_error={stop_on_error}")
    try:
        successful, errors = Variable.bulk_create_with_validation(variables_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk created {len(successful)} variables successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk variable creation: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_create_variables: {str(e)}")
        raise

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
    logger.info(f"Bulk creating {len(variables_data)} categorical variables, stop_on_error={stop_on_error}")
    try:
        successful, errors = Variable.bulk_create_categorical(variables_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk created {len(successful)} categorical variables successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk categorical variable creation: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_create_categorical_variables: {str(e)}")
        raise

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
    logger.info(f"Bulk updating {len(variables_data)} variables, stop_on_error={stop_on_error}")
    try:
        successful, errors = Variable.bulk_update(variables_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk updated {len(successful)} variables successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk variable update: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_update_variables: {str(e)}")
        raise

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
    logger.info(f"Bulk deleting {len(variable_ids)} variables, stop_on_error={stop_on_error}")
    try:
        successful, errors = Variable.bulk_delete(variable_ids, stop_on_error=stop_on_error)
        logger.info(f"Bulk deleted {len(successful)} variables successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk variable deletion: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_delete_variables: {str(e)}")
        raise

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
    logger.info(f"Bulk creating {len(category_sets_data)} category sets, stop_on_error={stop_on_error}")
    try:
        successful, errors = CategorySet.bulk_create_with_categories(category_sets_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk created {len(successful)} category sets successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category set creation: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_create_category_sets: {str(e)}")
        raise

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
    logger.info(f"Bulk updating {len(category_sets_data)} category sets, stop_on_error={stop_on_error}")
    try:
        successful, errors = CategorySet.bulk_update(category_sets_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk updated {len(successful)} category sets successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category set update: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_update_category_sets: {str(e)}")
        raise

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
    logger.info(f"Bulk deleting {len(category_set_ids)} category sets, stop_on_error={stop_on_error}")
    try:
        successful, errors = CategorySet.bulk_delete(category_set_ids, stop_on_error=stop_on_error)
        logger.info(f"Bulk deleted {len(successful)} category sets successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category set deletion: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_delete_category_sets: {str(e)}")
        raise

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
    logger.info(f"Bulk creating {len(categories_data)} categories, stop_on_error={stop_on_error}")
    try:
        successful, errors = Category.bulk_create_with_labels(categories_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk created {len(successful)} categories successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category creation: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_create_categories: {str(e)}")
        raise

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
    logger.info(f"Bulk updating {len(categories_data)} categories, stop_on_error={stop_on_error}")
    try:
        successful, errors = Category.bulk_update(categories_data, stop_on_error=stop_on_error)
        logger.info(f"Bulk updated {len(successful)} categories successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category update: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_update_categories: {str(e)}")
        raise

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
    logger.info(f"Bulk deleting {len(category_ids)} categories, stop_on_error={stop_on_error}")
    try:
        successful, errors = Category.bulk_delete(category_ids, stop_on_error=stop_on_error)
        logger.info(f"Bulk deleted {len(successful)} categories successfully, {len(errors)} errors")
        if errors:
            logger.warning(f"Errors during bulk category deletion: {errors}")
        return successful, errors
    except Exception as e:
        logger.error(f"Error in bulk_delete_categories: {str(e)}")
        raise
