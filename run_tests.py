#!/usr/bin/env python3
"""Script to run tests with coverage reporting."""

import os
import sys
import subprocess


def run_tests():
    """Run the tests with coverage reporting."""
    # Run pytest with coverage
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=varman",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\nTests passed successfully!")
        print("\nCoverage report has been generated in the coverage_html directory.")
        print("Open coverage_html/index.html in a browser to view the detailed report.")
    else:
        print("\nTests failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run_tests()
