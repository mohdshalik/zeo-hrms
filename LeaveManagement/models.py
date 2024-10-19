from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta,timezone, time
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date
from django.contrib.auth import get_user_model
from UserManagement.models import CustomUser
from datetime import date
# import datetime
from datetime import datetime  # Import the 'datetime' class from the 'datetime' module

# Create your models here.

class leave_type(models.Model):
    type_choice =   [
        ('paid','paid'),
        ('unpaid','unpaid'),
    ]
    unit_choice = [
        ('days','days'),
        ('hours','hours'),
    ]

    balance_choice = [
        ('fixed','fixed'),
        ('leave_grant','leave_grant')
    ]
    
    name = models.CharField(max_length=50,unique=True)
    image = models.ImageField(upload_to='leave_images/')
    code =  models.CharField(max_length=30,unique=True)
    # no_of_days = models.IntegerField()
    type = models.CharField(max_length=20,choices=type_choice)
    unit = models.CharField(max_length=10,choices=unit_choice)
    negative = models.BooleanField(default=False)
    description = models.CharField(max_length=200)  
    allow_half_day = models.BooleanField(default=False)  # Allows half-day leave if set to True
    valid_from = models.DateField()
    valid_to = models.DateField(null=True,blank=True)
    include_weekend_and_holiday = models.BooleanField(default=False)
    # allow_opening_balance =models.BooleanField(default=False)
    def __str__(self):
        return f"{self.name}"



class leave_entitlement(models.Model):  
    EFFECTIVE_AFTER_CHOICES = [
        ('date_of_joining', 'Date of Joining'),
        ('date_of_confirmation', 'Date of Confirmation'),
    ]
    TIME_UNIT_CHOICES = [
        ('years', 'Years'),
        ('months', 'Months'),
        ('days','days')

    ]
    ROUND_OF_TYPE = [ 
        ('nearest_lowest','nearest_lowest'),
        ('nearest_highest','nearest_highest')
    ]
    DAY_CHOICES = [
        ('1st', '1st Day of the Month'),
        ('last', 'Last Day of the Month'),
    ]
    UNIT_CHOICES =[
        ('percentage','percentage'),
        ('unit','unit')
    ]
    MONTH_CHOICES = [
        ('Jan', 'January'),
        ('Feb', 'February'),
        ('Mar', 'March'),
        ('Apr', 'April'),
        ('May', 'May'),
        ('Jun', 'June'),
        ('Jul', 'July'),
        ('Aug', 'August'),
        ('Sep', 'September'),
        ('Oct', 'October'),
        ('Nov', 'November'),
        ('Dec', 'December')
    ]
    CARRY_CHOICE = [
        ('carry_forward','carry forward'),
        ('carry_forward_with_expiry','carry forward with expiry')
    ]
    PRORATE_CHOICES = [
        ('start_of_policy', 'Start of Policy'),
        ('start_and_end_of_policy', 'Start and End of Policy'),
        ('do_not_prorate', 'Do not Prorate')
    ]
    leave_type = models.ForeignKey(leave_type, on_delete=models.CASCADE)
    effective_after = models.PositiveIntegerField(default=0)
    effective_after_unit = models.CharField(max_length=10, choices=TIME_UNIT_CHOICES, default='months')
    effective_after_from = models.CharField(max_length=20, choices=EFFECTIVE_AFTER_CHOICES)


    accrual = models.BooleanField(default=False)
    accrual_rate = models.FloatField(default=0, help_text="Accrual rate per period (e.g., days/months/yearly)")
    accrual_frequency = models.CharField(max_length=20, choices=TIME_UNIT_CHOICES)
    accrual_month = models.CharField(max_length=3, choices=MONTH_CHOICES, default='Jan',null=True,blank=True)
    accrual_day = models.CharField(max_length=10, choices=DAY_CHOICES, default='1st')
    round_of = models.CharField(choices=ROUND_OF_TYPE,max_length=20)


    reset = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20, choices=TIME_UNIT_CHOICES)
    month = models.CharField(max_length=30, choices=MONTH_CHOICES, default='Dec')
    day = models.CharField(max_length=20, choices=DAY_CHOICES)


    carry_forward_choice=models.CharField(max_length=100,choices=CARRY_CHOICE)
    cf_value = models.PositiveIntegerField()
    cf_unit_or_percentage = models.CharField(max_length=50,choices=UNIT_CHOICES)
    cf_max_limit = models.PositiveIntegerField()
    cf_expires_in_value = models.PositiveIntegerField()
    cf_time_choice=models.CharField(max_length=20,choices=TIME_UNIT_CHOICES)


    encashment_value = models.PositiveIntegerField(default=50)
    encashment_unit_or_percentage = models.CharField(max_length=50,choices=UNIT_CHOICES)
    encashment_max_limit = models.PositiveIntegerField()


    prorate_accrual = models.BooleanField(default=False, help_text="Enable prorate accrual for this leave type.")
    prorate_type = models.CharField(max_length=30, choices=PRORATE_CHOICES, null=True, blank=True, help_text="Prorate accrual type.")
    def __str__(self):
        return f"{self.leave_type.name} Entitlement"


# from django.db.models import Q

class emp_leave_balance(models.Model):
    employee = models.ForeignKey('EmpManagement.emp_master',on_delete=models.CASCADE)
    leave_type= models.ForeignKey('leave_type',on_delete=models.CASCADE)
    balance = models.FloatField(null=True,blank=True)
    openings = models.IntegerField(null=True,blank=True)
    # accrued = models.FloatField(null=True, blank=True)
    # carried_forward = models.FloatField(null=True, blank=True)
    # encashed = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track last update
    def is_weekend(self, date):
        """ Check if the given date is a weekend based on the employee's weekend calendar """
        if self.employee.emp_weekend_calendar:
            # Assuming emp_weekend_calendar has a method is_weekend
            return self.employee.emp_weekend_calendar.is_weekend(date)
        return False

    def is_holiday(self, date):
        """ Check if the given date is a holiday based on the employee's holiday calendar """
        if self.employee.holiday_calendar:
            # Assuming holiday_calendar has a method is_holiday
            return self.employee.holiday_calendar.is_holiday(date)
        return False

    def get_leave_days(self, start_date, end_date):
        """ Calculate total leave days between start and end date, excluding weekends and holidays if applicable """
        total_days = 0
        current_date = start_date
        while current_date <= end_date:
            is_weekend = self.is_weekend(current_date)
            is_holiday = self.is_holiday(current_date)

            if self.leave_type.include_weekend_and_holiday:
                # Include both weekends and holidays
                total_days += 1
            else:
                # Exclude weekends and holidays
                if not is_weekend and not is_holiday:
                    total_days += 1

            current_date += timedelta(days=1)

        return total_days

    def deduct_leave(self, start_date, end_date, is_half_day=False):
        """ Deduct leave from balance, considering half-day and whether weekends/holidays are included """
        if is_half_day:
            leave_days = 0.5
        else:
            leave_days = self.get_leave_days(start_date, end_date)

        self.balance -= leave_days
        self.save()


from django.db import models
from django.core.validators import MinValueValidator

class leave_accrual_transaction(models.Model):
    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(leave_type, on_delete=models.CASCADE)
    accrual_date = models.DateField()
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    year = models.PositiveIntegerField(default=datetime.now().year)

class leave_reset_transaction(models.Model):
    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE)
    leave_type = models.ForeignKey('leave_type',on_delete=models.CASCADE)
    reset_date = models.DateField()
    carry_forward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    encashment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reset_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # accrual_details = models.JSONField(null=True, blank=True)  # Store accrual details as JSON
    year = models.PositiveIntegerField(default=datetime.now().year) 
    def __str__(self):
        return f"{self.employee} - {self.leave_type} Reset on {self.reset_date}"
    

class applicablity_critirea(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]
    
    leave_type = models.ForeignKey(leave_type,on_delete=models.CASCADE)
    gender= models.CharField(choices=GENDER_CHOICES,null=True,blank=True)
    branch= models.ManyToManyField('OrganisationManager.brnch_mstr',blank=True)
    department = models.ManyToManyField('OrganisationManager.dept_master',blank=True)
    designation = models.ManyToManyField('OrganisationManager.desgntn_master',blank=True)
    role = models.ManyToManyField('OrganisationManager.ctgry_master',blank=True)



class employee_leave_request(models.Model):
    LEAVE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    HALF_DAY_CHOICES = [
        ('first_half', 'First Half'),
        ('second_half', 'Second Half'),
    ]
    
    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(leave_type, on_delete=models.CASCADE)    
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=LEAVE_STATUS_CHOICES, default='pending')
    applied_on = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_on = models.DateField(null=True, blank=True)
    dis_half_day = models.BooleanField(default=False)  # True if it's a half-day leave
    half_day_period = models.CharField(max_length=20, choices=HALF_DAY_CHOICES, null=True, blank=True)  # First Half / Second Half

    def clean(self):
        super().clean()
        # Validate if half-day leave is allowed for this leave type
        if self.dis_half_day and not self.leave_type.allow_half_day:
            raise ValidationError(f"{self.leave_type} does not allow half-day leaves.")

        # If half-day leave is chosen, ensure the date range is correct
        if self.dis_half_day and self.start_date != self.end_date:
            raise ValidationError("Half-day leave should be on the same day.")

    # def save(self, *args, **kwargs):
    #     # Perform proration calculation if necessary
    #     if self.leave_type.leave_entitlement.prorate_accrual:
    #         accrual_transaction = leave_accrual_transaction.objects.create(
    #             employee=self.employee,
    #             leave_type=self.leave_type,
    #             accrual_date=datetime.now(),
    #             amount=self.leave_type.leave_entitlement.calculate_prorated_leave()
    #         )
    #         accrual_transaction.save()

    #     # Deduct the appropriate amount of leave based on half-day or full-day leave
    #     leave_balance = emp_leave_balance.objects.get(employee=self.employee, leave_type=self.leave_type)
        
    #     if self.dis_half_day and self.leave_type.allow_half_day:
    #     # Deduct half a day if allowed and the request is for half-day leave
    #         self.employee.leave_balance.deduct_leave(is_half_day=True)
    #     else:
    #         # Deduct full day leave
    #         self.employee.leave_balance.deduct_leave()

    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} from {self.start_date} to {self.end_date}"

class LeaveApprovalLevels(models.Model):
    level = models.IntegerField()
    role = models.CharField(max_length=50, null=True, blank=True)  # Use this for role-based approval like 'CEO' or 'Manager'
    approver = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)  # Use this for user-based approval
    request_type = models.ForeignKey('leave_type', related_name='leave_approval_levels', on_delete=models.CASCADE, null=True, blank=True)  # Nullable for common workflow
    # min_leave=models.IntegerField(default=0)
    # max_leave=models.IntegerField()
    class Meta:
        unique_together = ('level', 'request_type')

class LeaveApproval(models.Model):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    leave_request = models.ForeignKey(employee_leave_request, related_name='approvals', on_delete=models.CASCADE)
    approver = models.ForeignKey('UserManagement.CustomUser', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, null=True, blank=True)
    level = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,default=PENDING)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)



class EmployeeMachineMapping(models.Model):
    employee = models.ForeignKey("EmpManagement.emp_master", on_delete=models.CASCADE)
    machine_code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'{self.employee.emp_code} - {self.machine_code}'

class Shift(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField(null=True, blank=True)  # Optional for off days
    end_time = models.TimeField(null=True, blank=True)    # Optional for off days
    break_duration = models.DurationField(default=timedelta(minutes=0))  # Break time in minutes

    def __str__(self):
        return f"{self.name}"

class WeeklyShiftSchedule(models.Model):
    employee = models.ManyToManyField('EmpManagement.emp_master', null=True,blank=True)
    branch= models.ManyToManyField('OrganisationManager.brnch_mstr',null=True,blank=True)
    department = models.ManyToManyField('OrganisationManager.dept_master',null=True,blank=True)
    designation = models.ManyToManyField('OrganisationManager.desgntn_master',null=True,blank=True)
    role = models.ManyToManyField('OrganisationManager.ctgry_master',null=True,blank=True)
    # Each day of the week is assigned a shift, including weekends
    monday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='monday_shift')
    tuesday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='tuesday_shift')
    wednesday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='wednesday_shift')
    thursday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='thursday_shift')
    friday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='friday_shift')
    saturday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='saturday_shift')
    sunday_shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, related_name='sunday_shift')


    def get_shift_for_day(self, date):
        weekday = date.weekday()  # 0 = Monday, 6 = Sunday
        shifts = {
            0: self.monday_shift,
            1: self.tuesday_shift,
            2: self.wednesday_shift,
            3: self.thursday_shift,
            4: self.friday_shift,
            5: self.saturday_shift,
            6: self.sunday_shift,
        }
        return shifts.get(weekday, None)

    def __str__(self):
        return f"Weekly Shift Schedule for {self.employee}"
class Attendance(models.Model):
    employee = models.ForeignKey("EmpManagement.emp_master", on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    total_hours = models.DurationField(null=True, blank=True)
    class Meta:
        unique_together = ('employee', 'date')
    
    def calculate_total_hours(self):
        if self.check_in_time and self.check_out_time:
            # Ensure that check_in_time and check_out_time are time objects
            check_in_time = self.check_in_time if isinstance(self.check_in_time, time) else self.check_in_time.time()
            check_out_time = self.check_out_time if isinstance(self.check_out_time, time) else self.check_out_time.time()

            # Combine the date with the check-in and check-out times to get datetime objects
            check_in_datetime = datetime.combine(self.date, check_in_time)
            check_out_datetime = datetime.combine(self.date, check_out_time)

            # Handle check-out after midnight
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timedelta(days=1)

            # Calculate total time worked as a timedelta
            total_duration = check_out_datetime - check_in_datetime
            self.total_hours = total_duration  # Store as timedelta (if using DurationField)
            self.save()
    
class LeaveReport(models.Model):
    file_name = models.CharField(max_length=100,null=True,unique=True)
    report_data = models.FileField(upload_to='leave_report/', null=True, blank=True)
    class Meta:
        permissions = (
            ('export_report', 'Can export report'),
            # Add more custom permissions here
        )
    
    
    def __str__(self):
        return self.file_name 

    
    
    
    

    
    
    