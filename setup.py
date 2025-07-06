from setuptools import setup, find_packages

setup(
    name="varman",
    version="0.1.0",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=[
        # No external dependencies required
    ],
    entry_points={
        "console_scripts": [
            "varman=varman.cli.main:cli",
        ],
    },
    author="Author",
    author_email="author@example.com",
    description="A package for managing variables for a tabular dataset",
    keywords="tabular, data, variables, categories",
    python_requires=">=3.6",
)
