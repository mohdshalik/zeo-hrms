from django.db import models
from OrganisationManager.models import brnch_mstr
# Create your models here.
from django.contrib.auth.models import AbstractUser,AbstractBaseUser,BaseUserManager

from phonenumber_field.modelfields import PhoneNumberField
from .manager import CustomUserManager
from django.contrib.auth.models import User,Group
from django.contrib.auth import get_user_model
import uuid
from tenant_users.tenants.models import TenantBase,UserProfile
from tenant_users.tenants.tasks import provision_tenant
from django_tenants.models import TenantMixin, DomainMixin
from django_tenants.utils import schema_context






class company(TenantBase):
    name = models.CharField(max_length=100)
    paid_until = models.DateField(auto_now_add=True)
    created_on = models.DateField(auto_now_add=True)
    country = models.ForeignKey('Core.cntry_mstr', on_delete=models.CASCADE)
    logo = models.ImageField(null=True, blank=True)

    # Ensures schema is automatically created
    auto_create_schema = True

    def get_timezone(self):
        return self.country.timezone if self.country else 'UTC'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the company and create the schema

        # Ensure a domain exists for the tenant
        if not Domain.objects.filter(domain=f"{self.schema_name}.localhost").exists():
            Domain.objects.create(domain=f"{self.schema_name}.localhost", tenant=self)

        # Switch to the newly created schema
        with schema_context(self.schema_name):
            # Set up the timezone for the tenant's schema
            from django.conf import settings
            settings.TIME_ZONE = self.get_timezone()

            # Create the default branch
            brnch_mstr.objects.create(
                branch_name=self.name,
                branch_logo=self.logo,
                branch_code='BR001',
                notification_period_days=30,
                br_country_id=self.country.id,
                br_city='Sample City',
                br_pincode='123456',
                br_branch_nmbr_1='BR-0001',
                br_branch_mail='branch@example.com',
            )

class Domain(DomainMixin):
    pass
class CustomUser(UserProfile):
    username = models.CharField(max_length=150,unique=True)
    email = models.EmailField(("email address"), unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Added max_length for ContactNumber field
    is_ess = models.BooleanField(default=False,null=True,blank =True)
    # approvals = models.ManyToManyField('EmpManagement.Approval', related_name='users', blank=True)
    
    USERNAME_FIELD = 'username'  # Change USERNAME_FIELD to 'username'
    REQUIRED_FIELDS = ['email']  # Remove 'username' from REQUIRED_FIELDS
    

    objects = CustomUserManager()
    def save(self, *args, **kwargs):
        # Set is_active to True before saving
        self.is_active = True
        super().save(*args, **kwargs)
    
    # def get_approvals(self):
    #     return Approval.objects.filter(approver=self)
    # def get_approvals(self):
    #     # Fetch approvals assigned to this user
    #     return Approval.objects.filter(approver=self).order_by('-created_at')
    
    