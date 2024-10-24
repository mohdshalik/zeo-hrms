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
from EmpManagement.models import Approval,RequestNotification




class company(TenantBase):
    name = models.CharField(max_length=100)
    paid_until =  models.DateField(auto_now_add=True)
    # on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True
    def __str__(self):
        return self.schema_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create corresponding domain entry
        domain_name = self.schema_name + ".localhost"
        Domain.objects.create(domain=domain_name, tenant=self)

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
    def get_approvals(self):
        # Fetch approvals assigned to this user
        return Approval.objects.filter(approver=self).order_by('-created_at')
    
    def get_requestsnotification(self):
        # Fetch approvals assigned to this user
        return RequestNotification.objects.filter(recipient_user=self).order_by('-created_at')
    def get_lv_approvals(self):
        from LeaveManagement.models import LeaveApproval
        # Fetch approvals assigned to this user
        return LeaveApproval.objects.filter(approver=self).order_by('-created_at')
