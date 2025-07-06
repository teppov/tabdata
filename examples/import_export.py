"""
Example script demonstrating how to import and export variables using the varman package.
"""

from varman import import_variables, export_variables, list_variables

# Import variables from a JSON file
imported, errors, overwritten = import_variables("examples/example_variables.json")
print(f"Imported {len(imported)} variables")
if errors:
    print(f"Errors: {errors}")

# List all variables
variables = list_variables()
print(f"Total variables: {len(variables)}")

# Export variables to a JSON file
export_variables("examples/exported_variables.json")
print(f"Exported {len(variables)} variables to exported_variables.json")