#!/usr/bin/env python3
"""Script to run tests with coverage reporting."""

import sys
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup


def save_coverage_url(coverage):
    """ Save a shields.io URL for the coverage badge. """

    # Determine color based on coverage percentage
    if coverage >= 80:
        color = "brightgreen"
    elif coverage >= 60:
        color = "yellow"
    elif coverage >= 40:
        color = "orange"
    else:
        color = "red"

    # Save the badge URL to a file.
    badge_file = Path("coverage_badge.txt")
    badge_file.write_text(f"https://img.shields.io/badge/coverage-{coverage}%25-{color}")
    print(f"Badge URL saved to {badge_file}")


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

    # Extract coverage % from the report and save badge url to a file
    with open("coverage_html/index.html", "r") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "lxml")
    total_coverage_td = soup.body.table.tfoot.tr.find_all('td')[4]
    if total_coverage_td:
        save_coverage_url(int(total_coverage_td.text.strip()[:-1]))

    if result.returncode == 0:
        print("\nTests passed successfully!")
        print("\nCoverage report has been generated in the coverage_html directory.")
        print("Open coverage_html/index.html in a browser to view the detailed report.")
    else:
        print("\nTests failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run_tests()
