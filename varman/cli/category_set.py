"""Command-line interface for category sets."""

import argparse
import sys
from typing import List, Optional

from varman.models.category_set import CategorySet
from varman.models.category import Category
from varman.cli.utils import confirm_action


def create_category_set_command(args):
    """Create a new category set."""
    # Validate name
    if not args.name.isidentifier() or not args.name.islower():
        print(f"Error: Name must be a valid Python identifier and lowercase.")
        return

    # Check if category set already exists
    existing = CategorySet.get_by("name", args.name)
    if existing:
        print(f"Error: Category set '{args.name}' already exists.")
        return

    # Create category set with categories
    category_set = CategorySet.create_with_categories(args.name, args.categories)

    print(f"Category set '{args.name}' created with {len(args.categories)} categories.")


def list_category_sets_command(args):
    """List all category sets."""
    category_sets = CategorySet.get_all()

    if not category_sets:
        print("No category sets found.")
        return

    print("Category sets:")
    for category_set in category_sets:
        print(f"  {category_set.name} ({len(category_set.categories)} categories)")


def show_category_set_command(args):
    """Show details of a category set."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    print(f"Name: {category_set.name}")
    print("Categories:")

    for category in category_set.categories:
        print(f"  {category.name}")

        if category.labels:
            for label in category.labels:
                if label.purpose:
                    print(f"    {label.language_code or label.language} ({label.purpose}): {label.text}")
                else:
                    print(f"    {label.language_code or label.language}: {label.text}")


def add_category_command(args):
    """Add a category to a category set."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    # Check if category already exists
    for category in category_set.categories:
        if category.name == args.category_name:
            print(f"Error: Category '{args.category_name}' already exists in this category set.")
            return

    # Add category
    category_set.add_category(args.category_name)

    print(f"Category '{args.category_name}' added to category set '{args.name}'.")


def remove_category_command(args):
    """Remove a category from a category set."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    # Find category
    category = None
    for c in category_set.categories:
        if c.name == args.category_name:
            category = c
            break

    if not category:
        print(f"Error: Category '{args.category_name}' does not exist in this category set.")
        return

    # Confirm and remove category
    if args.yes or confirm_action("Are you sure you want to remove this category?"):
        category_set.remove_category(category.id)
        print(f"Category '{args.category_name}' removed from category set '{args.name}'.")
    else:
        print("Operation cancelled.")


def add_label_command(args):
    """Add a label to a category."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    # Find category
    category = None
    for c in category_set.categories:
        if c.name == args.category_name:
            category = c
            break

    if not category:
        print(f"Error: Category '{args.category_name}' does not exist in this category set.")
        return

    # Parse label
    parts = args.label_str.split(":", 2)
    if len(parts) == 2:
        language, text = parts
        purpose = None
    elif len(parts) == 3:
        language, purpose, text = parts
    else:
        print(f"Error: Invalid label format: {args.label_str}")
        return

    # Add label
    if len(language) == 2 and language.isalpha():
        category.add_label(text=text, language_code=language, purpose=purpose)
    else:
        category.add_label(text=text, language=language, purpose=purpose)

    print(f"Label added to category '{args.category_name}' in category set '{args.name}'.")


def remove_label_command(args):
    """Remove a label from a category."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    # Find category
    category = None
    for c in category_set.categories:
        if c.name == args.category_name:
            category = c
            break

    if not category:
        print(f"Error: Category '{args.category_name}' does not exist in this category set.")
        return

    # Confirm and remove label
    if args.yes or confirm_action("Are you sure you want to remove this label?"):
        try:
            category.remove_label(args.label_id)
            print(f"Label removed from category '{args.category_name}' in category set '{args.name}'.")
        except ValueError as e:
            print(f"Error: {str(e)}")
    else:
        print("Operation cancelled.")


def delete_category_set_command(args):
    """Delete a category set."""
    category_set = CategorySet.get_by("name", args.name)
    if not category_set:
        print(f"Error: Category set '{args.name}' does not exist.")
        return

    # Confirm and delete
    if args.yes or confirm_action("Are you sure you want to delete this category set?"):
        category_set.delete()
        print(f"Category set '{args.name}' deleted.")
    else:
        print("Operation cancelled.")


def setup_category_set_parser(subparsers):
    """Set up the category set command parser."""
    # Category set command group
    category_set_parser = subparsers.add_parser("category-set", help="Manage category sets")
    category_set_subparsers = category_set_parser.add_subparsers(dest="subcommand", help="Category set commands")

    # Create command
    create_parser = category_set_subparsers.add_parser("create", help="Create a new category set")
    create_parser.add_argument("name", help="Category set name")
    create_parser.add_argument("--category", "-c", dest="categories", action="append", required=True, 
                              help="Category name")
    create_parser.set_defaults(func=create_category_set_command)

    # List command
    list_parser = category_set_subparsers.add_parser("list", help="List all category sets")
    list_parser.set_defaults(func=list_category_sets_command)

    # Show command
    show_parser = category_set_subparsers.add_parser("show", help="Show details of a category set")
    show_parser.add_argument("name", help="Category set name")
    show_parser.set_defaults(func=show_category_set_command)

    # Add category command
    add_category_parser = category_set_subparsers.add_parser("add-category", help="Add a category to a category set")
    add_category_parser.add_argument("name", help="Category set name")
    add_category_parser.add_argument("--category", "-c", dest="category_name", required=True, 
                                    help="Category name")
    add_category_parser.set_defaults(func=add_category_command)

    # Remove category command
    remove_category_parser = category_set_subparsers.add_parser("remove-category", 
                                                              help="Remove a category from a category set")
    remove_category_parser.add_argument("name", help="Category set name")
    remove_category_parser.add_argument("--category", "-c", dest="category_name", required=True, 
                                       help="Category name")
    remove_category_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    remove_category_parser.set_defaults(func=remove_category_command)

    # Add label command
    add_label_parser = category_set_subparsers.add_parser("add-label", help="Add a label to a category")
    add_label_parser.add_argument("name", help="Category set name")
    add_label_parser.add_argument("--category", "-c", dest="category_name", required=True, 
                                 help="Category name")
    add_label_parser.add_argument("--label", "-l", dest="label_str", required=True, 
                                 help="Label in format 'language:text' or 'language:purpose:text'")
    add_label_parser.set_defaults(func=add_label_command)

    # Remove label command
    remove_label_parser = category_set_subparsers.add_parser("remove-label", help="Remove a label from a category")
    remove_label_parser.add_argument("name", help="Category set name")
    remove_label_parser.add_argument("--category", "-c", dest="category_name", required=True, 
                                    help="Category name")
    remove_label_parser.add_argument("--label-id", "-l", dest="label_id", required=True, type=int, 
                                    help="Label ID")
    remove_label_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    remove_label_parser.set_defaults(func=remove_label_command)

    # Delete command
    delete_parser = category_set_subparsers.add_parser("delete", help="Delete a category set")
    delete_parser.add_argument("name", help="Category set name")
    delete_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    delete_parser.set_defaults(func=delete_category_set_command)
