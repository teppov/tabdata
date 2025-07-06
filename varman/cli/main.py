"""Command-line interface for varman."""

import argparse
import sys

from varman.db.schema import init_db, reset_db
from varman.cli.variable import setup_variable_parser
from varman.cli.category_set import setup_category_set_parser
from varman.cli.utils import confirm_action


def reset_command(args):
    """Reset the database."""
    if args.yes or confirm_action("Are you sure you want to reset the database?"):
        reset_db()
        print("Database reset.")
    else:
        print("Operation cancelled.")


def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="Manage variables for a tabular dataset."
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset the database")
    reset_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )
    reset_parser.set_defaults(func=reset_command)

    # Add variable and category-set command groups
    setup_variable_parser(subparsers)
    setup_category_set_parser(subparsers)

    return parser


def cli():
    """Main entry point for the CLI."""
    # Initialize the database
    init_db()

    # Parse arguments
    parser = setup_parser()
    args = parser.parse_args()

    # Execute command
    if hasattr(args, "func"):
        args.func(args)
    else:
        # If a command was specified but no subcommand, show help for that command
        if hasattr(args, "command") and args.command:
            # Get the subparser for the specified command
            subparsers = parser._subparsers._group_actions[0]
            for action in subparsers._choices_actions:
                if action.dest == args.command:
                    subparsers.choices[args.command].print_help()
                    return
        # Otherwise show the main help
        parser.print_help()


if __name__ == "__main__":
    cli()
