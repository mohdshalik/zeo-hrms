from django.db import models
from EmpManagement.models import emp_master
from datetime import datetime, timedelta


#branch model
class brnch_mstr(models.Model):
    branch_name = models.CharField(max_length=100)
    branch_code = models.CharField(max_length=50,unique=True,null=True,blank =True)
    notification_period_days = models.IntegerField()
    br_start_date = models.DateField(null=True)
    branch_users = models.ManyToManyField("UserManagement.CustomUser",related_name='branches')
    br_is_active = models.BooleanField(default=True)
    # country_id = models.ForeignKey('cntry_mstr',on_delete = models.CASCADE)
    br_state_id = models.ForeignKey("Core.state_mstr",on_delete=models.SET_DEFAULT, default="1", null=True)  
    br_city = models.CharField(max_length=50)
    br_pincode = models.CharField(max_length=20)
    br_branch_nmbr_1 = models.CharField(max_length=20,unique=True)
    br_branch_nmbr_2 = models.CharField(max_length=20,blank=True, null=True)
    br_branch_mail = models.EmailField(unique=True)
    br_country = models.ForeignKey("Core.cntry_mstr",on_delete=models.SET_DEFAULT, default="1", null=True) 
    br_created_at = models.DateTimeField(auto_now_add=True)
    br_created_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.CASCADE, null=True, related_name='%(class)s_created_by')
    br_updated_at = models.DateTimeField(auto_now=True)
    br_updated_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    def __str__(self):
        return self.branch_name
    

#departments model
class dept_master(models.Model):
    dept_name = models.CharField(max_length=50)
    dept_code = models.CharField(max_length=50,unique=True,null=True,blank =True)
    dept_description = models.CharField(max_length=200)
    dept_created_at = models.DateTimeField(auto_now_add=True)
    dept_created_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    dept_updated_at = models.DateTimeField(auto_now=True)
    dept_updated_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    dept_is_active = models.BooleanField(default=True)
    branch_id = models.ForeignKey("brnch_mstr", on_delete=models.SET_NULL, null=True)
    
    # Method to fetch all department users
    def get_department_users(self):
        # You can customize this to fetch relevant users within the department
        return 'UserManagement.CustomUser'.objects.filter(department=self, is_active=True)


    def __str__(self):
        return self.dept_name

#designation master
class desgntn_master(models.Model):
    desgntn_job_title =  models.CharField(max_length=50)
    desgntn_code = models.CharField(max_length=50,unique=True,null=True,blank =True)
    desgntn_description = models.CharField(max_length=200)
    desgntn_created_at = models.DateTimeField(auto_now_add=True)
    desgntn_created_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    desgntn_updated_at = models.DateTimeField(auto_now=True)
    desgntn_updated_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    desgntn_is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.desgntn_job_title

#CATOGARY master
class ctgry_master(models.Model):
    ctgry_title =  models.CharField(max_length=50)
    ctgry_code = models.CharField(max_length=50,unique=True,null=True,blank =True)    
    ctgry_description = models.CharField(max_length=200)
    ctgry_created_at = models.DateTimeField(auto_now_add=True)
    ctgry_created_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    ctgry_updated_at = models.DateTimeField(auto_now=True)
    ctgry_updated_by = models.ForeignKey('UserManagement.CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated_by')
    ctgry_is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.ctgry_title

class FiscalYear(models.Model):
    branch_id = models.ForeignKey("brnch_mstr",on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date=models.DateField(blank=True,null=True)

class FiscalPeriod(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    period_number = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    branch = models.ForeignKey("brnch_mstr", on_delete=models.CASCADE, related_name='fiscal_periods')
    class Meta:
        unique_together = ('fiscal_year', 'period_number')


class document_numbering(models.Model):
    branch_id=models.ForeignKey('brnch_mstr',on_delete=models.CASCADE)
    category=models.ForeignKey('ctgry_master',on_delete=models.CASCADE)
    user=models.ForeignKey('UserManagement.CustomUser',on_delete=models.CASCADE)
    automatic_numbering=models.BooleanField()
    preffix=models.CharField(unique=True,max_length=50)
    suffix=models.CharField(max_length=50)
    year=models.DateField()
    start_number=models.IntegerField()
    current_number=models.IntegerField()
    end_number=models.IntegerField()
    # class Meta:
    #     unique_together = ('branch_id')  # Ensure unique constraint on branch and category


class CompanyPolicy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    policy_file = models.FileField(upload_to='policies/')
    branch = models.ForeignKey('brnch_mstr',on_delete=models.CASCADE, related_name='policies')
    department = models.ForeignKey('dept_master', on_delete=models.CASCADE, related_name='policies', blank=True, null=True)
    category = models.ForeignKey('ctgry_master', on_delete=models.CASCADE, related_name='policies', blank=True, null=True)
    # specific_employees = models.ManyToManyField(emp_master, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
# class Shift(models.Model):
#     name = models.CharField(max_length=50)
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     break_duration = models.DurationField()

# class Attendance(models.Model):
#     employee = models.ForeignKey("EmpManagement.emp_master", on_delete=models.CASCADE)
#     shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True)
#     check_in_time = models.DateTimeField()
#     check_out_time = models.DateTimeField(null=True, blank=True)
#     date = models.DateField(auto_now_add=True)
#     total_hours = models.DurationField(null=True, blank=True)

#     def calculate_total_hours(self):
#         if self.check_in_time and self.check_out_time:
#             return self.check_out_time - self.check_in_time
#         return None

#     def save(self, *args, **kwargs):
#         # Automatically calculate total hours on save
#         self.total_hours = self.calculate_total_hours()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.employee.username} - {self.date}"



# class Attendance(models.Model):
#     employee = models.ForeignKey("EmpManagement.emp_master", on_delete=models.CASCADE)
#     date = models.DateField()
#     check_in = models.TimeField(null=True, blank=True)
#     check_out = models.TimeField(null=True, blank=True)
#     total_hours = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

#     class Meta:
#         unique_together = ('employee', 'date')
    
#     def __str__(self):
#         return f"{self.employee} - {self.date}"

#     def calculate_total_hours(self):
#         if self.check_in and self.check_out:
#             # Ensure check_in and check_out are time fields
#             if isinstance(self.check_in, datetime):
#                 check_in_time = self.check_in.time()
#             else:
#                 check_in_time = self.check_in

#             if isinstance(self.check_out, datetime):
#                 check_out_time = self.check_out.time()
#             else:
#                 check_out_time = self.check_out

#             # Combine the date with check_in and check_out times
#             check_in_datetime = datetime.combine(self.date, check_in_time)
#             check_out_datetime = datetime.combine(self.date, check_out_time)

#             # Handle the case where check_out is after midnight
#             if check_out_datetime < check_in_datetime:
#                 check_out_datetime += timedelta(days=1)

#             # Calculate the total seconds worked
#             total_seconds = (check_out_datetime - check_in_datetime).total_seconds()

#             # Convert seconds to hours (with full precision)
#             self.total_hours = total_seconds / 3600
#             self.save()

#     def __str__(self):
#         return f"{self.employee} - {self.date}"