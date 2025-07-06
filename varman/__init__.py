"""
varman - A package for managing variables for tabular datasets.
"""

# Import main models for easy access
from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.models.category import Category
from varman.models.label import Label
from varman.utils.constraints import (
    Constraint, MinValueConstraint, MaxValueConstraint, 
    EmailConstraint, UrlConstraint, RegexConstraint
)

# Import API functions
from varman.api import (
    create_variable, create_categorical_variable, 
    get_variable, list_variables,
    import_variables, export_variables
)

# Initialize database on import
from varman.db.schema import init_db
init_db()

# Version information
__version__ = "0.1.0"
