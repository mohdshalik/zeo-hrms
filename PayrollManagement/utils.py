import re
from decimal import Decimal
from EmpManagement.models import emp_master
from .models import EmployeeSalaryStructure, SalaryComponent, PayrollFormula

def evaluate_payroll_formula(employee, formula_text):
    """
    Evaluate payroll formula dynamically by substituting component values.
    """
    try:
        # Fetch all salary components assigned to the employee
        salary_components = EmployeeSalaryStructure.objects.filter(
            employee=employee, is_active=True
        )

        # Create a dictionary with component names and their values
        component_values = {comp.component.name: comp.amount for comp in salary_components}

        # Validate formula variables
        variables = set(re.findall(r'[a-zA-Z_]+', formula_text))
        for var in variables:
            if var not in component_values:
                component_values[var] = Decimal('0.00')  # Default to 0 if the component isn't assigned

        # Safely evaluate the formula
        allowed_names = {key: float(value) for key, value in component_values.items()}
        net_salary = eval(formula_text, {"__builtins__": {}}, allowed_names)

        return Decimal(net_salary)

    except Exception as e:
        print(f"Error in formula evaluation: {e}")
        return Decimal('0.00')  # Return 0 in case of any error