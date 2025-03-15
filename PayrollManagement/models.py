from django.db import models
from EmpManagement.models import emp_master
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
import re
# from calendars .models import LeaveApproval

# Create your models here.
class SalaryComponent(models.Model):
    COMPONENT_TYPES = [
        ('deduction', 'Deduction'),
        ('addition', 'Addition'),
        ('others', 'Others'),
    ]

    name = models.CharField(max_length=100, unique=True)  # Component name (e.g., HRA, PF)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    glcode = models.CharField(max_length=20,null=True)
    # printdiscription= models.CharField(max_length=20,null=True)
    is_fixed = models.BooleanField(default=True, help_text="Is this component fixed (True) or variable (False)?")
    description = models.TextField(blank=True, null=True)

    #hop rules
    affected_by_unpaid_leave = models.BooleanField(default=False,
                                                   help_text="Is this component affected by unpaid leave?")
    affected_by_halfpaid_leave = models.BooleanField(default=False,
                                                     help_text="Is this component affected by half-paid leave?")
    # prorata_calculation = models.BooleanField(default=False, help_text="Should this component use prorata calculation?")
    # is_emi_deduction = models.BooleanField(default=False, help_text="Is this component used for EMI deduction from loan?")


    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"

class EmployeeSalaryStructure(models.Model):
    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE, related_name='salary_structures')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='employee_components')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Amount for this component")
    is_active = models.BooleanField(default=True, help_text="Is this component active for the employee?")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'component')  # Ensure no duplicate components for an employee

    def __str__(self):
        return f"{self.employee} - {self.component.name} ({self.amount})"



class PayrollFormula(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the formula (e.g., 'Net Salary')")
    formula_text = models.TextField(
        help_text="Formula using component names (e.g., 'Basic + HRA - PF'). Use component names as variables."
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def validate_formula(self):
        """Basic validation to ensure formula references valid components."""
        component_names = set(
            SalaryComponent.objects.values_list('name', flat=True)
        )
        # Extract variables from formula (assume simple words for now)
        variables = re.findall(r'[a-zA-Z_]+', self.formula_text)
        invalid_vars = [var for var in variables if var not in component_names and var not in ['+', '-', '*', '/', '(', ')']]
        if invalid_vars:
            raise ValueError(f"Invalid variables in formula: {invalid_vars}")
        return True



class PayrollTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE)
    pay_period_start = models.DateField()  # From Calendar model
    pay_period_end = models.DateField()    # From Calendar model
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("processed", "Processed")],
        default="pending"
    )

    def __str__(self):
        return f"Payroll {self.transaction_id} for {self.employee}"

    class Meta:
        verbose_name = "Payroll Transaction"
        verbose_name_plural = "Payroll Transactions"

    

class Payslip(models.Model):
    payroll = models.OneToOneField(PayrollTransaction, on_delete=models.CASCADE, related_name='payslip')
    issued_date = models.DateTimeField(auto_now_add=True)
    payslip_pdf = models.FileField(upload_to='payslips/', blank=True, null=True, help_text="Generated Payslip PDF")
    created_at         = models.DateTimeField(auto_now_add=True)
    
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    def __str__(self):
        return f"Payslip for {self.payroll.employee} - {self.payroll.period.name}"


class PaySlipComponent(models.Model):
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='components')
    salary_component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.payslip} - {self.salary_component.name}"



class SalaryFormula(models.Model):
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='formulas')
    formula = models.TextField(help_text="Formula for calculating the component amount. Use placeholders for employee attributes.")
    description = models.TextField(blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


    def __str__(self):
        return f"Formula for {self.component.name}"

class LoanCommonWorkflow(models.Model):
    level    = models.IntegerField()
    role     = models.CharField(max_length=50, null=True, blank=True)
    approver = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    created_at         = models.DateTimeField(auto_now_add=True)
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['level'], name='Loan_common_workflow_levels')
        ]
    def __str__(self):
        return f"Level {self.level} - {self.role or self.approver}"
    
class LoanType(models.Model):
    loan_type           = models.CharField(max_length=255)  # e.g., Personal, Housing, Car
    max_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    repayment_period    = models.PositiveIntegerField()  # in months
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    use_common_workflow = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
    created_by          = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


    def __str__(self):
        return f"{self.loan_type}"

class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Disbursed', 'Disbursed'),
        ('Rejected', 'Rejected'),
        ('Paused', 'Paused'),
        ('In Progress', 'In Progress'),
        ('Closed', 'Closed'),

    ]

    employee = models.ForeignKey('EmpManagement.emp_master', on_delete=models.CASCADE)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    repayment_period = models.PositiveIntegerField()  # In months
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    pause_start_date = models.DateField(null=True, blank=True)
    resume_date = models.DateField(null=True, blank=True)
    pause_reason = models.TextField(null=True, blank=True)
    def clean(self):
        """
        Custom validation to ensure no duplicate active loans of the same type.
        """
        # Check for existing loans of the same type for the same employee
        existing_loans = LoanApplication.objects.filter(
            employee=self.employee,
            loan_type=self.loan_type,
            status__in=['Pending', 'Approved', 'Disbursed', 'Paused', 'In Progress']
        ).exclude(pk=self.pk)  # Exclude the current instance during update

        if existing_loans.exists():
            raise ValidationError(
                f"An active loan of type '{self.loan_type}' already exists for this employee."
            )

    def save(self, *args, **kwargs):
        self.clean()
        """Override save to initialize remaining balance and EMI."""
        if self.amount_requested and self.repayment_period and not self.emi_amount:
            self.emi_amount = round(self.amount_requested / self.repayment_period, 2)
        if self.remaining_balance is None:
            self.remaining_balance = self.amount_requested
        super().save(*args, **kwargs)

    # def pause(self, start_date, reason=None):
    #     """Pause the loan repayments."""
    #     self.status = 'Paused'
    #     self.pause_start_date = start_date
    #     self.pause_reason = reason
    #     self.save()

    # def resume(self, resume_date, reason=None):
    #     """Resume the loan repayments."""
    #     if self.status != 'Paused':
    #         raise ValidationError("Loan is not currently paused.")
    #     self.status = 'In Progress'
    #     self.resume_date = resume_date
    #     self.resume_reason = reason
    #     self.save()
    def pause(self, start_date, reason=None):
        """Pause the loan repayments."""
        if self.status not in ['Approved', 'In Progress']:
            raise ValidationError("Only active loans can be paused.")
        self.status = 'Paused'
        self.pause_start_date = start_date
        self.pause_reason = reason
        self.save()

    def resume(self, resume_date, reason=None):
        """Resume the loan repayments."""
        if self.status != 'Paused':
            raise ValidationError("Loan is not currently paused.")
        self.status = 'In Progress'
        self.resume_date = resume_date
        self.resume_reason = reason
        self.save()
        def __str__(self):
            return f"{self.employee} - {self.loan_type} - {self.status}"
      
    
    def move_to_next_level(self):
        if self.approvals.filter(status=LoanApproval.REJECTED).exists():
            self.status = 'Rejected'
            self.save()


        current_approved_levels = self.approvals.filter(status=LoanApproval.APPROVED).count()

        if self.loan_type.use_common_workflow:
            next_level = LoanCommonWorkflow.objects.filter(level=current_approved_levels + 1).first()
        else:
            next_level = LoanApprovalLevels.objects.filter(loan_type=self.loan_type, level=current_approved_levels + 1).first()

        if next_level:
            last_approval = self.approvals.order_by('-level').first()
            LoanApproval.objects.create(
                loan_request=self,
                approver=next_level.approver,
                role=next_level.role,
                level=next_level.level,
                status=LoanApproval.PENDING,
                note=last_approval.note if last_approval else None
            )

        else:
            self.status = 'Approved'
            self.save()

            

class LoanRepayment(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    repayment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    # def save(self, *args, **kwargs):
    #     # Prevent negative balance
    #     if self.remaining_balance < 0:
    #         self.remaining_balance = 0

    #     # Ensure no duplicate repayments for the same date
    #     if LoanRepayment.objects.filter(loan=self.loan, repayment_date=self.repayment_date).exists():
    #         raise ValidationError("Repayment for this date already exists.")

    #     super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        """Ensure repayments don't result in negative balance."""
        if self.remaining_balance < 0:
            self.remaining_balance = 0
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.loan} - {self.repayment_date}"

class LoanApprovalLevels(models.Model):
    level            = models.IntegerField()
    role             = models.CharField(max_length=50, null=True, blank=True)  # Use this for role-based approval like 'CEO' or 'Manager'
    approver         = models.ForeignKey('UserManagement.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)  # Use this for user-based approval
    loan_type        = models.ForeignKey('LoanType', related_name='loan_approval_levels', on_delete=models.CASCADE, null=True, blank=True)  # Nullable for common workflow
    class Meta:
        unique_together = ('level', 'loan_type')

class LoanApproval(models.Model):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    loan_request         = models.ForeignKey(LoanApplication, related_name='approvals', on_delete=models.CASCADE,null=True, blank=True)
    approver             = models.ForeignKey('UserManagement.CustomUser', on_delete=models.CASCADE)
    role                 = models.CharField(max_length=50, null=True, blank=True)
    level                = models.IntegerField(default=1)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES,default=PENDING)
    note                 = models.TextField(null=True, blank=True)
    rejection_reason     = models.TextField(null=True, blank=True)
    created_at           = models.DateField(auto_now_add=True)
    updated_at           = models.DateField(auto_now=True)
    employee_id          = models.IntegerField(null=True, blank=True)

    def approve(self, note=None):
        self.status = self.APPROVED
        if note:
            self.note = note
        self.save()
        if self.loan_request:
            self.loan_request.move_to_next_level()
        

    def reject(self, rejection_reason, note=None):
        if rejection_reason:
            self.rejection_reason = rejection_reason
        self.status = self.REJECTED
        if note:
            self.note = note
        self.save()
        if self.loan_request:
            self.loan_request.status = 'Rejected'
            self.loan_request.save()
        

@receiver(post_save, sender=LoanApplication)
def create_initial_approval(sender, instance, created, **kwargs):
    if created:
        if instance.loan_type.use_common_workflow:
            first_level = LoanCommonWorkflow.objects.order_by('level').first()
        else:
        # Select the first approval level
            first_level = LoanApprovalLevels.objects.filter(loan_type=instance.loan_type).order_by('level').first()

        if first_level:
            # Prevent duplicate creation of approvals at the same level
            if not instance.approvals.filter(level=first_level.level).exists():
                LoanApproval.objects.create(
                    loan_request=instance,
                    approver=first_level.approver,
                    role=first_level.role,
                    level=first_level.level,
                    status=LoanApproval.PENDING,
                    employee_id=instance.employee_id
                )
            