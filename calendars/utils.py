
from datetime import datetime, timedelta
from django.utils import timezone
from .models import leave_entitlement, leave_accrual_transaction

def calculate_leave_entitlement(employee, leave_type):
    today = timezone.now().date()
    leave_entitlements = leave_entitlement.objects.filter(leave_type=leave_type)

    for entitlement in leave_entitlements:
        # Check the effective date
        if entitlement.effective_after_from == 'date_of_joining':
            effective_date = employee.emp_joined_date
        else:
            effective_date = employee.emp_date_of_confirmation
        
        if today < effective_date:
            return 0

        # Check if the accrual date matches
        if entitlement.accrual:
            if entitlement.accrual_frequency == 'years':
                if today.month == 1 and today.day == 1:
                    # Accrue leave on 1st January
                    return entitlement.effective_after if not entitlement.prorate_accrual else prorated_accrual(entitlement, effective_date)
            else:
                # Handle other frequency cases (e.g., months, days)
                pass

    return 0

def prorated_accrual(entitlement, effective_date):
    today = timezone.now().date()
    total_days = (today - effective_date).days
    if entitlement.effective_after_unit == 'months':
        total_days //= 30
    elif entitlement.effective_after_unit == 'years':
        total_days //= 365
    
    return entitlement.effective_after * (total_days / (365 if entitlement.effective_after_unit == 'years' else 30))