"""Utility functions for the command-line interface."""

def confirm_action(prompt="Are you sure?"):
    """Ask for confirmation before proceeding."""
    response = input(f"{prompt} [y/N] ").lower()
    return response in ("y", "yes")