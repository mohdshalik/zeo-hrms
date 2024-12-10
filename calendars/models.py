import logging
from django.db import models
from LeaveManagement .models import EmployeeYearlyCalendar

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from OrganisationManager.models import brnch_mstr,ctgry_master,dept_master
from EmpManagement.models import emp_master
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.dispatch import receiver
from django.db.models.signals import post_save
import calendar
from datetime import datetime, timedelta


# Create your models here.
class weekend_calendar(models.Model):
    DAY_TYPE_CHOICES = [
        ('leave', 'Leave'),
        ('fullday', 'fullday'),
        ('halfday', 'Halfday'),
    ]
    description = models.TextField()
    calendar_code = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    monday = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    tuesday=models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    wednesday=models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    thursday = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    friday = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    saturday = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    sunday = models.CharField(choices=DAY_TYPE_CHOICES,default='fullday')
    def __str__(self):
        return f"{self.calendar_code} - {self.year}"
    def is_weekend(self, date):
        """Check if the given date is a weekend based on the calendar configuration."""
        day_name = date.strftime('%A').lower()
        print("dayyy",day_name)
        day_type = getattr(self, day_name, 'fullday')
        return day_type == 'leave'

    def __str__(self):
        return f"{self.calendar_code} - {self.year}"
class WeekendDetail(models.Model):
    WEEKDAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    DAY_TYPE_CHOICES = [
        ('leave', 'Leave'),
        ('work', 'Work'),
        ('halfday', 'Halfday'),
    ]
    weekend_calendar = models.ForeignKey(weekend_calendar, related_name='details', on_delete=models.CASCADE)
    weekday = models.CharField(max_length=9, choices=WEEKDAY_CHOICES)
    day_type = models.CharField(max_length=7, choices=DAY_TYPE_CHOICES)
    week_of_month = models.PositiveIntegerField(null=True, blank=True)  # 1 to 5 for specifying specific weeks
    month_of_year = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)  # Specific date for the day
    class Meta:
        ordering = [ 'pk']
@receiver(post_save, sender=weekend_calendar)
def create_weekend_details(sender, instance, created, **kwargs):
    if created:
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_types = {
            'monday': instance.monday,
            'tuesday': instance.tuesday,
            'wednesday': instance.wednesday,
            'thursday': instance.thursday,
            'friday': instance.friday,
            'saturday': instance.saturday,
            'sunday': instance.sunday,
        }

        year = instance.year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        delta = timedelta(days=1)

        while start_date <= end_date:
            weekday_name = calendar.day_name[start_date.weekday()].lower()
            WeekendDetail.objects.create(
                weekend_calendar=instance,
                weekday=weekday_name.capitalize(),
                day_type=day_types[weekday_name],
                week_of_month=(start_date.day - 1) // 7 + 1,
                month_of_year=start_date.month,
                date=start_date.date()
            )
            start_date += delta

    def __str__(self):
        return f"{self.weekday} - {self.day_type}"

class assign_weekend(models.Model):
    EMP_CHOICES = [
        ("branch", "Branch"),
        ("department", "Department"),
        ("category", "Category"),
        ("employee", "Employee"),
    ]
    related_to = models.CharField(max_length=20, choices=EMP_CHOICES,null=True)
    branch = models.ManyToManyField('OrganisationManager.brnch_mstr',  null=True, blank=True)
    department = models.ManyToManyField('OrganisationManager.ctgry_master', null=True, blank=True)
    category = models.ManyToManyField('OrganisationManager.dept_master',  null=True, blank=True)
    employee= models.ManyToManyField('EmpManagement.emp_master',  null=True, blank=True)
    weekend_model = models.ForeignKey(weekend_calendar,on_delete=models.CASCADE)

@receiver(m2m_changed, sender=assign_weekend.branch.through)
def update_branch_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "branch":
        branches = instance.branch.all()
        logger.debug(f"Updating employees for branches: {[branch.id for branch in branches]}")
        for branch in branches:
            updated_count = emp_master.objects.filter(emp_branch_id=branch.id).update(emp_weekend_calendar=instance.weekend_model)
            logger.debug(f"Updated {updated_count} employees for branch ID {branch.id}")

@receiver(m2m_changed, sender=assign_weekend.department.through)
def update_department_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "department":
        departments = instance.department.all()
        logger.debug(f"Updating employees for departments: {[department.id for department in departments]}")
        for department in departments:
            updated_count = emp_master.objects.filter(emp_dept_id=department.id).update(emp_weekend_calendar=instance.weekend_model)
            logger.debug(f"Updated {updated_count} employees for department ID {department.id}")

@receiver(m2m_changed, sender=assign_weekend.category.through)
def update_category_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "category":
        categories = instance.category.all()
        logger.debug(f"Updating employees for categories: {[category.id for category in categories]}")
        for category in categories:
            updated_count = emp_master.objects.filter(emp_ctgry_id=category.id).update(emp_weekend_calendar=instance.weekend_model)
            logger.debug(f"Updated {updated_count} employees for category ID {category.id}")

@receiver(m2m_changed, sender=assign_weekend.employee.through)
def update_employee_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "employee":
        employees = instance.employee.all()
        logger.debug(f"Updating employees: {[employee.id for employee in employees]}")
        for employee in employees:
            employee.emp_weekend_calendar = instance.weekend_model
            employee.save()
            logger.debug(f"Updated employee ID {employee.id}")
def update_employee_yearly_calendar(employee, weekend_model):
    year = weekend_model.year
    # Check if EmployeeYearlyCalendar for this employee and year already exists
    try:
        yearly_calendar = EmployeeYearlyCalendar.objects.get(emp=employee, year=year)
        logger.debug(f"Found existing EmployeeYearlyCalendar for employee ID {employee.id} for year {year}")
    except EmployeeYearlyCalendar.DoesNotExist:
        yearly_calendar = EmployeeYearlyCalendar(emp=employee, year=year, daily_data={})
        logger.debug(f"Created new EmployeeYearlyCalendar for employee ID {employee.id} for year {year}")

    # Merge new weekend details into existing `daily_data` without overwriting existing data
    weekend_details = WeekendDetail.objects.filter(weekend_calendar=weekend_model)
    updated_data = yearly_calendar.daily_data  # Copy of existing data

    for detail in weekend_details:
        date_str = detail.date.strftime("%Y-%m-%d")
        # Only add or update if the date is not already set or if you need to update existing data
        if date_str not in updated_data or updated_data[date_str].get("status") != "Leave":
            updated_data[date_str] = {
                "status": "Leave" if detail.day_type == 'leave' else detail.day_type,
                "remarks": "Weekend assigned"
            }

    # Save the updated or newly created yearly calendar with merged data
    yearly_calendar.daily_data = updated_data
    yearly_calendar.save()
    logger.debug(f"Updated EmployeeYearlyCalendar for employee ID {employee.id} with new weekend data")


class holiday(models.Model):
    description =models.CharField(max_length=50,unique=True)
    start_date=models.DateField()
    end_date=models.DateField()
    restricted=models.BooleanField(default=False)

class holiday_calendar(models.Model):
    calendar_title=models.CharField(max_length=50)
    year = models.IntegerField()
    holiday=models.ManyToManyField(holiday)

class assign_holiday(models.Model):
    EMP_CHOICES = [
        ("branch", "Branch"),
        ("department", "Department"),
        ("category", "Category"),
        ("employee", "Employee"),
    ]
    related_to = models.CharField(max_length=20, choices=EMP_CHOICES,null=True)
    branch = models.ManyToManyField('OrganisationManager.brnch_mstr',  null=True, blank=True)
    department = models.ManyToManyField('OrganisationManager.ctgry_master', null=True, blank=True)
    category = models.ManyToManyField('OrganisationManager.dept_master',  null=True, blank=True)
    employee= models.ManyToManyField('EmpManagement.emp_master',  null=True, blank=True)
    holiday_model = models.ForeignKey(holiday_calendar,on_delete=models.CASCADE)

@receiver(m2m_changed, sender=assign_holiday.branch.through)
def update_branch_holiday_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "branch":
        branches = instance.branch.all()
        # logger.debug(f"Updating employees for branches: {[branch.id for branch in branches]}")
        for branch in branches:
            updated_count = emp_master.objects.filter(emp_branch_id=branch.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for branch ID {branch.id}")
@receiver(m2m_changed, sender=assign_weekend.department.through)
def update_department_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "department":
        departments = instance.department.all()
        # logger.debug(f"Updating employees for departments: {[department.id for department in departments]}")
        for department in departments:
            updated_count = emp_master.objects.filter(emp_dept_id=department.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for department ID {department.id}")
@receiver(m2m_changed, sender=assign_weekend.category.through)
def update_category_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "category":
        categories = instance.category.all()
        # logger.debug(f"Updating employees for categories: {[category.id for category in categories]}")
        for category in categories:
            updated_count = emp_master.objects.filter(emp_ctgry_id=category.id).update(holiday_calendar=instance.holiday_model)
            # logger.debug(f"Updated {updated_count} employees for category ID {category.id}")
@receiver(m2m_changed, sender=assign_weekend.employee.through)
def update_employee_weekend_calendar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.related_to == "employee":
        employees = instance.employee.all()
        # logger.debug(f"Updating employees: {[employee.id for employee in employees]}")
        for employee in employees:
            employee.holiday_calendar = instance.holiday_model
            employee.save()
            # logger.debug(f"Updated employee ID {employee.id}")
def update_employee_yearly_calendar_with_holidays(employee, holiday_calendar):
    year = holiday_calendar.year
    try:
        yearly_calendar, created = EmployeeYearlyCalendar.objects.get_or_create(emp=employee, year=year)
        updated_data = yearly_calendar.daily_data
        for holiday in holiday_calendar.holiday.all():
            current_date = holiday.start_date
            while current_date <= holiday.end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                # Only add holiday data if not already set or if replacing certain data is allowed
                if date_str not in updated_data or updated_data[date_str].get("status") != "Leave":
                    updated_data[date_str] = {
                        "status": "Leave" if holiday.restricted else "Holiday",
                        "remarks": holiday.description
                    }
                current_date += timedelta(days=1)

        yearly_calendar.daily_data = updated_data
        yearly_calendar.save()

    except Exception as e:
        logger.error(f"Failed to update EmployeeYearlyCalendar for employee ID {employee.id}: {e}")
            