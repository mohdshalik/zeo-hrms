from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta,timezone, time
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from UserManagement.models import CustomUser
from EmpManagement.models import EmailConfiguration
from django.core.mail import EmailMultiAlternatives,get_connection, send_mail
from django.template import Context, Template
from django.utils.html import strip_tags

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
    use_common_workflow = models.BooleanField(default=False)
    # allow_opening_balance =models.BooleanField(default=False)
    def __str__(self):
        return f"{self.name}"
    def get_email_template(self, template_type):
        # Try fetching a specific template for the request type
        email_templates = self.email_templates.filter(template_type=template_type)

        # Check if there are multiple templates and handle appropriately
        if email_templates.count() > 1:
            raise ValueError(f"Multiple email templates found for template type '{template_type}' and request type '{self.name}'")
        elif email_templates.exists():
            return email_templates.first()


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

class LvEmailTemplate(models.Model):
    request_type = models.ForeignKey('leave_type', related_name='email_templates', on_delete=models.CASCADE,null=True)
    template_type = models.CharField(max_length=50, choices=[
        ('request_created', 'Request Created'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected')
    ])
    subject = models.CharField(max_length=255)
    body = models.TextField()
    
class LvApprovalNotify(models.Model):
    recipient_user = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True,on_delete=models.CASCADE)
    recipient_employee = models.ForeignKey('EmpManagement.emp_master', null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        if self.recipient_user:
            return f"Notification for {self.recipient_user.username}: {self.message}"
        else:
            return f"Notification for employee: {self.message}"    
    
    def send_email_notification(self, template_type, context):
         # Try to retrieve the active email configuration
        try:
            email_config = EmailConfiguration.objects.get(is_active=True)
            use_custom_config = True
        except EmailConfiguration.DoesNotExist:
            use_custom_config = False
            default_email = settings.EMAIL_HOST_USER

        # Use custom or default email configuration
        if use_custom_config:
            default_email = email_config.email_host_user
            connection = get_connection(
                host=email_config.email_host,
                port=email_config.email_port,
                username=email_config.email_host_user,
                password=email_config.email_host_password,
                use_tls=email_config.email_use_tls,
            )
        else:
            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )

        # Determine recipient email and name
        to_email = None
        recipient_name = None
        if self.recipient_user and self.recipient_user.email:
            to_email = self.recipient_user.email
            recipient_name = self.recipient_user.username
        elif self.recipient_employee and self.recipient_employee.emp_personal_email:
            to_email = self.recipient_employee.emp_personal_email
            recipient_name = self.recipient_employee.emp_first_name

        if to_email:
            context.update({'recipient_name': recipient_name})

            # Fetch the email template
            try:
                email_template = LvEmailTemplate.objects.get(template_type=template_type)
                subject = email_template.subject
                template = Template(email_template.body)
                html_message = template.render(Context(context))
            except LvEmailTemplate.DoesNotExist:
                subject = "Request Notification"
            plain_message = strip_tags(html_message)

            # Send the email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=default_email,  # From email
                to=[to_email],  # Recipient list
                connection=connection,
                headers={'From': 'zeosoftware@abc.com'}  # Custom header
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
class LvCommonWorkflow(models.Model):
    level = models.IntegerField()
    role = models.CharField(max_length=50, null=True, blank=True)
    approver = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['level'], name='Lv_common_workflow_level')
        ]
    def __str__(self):
        return f"Level {self.level} - {self.role or self.approver}"
      
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
    # approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    # approved_on = models.DateField(null=True, blank=True)
    dis_half_day = models.BooleanField(default=False)  # True if it's a half-day leave
    half_day_period = models.CharField(max_length=20, choices=HALF_DAY_CHOICES, null=True, blank=True)  # First Half / Second Half
    created_by=models.ForeignKey('UserManagement.CustomUser',on_delete=models.CASCADE,null=True,blank=True)
    number_of_days = models.FloatField(default=1)
    def clean(self):
        super().clean()
        # Validate if half-day leave is allowed for this leave type
        if self.dis_half_day and not self.leave_type.allow_half_day:
            raise ValidationError(f"{self.leave_type} does not allow half-day leaves.")

        # If half-day leave is chosen, ensure the date range is correct
        if self.dis_half_day and self.start_date != self.end_date:
            raise ValidationError("Half-day leave should be on the same day.")

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            # Get the employee's leave balance record
            leave_balance = emp_leave_balance.objects.get(employee=self.employee, leave_type=self.leave_type)

            # Calculate leave days considering weekends and holidays
            if self.dis_half_day:
                self.number_of_days = 0.5
            else:
                self.number_of_days = leave_balance.get_leave_days(self.start_date, self.end_date)

        # Deduct leave only if the status is set to 'approved' and it's a new request (not an update)
        if self.status == 'approved' and not self.pk:
            leave_balance.deduct_leave(self.number_of_days)

        super().save(*args, **kwargs)  # Call the parent class's save method

    def __str__(self):
        return f"{self.employee} - {self.leave_type} from {self.start_date} to {self.end_date}"

    # def save(self, *args, **kwargs):
    #     if self.start_date and self.end_date:
    #         delta = (self.end_date - self.start_date).days + 1  # Add 1 to include both start and end date

    #         # If it's a half-day leave, count it as 0.5 day
    #         if self.dis_half_day:
    #             self.number_of_days = 0.5
    #         else:
    #             self.number_of_days = delta
        
    #     if self.status == 'approved' and not self.pk:
    #         # Calculate leave days based on whether it's a half-day or full-day leave
    #         if self.dis_half_day:
    #             leave_days = 0.5
    #         else:
    #             leave_balance = emp_leave_balance.objects.get(employee=self.employee, leave_type=self.leave_type)
    #             leave_days = leave_balance.get_leave_days(self.start_date, self.end_date, include_weekends_holidays=self.leave_type.include_weekend_and_holiday)

    #         # Deduct the calculated leave days from the employee's leave balance
    #         leave_balance.deduct_leave(leave_days)

        # # Perform proration calculation if necessary
        # if self.leave_type.leave_entitlement.prorate_accrual:
        #     accrual_transaction = leave_accrual_transaction.objects.create(
        #         employee=self.employee,
        #         leave_type=self.leave_type,
        #         accrual_date=datetime.now(),
        #         amount=self.leave_type.leave_entitlement.calculate_prorated_leave()
        #     )
        #     accrual_transaction.save()

        # # Deduct the appropriate amount of leave based on half-day or full-day leave
        # leave_balance = emp_leave_balance.objects.get(employee=self.employee, leave_type=self.leave_type)
        
        # if self.dis_half_day and self.leave_type.allow_half_day:
        # # Deduct half a day if allowed and the request is for half-day leave
        #     self.employee.leave_balance.deduct_leave(is_half_day=True)
        # else:
        #     # Deduct full day leave
        #     self.employee.leave_balance.deduct_leave()

        # super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} from {self.start_date} to {self.end_date}"
    
    # def get_employee_requests(employee_id):
    #     return employee_leave_request.objects.filter(employee_id=employee_id).order_by('-applied_on')
     
    def move_to_next_level(self):
        if self.approvals.filter(status=LeaveApproval.REJECTED).exists():
            self.status = 'Rejected'
            self.save()

            # Notify rejection
            notification = LvApprovalNotify.objects.create(
                recipient_user=self.created_by,
                message=f"Your request for  {self.leave_type} has been rejected."
            )
            notification.send_email_notification('request_rejected', {
                'request_type': self.leave_type,
                'rejection_reason': 'Reason for rejection...',
                'emp_gender': self.employee.emp_gender,
                'emp_date_of_birth': self.employee.emp_date_of_birth,
                'emp_personal_email': self.employee.emp_personal_email,
                'emp_company_email': self.employee.emp_company_email,
                'emp_branch_name': self.employee.emp_branch_id,
                'emp_department_name': self.employee.emp_dept_id,
                'emp_designation_name': self.employee.emp_desgntn_id,
            })

            if self.employee:
                notification = LvApprovalNotify.objects.create(
                    recipient_employee=self.employee,
                    message=f"Request {self.leave_type} has been rejected."
                )
                notification.send_email_notification('request_rejected', {
                    'request_type': self.leave_type,
                    'rejection_reason': 'Reason for rejection...',
                    'emp_gender': self.employee.emp_gender,
                    'emp_date_of_birth': self.employee.emp_date_of_birth,
                    'emp_personal_email': self.employee.emp_personal_email,
                    'emp_company_email': self.employee.emp_company_email,
                    'emp_branch_name': self.employee.emp_branch_id,
                    'emp_department_name': self.employee.emp_dept_id,
                    'emp_designation_name': self.employee.emp_desgntn_id,
                })
            return

        current_approved_levels = self.approvals.filter(status=LeaveApproval.APPROVED).count()

        if self.leave_type.use_common_workflow:
            next_level = LvCommonWorkflow.objects.filter(level=current_approved_levels + 1).first()
        else:
            next_level = LeaveApprovalLevels.objects.filter(request_type=self.leave_type, level=current_approved_levels + 1).first()

        if next_level:
            last_approval = self.approvals.order_by('-level').first()
            LeaveApproval.objects.create(
                leave_request=self,
                approver=next_level.approver,
                role=next_level.role,
                level=next_level.level,
                status=LeaveApproval.PENDING,
                note=last_approval.note if last_approval else None
            )

            # Notify next approver
            notification = LvApprovalNotify.objects.create(
                recipient_user=next_level.approver,
                message=f"New request for approval: {self.leave_type}, employee: {self.employee}"
            )
            notification.send_email_notification('request_created', {
                'request_type': self.leave_type,
                'employee_name': self.employee.emp_first_name,
                'reason': self.reason,
                'note': last_approval.note if last_approval else None,
                'emp_gender': self.employee.emp_gender,
                'emp_date_of_birth': self.employee.emp_date_of_birth,
                'emp_personal_email': self.employee.emp_personal_email,
                'emp_company_email': self.employee.emp_company_email,
                'emp_branch_name': self.employee.emp_branch_id,
                'emp_department_name': self.employee.emp_dept_id,
                'emp_designation_name': self.employee.emp_desgntn_id,
            })
        else:
            self.status = 'Approved'
            self.save()

            # Notify the creator about approval
            notification = LvApprovalNotify.objects.create(
                recipient_user=self.created_by,
                message=f"Your request {self.leave_type} has been approved."
            )
            notification.send_email_notification('request_approved', {
                'request_type': self.leave_type,
                'emp_gender': self.employee.emp_gender,
                'emp_date_of_birth': self.employee.emp_date_of_birth,
                'emp_personal_email': self.employee.emp_personal_email,
                'emp_company_email': self.employee.emp_company_email,
                'emp_branch_name': self.employee.emp_branch_id,
                'emp_department_name': self.employee.emp_dept_id,
                'emp_designation_name': self.employee.emp_desgntn_id,
            })

            if self.employee:
                notification = LvApprovalNotify.objects.create(
                    recipient_employee=self.employee,
                    message=f"Request {self.leave_type} has been approved."
                )
                notification.send_email_notification('request_approved', {
                    'request_type': self.leave_type,
                    'emp_gender': self.employee.emp_gender,
                    'emp_date_of_birth': self.employee.emp_date_of_birth,
                    'emp_personal_email': self.employee.emp_personal_email,
                    'emp_company_email': self.employee.emp_company_email,
                    'emp_branch_name': self.employee.emp_branch_id,
                    'emp_department_name': self.employee.emp_dept_id,
                    'emp_designation_name': self.employee.emp_desgntn_id,
                })
    
class LvRejectionReason(models.Model):
    reason_text = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.reason_text

class LeaveApprovalLevels(models.Model):
    level = models.IntegerField()
    role = models.CharField(max_length=50, null=True, blank=True)  # Use this for role-based approval like 'CEO' or 'Manager'
    approver = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)  # Use this for user-based approval
    request_type = models.ForeignKey('leave_type', related_name='leave_approval_levels', on_delete=models.CASCADE, null=True, blank=True)  # Nullable for common workflow
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
    rejection_reason = models.ForeignKey(LvRejectionReason,null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def approve(self,note=None):
        self.status = self.APPROVED
        if note:
            self.note = note
        self.save()
        self.leave_request.move_to_next_level()
   
    # def reject(self,note=None):
    #     self.status = self.REJECTED
    #     if note:
    #         self.note = note
    #     self.save()
    #     self.leave_request.status = 'Rejected'
    #     self.leave_request.save()
    def reject(self, rejection_reason, note=None):
        if rejection_reason:
            self.rejection_reason = rejection_reason
        self.status = self.REJECTED
        if note:
            self.note = note
        self.save()
        self.leave_request.status = 'Rejected'
        self.leave_request.save()

        notification = LvApprovalNotify.objects.create(
            recipient_user=self.leave_request.created_by,
            message=f"Your request {self.leave_request} has been rejected."
        )
        notification.send_email_notification('request_rejected', {
            'request_type': self.leave_request,
            'rejection_reason': self.rejection_reason.reason_text if self.rejection_reason else "No reason provided",  # Add actual reason if available
            'emp_gender': self.leave_request.employee.emp_gender,
            'emp_date_of_birth': self.leave_request.employee.emp_date_of_birth,
            'emp_personal_email': self.leave_request.employee.emp_personal_email,
            'emp_company_email': self.leave_request.employee.emp_company_email,
            'emp_branch_name': self.leave_request.employee.emp_branch_id,
            'emp_department_name': self.leave_request.employee.emp_dept_id,
            'emp_designation_name': self.leave_request.employee.emp_desgntn_id,
            'emp_hired_date':self.leave_request.employee.emp_hired_date,

        })

        if self.leave_request.employee:
            notification = LvApprovalNotify.objects.create(
                recipient_employee=self.leave_request.employee,
                message=f"Request {self.leave_request} has been rejected."
            )
            notification.send_email_notification('request_rejected', {
            'request_type': self.leave_request,
            'rejection_reason': self.rejection_reason.reason_text if self.rejection_reason else "No reason provided",  # Add actual reason if available
            'emp_gender': self.leave_request.employee.emp_gender,
            'emp_date_of_birth': self.leave_request.employee.emp_date_of_birth,
            'emp_personal_email': self.leave_request.employee.emp_personal_email,
            'emp_company_email': self.leave_request.employee.emp_company_email,
            'emp_branch_name': self.leave_request.employee.emp_branch_id,
            'emp_department_name': self.leave_request.employee.emp_dept_id,
            'emp_designation_name': self.leave_request.employee.emp_desgntn_id,
            'emp_hired_date':self.leave_request.employee.emp_hired_date,

        })

@receiver(post_save, sender=employee_leave_request)
def create_initial_approval(sender, instance, created, **kwargs):
    if created:
        if instance.leave_type.use_common_workflow:
            first_level = LvCommonWorkflow.objects.order_by('level').first()
        else:
        # Select the first approval level
            first_level = LeaveApprovalLevels.objects.filter(request_type=instance.leave_type).order_by('level').first()

        if first_level:
            # Prevent duplicate creation of approvals at the same level
            if not instance.approvals.filter(level=first_level.level).exists():
                LeaveApproval.objects.create(
                    leave_request=instance,
                    approver=first_level.approver,
                    role=first_level.role,
                    level=first_level.level,
                    status=LeaveApproval.PENDING
                )
            # Notify first approver
            notification = LvApprovalNotify.objects.create(
                recipient_user=first_level.approver,
                message=f"New request for approval: {instance.leave_type}, employee: {instance.employee}"
            )
            notification.send_email_notification('request_created', {
                'request_type': instance.leave_type,
                'employee_name': instance.employee.emp_first_name,
                'reason': instance.reason,
                'emp_gender':instance.employee.emp_gender,
                'emp_date_of_birth':instance.employee.emp_date_of_birth,
                'emp_personal_email':instance.employee.emp_personal_email,
                'emp_company_email':instance.employee.emp_company_email,
                'emp_branch_name':instance.employee.emp_branch_id,
                'emp_department_name':instance.employee.emp_dept_id,
                'emp_designation_name':instance.employee.emp_desgntn_id,
            }) 


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
    
class LeaveApprovalReport(models.Model):
    file_name = models.CharField(max_length=100,null=True,unique=True)
    report_data = models.FileField(upload_to='leave_approval_report/', null=True, blank=True)
    class Meta:
        permissions = (
            ('export_report', 'Can export report'),
            # Add more custom permissions here
        )
       
    def __str__(self):
        return self.file_name 

class AttendanceReport(models.Model):
    file_name = models.CharField(max_length=100,null=True,unique=True)
    report_data = models.FileField(upload_to='attendance_report/', null=True, blank=True)
    class Meta:
        permissions = (
            ('export_report', 'Can export report'),
            # Add more custom permissions here
        )
       
    def __str__(self):
        return self.file_name 

class lvBalanceReport(models.Model):
    file_name = models.CharField(max_length=100,null=True,unique=True)
    report_data = models.FileField(upload_to='lvbalance_report/', null=True, blank=True)
    class Meta:
        permissions = (
            ('export_report', 'Can export report'),
            # Add more custom permissions here
        )
       
    def __str__(self):
        return self.file_name

    
    
    
    

    
    
    