from celery import shared_task
from django_tenants.utils import schema_context 
from django_tenants.utils import get_tenant_model                                 
from django.utils import timezone
from django.apps import apps
from datetime import datetime, timedelta
from EmpManagement.models import emp_master
from LeaveManagement.models import leave_entitlement,leave_accrual_transaction,emp_leave_balance,leave_reset_transaction
from celery.schedules import crontab
import logging
logger = logging.getLogger(__name__)

# def month_name_to_number(month_name):
#     # Helper function to convert month name to number
#     month_dict = {
#         'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
#         'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
#     }
#     return month_dict.get(month_name)

@shared_task
def accrue_leaves():
    tenants = get_all_tenant_schemas()  # Fetch all tenant schemas
    today = timezone.now().date()

    for tenant_schema_name in tenants:
        try:
            with schema_context(tenant_schema_name):
                logger.info(f"Accrue leaves task started on {today} for tenant {tenant_schema_name}")

                # Fetch all active leave entitlements with accrual enabled
                entitlements = leave_entitlement.objects.filter(accrual=True)

                for entitlement in entitlements:
                    leave_type = entitlement.leave_type
                    effective_after_unit = entitlement.effective_after_unit
                    effective_after = entitlement.effective_after
                    effective_after_from = entitlement.effective_after_from
                    accrual_frequency = entitlement.accrual_frequency
                    accrual_month = entitlement.accrual_month
                    accrual_day = entitlement.accrual_day
                    accrual_rate = entitlement.accrual_rate
                    prorate_accrual = entitlement.prorate_accrual
                    logger.info(f"Processing entitlement for leave type: {leave_type}")

                    # Fetch employees who have the leave type assigned in emp_leave_balance
                    employee_balances = emp_leave_balance.objects.filter(leave_type=leave_type)

                    for leave_balance in employee_balances:
                        emp = leave_balance.employee  # Fetch the employee from emp_leave_balance (emp_master instance)
                        accrual_date = None

                        # Determine accrual start date based on 'effective_after_from'
                        if effective_after_from == 'date_of_joining':
                            accrual_date = emp.emp_joined_date + timedelta(**{effective_after_unit: effective_after})
                        elif effective_after_from == 'date_of_confirmation':
                            accrual_date = emp.emp_date_of_confirmation + timedelta(**{effective_after_unit: effective_after})

                        if accrual_date and accrual_date <= today:
                            last_accrual = leave_accrual_transaction.objects.filter(
                                employee=emp,
                                leave_type=leave_type
                            ).order_by('-accrual_date').first()

                            accrue_today = False

                            # Daily Accrual
                            if accrual_frequency == 'days':
                                accrue_today = True

                            # Monthly Accrual (1st or last day of the month)
                            elif accrual_frequency == 'months':
                                if accrual_day == '1st' and today.day == 1:
                                    accrue_today = True
                                elif accrual_day == 'last':
                                    last_day_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                    if today == last_day_of_month:
                                        accrue_today = True

                            # Yearly Accrual (specific month)
                            elif accrual_frequency == 'years':
                                if today.month == month_name_to_number(accrual_month) and today.day == 1:
                                    accrue_today = True

                            if accrue_today:
                                if not last_accrual or (last_accrual.accrual_date < today):
                                    amount_to_accrue = accrual_rate

                                    # **Handle Prorated Accrual**
                                    if prorate_accrual:
                                        if accrual_frequency == 'years':
                                            months_left = 12 - today.month + 1
                                            amount_to_accrue = accrual_rate * (months_left / 12)
                                        elif accrual_frequency == 'months':
                                            total_days_in_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                            days_left = total_days_in_month - today.day + 1
                                            amount_to_accrue = accrual_rate * (days_left / total_days_in_month)

                                    # Record accrual transaction in leave_accrual_transaction
                                    leave_accrual_transaction.objects.create(
                                        employee=emp,
                                        leave_type=leave_type,
                                        accrual_date=today,
                                        amount=amount_to_accrue,
                                        year=today.year
                                    )

                                    # Update leave balance in emp_leave_balance
                                    leave_balance.accrued = (leave_balance.accrued or 0) + amount_to_accrue
                                    leave_balance.save()

                                    logger.info(f"Accrued {amount_to_accrue} for employee {emp.emp_code} on {today}.")
                                else:
                                    logger.info(f"Accrual already done for employee {emp.emp_code} on {last_accrual.accrual_date}.")
                            else:
                                logger.info(f"Accrual condition not met for employee {emp.emp_code} on {today}.")
                
                logger.info(f"Accrue leaves task completed for tenant {tenant_schema_name}.")
        
        except Exception as e:
            logger.error(f"Error processing tenant {tenant_schema_name}: {e}")

def month_name_to_number(month_name):
    """Helper function to convert month names to month numbers."""
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    return month_map.get(month_name)    

@shared_task
def reset_leave_balances():
    tenants = get_all_tenant_schemas()  # Fetch all tenant schemas
    today = timezone.now().date()
    logger.info(f"Reset leave balances task started on {today}")
    for tenant_schema_name in tenants: 
        try:
            with schema_context(tenant_schema_name):                                                 
                logger.info(f"Accrue leaves task started on {today} for tenant {tenant_schema_name}")
                
                # Fetch all active leave entitlements with accrual enabled
                entitlements = leave_entitlement.objects.filter(accrual=True)

                for entitlement in entitlements:
                    


                    frequency = entitlement.frequency
                    day = entitlement.day
                    month = entitlement.month
                    leave_type = entitlement.leave_type

                    logger.info(f"Processing reset for leave type: {leave_type}")

                    # Determine the reset date based on frequency
                    if frequency == 'years':
                        reset_date = today.replace(month=month, day=day)
                    elif frequency == 'months':
                        reset_date = today.replace(day=day)
                    else:
                        reset_date = today

                    if today == reset_date:
                        for emp in emp_master.objects.all():
                            leave_balance = emp_leave_balance.objects.filter(employee=emp, leave_type=leave_type).first()

                            if leave_balance:
                                # Calculate carry forward amount
                                carry_forward_amount = min(
                                    leave_balance.balance, 
                                    entitlement.carry_forward_limit or entitlement.carry_forward
                                )

                                # Reset the balance, carry forward amount remains
                                leave_balance.balance = carry_forward_amount

                                # Calculate encashment amount
                                encashment_amount = min(
                                    leave_balance.balance * (entitlement.encashment / 100),
                                    entitlement.encashment_limit or leave_balance.balance
                                )

                                # Deduct encashment from balance
                                leave_balance.balance -= encashment_amount

                                # Save the reset balance in the emp_leave_balance model
                                leave_balance.save()

                                logger.info(
                                    f"Reset leave balance for employee {emp.user.username}. "
                                    f"Carry forward: {carry_forward_amount}, Encashment: {encashment_amount}"
                                )

                                # Log the reset transaction in leave_reset_transaction
                                leave_reset_transaction.objects.create(
                                    employee=emp,
                                    leave_type=leave_type,
                                    reset_date=today,
                                    carry_forward_amount=carry_forward_amount,
                                    encashment_amount=encashment_amount,
                                    reset_balance=leave_balance.balance
                                )
        except Exception as e:
            logger.error(f"Error processing tenant {tenant_schema_name}: {e}")                  
    logger.info("Reset leave balances task completed.")
def get_all_tenant_schemas(): 
    # Implement this function based on your tenant management system 
    TenantModel = get_tenant_model() 
    return TenantModel.objects.values_list('schema_name', flat=True)