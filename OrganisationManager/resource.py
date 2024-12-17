from import_export import resources,fields
from import_export.admin import ImportMixin
from import_export.signals import post_import
from import_export.fields import Field
from .models import brnch_mstr,dept_master,desgntn_master,ctgry_master

class BranchResource(resources.ModelResource):
    class Meta:
        model = brnch_mstr
       
        fields = ('id',
                  'branch_name',
                  'branch_code',
                  'br_notification_period_days',
                  'br_start_date',
                  'br_is_active',
                  'br_country',
                  'br_state_id',
                  'br_city',
                  'br_pincode',
                  'br_branch_nmbr_1',
                  'br_branch_nmbr_2',
                  'br_branch_mail',
                                                            
        )

class DepartmentResource(resources.ModelResource):
    dept_name = fields.Field(attribute='dept_name', column_name='Department Name')
    dept_code = fields.Field(attribute='dept_code', column_name='Department Code')
    dept_description = fields.Field(attribute='dept_description', column_name='Description')
    dept_is_active = fields.Field(attribute='dept_is_active', column_name='Active')
    class Meta:
        model = dept_master
       
        fields = (
                  'dept_name',
                  'dept_code',
                  'dept_description',
                  'dept_is_active',
        ) 
        import_id_fields = ()

class DeptReportResource(resources.ModelResource):
    dept_name = fields.Field(attribute='dept_name', column_name='Department Name')
    dept_code = fields.Field(attribute='dept_code', column_name='Department Code')
    dept_description = fields.Field(attribute='dept_description', column_name='Description')
    dept_is_active = fields.Field(attribute='dept_is_active', column_name='Active')
    class Meta:
        model = dept_master
       
        fields = (
                  'dept_name',
                  'dept_code',
                  'dept_description',
                  'dept_is_active',
        ) 
class DesignationResource(resources.ModelResource):
    desgntn_job_title = fields.Field(attribute='desgntn_job_title', column_name='Designation')
    desgntn_code = fields.Field(attribute='desgntn_code', column_name='Designation Code')
    desgntn_description = fields.Field(attribute='desgntn_description', column_name='Description')
    desgntn_is_active = fields.Field(attribute='desgntn_is_active', column_name='Active')


    class Meta:
        model = desgntn_master
       
        fields = (
                  'desgntn_job_title',
                  'desgntn_code',
                  'desgntn_description',
                  'desgntn_is_active',
                  
        )  
        import_id_fields = ()           
class DesgtnReportResource(resources.ModelResource):
    desgntn_job_title = fields.Field(attribute='desgntn_job_title', column_name='Designation')
    desgntn_code = fields.Field(attribute='desgntn_code', column_name='Designation Code')
    desgntn_description = fields.Field(attribute='desgntn_description', column_name='Description')
    desgntn_is_active = fields.Field(attribute='desgntn_is_active', column_name='Active')

    class Meta:
        model = desgntn_master
       
        fields = (
                  'desgntn_job_title',
                  'desgntn_code',
                  'desgntn_description',
                  'desgntn_is_active',
                  
        )  


class CategoryResource(resources.ModelResource):
    class Meta:
        model = ctgry_master
       
        fields = ('id',
                  'ctgry_title',
                  'ctgry_code',
                  'ctgry_description',
                  'ctgry_is_active',
                  
        )       


        