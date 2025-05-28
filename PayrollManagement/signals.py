from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PayslipComponent, LoanRepayment, EmployeeSalaryStructure,SalaryComponent,LoanApplication
from calendars.models import Attendance
from django.db.models import Q
import logging
from datetime import datetime
from calendar import monthrange

logger = logging.getLogger(__name__)
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal
from django.db.models import Count
from django.db import transaction

from datetime import date
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import relativedelta
from simpleeval import SimpleEval, NameNotDefined, FunctionNotDefined


# Initialize logger
logger = logging.getLogger('PayrollManagement')

def evaluate_formula(formula, variables, employee, component):
    try:
        logger.debug(f"Evaluating formula: {formula} with variables: {variables} for employee: {employee}")
        formula = formula.strip("'")

        s = SimpleEval()
        s.names = variables  # ✅ Set variables here

        s.operators.update({
            '<': lambda x, y: x < y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            'and': lambda x, y: x and y,
            'or': lambda x, y: x or y,
            'not': lambda x: not x,
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '%': lambda x, y: x % y
        })

        s.functions.update({
            'MAX': max,
            'MIN': min,
            'AVG': lambda *args: sum(args) / len(args) if args else 0,
            'SUM': sum,
            'ROUND': round
        })

        result = s.eval(formula)  # ✅ No keyword argument here
        return round(float(result), 2)

    except (NameNotDefined, FunctionNotDefined) as e:
        logger.error(f"Invalid variable or function in formula '{formula}' for employee {employee}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error evaluating formula '{formula}' for employee {employee}: {e}")
        return 0

@receiver(post_save, sender=SalaryComponent)
def update_employee_salary_structure(sender, instance, created, **kwargs):
    if not instance.is_fixed and instance.formula:
        EmpMaster = apps.get_model('EmpManagement', 'emp_master')
        EmployeeSalaryStructure = apps.get_model('PayrollManagement', 'EmployeeSalaryStructure')
        employees = EmpMaster.objects.all()

        for employee in employees:
            # Get variables including fixed components, calendar_days, ot_hours etc.
            variables = get_formula_variables(employee)

            try:
                amount = evaluate_formula(instance.formula, variables, employee, instance)
            except Exception as e:
                logger.error(f"Formula evaluation error for {employee}: {e}")
                amount = Decimal('0.00')

            logger.info(f"Calculated amount for {instance.name} ({instance.code}) for employee {employee}: {amount}")

            EmployeeSalaryStructure.objects.update_or_create(
                employee=employee,
                component=instance,
                defaults={'amount': amount, 'is_active': True}
            )
            logger.info(f"Updated EmployeeSalaryStructure for {employee} with component {instance.name} - Amount: {amount}")

def get_formula_variables(employee, start_date=None, end_date=None):
    Attendance = apps.get_model('calendars', 'Attendance')
    EmployeeOvertime = apps.get_model('calendars', 'EmployeeOvertime')
    EmployeeSalaryStructure = apps.get_model('PayrollManagement', 'EmployeeSalaryStructure')

    if not start_date or not end_date:
        today = datetime.today().date()
        start_date = today.replace(day=1)
        end_date = today.replace(day=monthrange(today.year, today.month)[1])

    variables = {
        'calendar_days': Decimal(str((end_date - start_date).days + 1)),
        'fixed_days': Decimal('30.0'),
        'standard_hours': Decimal('160.0'),
    }

    variables['ot_hours'] = EmployeeOvertime.objects.filter(
        employee=employee, date__range=(start_date, end_date), approved=True
    ).aggregate(total_hours=Sum('hours'))['total_hours'] or Decimal('0.00')

    working_days = Attendance.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        check_in_time__isnull=False,
        check_out_time__isnull=False
    ).exclude(date__week_day__in=[1, 7]).count()

    variables['working_days'] = Decimal(str(working_days))

    variables['employee.grade'] = str(getattr(employee, 'grade', ''))
    variables['employee.employee_type'] = str(getattr(employee, 'employee_type', ''))
    variables['employee.joining_date'] = (
        employee.joining_date.strftime('%Y-%m-%d') if getattr(employee, 'joining_date', None) else ''
    )

    if getattr(employee, 'joining_date', None):
        delta = relativedelta(end_date, employee.joining_date)
        variables['years_of_service'] = round(delta.years + delta.months / 12.0, 2)
    else:
        variables['years_of_service'] = 0.0

    salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
    for sc in salary_components:
        if sc.component and sc.amount is not None:
            variables[sc.component.code] = Decimal(str(sc.amount))

    return variables


@receiver(post_save, sender='PayrollManagement.PayrollRun')
def run_payroll_on_save(sender, instance, created, **kwargs):
    logger.info(f"Signal received for PayrollRun {instance.id} (Created: {created}, Status: {instance.status})")

    if not created or instance.status != 'pending':
        return

    # Load models dynamically
    EmpMaster = apps.get_model('EmpManagement', 'emp_master')
    SalaryComponent = apps.get_model('PayrollManagement', 'SalaryComponent')
    EmployeeSalaryStructure = apps.get_model('PayrollManagement', 'EmployeeSalaryStructure')
    Payslip = apps.get_model('PayrollManagement', 'Payslip')
    PayslipComponent = apps.get_model('PayrollManagement', 'PayslipComponent')
    Attendance = apps.get_model('calendars', 'Attendance')
    GeneralRequest = apps.get_model('EmpManagement', 'GeneralRequest')
    EmployeeOvertime = apps.get_model('calendars', 'EmployeeOvertime')
    LoanRequest = apps.get_model('PayrollManagement', 'LoanApplication')
    LoanRepayment = apps.get_model('PayrollManagement', 'LoanRepayment')
    # Holiday = apps.get_model('calendars', 'Holiday')

    # Set date range
    try:
        total_working_days = monthrange(instance.year, instance.month)[1]
        start_date = datetime(instance.year, instance.month, 1).date()
        end_date = datetime(instance.year, instance.month, total_working_days).date()
    except Exception as e:
        logger.error(f"Invalid date setup for PayrollRun {instance.id}: {e}")
        return

    employees = EmpMaster.objects.filter(is_active=True)
    logger.info(f"Found {employees.count()} active employees")

    for employee in employees:
        logger.debug(f"Processing employee: {employee.id} - {employee}")

        # Attendance
        days_worked = Attendance.objects.filter(
            employee=employee,
            date__range=(start_date, end_date)
        ).exclude(
            Q(check_in_time__isnull=True) & Q(check_out_time__isnull=True)
        ).count()

        # Salary structure
        salary_components = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
        total_additions = Decimal('0.00')
        total_deductions = Decimal('0.00')

        # Create Payslip
        payslip = Payslip.objects.create(
            payroll_run=instance,
            employee=employee,
            total_working_days=total_working_days,
            days_worked=days_worked,
        )

        # Overtime hours
        overtime_hours = EmployeeOvertime.objects.filter(
            employee=employee,
            date__range=(start_date, end_date),
            approved=True
        ).aggregate(total_hours=Sum('hours'))['total_hours'] or Decimal('0.00')
        if not isinstance(overtime_hours, Decimal):
            overtime_hours = Decimal(str(overtime_hours))
        logger.debug(f"Overtime hours: {overtime_hours}")

        variables = {
            'ot_hours': Decimal(str(overtime_hours)),
            'calendar_days': Decimal(str((end_date - start_date).days + 1)),
            'fixed_days': Decimal('30.0'),
            'standard_hours': Decimal('160.0'),
        }
        # Add employee attributes
        variables['employee.grade'] = str(getattr(employee, 'grade', ''))
        variables['employee.employee_type'] = str(getattr(employee, 'employee_type', ''))
        variables['employee.joining_date'] = (
            employee.joining_date.strftime('%Y-%m-%d')
            if hasattr(employee, 'joining_date') and employee.joining_date else ''
        )

        if hasattr(employee, 'joining_date') and employee.joining_date:
            years_of_service = relativedelta(end_date, employee.joining_date).years + \
                               relativedelta(end_date, employee.joining_date).months / 12.0
            variables['years_of_service'] = round(years_of_service, 2)
        else:
            variables['years_of_service'] = 0.0

        # Calculate working_days
        working_days = Attendance.objects.filter(
            employee=employee,
            date__range=(start_date, end_date),
            check_in_time__isnull=False,
            check_out_time__isnull=False
        # ).exclude(
        #     date__in=Holiday.objects.filter(date__range=(start_date, end_date)).values('date')
        ).exclude(
            date__week_day__in=[1, 7]
        ).count()

        variables['working_days'] = float(working_days)
        logger.debug(f"Variables for {employee.id}: {variables}")

        # Include fixed salary components in variables
        for sc in salary_components:
            comp = sc.component
            if comp:
                # variables[comp.name.upper()] = sc.amount or Decimal('0.00')
                variables[comp.code] = sc.amount or Decimal('0.00')
                # logger.debug(f"Fixed component: {comp.name.upper()} = {variables[comp.name.upper()]}")

        # Evaluate OTAmount
        ot_amount_component = SalaryComponent.objects.filter(code__iexact='OTAmount').first()
        ot_amount_value = Decimal('0.00')
        if ot_amount_component and ot_amount_component.formula:
            try:
                ot_amount_value = Decimal(str(evaluate_formula(ot_amount_component.formula, variables, employee, ot_amount_component)))
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=ot_amount_component,
                    amount=ot_amount_value
                )
                logger.debug(f"OTAmount for {employee.id}: {ot_amount_value}")
            except Exception as e:
                logger.error(f"OTAmount error for {employee.id}: {e}")
        variables['OTAmount'] = ot_amount_value

        # Other salary components
        for sc in salary_components:
            component = sc.component
            if component == ot_amount_component:
                continue

            amount = sc.amount or Decimal('0.00')
            if not component.is_fixed and component.formula:
                try:
                    amount = Decimal(str(evaluate_formula(component.formula, variables, employee, component)))
                    logger.debug(f"Evaluated {component.name}: {amount}")
                except Exception as e:
                    logger.error(f"Formula error for {component.name}: {e}")
                    amount = Decimal('0.00')

            PayslipComponent.objects.create(
                payslip=payslip,
                component=component,
                amount=amount
            )

            if component.component_type == 'addition':
                total_additions += amount
            elif component.component_type == 'deduction':
                total_deductions += amount

        # Approved request components
        approved_requests = GeneralRequest.objects.filter(
            employee=employee,
            status='Approved',
            request_type__salary_component__isnull=False
        ).select_related('request_type__salary_component')

        for request in approved_requests:
            component = request.request_type.salary_component
            if component and request.total is not None:
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=component,
                    amount=request.total
                )
                if component.component_type == 'addition':
                    total_additions += request.total
                elif component.component_type == 'deduction':
                    total_deductions += request.total
        #loan
        active_loans = LoanRequest.objects.filter(
        employee=employee,
        status='Approved',
        )

        for loan in active_loans:
            # Count past repayments
            repayment_count = LoanRepayment.objects.filter(loan=loan).count()

            if repayment_count < loan.repayment_period:
                # Deduct this month's EMI
                emi_amount = loan.emi_amount
                loan_component = SalaryComponent.objects.filter(is_loan_component=True).first()

                if loan_component:
                    # Add EMI as deduction in payslip
                    PayslipComponent.objects.create(
                        payslip=payslip,
                        component=loan_component,
                        amount=emi_amount
                    )
                    total_deductions += emi_amount

                    total_paid = LoanRepayment.objects.filter(loan=loan).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
                    remaining_balance = loan.amount_requested - total_paid - emi_amount
                    
                    # Save LoanRepayment
                    LoanRepayment.objects.create(
                        loan=loan,
                        payslip=payslip,
                        repayment_date=instance.payment_date,
                        amount_paid=emi_amount,
                        remaining_balance=remaining_balance
                    )
                    loan.remaining_balance = remaining_balance
                    loan.save(update_fields=['remaining_balance'])
                    # If loan fully paid, close it
                    if remaining_balance <= 0:
                        loan.status = 'Closed'
                        loan.save()
        # Finalize payslip
        gross_salary = total_additions
        net_salary = gross_salary - total_deductions

        payslip.total_additions = total_additions
        payslip.total_deductions = total_deductions
        payslip.gross_salary = gross_salary
        payslip.net_salary = net_salary
        payslip.save()

    instance.status = 'processed'
    instance.save()

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

