import re
from decimal import Decimal
from django.db import transaction
from .models import PayrollRun, Payslip, PayslipComponent, EmployeeSalaryStructure, SalaryComponent

def process_payroll(payroll_run_id):
    payroll_run = PayrollRun.objects.get(id=payroll_run_id)  # Use 'id' as the field name    # Fetch employees based on branch (and optionally dept/category)
    employees = payroll_run.branch.emp_master_set.all()  # Assuming emp_master has a related_name to branch
    
    with transaction.atomic():  # Ensure atomicity
        for employee in employees:
            # Get employee's salary structure
            salary_structures = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            
            # Initialize totals
            total_additions = Decimal('0.00')
            total_deductions = Decimal('0.00')
            basic_salary = None
            
            # Create payslip
            payslip = Payslip.objects.create(
                payroll_run=payroll_run,
                employee=employee,
                status='pending'
            )
            
            # Process each component
            for structure in salary_structures:
                component = structure.component
                amount = structure.amount or Decimal('0.00')
                
                # Save to PayslipComponent
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=component,
                    amount=amount
                )
                
                # Categorize amounts
                if component.component_type == 'addition':
                    total_additions += amount
                    if component.name.lower() == 'basic':  # Assuming 'Basic' is the basic salary component
                        basic_salary = amount
                elif component.component_type == 'deduction':
                    total_deductions += amount
            
            # Calculate gross and net salary
            gross_salary = total_additions
            net_salary = total_additions - total_deductions
            
            # Apply formula (basic parsing for now)
            formula = payroll_run.pay_formula.formula_text
            components_dict = {s.component.name: s.amount for s in salary_structures}
            try:
                net_salary = eval_formula(formula, components_dict)
            except Exception as e:
                raise ValueError(f"Error evaluating formula: {e}")
            
            # Update payslip
            payslip.basic_salary = basic_salary
            payslip.gross_salary = gross_salary
            payslip.net_salary = net_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.save()
        
        # Mark payroll as processed
        payroll_run.status = 'processed'
        payroll_run.save()

def eval_formula(formula, components_dict):
    # Replace component names with their values in the formula
    for name, value in components_dict.items():
        formula = formula.replace(name, str(value or 0))
    return Decimal(eval(formula))  # Use with caution; consider a safer parser