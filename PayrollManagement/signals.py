from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import PayrollRun,EmployeeSalaryStructure,Payslip,PayslipComponent
import logging
from calendars.models import Attendance
from django.db.models import Q
logger = logging.getLogger(__name__)

@receiver(post_save, sender=PayrollRun)
def run_payroll_on_save(sender, instance, created, **kwargs):
    if created and instance.status == 'pending':
        employees = instance.get_employees()

        # Calculate total working days from start_date and end_date
        total_working_days = (instance.end_date - instance.start_date).days + 1  # Include both start and end dates

        for employee in employees:
            # Calculate days worked from Attendance model
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
                days_worked=days_worked,  # Now using dynamic value from Attendance
            )

            component_amounts = {}

            # Log all salary components retrieved
            logger.info(f"Processing employee: {employee.emp_code}")
            logger.info(f"Total salary components found: {salary_components.count()}")
            logger.info(f"Total working days for payroll run {instance.name}: {total_working_days}")
            logger.info(f"Days worked for employee {employee.emp_code}: {days_worked}")
            
            for sc in salary_components:
                logger.info(f"Component: {sc.component.name} (Code: {sc.component.code}, Is Fixed: {sc.component.is_fixed}, Amount: {sc.amount})")

            # Step 1: Populate fixed components
            for salary_component in salary_components:
                component = salary_component.component
                if component.is_fixed:
                    amount = float(salary_component.amount)
                    component_amounts[component.code] = amount
                    logger.info(f"Fixed component: {component.name} ({component.code}) - Amount: {amount}")

            # Step 2: Evaluate non-fixed components
            for salary_component in salary_components:
                component = salary_component.component
                if not component.is_fixed:
                    logger.info(f"Evaluating formula for component: {component.name} ({component.code}) - Formula: {component.formula}")
                    amount = evaluate_formula(component.formula, component_amounts)
                    component_amounts[component.code] = amount
                    logger.info(f"Evaluated amount for {component.name} ({component.code}): {amount}")
                else:
                    amount = component_amounts[component.code]

                # Step 3: Add to payslip and update totals
                PayslipComponent.objects.create(payslip=payslip, component=component, amount=amount)
                if component.component_type == 'addition':
                    total_additions += amount
                    logger.info(f"Added {component.name} ({amount}) to total_additions: {total_additions}")
                elif component.component_type == 'deduction':
                    total_deductions += amount

            # Step 4: Calculate salaries
            gross_salary = total_additions
            net_salary = gross_salary - total_deductions

            logger.info(f"Final Gross Salary for {employee.emp_code}: {gross_salary}")
            logger.info(f"Final Net Salary for {employee.emp_code}: {net_salary}")

            payslip.gross_salary = gross_salary
            payslip.net_salary = net_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.save()

        instance.status = 'processed'
        instance.save()

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