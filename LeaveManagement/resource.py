# resources.py
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget, TimeWidget
from .models import Attendance, Shift, WeeklyShiftSchedule,EmployeeMachineMapping
from EmpManagement.models import emp_master
from django.core.exceptions import ValidationError
from datetime import datetime,time 


class CustomEmployeeWidget(ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None       
        try:
            return emp_master.objects.get(emp_code=value)
        except emp_master.DoesNotExist:
            try:
                mapping = EmployeeMachineMapping.objects.get(machine_code=value)
                return mapping.employee
            except EmployeeMachineMapping.DoesNotExist:
                error_msg = f"Identifier Code '{value}' does not exist in employee or machine code mappings."
                raise ValueError(error_msg)  # Raise ValueError with informative message
            except Exception as e:
                raise

class AttendanceResource(resources.ModelResource):
    employee = fields.Field(column_name='Identifier Code',attribute='employee',widget=CustomEmployeeWidget(emp_master, 'emp_code'))
    check_in_time = fields.Field(attribute='check_in_time', column_name='Check In Time')
    check_out_time = fields.Field(attribute='check_out_time', column_name='Check Out Time')
    date = fields.Field(attribute='date', column_name='Date')

    class Meta:
        model = Attendance
        fields = ('employee', 'check_in_time', 'check_out_time', 'date')
        import_id_fields = ('employee', 'date')  # Must be actual model fields

    def before_import_row(self, row, row_number=None, **kwargs):
        errors = []
        
        identifier_code = row.get('Identifier Code')
        date = row.get('Date')
        check_in_time = row.get('Check In Time')
        check_out_time = row.get('Check Out Time')
        
        # Validate employee code
        employee = None
        if isinstance(identifier_code, str):
            try:
                employee = emp_master.objects.get(emp_code=identifier_code)
            except emp_master.DoesNotExist:
                try:
                    mapping = EmployeeMachineMapping.objects.get(machine_code=identifier_code)
                    employee = mapping.employee
                except EmployeeMachineMapping.DoesNotExist:
                    errors.append(f"Identifier Code '{identifier_code}' does not exist.")
        
        if not employee:
            errors.append(f"Employee not found for Identifier Code '{identifier_code}'.")

        if date and employee:
            if Attendance.objects.filter(employee=employee, date=date).exists():
                errors.append(f"Duplicate attendance record for Identifier '{identifier_code}' on {date}.")
        
        # Validate time fields
        for field, time_value in zip(['Check In Time', 'Check Out Time'], [check_in_time, check_out_time]):
            if isinstance(time_value, str):
                try:
                    row[field] = datetime.strptime(time_value, '%H:%M:%S').time()
                except ValueError:
                    errors.append(f"Invalid time format for {field}: {time_value}")

        # If employee is found, store it in the row dictionary
        if employee:
            row['employee'] = employee
        
        # Raise errors if any exist
        if errors:
            raise ValidationError(errors)

    def after_import_row(self, row, row_result, **kwargs):
        print("After import row called for:", row)
        employee = row.get('employee')
        date = row.get('Date')
        
        if employee and date:
            try:
                attendance = Attendance.objects.get(employee=employee, date=date)
                
                # Assign shift
                schedule = WeeklyShiftSchedule.objects.filter(employee=employee).first()
                shift = schedule.get_shift_for_day(attendance.date) if schedule else None
                attendance.shift = shift
                
                # Calculate total hours
                attendance.calculate_total_hours()
                
                attendance.save()
            except Attendance.DoesNotExist:
                print(f"Attendance record not found for {employee} on {date}")

    