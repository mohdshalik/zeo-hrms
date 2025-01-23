from django.db import models
from OrganisationManager.models import brnch_mstr
# Create your models here.
from django.contrib.auth.models import AbstractUser,AbstractBaseUser,BaseUserManager,PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from .manager import CustomUserManager
from django.contrib.auth import get_user_model
import uuid
from tenant_users.tenants.models import TenantBase,UserProfile
# from tenant_users.tenants.tasks import provision_tenant
from django_tenants.models import TenantMixin, DomainMixin
from tenant_users.tenants.models import UserTenantPermissions
import re

from django_tenants.utils import schema_context

class company(TenantBase):
    name = models.CharField(max_length=100)
    paid_until =  models.DateField(auto_now_add=True)
    created_on = models.DateField(auto_now_add=True)
    country=models.ForeignKey('Core.cntry_mstr',on_delete=models.CASCADE)
    logo= models.ImageField(null=True,blank =True )

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def get_timezone(self):
        return self.country.timezone if self.country else 'UTC'
    
    def save(self, *args, **kwargs):
        # if self.name:
        #     self.schema_name = self.name.replace(' ', '_')
        if self.name:
            # Sanitize name to create a valid schema name
            sanitized_name = re.sub(r'[^a-zA-Z0-9]+', '_', self.name.lower())  # Replace invalid characters with '_'
            self.schema_name = re.sub(r'_+', '_', sanitized_name).strip('_')  # Avoid continuous underscores and trim

        super().save(*args, **kwargs)  # Save the company and create the schema

        # Check if Domain exists (optional, using a Manager)
        if not Domain.objects.filter(domain=f"{self.schema_name}.localhost").exists():
            Domain.objects.create(domain=f"{self.schema_name}.localhost", tenant=self)

        # Switch to the newly created schema using schema_context
        with schema_context(self.schema_name):
            # Create the branch within the company's schema
            brnch_mstr.objects.create(
        branch_name=self.name,
        branch_logo=self.logo,
        branch_code='BR001',  # Provide a default or unique branch code
        notification_period_days=30,  # Provide a value for non-nullable field
        # branc_logo=None,  # This can be optional
        br_country_id=1,  # Set the country or use default ID
        # br_state_id=1,  # Set the state or use default ID
        br_city='Sample City',
        br_pincode='123456',
        br_branch_nmbr_1='BR-0001',  # Provide a unique branch number
        br_branch_mail='branch@example.com',  # Provide a valid email
    )

    def __str__(self):
        return self.schema_name
    
class Domain(DomainMixin):
    pass


class CustomUser(UserProfile):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(
        ("Email Address"),
        unique=True,
        blank=True,  # Allow email to be optional
        null=True,   # Allow email to be optional
    )
    is_ess = models.BooleanField(default=False, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'  # Authentication uses username
    REQUIRED_FIELDS = []  # No required fields other than username

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # Set is_active to True before saving
        self.is_active = True
        super().save(*args, **kwargs)
    
    # Add any additional fields if needed

