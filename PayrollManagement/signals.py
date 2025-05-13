from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payslip, PayslipComponent, EmployeeSalaryStructure,SalaryComponent
from calendars.models import Attendance
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps


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
    """
    Simplified payslip creation using pre-calculated amounts from EmployeeSalaryStructure.
    Only processes employees with is_active=True.
    """
    logger.info(f"Signal received for PayrollRun {instance.id}")
    logger.info(f"Created: {created}, Status: {instance.status}")
    logger.info(f"Sender: {sender}")
    if created and instance.status == 'pending':
        logger.debug(f"Starting payroll processing for {instance.id}")
        # Get the EmpMaster model dynamically
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        try:
            employees = EmpMaster.objects.filter(is_active=True)
            logger.info(f"Found {employees.count()} active employees")
        except Exception as e:
            logger.error(f"Error fetching employees: {e}")
            return

        total_working_days = (instance.end_date - instance.start_date).days + 1
        logger.debug(f"Total working days: {total_working_days}")

        for employee in employees:
            logger.debug(f"Processing employee: {employee.id} - {employee}")
            try:
                days_worked = Attendance.objects.filter(
                    employee=employee,
                    date__gte=instance.start_date,
                    date__lte=instance.end_date
                ).exclude(
                    Q(check_in_time__isnull=True) & Q(check_out_time__isnull=True)
                ).count()
                logger.debug(f"Days worked for {employee.id}: {days_worked}")
            except Exception as e:
                logger.error(f"Error fetching attendance for {employee.id}: {e}")
                continue

            salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            logger.debug(f"Found {salary_components.count()} salary components for {employee.id}")
            total_additions = 0
            total_deductions = 0

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

            for salary_component in salary_components:
                component = salary_component.component
                amount = float(salary_component.amount or 0)
                calculated_amount = amount

                # Adjust amount for leave deduction if applicable
                if component.deduct_leave and total_working_days > 0:
                    calculated_amount = (amount / total_working_days) * days_worked
                    logger.debug(f"Adjusted {component.name} for leave: {calculated_amount}")

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

                # Update totals
                if component.component_type == 'addition':
                    total_additions += calculated_amount
                elif component.component_type == 'deduction':
                    total_deductions += calculated_amount

            # Calculate and save payslip totals
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
                continue

        try:
            instance.status = 'processed'
            instance.save()
            logger.info(f"PayrollRun {instance.id} status updated to 'processed'")
        except Exception as e:
            logger.error(f"Error updating PayrollRun status: {e}")

@receiver(post_save, sender=EmployeeSalaryStructure)
def update_variable_components_on_fixed_change(sender, instance, **kwargs):
    """
    Trigger update for variable components if a fixed component (like basic_salary) is changed.
    """
    if instance.component.is_fixed:
        logger.info(f"Fixed component '{instance.component.code}' changed for {instance.employee}. Updating variable components.")

        # Get all variable components that depend on fixed ones
        variable_components = SalaryComponent.objects.filter(is_fixed=False).exclude(formula__isnull=True).exclude(formula__exact='')

        for vc in variable_components:
            # Prepare context for formula evaluation
            salary_structures = EmployeeSalaryStructure.objects.filter(employee=instance.employee)
            variables = {
                sc.component.code: float(sc.amount) if sc.amount is not None else 0
                for sc in salary_structures
                if sc.component.code
            }

            amount = evaluate_formula(vc.formula, variables)

            EmployeeSalaryStructure.objects.update_or_create(
                employee=instance.employee,
                component=vc,
                defaults={
                    'amount': amount,
                    'is_active': True,
                }
            )
            logger.info(f"Updated variable component '{vc.name}' for employee {instance.employee}: {amount}")