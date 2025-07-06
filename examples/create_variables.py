"""
Example script demonstrating how to create variables using the varman package.
"""

from varman import create_variable, create_categorical_variable
from varman import MinValueConstraint, MaxValueConstraint

# Create a discrete variable
age = create_variable(
    name="age",
    data_type="discrete",
    description="Age of the participant in years"
)

# Add constraints
age.add_constraint(MinValueConstraint(0))
age.add_constraint(MaxValueConstraint(120))

# Create a categorical variable
gender = create_categorical_variable(
    name="gender",
    data_type="nominal",
    categories=["male", "female", "other", "prefer_not_to_say"],
    description="Gender of the participant"
)

# Add labels
gender.add_label(text="Gender", language_code="en", purpose="short")
gender.add_label(text="Participant's gender", language_code="en", purpose="long")

print(f"Created variables: age, gender")