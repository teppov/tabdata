# Test Coverage Documentation

## Overview
This document explains how to evaluate and interpret test coverage for the tabdata project.

## Running Tests with Coverage

To run tests with coverage reporting, use the provided `run_tests.py` script:

```bash
python run_tests.py
```

This script will:
1. Run all tests in the `tests/` directory
2. Generate a terminal coverage report
3. Create an HTML coverage report in the `coverage_html/` directory

## Interpreting Coverage Results

The coverage report shows:
- The percentage of code lines that are executed during tests
- A breakdown by module showing which parts of the code have good or poor coverage
- Lines that are not covered by tests

### Current Coverage Summary
As of the latest run, the overall test coverage is 55%. Some modules have excellent coverage (100%), while others need improvement:

- **High coverage (80-100%)**:
  - `varman/db/connection.py`: 100%
  - `varman/db/schema.py`: 100%
  - `varman/models/variable.py`: 82%
  - `varman/cli/main.py`: 78%

- **Medium coverage (50-79%)**:
  - `varman/models/base.py`: 72%
  - `varman/models/label.py`: 60%
  - `varman/models/category_set.py`: 57%

- **Low coverage (0-49%)**:
  - `varman/cli/category_set.py`: 35%
  - `varman/cli/variable.py`: 38%
  - `varman/models/category.py`: 34%
  - `varman/cli/utils.py`: 33%
  - `varman/utils/validation.py`: 0%

## Viewing Detailed Coverage Reports

For a detailed view of which lines are covered:

1. Open the HTML report in your browser:
   ```bash
   # On Linux/macOS
   open coverage_html/index.html
   
   # Or navigate to the file in your file explorer
   ```

2. The HTML report allows you to:
   - Navigate through modules
   - See exactly which lines are covered (green) or not covered (red)
   - Identify branches that aren't fully tested

## Improving Test Coverage

To improve test coverage:

1. Focus on modules with the lowest coverage first
2. Write tests for untested functions and methods
3. Ensure all code paths (if/else branches, exception handling) are tested
4. Pay special attention to `varman/utils/validation.py` which currently has 0% coverage

## Configuration

The coverage configuration is defined in `pytest.ini`:
- Source package: `varman`
- Excluded paths: `tests/*`
- Excluded lines: pragmas, `__repr__` methods, etc.

You can modify these settings to adjust what's included in the coverage analysis.