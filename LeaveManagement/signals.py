from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import applicablity_critirea, emp_leave_balance, leave_type
from EmpManagement.models import emp_master
from django.db import models  # Ensure models import is included

import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=applicablity_critirea)
def update_emp_leave_balance(sender, instance, created, **kwargs):
    leave_type_instance = instance.leave_type
    criteria = instance

    # Start with all employees
    employees = emp_master.objects.all()

    # Apply gender filter if specified
    if criteria.gender:
        employees = employees.filter(emp_gender=criteria.gender)

    # Apply branch filter if specified
    if criteria.branch.exists():
        employees = employees.filter(emp_branch_id__in=criteria.branch.all())

    # Apply department filter if specified
    if criteria.department.exists():
        employees = employees.filter(emp_dept_id__in=criteria.department.all())

    # Apply designation filter if specified
    if criteria.designation.exists():
        employees = employees.filter(emp_desgntn_id__in=criteria.designation.all())

    # Apply role filter if specified
    if criteria.role.exists():
        employees = employees.filter(emp_ctgry_id__in=criteria.role.all())

    # Create emp_leave_balance entries for each matching employee only if they don't already exist
    for employee in employees:
        emp_leave_balance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type_instance,
            defaults={'balance': 0, 'openings': 0}
        )

    print(f"Leave balance checked for employees: {', '.join([emp.emp_code for emp in employees])}")


@receiver(post_save, sender=emp_master)
def update_emp_leave_balance_on_employee_create(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New employee created: {instance.emp_code}")

        # Get all applicable applicability criteria based on the new employee's attributes
        applicable_criteria = applicablity_critirea.objects.filter(
            models.Q(gender=instance.emp_gender) | models.Q(gender=None),
            models.Q(branch=instance.emp_branch_id) | models.Q(branch=None),
            models.Q(department=instance.emp_dept_id) | models.Q(department=None),
            models.Q(designation=instance.emp_desgntn_id) | models.Q(designation=None),
            models.Q(role=instance.emp_ctgry_id) | models.Q(role=None),
        ).distinct()

        # Create emp_leave_balance entries for each applicable criteria only if they don't already exist
        for criteria in applicable_criteria:
            emp_leave_balance.objects.get_or_create(
                employee=instance,
                leave_type=criteria.leave_type,
                defaults={'balance': 0, 'openings': 0}
            )

            logger.info(f"Checked leave balance for employee {instance.emp_code} based on criteria: {criteria}")

        logger.info(f"Leave balance update completed for employee {instance.emp_code}")