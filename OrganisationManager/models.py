from django.db import models
from EmpManagement.models import emp_master
from datetime import datetime, timedelta
from EmpManagement .models import Emp_CustomField


#branch model
class brnch_mstr(models.Model):
    branch_name               = models.CharField(max_length=100)
    branch_code               = models.CharField(max_length=50,unique=True)
    branch_logo               = models.ImageField(null=True)
    notification_period_days  = models.IntegerField()
    br_start_date             = models.DateField(null=True)
    branch_users              = models.ManyToManyField("UserManagement.CustomUser",related_name='branches')
    br_is_active              = models.BooleanField(default=True)
    br_state_id               = models.ForeignKey("Core.state_mstr",on_delete=models.CASCADE,null=True)  
    br_city                   = models.CharField(max_length=50)
    br_pincode                = models.CharField(max_length=20)
    br_branch_nmbr_1          = models.CharField(max_length=20,unique=True)
    br_branch_nmbr_2          = models.CharField(max_length=20,blank=True, null=True)
    br_branch_mail            = models.EmailField(unique=True)
    br_country                = models.ForeignKey("Core.cntry_mstr",on_delete=models.SET_DEFAULT, default="1", null=True) 
    br_created_at             = models.DateTimeField(auto_now_add=True)
    br_created_by             = models.ForeignKey('UserManagement.CustomUser', on_delete=models.CASCADE, null=True, related_name='%(class)s_created_by')
    br_updated_at             = models.DateTimeField(auto_now=True)
    br_updated_by             = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    def __str__(self):
        return self.branch_name
    

#departments model
class dept_master(models.Model):
    dept_name        = models.CharField(max_length=50)
    dept_code        = models.CharField(max_length=50,unique=True)
    dept_description = models.CharField(max_length=200)
    dept_created_at  = models.DateTimeField(auto_now_add=True)
    dept_created_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    dept_updated_at  = models.DateTimeField(auto_now=True)
    dept_updated_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    dept_is_active   = models.BooleanField(default=True)
    branch_id = models.ForeignKey("brnch_mstr", on_delete=models.SET_NULL, null=True)
    
    # Method to fetch all department users
    def get_department_users(self):
        # You can customize this to fetch relevant users within the department
        return 'UserManagement.CustomUser'.objects.filter(department=self, is_active=True)


    def __str__(self):
        return self.dept_name

#designation master
class desgntn_master(models.Model):
    desgntn_job_title   =  models.CharField(max_length=50)
    desgntn_code        = models.CharField(max_length=50,unique=True)
    desgntn_description = models.CharField(max_length=200)
    desgntn_created_at  = models.DateTimeField(auto_now_add=True)
    desgntn_created_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    desgntn_updated_at  = models.DateTimeField(auto_now=True)
    desgntn_updated_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    desgntn_is_active   = models.BooleanField(default=True)
    def __str__(self):
        return self.desgntn_job_title

#CATOGARY master
class ctgry_master(models.Model):
    ctgry_title       =  models.CharField(max_length=50)
    ctgry_code        = models.CharField(max_length=50,unique=True)    
    ctgry_description = models.CharField(max_length=200)
    ctgry_created_at  = models.DateTimeField(auto_now_add=True)
    ctgry_created_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    ctgry_updated_at  = models.DateTimeField(auto_now=True)
    ctgry_updated_by  = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    ctgry_is_active   = models.BooleanField(default=True)
    def __str__(self):
        return self.ctgry_title

class FiscalYear(models.Model):
    branch_id  = models.ForeignKey("brnch_mstr",on_delete=models.CASCADE)
    name       = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date   = models.DateField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


class FiscalPeriod(models.Model):
    fiscal_year   = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    period_number = models.PositiveIntegerField()
    start_date    = models.DateField()
    end_date      = models.DateField()
    branch        = models.ForeignKey("brnch_mstr", on_delete=models.CASCADE, related_name='fiscal_periods')
    class Meta:
        unique_together = ('fiscal_year', 'period_number')

class document_numbering(models.Model):
    DOCUMENT_TYPES = [
        ('general_request', 'General Request'),
        ('leave_request', 'Leave Request'),
        # Add other types as needed
    ]
    branch_id              = models.ForeignKey('brnch_mstr',on_delete=models.CASCADE)
    category               = models.ForeignKey('ctgry_master',on_delete=models.CASCADE)
    type                   = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    user                   = models.ForeignKey('UserManagement.CustomUser',on_delete=models.CASCADE)
    automatic_numbering    = models.BooleanField()
    preffix                = models.CharField(unique=True,max_length=50)
    suffix                 = models.CharField(max_length=50)
    year                   = models.DateField()
    start_number           = models.IntegerField()
    current_number         = models.IntegerField()
    end_number             = models.IntegerField()
    created_at             = models.DateTimeField(auto_now_add=True)
    created_by             = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    class Meta:
        unique_together = ('branch_id', 'category', 'type')
    def str(self):
        return f"{self.branch_id.branch_name} - {self.category.ctgry_title} - {self.type}"
    

class CompanyPolicy(models.Model):
    title           = models.CharField(max_length=200)
    description     = models.TextField()
    policy_file     = models.FileField(upload_to='policies/')
    branch          = models.ForeignKey('brnch_mstr',on_delete=models.CASCADE, related_name='policies')
    department      = models.ForeignKey('dept_master', on_delete=models.CASCADE, related_name='policies', blank=True, null=True)
    category        = models.ForeignKey('ctgry_master', on_delete=models.CASCADE, related_name='policies', blank=True, null=True)
    # specific_employees = models.ManyToManyField(emp_master, blank=True)
    specific_users  = models.ManyToManyField('UserManagement.CustomUser', blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    created_by     = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    def __str__(self):
        return self.title
    
class AssetMaster(models.Model):
    name               = models.CharField(max_length=255)
    description        = models.TextField(blank=True, null=True)
    total_quantity     = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


    def __str__(self):
        return self.name
class AssetTransaction(models.Model):
    ISSUE = 'ISSUE'
    RETURN = 'RETURN'

    TRANSACTION_TYPE_CHOICES = [
        (ISSUE, 'Issue'),
        (RETURN, 'Return'),
    ]

    employee         = models.ForeignKey(emp_master, on_delete=models.CASCADE, related_name="asset_transactions")
    asset            = models.ForeignKey(AssetMaster, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    quantity         = models.PositiveIntegerField()
    date             = models.DateField(auto_now_add=True)
    remarks          = models.TextField(blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')


    def __str__(self):
        return f"{self.transaction_type} - {self.asset.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        # Update available quantity in AssetMaster
        if self.transaction_type == self.ISSUE:
            self.asset.available_quantity -= self.quantity
        elif self.transaction_type == self.RETURN:
            self.asset.available_quantity += self.quantity

        self.asset.save()
        super().save(*args, **kwargs)

class Asset_CustomFieldValue(models.Model):
    asset_custom_field = models.CharField(max_length=100)
    field_value      = models.TextField(null=True, blank=True)  # Field value provided by end user
    asset_master      = models.ForeignKey('AssetMaster', on_delete=models.CASCADE, related_name='custom_field_values',null=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    created_by         = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')

    def __str__(self):
        return f'{self.asset_custom_field.emp_custom_field}: {self.field_value}'
    
    def save(self, *args, **kwargs):
        if not self.asset_custom_field:
            raise ValueError("Field name cannot be None or empty.")
        if not Emp_CustomField.objects.filter(emp_custom_field=self.asset_custom_field).exists():
            raise ValueError(f"Field name '{self.asset_custom_field}' does not exist in Emp_CustomField.")

        # Check if a custom field value already exists for the same emp_master and emp_custom_field
        existing_value = Asset_CustomFieldValue.objects.filter(
            emp_custom_field=self.asset_custom_field,
            emp_master=self.emp_master
        ).first()

        if existing_value:
            # If it exists, update the existing record instead of creating a new one
            existing_value.field_value = self.field_value
            # Use update() to avoid calling save() and prevent recursion
            Asset_CustomFieldValue.objects.filter(
                id=existing_value.id
            ).update(field_value=self.field_value)
        else:
            # Call full_clean to ensure that the clean method is called
            self.full_clean()
            super().save(*args, **kwargs)
