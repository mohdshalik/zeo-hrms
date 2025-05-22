from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip, PayslipComponent, EmployeeSalaryStructure,SalaryComponent
from calendars.models import Attendance
from django.db.models import Q
import logging
from datetime import datetime
from calendar import monthrange

logger = logging.getLogger(__name__)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal


# Initialize logger
logger = logging.getLogger('PayrollManagement')

def evaluate_formula(formula, variables):
    """
    Evaluate formula by replacing variables with component values.
    """
    try:
        logger.debug(f"Evaluating formula: {formula} with variables: {variables}")
        formula = formula.strip("'")
        for key, value in variables.items():
            formula = formula.replace(key, str(value))
        logger.debug(f"Formula after substitution: {formula}")
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
        employees = EmpMaster.objects.all()

        for employee in employees:
            # Fetch all existing salary components for this employee to use in formula
            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee)
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
    logger.info(f"Signal received for PayrollRun {instance.id} (Created: {created}, Status: {instance.status})")
    if created and instance.status == 'pending':
        logger.debug(f"Starting payroll processing for PayrollRun {instance.id}")
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        SalaryComponent = apps.get_model('PayrollManagement', 'SalaryComponent')
        EmployeeSalaryStructure = apps.get_model('PayrollManagement', 'EmployeeSalaryStructure')
        Payslip = apps.get_model('PayrollManagement', 'Payslip')
        PayslipComponent = apps.get_model('PayrollManagement', 'PayslipComponent')
        Attendance = apps.get_model('calendars', 'Attendance')

        try:
            employees = EmpMaster.objects.filter(is_active=True)
            logger.info(f"Found {employees.count()} active employees")
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return

        # Calculate total working days in the month
        try:
            total_working_days = monthrange(instance.year, instance.month)[1]
            logger.debug(f"Total working days in {instance.get_month_display()} {instance.year}: {total_working_days}")
        except ValueError as e:
            logger.error(f"Invalid month/year for PayrollRun {instance.id}: {e}")
            return

        # Determine the date range for the month
        try:
            start_date = datetime(instance.year, instance.month, 1).date()
            _, last_day = monthrange(instance.year, instance.month)
            end_date = datetime(instance.year, instance.month, last_day).date()
        except ValueError as e:
            logger.error(f"Invalid month/year for PayrollRun {instance.id}: {e}")
            return

        for employee in employees:
            logger.debug(f"Processing employee: {employee.id} - {employee}")
            # Fetch attendance for the month
            try:
                days_worked = Attendance.objects.filter(
                    employee=employee,
                    date__gte=start_date,
                    date__lte=end_date
                ).exclude(
                    Q(check_in_time__isnull=True) & Q(check_out_time__isnull=True)
                ).count()
                logger.debug(f"Days worked for {employee.id}: {days_worked}")
            except Exception as e:
                logger.error(f"Error fetching attendance for {employee.id}: {e}")
                days_worked = 0

            # Fetch salary components
            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            logger.debug(f"Found {salary_components.count()} salary components for {employee.id}")
            total_additions = Decimal('0.00')
            total_deductions = Decimal('0.00')

            # Create payslip
            try:
                payslip = Payslip.objects.create(
                    payroll_run=instance,
                    employee=employee,
                    total_working_days=total_working_days,
                    days_worked=days_worked,
                )
                logger.info(f"Created payslip {payslip.id} for {employee.id}")
            except Exception as e:
                logger.error(f"Error creating payslip for {employee.id}: {e}")
                continue

            # Process regular salary components
            for salary_component in salary_components:
                component = salary_component.component
                amount = Decimal(str(salary_component.amount or 0))
                calculated_amount = amount

                # Create PayslipComponent
                try:
                    PayslipComponent.objects.create(
                        payslip=payslip,
                        component=component,
                        amount=calculated_amount
                    )
                    logger.debug(f"Added component {component.name} to payslip {payslip.id}")
                except Exception as e:
                    logger.error(f"Error adding component {component.name} to payslip {payslip.id}: {e}")
                    continue

                # Update totals based on component_type and is_fixed
                if component.component_type == 'addition' or getattr(component, 'is_fixed', False) or getattr(component, 'deduct_leave', False):
                    total_additions += calculated_amount
                elif component.component_type == 'deduction':
                    total_deductions += calculated_amount

            # Update payslip totals
            gross_salary = total_additions
            net_salary = gross_salary - total_deductions

            try:
                payslip.gross_salary = gross_salary
                payslip.net_salary = net_salary
                payslip.total_additions = total_additions
                payslip.total_deductions = total_deductions
                payslip.save()
                logger.info(f"Updated payslip {payslip.id}: Gross={gross_salary}, Net={net_salary}")
            except Exception as e:
                logger.error(f"Error updating payslip {payslip.id}: {e}")

        # Update PayrollRun status
        try:
            instance.status = 'processed'
            instance.save()
            logger.info(f"PayrollRun {instance.id} status updated to 'processed'")
        except Exception as e:
            logger.error(f"Error updating PayrollRun status: {e}")
@receiver(post_save, sender=EmployeeSalaryStructure)
def update_dependent_salary_components(sender, instance, created, **kwargs):
    """
    When an EmployeeSalaryStructure's amount is updated, recalculate amounts for
    other components that use this component in their formulas.
    """
    # Only proceed if the amount was updated (not created) and the component is fixed
    if created or not instance.component.is_fixed:
        return

    # Get the EmpMaster model dynamically
    EmpMaster = apps.get_model('EmpManagement', 'emp_master')
    
    # Get all employees to update their dependent components
    employees = EmpMaster.objects.all()

    # Find all variable SalaryComponents that might depend on this component
    dependent_components = SalaryComponent.objects.filter(
        is_fixed=False,
        formula__contains=instance.component.code  # Check if the updated component's code appears in the formula
    )

    for employee in employees:
        # Fetch all salary components for this employee to use in formula evaluation
        salary_components = EmployeeSalaryStructure.objects.filter(employee=employee)
        component_amounts = {}

        # Populate fixed component amounts for formula evaluation
        for sc in salary_components:
            if sc.component.is_fixed and sc.amount is not None:
                component_amounts[sc.component.code] = float(sc.amount)
                logger.info(f"Using fixed component {sc.component.name} ({sc.component.code}): {sc.amount}")

        # Recalculate amounts for dependent components
        for component in dependent_components:
            # Calculate the new amount using the formula
            amount = evaluate_formula(component.formula, component_amounts)
            logger.info(f"Calculated amount for {component.name} ({component.code}) for employee {employee}: {amount}")

            # Update or create the EmployeeSalaryStructure entry for the dependent component
            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=component,
                defaults={
                    'amount': amount,
                    'is_active': True,
                }
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {component.name} - Amount: {amount}")