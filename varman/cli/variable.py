"""Command-line interface for variables."""

import argparse
import json
import sys
import os
from typing import List, Optional

from varman.models.variable import Variable
from varman.models.category_set import CategorySet
from varman.cli.utils import confirm_action
from varman.utils.constraints import (
    Constraint, MinValueConstraint, MaxValueConstraint,
    EmailConstraint, UrlConstraint, RegexConstraint, create_constraint
)


class ArgumentParserError(Exception):
    """Exception raised when there's an error in argument parsing."""
    pass


class ArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that raises an exception instead of exiting."""

    def error(self, message):
        raise ArgumentParserError(message)


def create_variable_command(args):
    """Create a new variable."""
    # Validate name
    if not args.name.isidentifier() or not args.name.islower():
        print(f"Error: Name must be a valid Python identifier and lowercase.")
        return

    # Check if variable already exists
    existing = Variable.get_by("name", args.name)
    if existing:
        print(f"Error: Variable '{args.name}' already exists.")
        return

    # Handle categorical variables
    if args.data_type in Variable.CATEGORICAL_TYPES:
        if args.category_set_name and args.categories:
            print("Error: Cannot specify both category set and categories.")
            return

        if args.category_set_name:
            # Use existing category set
            category_set = CategorySet.get_by("name", args.category_set_name)
            if not category_set:
                print(f"Error: Category set '{args.category_set_name}' does not exist.")
                return

            variable = Variable.create_with_validation(
                name=args.name,
                data_type=args.data_type,
                category_set_id=category_set.id,
                description=args.description,
                reference=args.reference
            )
        elif args.categories:
            # Create new category set
            variable = Variable.create_categorical(
                name=args.name,
                data_type=args.data_type,
                category_names=args.categories,
                description=args.description,
                reference=args.reference
            )
        else:
            print("Error: Must specify either category set or categories for nominal and ordinal types.")
            return
    else:
        # Non-categorical variable
        if args.category_set_name or args.categories:
            print("Error: Cannot specify category set or categories for non-categorical types.")
            return

        variable = Variable.create_with_validation(
            name=args.name,
            data_type=args.data_type,
            description=args.description,
            reference=args.reference
        )

    # Add labels
    if args.label:
        for label_str in args.label:
            parts = label_str.split(":", 2)
            if len(parts) == 2:
                language, text = parts
                purpose = None
            elif len(parts) == 3:
                language, purpose, text = parts
            else:
                print(f"Error: Invalid label format: {label_str}")
                continue

            # Check if language is a language code or name
            if len(language) == 2 and language.isalpha():
                variable.add_label(text=text, language_code=language, purpose=purpose)
            else:
                variable.add_label(text=text, language=language, purpose=purpose)

    # Add constraints
    if args.min_value is not None:
        try:
            min_value = float(args.min_value)
            variable.add_constraint(MinValueConstraint(min_value))
        except ValueError:
            print(f"Error: Invalid minimum value: {args.min_value}")

    if args.max_value is not None:
        try:
            max_value = float(args.max_value)
            variable.add_constraint(MaxValueConstraint(max_value))
        except ValueError:
            print(f"Error: Invalid maximum value: {args.max_value}")

    if args.email:
        variable.add_constraint(EmailConstraint())

    if args.url:
        variable.add_constraint(UrlConstraint())

    if args.regex:
        try:
            variable.add_constraint(RegexConstraint(args.regex))
        except Exception as e:
            print(f"Error: Invalid regex pattern: {str(e)}")

    print(f"Variable '{args.name}' created.")


def list_variables_command(args):
    """List all variables."""
    if args.data_type:
        variables = Variable.filter({"data_type": args.data_type})
    else:
        variables = Variable.get_all()

    if not variables:
        print("No variables found.")
        return

    print("Variables:")
    for variable in variables:
        print(f"  {variable.name} ({variable.data_type})")


def show_variable_command(args):
    """Show details of a variable."""

    variable = Variable.get_by("name", args.name)
    if not variable:
        print(f"Error: Variable '{args.name}' does not exist.")
        return

    if args.json is True:
        print(json.dumps(variable.to_dict(), indent=4))

    else:

        print(f"Name: {variable.name}")
        print(f"Type: {variable.data_type}")

        if variable.description:
            print(f"Description: {variable.description}")

        if variable.reference:
            print(f"Reference: {variable.reference}")

        if variable.category_set_id:
            print("Categories:")
            for category in variable.category_set.categories:
                print(f"  {category.name}")

        if variable.labels:
            print("Labels:")
            for label in variable.labels:
                if label.purpose:
                    print(f"  {label.language_code or label.language} ({label.purpose}): {label.text}")
                else:
                    print(f"  {label.language_code or label.language}: {label.text}")

        if variable.constraints:
            print("Constraints:")
            for constraint in variable.constraints:
                constraint_dict = constraint.to_dict()
                constraint_type = constraint_dict["type"]

                if constraint_type == "min_value":
                    print(f"  Minimum value: {constraint_dict['min_value']}")
                elif constraint_type == "max_value":
                    print(f"  Maximum value: {constraint_dict['max_value']}")
                elif constraint_type == "email":
                    print(f"  Must be a valid email address")
                elif constraint_type == "url":
                    print(f"  Must be a valid URL")
                elif constraint_type == "regex":
                    print(f"  Must match pattern: {constraint_dict['pattern']}")
                else:
                    print(f"  {constraint_type}: {constraint_dict}")


def update_variable_command(args):
    """Update a variable."""
    variable = Variable.get_by("name", args.name)
    if not variable:
        print(f"Error: Variable '{args.name}' does not exist.")
        return

    # Update fields
    update_data = {}
    if args.description is not None:
        update_data["description"] = args.description

    if args.reference is not None:
        update_data["reference"] = args.reference

    if update_data:
        success, errors = variable.update(update_data)
        if not success:
            print(f"Error updating variable: {errors}")
            return

    # Add labels
    if args.add_label:
        for label_str in args.add_label:
            parts = label_str.split(":", 2)
            if len(parts) == 2:
                language, text = parts
                purpose = None
            elif len(parts) == 3:
                language, purpose, text = parts
            else:
                print(f"Error: Invalid label format: {label_str}")
                continue

            # Check if language is a language code or name
            if len(language) == 2 and language.isalpha():
                variable.add_label(text=text, language_code=language, purpose=purpose)
            else:
                variable.add_label(text=text, language=language, purpose=purpose)

    # Remove labels
    if args.remove_label:
        for label_id in args.remove_label:
            try:
                variable.remove_label(label_id)
            except ValueError as e:
                print(f"Warning: {str(e)}")

    # Add constraints
    if args.min_value is not None:
        try:
            min_value = float(args.min_value)
            variable.add_constraint(MinValueConstraint(min_value))
        except ValueError:
            print(f"Error: Invalid minimum value: {args.min_value}")

    if args.max_value is not None:
        try:
            max_value = float(args.max_value)
            variable.add_constraint(MaxValueConstraint(max_value))
        except ValueError:
            print(f"Error: Invalid maximum value: {args.max_value}")

    if args.email:
        variable.add_constraint(EmailConstraint())

    if args.url:
        variable.add_constraint(UrlConstraint())

    if args.regex:
        try:
            variable.add_constraint(RegexConstraint(args.regex))
        except Exception as e:
            print(f"Error: Invalid regex pattern: {str(e)}")

    # Remove constraints
    if args.remove_min_value:
        variable.remove_constraint("min_value")

    if args.remove_max_value:
        variable.remove_constraint("max_value")

    if args.remove_email:
        variable.remove_constraint("email")

    if args.remove_url:
        variable.remove_constraint("url")

    if args.remove_regex:
        variable.remove_constraint("regex")

    print(f"Variable '{args.name}' updated.")


def delete_variable_command(args):
    """Delete a variable."""
    variable = Variable.get_by("name", args.name)
    if not variable:
        print(f"Error: Variable '{args.name}' does not exist.")
        return

    if args.yes or confirm_action("Are you sure you want to delete this variable?"):
        variable.delete()
        print(f"Variable '{args.name}' deleted.")
    else:
        print("Operation cancelled.")


def export_variables_command(args):
    """Export variables to a JSON file."""
    # Get variables to export
    if args.name:
        # Export specific variables
        variables = []
        for name in args.name:
            variable = Variable.get_by("name", name)
            if not variable:
                print(f"Warning: Variable '{name}' does not exist and will be skipped.")
                continue
            variables.append(variable)
    else:
        # Export all variables
        variables = Variable.get_all()

    if not variables:
        print("No variables to export.")
        return

    # Export to file
    try:
        Variable.export_to_json(variables, args.file)
        print(f"Exported {len(variables)} variable(s) to {args.file}")
    except Exception as e:
        print(f"Error exporting variables: {str(e)}")


def import_variables_command(args):
    """Import variables from a JSON file."""
    try:
        # Import from file
        imported_vars, errors, overwritten = Variable.import_from_json(
            args.file, 
            overwrite=args.overwrite
        )

        # Report results
        if imported_vars:
            print(f"Successfully imported {len(imported_vars)} variable(s).")

        if overwritten:
            print(f"Overwritten variables: {', '.join(overwritten)}")

        if errors:
            print("Errors:")
            for error in errors:
                print(f"  {error}")

    except Exception as e:
        print(f"Error importing variables: {str(e)}")


def setup_variable_parser(subparsers):
    """Set up the variable command parser."""

    # Variable command group
    variable_parser = subparsers.add_parser("variable", help="Manage variables")
    variable_subparsers = variable_parser.add_subparsers(dest="subcommand", help="Variable commands")

    # Create command
    create_parser = variable_subparsers.add_parser("create", help="Create a new variable")
    create_parser.add_argument("name", help="Variable name")
    create_parser.add_argument("--type", "-t", dest="data_type", choices=Variable.DATA_TYPES, 
                              required=True, help="Data type of the variable")
    create_parser.add_argument("--category-set", "-c", dest="category_set_name", 
                              help="Name of the category set (for nominal and ordinal types)")
    create_parser.add_argument("--categories", "-C", action="append", 
                              help="Category names (for nominal and ordinal types)")
    create_parser.add_argument("--description", "-d", help="Description of the variable")
    create_parser.add_argument("--reference", "-r", help="Reference for the variable")
    create_parser.add_argument("--label", "-l", action="append", 
                              help="Label for the variable in format 'language:text' or 'language:purpose:text'")

    # Constraint options
    create_parser.add_argument("--min-value", help="Minimum value constraint (for numeric types)")
    create_parser.add_argument("--max-value", help="Maximum value constraint (for numeric types)")
    create_parser.add_argument("--email", action="store_true", help="Email constraint (for text type)")
    create_parser.add_argument("--url", action="store_true", help="URL constraint (for text type)")
    create_parser.add_argument("--regex", help="Regular expression constraint (for text type)")

    create_parser.set_defaults(func=create_variable_command)

    # List command
    list_parser = variable_subparsers.add_parser("list", help="List all variables")
    list_parser.add_argument("--type", "-t", dest="data_type", choices=Variable.DATA_TYPES, 
                            help="Filter by data type")
    list_parser.set_defaults(func=list_variables_command)

    # Show command
    show_parser = variable_subparsers.add_parser("show", help="Show the details of a variable")
    show_parser.add_argument("name", help="Variable name")
    show_parser.add_argument("--json", "-j", help="Show the details in JSON format", action="store_true")
    show_parser.set_defaults(func=show_variable_command)

    # Update command
    update_parser = variable_subparsers.add_parser("update", help="Update a variable")
    update_parser.add_argument("name", help="Variable name")
    update_parser.add_argument("--description", "-d", help="New description of the variable")
    update_parser.add_argument("--reference", "-r", help="New reference for the variable")
    update_parser.add_argument("--add-label", "-l", action="append", 
                              help="Add a label in format 'language:text' or 'language:purpose:text'")
    update_parser.add_argument("--remove-label", "-L", dest="remove_label", action="append", type=int, 
                              help="Remove a label by ID")

    # Constraint options for adding
    update_parser.add_argument("--min-value", help="Add minimum value constraint (for numeric types)")
    update_parser.add_argument("--max-value", help="Add maximum value constraint (for numeric types)")
    update_parser.add_argument("--email", action="store_true", help="Add email constraint (for text type)")
    update_parser.add_argument("--url", action="store_true", help="Add URL constraint (for text type)")
    update_parser.add_argument("--regex", help="Add regular expression constraint (for text type)")

    # Constraint options for removing
    update_parser.add_argument("--remove-min-value", action="store_true", help="Remove minimum value constraint")
    update_parser.add_argument("--remove-max-value", action="store_true", help="Remove maximum value constraint")
    update_parser.add_argument("--remove-email", action="store_true", help="Remove email constraint")
    update_parser.add_argument("--remove-url", action="store_true", help="Remove URL constraint")
    update_parser.add_argument("--remove-regex", action="store_true", help="Remove regex constraint")

    update_parser.set_defaults(func=update_variable_command)

    # Delete command
    delete_parser = variable_subparsers.add_parser("delete", help="Delete a variable")
    delete_parser.add_argument("name", help="Variable name")
    delete_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    delete_parser.set_defaults(func=delete_variable_command)

    # Export command
    export_parser = variable_subparsers.add_parser("export", help="Export variables to a JSON file")
    export_parser.add_argument("file", help="Path to the output JSON file")
    export_parser.add_argument("--name", "-n", action="append", help="Name of variable to export (can be used multiple times, exports all if not specified)")
    export_parser.set_defaults(func=export_variables_command)

    # Import command
    import_parser = variable_subparsers.add_parser("import", help="Import variables from a JSON file")
    import_parser.add_argument("file", help="Path to the input JSON file")
    import_parser.add_argument("--overwrite", "-o", action="store_true", help="Overwrite existing variables")
    import_parser.set_defaults(func=import_variables_command)
