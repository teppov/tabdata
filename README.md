# TabData

[![Test Coverage](https://img.shields.io/badge/coverage-79%25-orange)](docs/test_coverage.md)

A pure Python package for managing variables for tabular datasets.

## Installation

```bash
pip install .
```

## Usage

**varman** provides a command-line interface for managing variables, category sets, categories, and labels. It can also be used programmatically in Python scripts.

### Programmatic Usage

While **varman** provides a command-line interface, you can also use it programmatically in your Python scripts:

```python
from varman import Variable, CategorySet, create_variable, import_variables

# Create a variable
age = create_variable(
    name="age",
    data_type="discrete",
    description="Age of the participant in years"
)

# Import variables from a JSON file
imported_vars, errors, overwritten = import_variables("variables.json")

# Get all variables
all_variables = Variable.get_all()

# Export variables to a JSON file
Variable.export_to_json(all_variables, "exported_variables.json")
```

See the `examples` directory for more examples of programmatic usage.

### Variables

Variables can be of the following data types:
- `discrete`: numeric data that is represented by integer numbers
- `continuous`: numeric data that is represented by decimal (float) numbers
- `nominal`: unordered categorical data
- `ordinal`: ordered categorical data
- `text`: text data

#### Creating Variables

Create a non-categorical variable:

```bash
varman variable create my_variable --type discrete --description "My variable description" --reference "My reference"
```

Create a categorical variable with a new category set:

```bash
varman variable create my_categorical_variable --type nominal --categories category1 --categories category2 --categories category3
```

Create a categorical variable with an existing category set:

```bash
varman variable create my_other_categorical_variable --type ordinal --category-set my_category_set
```

Add labels to a variable:

```bash
varman variable create my_variable --type discrete --label en:Short:My variable --label fi:Lyhyt:Muuttujani
```

#### Adding Constraints to Variables

Variables can have constraints that validate their values. The following constraints are available:

For numeric variables (discrete, continuous):
- `min-value`: Minimum allowed value
- `max-value`: Maximum allowed value

For text variables:
- `email`: Validates that the value is a valid email address
- `url`: Validates that the value is a valid URL
- `regex`: Validates that the value matches a regular expression pattern

Create a variable with constraints:

```bash
# Numeric constraints
varman variable create age --type discrete --min-value 0 --max-value 120

# Text constraints
varman variable create email --type text --email
varman variable create website --type text --url
varman variable create zipcode --type text --regex "^\d{5}(-\d{4})?$"
```

Update a variable to add constraints:

```bash
varman variable update age --min-value 0 --max-value 120
varman variable update email --email
```

Remove constraints from a variable:

```bash
varman variable update age --remove-min-value --remove-max-value
varman variable update email --remove-email
```

#### Listing Variables

List all variables:

```bash
varman variable list
```

List variables of a specific type:

```bash
varman variable list --type nominal
```

#### Showing Variable Details

Show details of a variable:

```bash
varman variable show my_variable
```

#### Updating Variables

Update a variable's description or reference:

```bash
varman variable update my_variable --description "New description" --reference "New reference"
```

Add a label to a variable:

```bash
varman variable update my_variable --add-label en:Long:My variable (long label)
```

Remove a label from a variable:

```bash
varman variable update my_variable --remove-label 1
```

#### Deleting Variables

Delete a variable:

```bash
varman variable delete my_variable
```

#### Exporting and Importing Variables

Export all variables to a JSON file:

```bash
varman variable export variables.json
```

Export specific variables to a JSON file:

```bash
varman variable export variables.json --name var1 --name var2
```

Import variables from a JSON file:

```bash
varman variable import variables.json
```

If a variable with the same name already exists, an error message will be displayed. To overwrite existing variables:

```bash
varman variable import variables.json --overwrite
```

When using the overwrite option, a report will be displayed showing which variables were replaced.

#### Example JSON Format

The package includes an example JSON file in the `examples` directory that demonstrates the format for all different types of variables, with labels in different languages, and with and without constraints:

```bash
examples/example_variables.json
```

This file can be used as a reference for creating your own JSON files for importing variables. It includes examples of:

- Discrete and continuous variables with min/max constraints
- Nominal and ordinal variables with category sets
- Text variables with email, URL, and regex constraints
- Labels in multiple languages (English and Finnish)
- Different label purposes (Short and Long)

### Validation

TabData includes a comprehensive validation layer that provides detailed feedback for variable data validation. This is particularly useful for web applications that need to provide meaningful error messages to users.

#### Validation Framework

The validation framework consists of the following components:

- `ValidationError`: An exception class for validation errors
- `ValidationResult`: A class to collect validation errors and warnings
- Validation methods in model classes: `Variable.validate_data`, `CategorySet.validate_data`, `Category.validate_data`

#### Programmatic Usage

You can use the validation framework programmatically to validate variable data before creating or updating variables:

```python
from varman import Variable

# Validate variable data
data = {
    "name": "age",
    "data_type": "discrete",
    "description": "Age of the participant in years"
}
validation_result = Variable.validate_data(data)

# Check if validation passed
if validation_result.is_valid:
    # Create variable if validation passed
    variable = Variable.create(data)
else:
    # Handle validation errors
    for error in validation_result.errors:
        print(f"Error in {error['field']}: {error['message']}")
```

#### Creating Variables with Validation

The `create_with_validation` method validates the data before creating a variable and returns both the created variable and any validation errors:

```python
from varman import Variable

# Create variable with validation
variable, errors = Variable.create_with_validation(
    name="age",
    data_type="discrete",
    description="Age of the participant in years"
)

# Check if validation passed
if variable:
    print(f"Variable created: {variable.name}")
else:
    # Handle validation errors
    for error in errors:
        print(f"Error in {error['field']}: {error['message']}")
```

#### Updating Variables with Validation

The `update` method in the `Variable` class now validates the data before updating the variable:

```python
from varman import Variable

# Get an existing variable
variable = Variable.get_by("name", "age")

# Update variable with validation
success, errors = variable.update({
    "description": "New description",
    "reference": "New reference"
})

# Check if validation passed
if success:
    print("Variable updated successfully")
else:
    # Handle validation errors
    for error in errors:
        print(f"Error in {error['field']}: {error['message']}")
```

#### Importing Variables with Validation

The `import_from_json` method validates each variable before importing it and collects validation errors:

```python
from varman import Variable

# Import variables with validation
imported_variables, errors, overwritten = Variable.import_from_json("variables.json")

# Check for validation errors
if errors:
    for var_error in errors:
        print(f"Errors in variable '{var_error['variable']}':")
        for error in var_error['errors']:
            print(f"  {error['field']}: {error['message']}")
```

### Category Sets

#### Creating Category Sets

Create a category set with categories:

```bash
varman category-set create my_category_set --category category1 --category category2 --category category3
```

#### Listing Category Sets

List all category sets:

```bash
varman category-set list
```

#### Showing Category Set Details

Show details of a category set:

```bash
varman category-set show my_category_set
```

#### Adding Categories

Add a category to a category set:

```bash
varman category-set add-category my_category_set --category new_category
```

#### Removing Categories

Remove a category from a category set:

```bash
varman category-set remove-category my_category_set --category category1
```

#### Adding Labels to Categories

Add a label to a category:

```bash
varman category-set add-label my_category_set --category category1 --label en:Category 1
```

#### Removing Labels from Categories

Remove a label from a category:

```bash
varman category-set remove-label my_category_set --category category1 --label-id 1
```

#### Deleting Category Sets

Delete a category set:

```bash
varman category-set delete my_category_set
```

### Database Management

Reset the database:

```bash
varman reset
```

## Data Structure

The data is stored in an SQLite database with the following tables:

- `variables`: Stores variable information
- `category_sets`: Stores category set information
- `categories`: Stores category information
- `labels`: Stores label information for variables and categories
- `variable_constraints`: Stores constraints for variables

## Testing

The package includes a comprehensive test suite to ensure functionality works as expected. To run the tests:

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run the tests with coverage reporting:
```bash
python run_tests.py
```

This will run all tests and generate a coverage report. The report will be displayed in the terminal and also saved as an HTML report in the `coverage_html` directory. Open `coverage_html/index.html` in a browser to view the detailed report.

Alternatively, you can run the tests directly with pytest:
```bash
pytest tests/ -v --cov=varman --cov-report=term --cov-report=html:coverage_html
```

### Test Coverage

The current test coverage is shown by the badge at the top of this README. For detailed information about test coverage and how to improve it, see the [Test Coverage Documentation](docs/test_coverage.md).

You can generate an updated coverage badge using the provided script:
```bash
./scripts/generate_coverage_badge.py
```

## License

MIT
