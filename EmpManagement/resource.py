from import_export import resources,fields,widgets
import phonenumbers
from phonenumbers import NumberParseException
from datetime import timedelta,timezone
from datetime import datetime,date
from .models import emp_master, Emp_CustomField,notification,Emp_Documents,LanguageSkill,MarketingSkill,ProgrammingLanguageSkill,Emp_CustomFieldValue
from import_export.widgets import DateWidget
from datetime import datetime
from import_export.widgets import Widget
from django.core.exceptions import ValidationError
from django.db import models
import re
from Core.models import document_type,state_mstr,cntry_mstr,Nationality
from OrganisationManager.models import brnch_mstr,ctgry_master,dept_master,desgntn_master
from import_export.widgets import ForeignKeyWidget

class NumericMobileNumberWidget(Widget):   
    def clean(self, value, row=None, *args, **kwargs):
        # Clean the value - convert it to an integer.    
        if value:
            try:
                return int(value)
            except ValueError:
                raise ValidationError("Mobile number must be numeric.")
        return None

# Custom Date Widget to handle the date format
class MultiTypeWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if value:
            try:
                # Attempt to parse date in the format 'YYYY-MM-DD'
                return datetime.strptime(value, '%d-%m-%y').date()
            except ValueError:
                try:
                    # Attempt to parse date in the format 'YYYY-MM-DD HH:MM:SS'
                    return datetime.strptime(value, '%d-%m-%y %H:%M:%S').date()
                except ValueError:
                    # Return as string if it's not a date
                    return value
        return None

    def render(self, value, obj=None):
        if isinstance(value, datetime):
            return value.strftime('%d-%m-%y')
        return str(value)

class EmployeeResource(resources.ModelResource):
    emp_code = fields.Field(attribute='emp_code', column_name='Employee Code')
    emp_first_name = fields.Field(attribute='emp_first_name', column_name='Employee First Name')
    emp_last_name = fields.Field(attribute='emp_last_name', column_name='Employee Last Name')
    emp_gender = fields.Field(attribute='emp_gender', column_name='Employee Gender')
    emp_date_of_birth = fields.Field(attribute='emp_date_of_birth', column_name='Employee DOB(DD/MM/YYYY)',widget=DateWidget(format='%d/%m/%Y'))
    emp_personal_email = fields.Field(attribute='emp_personal_email', column_name='Employee Personal Email ID')
    emp_company_email= fields.Field(attribute='emp_company_email', column_name='Employee Company Email ID')
    is_ess = fields.Field(attribute='is_ess', column_name='Iss ESS (True/False)')
    emp_mobile_number_1 = fields.Field(attribute='emp_mobile_number_1', column_name='Employee Personal Mob No',widget=NumericMobileNumberWidget())
    emp_mobile_number_2 = fields.Field(attribute='emp_mobile_number_2', column_name='Employee Company Mobile No',widget=NumericMobileNumberWidget())
    emp_country_id = fields.Field(attribute='emp_country_id', column_name='Employee Country Code',widget=ForeignKeyWidget(cntry_mstr, 'country_name'))
    emp_state_id = fields.Field(attribute='emp_state_id', column_name='Employee State',widget=ForeignKeyWidget(state_mstr, 'state_name'))
    emp_city = fields.Field(attribute='emp_city', column_name='Employee City')
    emp_permenent_address = fields.Field(attribute='emp_permenent_address', column_name='Employee Permanent Address')
    emp_present_address = fields.Field(attribute='emp_present_address', column_name='Employee Current Address')
    emp_status = fields.Field(attribute='emp_status', column_name='Employee Status(True/False)')
    emp_joined_date = fields.Field(attribute='emp_joined_date', column_name='Employee Joining Date(DD/MM/YYYY)')
    emp_date_of_confirmation = fields.Field(attribute='emp_date_of_confirmation', column_name='Employee Confirmaton Date(DD/MM/YYYY)')
    emp_relegion = fields.Field(attribute='emp_relegion', column_name='Employee Religion')
    emp_blood_group = fields.Field(attribute='emp_blood_group', column_name='Employee Blood Group')
    emp_nationality_id = fields.Field(attribute='emp_nationality_id', column_name='Employee Nationality')
    emp_marital_status = fields.Field(attribute='emp_marital_status', column_name='Employee Marital Status')
    emp_father_name = fields.Field(attribute='emp_father_name', column_name='Employee Father Name')
    emp_mother_name = fields.Field(attribute='emp_mother_name', column_name='Employee Mother Name')
    emp_posting_location = fields.Field(attribute='emp_posting_location', column_name='Employee Work Location')
    is_active = fields.Field(attribute='is_active', column_name='Employee Active(True/False)')
    epm_ot_applicable = fields.Field(attribute='epm_ot_applicable', column_name='Employee OT applicable(True/False)')
    emp_branch_id = fields.Field(attribute='emp_branch_id', column_name='Employee Branch Code',widget=ForeignKeyWidget(brnch_mstr, 'branch_name'))
    emp_dept_id = fields.Field(attribute='emp_dept_id', column_name='Employee Department Code',widget=ForeignKeyWidget(dept_master, 'dept_name'))
    emp_desgntn_id = fields.Field(attribute='emp_desgntn_id', column_name='Employee Designation Code',widget=ForeignKeyWidget(desgntn_master, 'desgntn_job_title'))
    emp_ctgry_id = fields.Field(attribute='emp_ctgry_id', column_name='Employee Category Code',widget=ForeignKeyWidget(ctgry_master, 'ctgry_title'))
       
    class Meta:
        model = emp_master     
        fields = (
            'emp_code',
            'emp_first_name',
            'emp_last_name',
            'emp_gender',
            'emp_date_of_birth',
            'emp_personal_email',
            'emp_company_email',
            'is_ess',
            'emp_mobile_number_1',
            'emp_mobile_number_2',
            'emp_country_id',
            'emp_state_id',
            'emp_city',
            'emp_permenent_address',
            'emp_present_address',
            'emp_status',
            'emp_joined_date',
            'emp_date_of_confirmation',
            'emp_relegion',
            'emp_blood_group',
            'emp_nationality_id',
            'emp_marital_status',
            'emp_father_name',
            'emp_mother_name',
            'emp_posting_location',
            'is_active',
            'epm_ot_applicable',
            'emp_branch_id',
            'emp_dept_id',
            'emp_desgntn_id',
            'emp_ctgry_id',
        )
        import_id_fields = ()

    def before_import_row(self, row, **kwargs):
        errors = []
        login_id = row.get('Employee Code')
        personal_email = row.get('Employee Personal Email ID')
       
        
        if emp_master.objects.filter(emp_code=login_id).exists():
            errors.append(f"Duplicate value found for Employee Code: {login_id}")
               
        department_name = row.get('Employee Department Code')
        branch_name = row.get('Employee Branch Code')

        # Fetch the branch using branch name (or code if it exists)
        matching_branch = brnch_mstr.objects.filter(branch_name=branch_name).first()

        if matching_branch:
            # Filter departments in the matching branch by department name
            matching_dept = dept_master.objects.filter(branch_id=matching_branch.id, dept_name=department_name)
            print("matching_dept",matching_dept)
            # Check the number of departments found
            dept_count = matching_dept.count()
            print("dept_count",dept_count)

            if dept_count == 1:
                # If exactly one department matches, use it
                dept = matching_dept.first()
                print("dept",dept)
                print(f"Department: {dept.dept_name} found for Employee in Branch: {matching_branch.branch_name}")
                row['emp_dept_id'] = dept.id  # Set the department ID in the row
            elif dept_count > 1:
                # If multiple departments match, handle accordingly
                print(f"Warning: Multiple matching departments found for Branch: {matching_branch.branch_name} and Department: {department_name}")
                # You could select which department to use based on additional logic or let the user decide
                # For now, we are picking the first one
                dept = matching_dept.first()
                row['emp_dept_id'] = dept.id  # Set the department ID in the row
                print(f"Selected Department: {dept.dept_name} for Employee.")
            else:
                # If no department matches, log the error
                print(f"No matching department found for Employee in Branch: {matching_branch.branch_name} and Department: {department_name}")
                errors.append(f"No matching department found for Department: {department_name} in Branch: {matching_branch.branch_name}")
 
        

        if emp_master.objects.filter(emp_personal_email=personal_email).exists():
            errors.append(f"Duplicate value found for Employee Personal Email ID: {personal_email}")
        
         # Validating gender field
        gender = row.get('Employee Gender')
        if gender and gender not in ['Male', 'Female', 'Other','M','F','O']:
            errors.append("Invalid value for Employee Gender field. Allowed values are 'Male', 'Female','Other','M','F','O'")
              

        # Validate date fields format
        date_fields = ['Employee DOB(DD/MM/YYYY)', 'Employee Joining Date(DD/MM/YYYY)', 'Employee Confirmaton Date(DD/MM/YYYY)']
        date_format = '%d-%m-%y'  # Format: dd-mm-yy

        for field in date_fields:
            date_value = row.get(field)
            if date_value:
                try:
                    if isinstance(date_value, datetime):  # Check if value is already a datetime object
                        date_value = date_value.strftime('%d-%m-%y')  # Convert datetime object to string
                    datetime.strptime(date_value, date_format)
                except ValueError:
                    errors.append(f"Invalid date format for {field}. Date should be in format dd-mm-yy")
            else:
                pass
                # errors.append(f"Date value for {field} is empty")
        # Validate email format
        email = row.get('Employee Personal Email ID')
        if email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append(f"Invalid email format for Employee Personal Email ID' field:{email}")

        
        # Validating marital status field
        marital_status = row.get('Employee Marital Status')
        if marital_status and marital_status not in ['Married', 'Single', 'Divorced', 'Widow','SINGLE','DIVORCED','WIDOW']:
            errors.append("Invalid value for marital status field. Allowed values are 'Married', 'Single', 'Divorced', 'Widow','SINGLE','DIVORCED','WIDOW'")      

        if errors:
            raise ValidationError(errors)

class EmpCustomFieldValueResource(resources.ModelResource):
    emp_master = fields.Field(attribute='emp_master',column_name='Employee Code',widget=ForeignKeyWidget(emp_master, 'emp_code'))
    emp_custom_field = fields.Field(attribute='emp_custom_field',column_name='Field Name',widget=ForeignKeyWidget(Emp_CustomField, 'emp_custom_field'))
    field_value = fields.Field(attribute='field_value',column_name='Field Value',widget=MultiTypeWidget())

    class Meta:
        model = Emp_CustomFieldValue
        fields = ('emp_master', 'emp_custom_field', 'field_value')
        import_id_fields = ()

    def before_import_row(self, row, row_idx=None, **kwargs):
        emp_code = row.get('Employee Code')
        field_name = row.get('Field Name')
        field_value = row.get('Field Value')

        if not emp_master.objects.filter(emp_code=emp_code).exists():
            raise ValidationError(f"emp_master with emp_code {emp_code} does not exist.")

        if not Emp_CustomField.objects.filter(emp_custom_field=field_name).exists():
            raise ValidationError(f"Emp_CustomField with field_name {field_name} does not exist.")

        custom_field = Emp_CustomField.objects.get(emp_custom_field=field_name)

        if custom_field.data_type == 'date':
            if isinstance(field_value, str):
                field_value = field_value.strip()  # Remove leading and trailing spaces
                
                # Check if the string contains time information
                if ' ' in field_value:
                    # Extract the date part (YYYY-MM-DD) from datetime string
                    field_value = field_value.split(' ')[0]
                
                try:
                    # Attempt to parse the date from the extracted or provided string
                    date_object = datetime.strptime(field_value, '%Y-%m-%d').date()
                    # Reformat to DD-MM-YYYY
                    field_value = date_object.strftime('%d-%m-%Y')
                except ValueError:
                    raise ValidationError(f"Invalid date format for field {field_name}. Date should be in DD-MM-YYYY format.")

            # Replace the original row value with the correctly formatted date
            row['Field Value'] = field_value

class DocumentResource(resources.ModelResource):
    emp_id = fields.Field(attribute='emp_id', column_name='Employee ID', widget=ForeignKeyWidget(emp_master, 'emp_code'))
    emp_sl_no = fields.Field(attribute='emp_sl_no', column_name='SerialNo')
    document_type = fields.Field(attribute='document_type', column_name='Document Type', widget=ForeignKeyWidget(document_type, 'type_name'))
    emp_doc_number = fields.Field(attribute='emp_doc_number', column_name='Document Number')
    emp_doc_issued_date = fields.Field(attribute='emp_doc_issued_date', column_name='Document Issued Date')
    emp_doc_expiry_date = fields.Field(attribute='emp_doc_expiry_date', column_name='Document Expiry Date')

    class Meta:
        model = Emp_Documents
        fields = (
            'emp_id',
            'emp_sl_no',
            'document_type',
            'emp_doc_number',
            'emp_doc_issued_date',
            'emp_doc_expiry_date',
        )
        import_id_fields = ('emp_sl_no',)

    def before_import_row(self, row, **kwargs):
        errors = []  
        emp_sl_no = row.get('SerialNo')
        emp_code = row.get('Employee ID')
        doc_type = row.get('Document Type')

        # Validate emp_id and document_type
        if Emp_Documents.objects.filter(emp_sl_no=emp_sl_no).exists():
            errors.append(f"Duplicate value found for Employee Code: {emp_sl_no}")

        if not emp_master.objects.filter(emp_code=emp_code).exists():
            errors.append(f"emp_master matching query does not exist for ID: {emp_code}")

        if not document_type.objects.filter(type_name=doc_type).exists():
            errors.append(f"Document_type matching query does not exist for ID: {doc_type}")

        # Validate and convert date fields format
        date_fields = ['Document Issued Date', 'Document Expiry Date']
        input_date_format = '%Y-%m-%d'  # The format after conversion from Excel

        for field in date_fields:
            date_value = row.get(field)
            if date_value:
                try:
                    # Check if date_value is already a datetime object
                    if isinstance(date_value, datetime):
                        parsed_date = date_value.date()  # Extract date part
                    elif isinstance(date_value, str):
                        parsed_date = datetime.strptime(date_value, input_date_format).date()
                    else:
                        raise ValueError(f"Unsupported date format for {field}")
                    
                    row[field] = parsed_date
                except ValueError as e:
                    errors.append(f"Invalid date format for {field}: {e}")
            else:
                errors.append(f"Date value for {field} is empty")

        if errors:
            raise ValidationError(errors)

    def after_import_instance(self, instance, new, **kwargs):
        """
        Handles the creation of notifications after the document instance is saved.
        """
        if new:
            today = timezone.now().date()
            expiry_date = instance.emp_doc_expiry_date
            
            # Check if emp_master exists and has a valid branch
            if instance.emp_id and instance.emp_id.emp_branch_id:
                branch_notification_days = instance.emp_id.emp_branch_id.notification_period_days
                if branch_notification_days is not None:
                    notification_delta = timedelta(days=branch_notification_days)  # Notify based on branch's notification period
                    
                    if expiry_date - today <= notification_delta:
                        notification_message = f"The document '{instance.document_type}' of '{instance.emp_id}' is expiring on {expiry_date}."
                        # Create notification for the newly created document
                        notification.objects.create(
                            message=notification_message,
                            document_id=instance
                        )
            else:
                # Handle cases where emp_id or emp_branch_id is not valid
                print("Warning: Invalid emp_id or emp_branch_id detected. Cannot create notification.")   

    
class LanguageSkillResource(resources.ModelResource):  
    class Meta:
        model = LanguageSkill
        fields = ('language',)
        import_id_fields = ()
        

class MarketingSkillResource(resources.ModelResource):
    class Meta:
        model = MarketingSkill
        fields = ('marketing')
        import_id_fields = ()

class ProLangSkillResource(resources.ModelResource):
    class Meta:
        model = ProgrammingLanguageSkill
        fields = ('programming_language ')
        import_id_fields = ()


    
