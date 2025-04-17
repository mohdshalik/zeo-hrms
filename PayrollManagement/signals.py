from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip, PayslipComponent, EmployeeSalaryStructure
from calendars.models import Attendance
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SalaryComponent, EmployeeSalaryStructure
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

def evaluate_formula(formula, variables):
    """
    Evaluate formula by replacing variables with component values.
    """
    try:
        logger.info(f"Evaluating formula: {formula} with variables: {variables}")
        formula = formula.strip("'")
        for key, value in variables.items():
            formula = formula.replace(key, str(value))
        logger.info(f"Formula after substitution: {formula}")
        result = eval(formula)
        return round(result, 2)
    except Exception as e:
        logger.error(f"Error evaluating formula '{formula}': {e}")
        return 0

@receiver(post_save, sender=SalaryComponent)
def update_employee_salary_structure(sender, instance, created, **kwargs):
    """
    When a SalaryComponent is created or updated, calculate and store the amount
    in EmployeeSalaryStructure for all employees if is_fixed=False.
    """
    if not instance.is_fixed and instance.formula:  # Only for variable components with a formula
        # Get the EmpMaster model dynamically
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        employees = EmpMaster.objects.filter(is_active=True)  # Only active employees

        for employee in employees:
            # Fetch all existing salary components for this employee to use in formula
            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            component_amounts = {}

            # Populate fixed component amounts for formula evaluation
            for sc in salary_components:
                if sc.component.is_fixed and sc.amount is not None:
                    component_amounts[sc.component.code] = float(sc.amount)
                    logger.info(f"Using fixed component {sc.component.name} ({sc.component.code}): {sc.amount}")

            # Calculate the amount using the formula
            amount = evaluate_formula(instance.formula, component_amounts)
            logger.info(f"Calculated amount for {instance.name} ({instance.code}) for employee {employee}: {amount}")

            # Update or create the EmployeeSalaryStructure entry
            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=instance,
                defaults={
                    'amount': amount,
                    'is_active': True,
                }
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {instance.name} - Amount: {amount}")

@receiver(post_save, sender='PayrollManagement.PayrollRun')
def run_payroll_on_save(sender, instance, created, **kwargs):
    """
    Simplified payslip creation using pre-calculated amounts from EmployeeSalaryStructure.
    Only processes employees with is_active=True.
    """
    if created and instance.status == 'pending':
        # Get the EmpMaster model dynamically
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        employees = EmpMaster.objects.filter(is_active=True)  # Only active employees
        total_working_days = (instance.end_date - instance.start_date).days + 1

        for employee in employees:
            days_worked = Attendance.objects.filter(
                employee=employee,
                date__gte=instance.start_date,
                date__lte=instance.end_date
            ).exclude(
                Q(check_in_time__isnull=True) & Q(check_out_time__isnull=True)
            ).count()

            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            total_additions = 0
            total_deductions = 0

            payslip = Payslip.objects.create(
                payroll_run=instance,
                employee=employee,
                total_working_days=total_working_days,
                days_worked=days_worked,
            )

            for salary_component in salary_components:
                component = salary_component.component
                amount = float(salary_component.amount or 0)
                calculated_amount = amount
            
                # Adjust amount for leave deduction if applicable
                if component.deduct_leave and total_working_days > 0:
                    calculated_amount = (amount / total_working_days) * days_worked
                    logger.info(f"Adjusted {component.name} for leave: {calculated_amount}")
            
                # Create PayslipComponent
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=component,
                    amount=calculated_amount
                )
            
                # Update totals
                if component.component_type == 'addition':
                    total_additions += calculated_amount
                elif component.component_type == 'deduction':
                    total_deductions += calculated_amount

            # Calculate and save payslip totals
            gross_salary = total_additions
            net_salary = gross_salary - total_deductions

            payslip.gross_salary = gross_salary
            payslip.net_salary = net_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.save()

        instance.status = 'processed'
        instance.save()