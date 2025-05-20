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
        EmployeeOvertime = apps.get_model('calendars', 'EmployeeOvertime')
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

        total_working_days = (instance.end_date - instance.start_date).days + 1
        logger.debug(f"Total working days: {total_working_days}")

        # Define possible codes for Basic Salary and Overtime
        basic_salary_codes = ['bs', 'basic', 'BS', 'BASIC', 'base', 'BASE']
        overtime_codes = ['ot', 'OT', 'overtime', 'OVERTIME']

        # Fetch Overtime SalaryComponent using Q objects
        overtime_component = None
        try:
            overtime_query = Q()
            for code in overtime_codes:
                overtime_query |= Q(code__iexact=code)
            overtime_component = SalaryComponent.objects.filter(overtime_query).first()
            if not overtime_component:
                logger.warning(f"No overtime component found with codes: {overtime_codes}")
            else:
                logger.debug(f"Overtime component verified: ID={overtime_component.id}, Code={overtime_component.code}")
        except Exception as e:
            logger.error(f"Error fetching overtime component: {e}")

        for employee in employees:
            logger.debug(f"Processing employee: {employee.id} - {employee}")
            # Fetch attendance
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

            # Initialize base_hourly_rate with a default value
            base_hourly_rate = Decimal('0.00')

            # Calculate base hourly rate from Basic Salary
            try:
                basic_query = Q()
                for code in basic_salary_codes:
                    basic_query |= Q(component__code__iexact=code)
                base_salary_component = salary_components.filter(basic_query).first()
                if base_salary_component and base_salary_component.amount:
                    monthly_salary = Decimal(str(base_salary_component.amount))
                    base_hourly_rate = monthly_salary / (total_working_days * 8)  # Assume 8 hours/day
                    logger.debug(f"Base hourly rate for {employee.id}: {base_hourly_rate}")
                else:
                    logger.warning(f"No valid basic salary component found for {employee.id}")
            except Exception as e:
                logger.error(f"Error fetching basic salary component for {employee.id}: {e}")

            # Process regular salary components
            for salary_component in salary_components:
                component = salary_component.component
                amount = Decimal(str(salary_component.amount or 0))
                calculated_amount = amount

                # Adjust for leave deduction
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

            # Process overtime if emp_ot_applicable=True and overtime_component exists
            if getattr(employee, 'emp_ot_applicable', False) and overtime_component:
                try:
                    overtime_records = EmployeeOvertime.objects.filter(
                        employee=employee,
                        date__gte=instance.start_date,
                        date__lte=instance.end_date,
                        approved=True
                    )
                    total_overtime_hours = sum(Decimal(str(record.hours)) for record in overtime_records)
                    logger.debug(f"Total overtime hours for {employee.id}: {total_overtime_hours}")

                    if total_overtime_hours > 0 and base_hourly_rate > 0:
                        overtime_rate_multiplier = Decimal(str(overtime_records.first().rate_multiplier)) if overtime_records else Decimal('1.5')
                        overtime_amount = total_overtime_hours * base_hourly_rate * overtime_rate_multiplier
                        logger.debug(f"Overtime amount for {employee.id}: {overtime_amount}")

                        # Create PayslipComponent for overtime
                        try:
                            PayslipComponent.objects.create(
                                payslip=payslip,
                                component=overtime_component,
                                amount=overtime_amount
                            )
                            total_additions += overtime_amount
                            logger.debug(f"Added overtime component to payslip {payslip.id}")
                        except Exception as e:
                            logger.error(f"Error adding overtime component to payslip {payslip.id}: {e}")
                    elif base_hourly_rate <= 0:
                        logger.warning(f"Skipping overtime for {employee.id}: base_hourly_rate is {base_hourly_rate}")
                except Exception as e:
                    logger.error(f"Error processing overtime for {employee.id}: {e}")

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