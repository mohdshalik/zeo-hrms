from django.shortcuts import render
from django.conf import settings
import os,json
from datetime import date
from collections import defaultdict
from django.core.cache import cache
import redis
from rest_framework import viewsets,filters, status
from datetime import datetime, timedelta
from django.db.models import Field
from . serializer import(LeaveTypeSerializer,LeaveEntitlementSerializer,ApplicableSerializer,EmployeeLeaveBalanceSerializer,AccrualSerializer,ResetSerializer,LeaveRequestSerializer,
                         AttendanceSerializer,ShiftSerializer,WeeklyShiftScheduleSerializer,ImportAttendanceSerializer,EmployeeMappingSerializer,LeaveReportSerializer,LvApprovalLevelSerializer,
                         LvApprovalSerializer,LvEmailTemplateSerializer,LvApprovalNotifySerializer,LvCommonWorkflowSerializer,LvRejectionReasonSerializer,LvApprovalReportSerializer,AttendanceReportSerializer,lvBalanceReportSerializer)
from .models import (leave_type,leave_entitlement,applicablity_critirea,emp_leave_balance,leave_accrual_transaction,leave_reset_transaction,employee_leave_request,Attendance,Shift,
                     WeeklyShiftSchedule,EmployeeMachineMapping,LeaveReport,LeaveApprovalLevels,LeaveApproval,LvEmailTemplate,LvApprovalNotify,LvCommonWorkflow,LvRejectionReason,LeaveApprovalReport,
                     AttendanceReport,lvBalanceReport
                     )
from rest_framework.parsers import MultiPartParser, FormParser
from EmpManagement.models import emp_master
from .resource import AttendanceResource
from django.http import HttpResponse,JsonResponse
import tablib
from tablib import Dataset
from io import BytesIO
import pandas as pd,openpyxl
from openpyxl.styles import PatternFill,Alignment,Font,NamedStyle
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
# from rest_framework import status
# from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
# Create your views here.



class LeaveTypeviewset(viewsets.ModelViewSet):
    queryset = leave_type.objects.all()
    serializer_class = LeaveTypeSerializer
    
class LvEmailTemplateviewset(viewsets.ModelViewSet):
    queryset = LvEmailTemplate.objects.all()
    serializer_class = LvEmailTemplateSerializer

class LvApprovalNotifyviewset(viewsets.ModelViewSet):
    queryset = LvApprovalNotify.objects.all()
    serializer_class = LvApprovalNotifySerializer
# class LeavePolicyviewset(viewsets.ModelViewSet):
#     queryset = leave_policy.objects.all()
#     serializer_class = LeavePolicySerializer

class LeaveEntitlementviewset(viewsets.ModelViewSet):
    queryset = leave_entitlement.objects.all()
    serializer_class = LeaveEntitlementSerializer
    def perform_create(self, serializer):
        instance = serializer.save()
        self.process_accrual(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.process_accrual(instance)

    def process_accrual(self, instance):
        if instance.accrual and instance.accrual_month == timezone.now().strftime('%b') and instance.accrual_day == '1st':
            employees = emp_leave_balance.objects.filter(leave_type=instance.leave_type)
            for emp_balance in employees:
                leave_accrual_transaction.objects.create(
                    employee=emp_balance.employee,
                    leave_type=instance.leave_type,
                    accrual_date=timezone.now().date(),
                    amount=instance.accrual_rate
                )
                emp_balance.balance += instance.accrual_rate
                emp_balance.save()

class Applicableviewset(viewsets.ModelViewSet):
    queryset = applicablity_critirea.objects.all()
    serializer_class = ApplicableSerializer


class leave_balance_viewset(viewsets.ModelViewSet):
    queryset = emp_leave_balance.objects.all()
    serializer_class = EmployeeLeaveBalanceSerializer


class Acrualviewset(viewsets.ModelViewSet):
    queryset = leave_accrual_transaction.objects.all()
    serializer_class = AccrualSerializer


class Resetviewset(viewsets.ModelViewSet):
    queryset = leave_reset_transaction.objects.all()
    serializer_class = ResetSerializer

# class Enchashviewset(viewsets.ModelViewSet):
#     queryset = leave_encashment.objects.all()
#     serializer_class = EnchashSerializer


class LeaveRequestviewset(viewsets.ModelViewSet):
    queryset = employee_leave_request.objects.all()
    serializer_class = LeaveRequestSerializer

    @action(detail=False, methods=['get'], url_path='leave-request-history')
    def employee_leave_request(self, request):
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        requests = employee_leave_request.objects.filter(employee_id=employee_id).order_by('-applied_on')
     
        # Manually serialize the fields you want
        history_data = []
        for request in requests:
            history_data.append({
                'start_date': request.start_date,
                'end_date': request.end_date,
                'leave_type': request.leave_type.name if request.leave_type else None,
                'reason': request.reason ,
                'status': request.status,
                'applied_on': request.applied_on,
                'number_of_days':request.number_of_days
            })

        return Response(history_data, status=status.HTTP_200_OK)
    
#     def get_serializer_class(self):
#         if self.request.method in ['POST', 'PUT']:
#             return EmployeeLeaveSerializer
#         return super().get_serializer_class()

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['employee_id'] = self.request.data.get('employee_id', None)
#         return context

#filtering for using assigned models for employees
from rest_framework.response import Response
from rest_framework.decorators import action

class LeaveTypeViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def available_leave_types(self, request):
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({"error": "employee_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = emp_master.objects.get(id=employee_id)
        except emp_master.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        leave_types = leave_type.objects.filter(
            id__in=emp_leave_balance.objects.filter(employee=employee).values_list('leave_type_id', flat=True)
        )
        serializer = LeaveTypeSerializer(leave_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMachineMappingViewset(viewsets.ModelViewSet):
    queryset =EmployeeMachineMapping.objects.all()
    serializer_class = EmployeeMappingSerializer

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer

class WeeklyShiftScheduleViewSet(viewsets.ModelViewSet):
    queryset = WeeklyShiftSchedule.objects.all()
    serializer_class = WeeklyShiftScheduleSerializer

    # POST method to assign a weekly shift schedule to an employee
    @action(detail=False, methods=['post'])
    def assign_weekly_shift(self, request):
        employee_id = request.data.get("employee_id")
        shift_data = request.data.get("shifts", {})
        
        try:
            employee = emp_master.objects.get(id=employee_id)
        except emp_master.DoesNotExist:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve or create weekly shift schedule for the employee
        schedule, created = WeeklyShiftSchedule.objects.get_or_create(employee=employee)

        # Assign shifts for each day of the week
        schedule.monday_shift = Shift.objects.get(id=shift_data.get("monday")) if shift_data.get("monday") else None
        schedule.tuesday_shift = Shift.objects.get(id=shift_data.get("tuesday")) if shift_data.get("tuesday") else None
        schedule.wednesday_shift = Shift.objects.get(id=shift_data.get("wednesday")) if shift_data.get("wednesday") else None
        schedule.thursday_shift = Shift.objects.get(id=shift_data.get("thursday")) if shift_data.get("thursday") else None
        schedule.friday_shift = Shift.objects.get(id=shift_data.get("friday")) if shift_data.get("friday") else None
        schedule.saturday_shift = Shift.objects.get(id=shift_data.get("saturday")) if shift_data.get("saturday") else None
        schedule.sunday_shift = Shift.objects.get(id=shift_data.get("sunday")) if shift_data.get("sunday") else None
        schedule.save()
        return Response({"status": "Weekly shift schedule assigned successfully"}, status=status.HTTP_200_OK)

    # GET method to retrieve the shift schedule for a specific employee
    @action(detail=False, methods=['get'])
    def get_employee_shift(self, request):
        employee_id = request.query_params.get("employee_id")
        
        try:
            employee = emp_master.objects.get(id=employee_id)
            schedule = WeeklyShiftSchedule.objects.get(employee=employee)
        except emp_master.DoesNotExist:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        except WeeklyShiftSchedule.DoesNotExist:
            return Response({"detail": "Shift schedule not found for this employee"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WeeklyShiftScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    @action(detail=False, methods=['post'])
    def check_in(self, request):
        emp_id = request.data.get("employee_id")
        date = timezone.now().date()
        # check_in_time = request.data.get("check_in_time", timezone.now().time())

        try:
            employee = emp_master.objects.get(id=emp_id)
        except emp_master.DoesNotExist:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        # attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)
        attendance, created = Attendance.objects.get_or_create(employee_id=emp_id, date=date)
        if attendance.check_in_time:
            return Response({"detail": "Already checked in"}, status=status.HTTP_400_BAD_REQUEST)

        schedule = WeeklyShiftSchedule.objects.filter(employee=employee).first()
        shift = schedule.get_shift_for_day(today) if  schedule else None

        attendance.check_in_time = timezone.now()
        attendance.shift = shift
        attendance.save()

        return Response({"status": "Check-in recorded successfully", "shift": shift.name if shift else None}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        emp_id = request.data.get("employee_id")
        date = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(employee_id=emp_id, date=date)
        except Attendance.DoesNotExist:
            return Response({"detail": "No check-in record found"}, status=status.HTTP_400_BAD_REQUEST)

        if attendance.check_out_time:
            return Response({"detail": "Already checked out"}, status=status.HTTP_400_BAD_REQUEST)
        attendance.check_out_time = timezone.now()
        attendance.calculate_total_hours()  # Ensure total hours are calculated
        attendance.save()

        return Response({
            "status": "Check-out recorded successfully",
        }, status=status.HTTP_200_OK)

class ImportAttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class= ImportAttendanceSerializer
    resource_class = AttendanceResource
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            excel_file = request.FILES['file']
            if excel_file.name.endswith('.xlsx'):
                try:
                    dataset = Dataset()
                    dataset.load(excel_file.read(), format='xlsx')
                    resource = AttendanceResource()
                    all_errors = []
                    valid_rows = []
                    
                    # Validate rows before import
                    for row_idx, row in enumerate(dataset.dict, start=2):
                        row_errors = []
                        try:
                            resource.before_import_row(row, row_idx=row_idx)
                        except ValidationError as e:
                            row_errors.extend([f"Row {row_idx}: {error}" for error in e.messages])
                        if row_errors:
                            all_errors.extend(row_errors)
                        else:
                            valid_rows.append(row)

                    if all_errors:
                        return Response({"errors": all_errors}, status=400)

                    # Import valid data and process shifts & total hours
                    result = resource.import_data(dataset, dry_run=False, raise_errors=True)

                    return Response({"message": f"{result.total_rows} attendances are added successfully"})
                except Exception as e:
                    return Response({"error": str(e)}, status=400)
            else:
                return Response({"error": "Invalid file format. Only Excel files (.xlsx) are supported."}, status=400)
        else:
            return Response({"error": "Please provide an Excel file."}, status=400)

class Leave_ReportViewset(viewsets.ModelViewSet):
    queryset = LeaveReport.objects.all()
    serializer_class = LeaveReportSerializer

    def __init__(self, *args, **kwargs):
        super(Leave_ReportViewset, self).__init__(*args, **kwargs)
        self.leave_standard_report_exists()
    def get_available_fields(self):
        excluded_fields = {'id', 'created_by'}
        included_emp_master_fields = { 'emp_first_name', 'emp_dept_id', 'emp_desgntn_id', 'emp_ctgry_id'}
        
        display_names = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "leave_type": "Leave Type",
            "reason": "Reason",
            "status":"Status",
            "approved_by": "Approved Request",
            "applied_on":"Request Date",
           
        }

        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name in included_emp_master_fields]
        leave_request_fields = [field.name for field in employee_leave_request._meta.get_fields() if isinstance(field, Field) and field.name not in excluded_fields]
        
        available_fields = {field: display_names.get(field, field) for field in emp_master_fields + leave_request_fields}
        return available_fields

    @action(detail=False, methods=['get'])
    def select_leavereport_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        return Response({'available_fields': available_fields})
       
    @action(detail=False, methods=['post'])
    def generate_leave_report(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                file_name = request.POST.get('file_name', 'report')
                fields_to_include = request.POST.getlist('fields', [])
                # from_date = parse_date(request.POST.get('from_date'))
                # to_date = parse_date(request.POST.get('to_date'))
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
            if not fields_to_include:
                fields_to_include = list(self.get_available_fields().keys())
            
            leavereport = employee_leave_request.objects.all()
            # documents = self.filter_documents_by_date_range(documents)

            report_data = self.generate_report_data(fields_to_include,leavereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)  # Serialize dates to string format


            LeaveReport.objects.create(file_name=file_name, report_data=file_name + '.json')
            return JsonResponse({'status': 'success', 'file_path': file_path,'selected_fields_data': fields_to_include,})
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

   
    def leave_standard_report_exists(self):
        # Update the standard report if it exists, otherwise create a new one
        if LeaveReport.objects.filter(file_name='leave_std_report').exists():
            self.generate_standard_report()
        else:
            self.generate_standard_report()
    
    def generate_standard_report(self):
        try:
            file_name = 'leave_std_report'
            fields_to_include = self.get_available_fields().keys()
            leavereport = employee_leave_request.objects.all()

            report_data = self.generate_report_data(fields_to_include, leavereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')

            # Save report data to a file
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)

            # Update or create the standard report entry in the database
            LeaveReport.objects.update_or_create(
                file_name=file_name,
                defaults={'report_data': file_name + '.json'}
            )

            print("Standard report generated successfully.")

        except Exception as e:
            print(f"Error generating standard report: {str(e)}")

    @action(detail=False, methods=['get'])
    def std_report(self, request, *args, **kwargs):
        try:
            # Ensure the standard report is up-to-date
            self.generate_standard_report()
            report = LeaveReport.objects.get(file_name='leave_std_report')
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        except LeaveReport.DoesNotExist:
            return Response({"error": "Standard report not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def generate_report_data(self, fields_to_include,generalreport):
        column_headings = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "leave_type": "Leave Type",
            "reason": "Reason",
            "status":"Status",
            "approved_by": "Approved Request",
            "applied_on":"Request Date",
        }

        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name != 'id']
        leave_request_fields = [field.name for field in employee_leave_request._meta.get_fields() if isinstance(field, Field) and field.name != 'id']

        report_data = []
        for document in generalreport:
            general_data = {}
            for field in fields_to_include:
                if field in emp_master_fields:
                    value = getattr(document.employee, field, 'N/A')
                    if isinstance(value, date):
                        value = value.isoformat()
                elif field in leave_request_fields:
                    value = getattr(document, field, 'N/A')
                else:
                    value = 'N/A'
                general_data[field] = value
            report_data.append(general_data)
        return report_data
    
    @action(detail=False, methods=['get'])
    def select_filter_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        selected_fields = request.session.get('selected_fields', [])
        report_id = request.GET.get('report_id')  # Get report_id from query parameters

        
        return Response({
            'available_fields': available_fields,
            'selected_fields': selected_fields,
            'report_id': report_id
        })
    
    @action(detail=False, methods=['post'])
    def filter_by_date(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # Replace slashes with hyphens
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')

        # Parse and validate the date range
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date format: {str(e)}'}, status=400)

        # Fetch report data from your database
        try:
            report_instance = LeaveReport.objects.get(id=report_id)
            report_data = json.loads(report_instance.report_data.read().decode('utf-8'))
        except LeaveReport.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)

        # Filter data by date range
        date_filtered_data = [
            row for row in report_data
            if 'applied_on' in row and row['applied_on'] and
            start_date <= datetime.fromisoformat(row['applied_on']) <= end_date
        ]

        # Save filtered data to Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        cache.set(cache_key, date_filtered_data, timeout=None)  # Set timeout as needed

        return JsonResponse({
            'date_filtered_data': date_filtered_data,
            'report_id': report_id,
        })
    
    @action(detail=False, methods=['post'])
    def generate_filter_table(self, request, *args, **kwargs):
        selected_fields = request.POST.getlist('selected_fields')
        report_id = request.data.get('report_id')

        # Save selected fields to session
        request.session['selected_fields'] = selected_fields

        # Fetch date-filtered report data from session
        date_filtered_data = request.session.get('date_filtered_data', [])
        print("previously date filtered ",date_filtered_data)
        
        # If no date-filtered data, attempt to fetch full report
        if not date_filtered_data:
            try:
                report = LeaveReport.objects.get(id=report_id)
                report_file_path = os.path.join(settings.MEDIA_ROOT, report.report_data.name)
                with open(report_file_path, 'r') as file:
                    report_content = json.load(file)
            except LeaveReport.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Report not found'})

            date_filtered_data = report_content

        # If no fields are selected for filtration, default to all existing fields in the report
        if not selected_fields:
            if date_filtered_data:
                selected_fields = list(date_filtered_data[0].keys())  # Default to all keys in the first record
            else:
                selected_fields = []  # No data in the report
            
        # Define display names for fields
        column_headings = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "leave_type": "Leave Type",
            "reason": "Reason",
            "status":"Status",
            "approved_by": "Approved Request",
            "applied_on":"Request Date",
        }

        # Get unique values for selected_fields from date-filtered data
        unique_values = self.get_unique_values_for_fields(date_filtered_data, selected_fields)

        processed_unique_values = {}
        for field, values in unique_values.items():
            processed_unique_values[field] = {
                'values': values,
            }

        return JsonResponse({
            'selected_fields': selected_fields,
            'report_id': report_id,
            'report_content': date_filtered_data,  # Pass filtered data to the frontend
            'unique_values': processed_unique_values,
            'column_headings':column_headings
        })
        

    def get_unique_values_for_fields(self, data, selected_fields):
        unique_values = {field: set() for field in selected_fields}
        # Extract data from the provided content
        for record in data:
            for field in selected_fields:
                if field in record:
                    unique_values[field].add(record[field])

        # Convert sets to lists
        for field in unique_values:
            unique_values[field] = list(unique_values[field])
        return unique_values
       
    
    @action(detail=False, methods=['post'])
    def general_filter_report(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')

        # Retrieve filtered data from Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        filtered_data = cache.get(cache_key)

        if filtered_data is None:
            return JsonResponse({'status': 'error', 'message': 'No date-filtered data available'}, status=404)
        # Apply additional filtering here if needed
        # For example, based on other fields:
        additional_filters = {key: value for key, value in request.data.items() if key not in ('report_id',)}
        
        # Further filter based on additional criteria
        filtered_data = [
            row for row in filtered_data
            if all(row.get(key) == value for key, value in additional_filters.items())
        ]
        return JsonResponse({
            'filtered_data': filtered_data,
            'report_id': report_id,
        })

    
class LvApprovalLevelViewset(viewsets.ModelViewSet):
    queryset=LeaveApprovalLevels.objects.all()
    serializer_class=LvApprovalLevelSerializer

class LvCommonWorkflowViewset(viewsets.ModelViewSet):
    queryset=LvCommonWorkflow.objects.all()
    serializer_class=LvCommonWorkflowSerializer

class LvRejectionViewset(viewsets.ModelViewSet):
    queryset=LvRejectionReason.objects.all()
    serializer_class=LvRejectionReasonSerializer

class LvApprovalViewset(viewsets.ModelViewSet):
    queryset=LeaveApproval.objects.all()
    serializer_class=LvApprovalSerializer
    lookup_field = 'pk'

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        note = request.data.get('note')  # Get the note from the request
        approval.approve(note=note)
        return Response({'status': 'approved', 'note': note}, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        note = request.data.get('note')
        rejection_reason_id = request.data.get('rejection_reason_id')

        if not rejection_reason_id:
            raise ValidationError("Rejection reason is required.")

        try:
            rejection_reason = LvRejectionReason.objects.get(id=rejection_reason_id)
        except LvRejectionReason.DoesNotExist:
            raise ValidationError("Invalid rejection reason.")

        approval.reject(rejection_reason=rejection_reason, note=note)
        return Response({'status': 'rejected', 'note': note, 'rejection_reason': rejection_reason.reason_text}, status=status.HTTP_200_OK)
    # Custom action to get grouped leave approvals
    @action(detail=False, methods=['get'])
    def grouped_approvals(self, request):
        approvals = LeaveApproval.objects.select_related('leave_request', 'approver').order_by('leave_request', 'level')
        
        # Group approvals by leave_request
        grouped_approvals = defaultdict(list)
        for approval in approvals:
            grouped_approvals[approval.leave_request.id].append({
                'id': approval.id,
                'role': approval.role,
                'level': approval.level,
                'status': approval.status,
                'note': approval.note,
                'created_at': approval.created_at,
                'updated_at': approval.updated_at,
                'approver': approval.approver.username,
                'rejection_reason': approval.rejection_reason.reason_text if approval.rejection_reason else None,
            })
        
        # Format data to a list of dictionaries
        response_data = [
            {
                'leave_request': leave_request_id,
                'approvals': levels
            }
            for leave_request_id, levels in grouped_approvals.items()
        ]

        return Response(response_data, status=status.HTTP_200_OK)
class Lv_Approval_ReportViewset(viewsets.ModelViewSet):
    queryset = LeaveApprovalReport.objects.all()
    serializer_class = LvApprovalReportSerializer
    def __init__(self, *args, **kwargs):
        super(Lv_Approval_ReportViewset, self).__init__(*args, **kwargs)
        self.lv_apprvl_std_report_exists()
    def get_available_fields(self):
        excluded_fields = {'id', 'created_by'}
        included_emp_master_fields = { 'emp_first_name', 'emp_dept_id', 'emp_desgntn_id', 'emp_ctgry_id'}
        
        display_names = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "leave_request": "Leave Request",
            "approver":"Approver",
            "level":"Level",
            "created_at": "Approve/Reject Date",
            "status":"Status",
            "note": "Comments",
            "rejection_reason":"Rejection Reason",
           
        }

        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name in included_emp_master_fields]
        leave_approval_fields = [field.name for field in LeaveApproval._meta.get_fields() if isinstance(field, Field) and field.name not in excluded_fields]
        
        available_fields = {field: display_names.get(field, field) for field in emp_master_fields + leave_approval_fields}
        return available_fields

    @action(detail=False, methods=['get'])
    def select_approve_report_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        return Response({'available_fields': available_fields})
       
    @action(detail=False, methods=['post'])
    def generate_leave_report(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                file_name = request.POST.get('file_name', 'report')
                fields_to_include = request.POST.getlist('fields', [])
                # from_date = parse_date(request.POST.get('from_date'))
                # to_date = parse_date(request.POST.get('to_date'))
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
            if not fields_to_include:
                fields_to_include = list(self.get_available_fields().keys())
            
            leavereport = LeaveApproval.objects.all()
            # documents = self.filter_documents_by_date_range(documents)

            report_data = self.generate_report_data(fields_to_include,leavereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)  # Serialize dates to string format


            LeaveApprovalReport.objects.create(file_name=file_name, report_data=file_name + '.json')
            return JsonResponse({'status': 'success', 'file_path': file_path,'selected_fields_data': fields_to_include,})
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

   
    def lv_apprvl_std_report_exists(self):
        # Update the standard report if it exists, otherwise create a new one
        if LeaveReport.objects.filter(file_name='lv_approv_std_report').exists():
            self.generate_standard_report()
        else:
            self.generate_standard_report()
    
    def generate_standard_report(self):
        try:
            file_name = 'lv_approv_std_report'
            fields_to_include = self.get_available_fields().keys()
            leavereport = LeaveApproval.objects.all()

            report_data = self.generate_report_data(fields_to_include, leavereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')

            # Save report data to a file
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)

            # Update or create the standard report entry in the database
            LeaveApprovalReport.objects.update_or_create(
                file_name=file_name,
                defaults={'report_data': file_name + '.json'}
            )

            print("Standard report generated successfully.")

        except Exception as e:
            print(f"Error generating standard report: {str(e)}")

    @action(detail=False, methods=['get'])
    def std_report(self, request, *args, **kwargs):
        try:
            # Ensure the standard report is up-to-date
            self.generate_standard_report()
            report = LeaveApprovalReport.objects.get(file_name='lv_approv_std_report')
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        except LeaveApprovalReport.DoesNotExist:
            return Response({"error": "Standard report not found."}, status=status.HTTP_404_NOT_FOUND)
    def generate_report_data(self, fields_to_include, generalreport):
        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name != 'id']
        leave_approval_fields = [field.name for field in LeaveApproval._meta.get_fields() if isinstance(field, Field) and field.name != 'id']

        report_data = defaultdict(list)

        for document in generalreport:
            leave_request_id = document.leave_request.id if document.leave_request else 'N/A'
            approval_data = {}

            leave_request = document.leave_request
            employee = leave_request.employee if leave_request else None

            for field in fields_to_include:
                if field in emp_master_fields and employee:
                    value = getattr(employee, field, 'N/A')
                elif field in leave_approval_fields:
                    value = getattr(document, field, 'N/A')
                elif field == 'leave_type' and leave_request:
                    value = leave_request.leave_type.name if leave_request.leave_type else 'N/A'
                elif field == 'reason' and leave_request:
                    value = leave_request.reason
                elif field == 'applied_on' and leave_request:
                    value = leave_request.applied_on.isoformat() if leave_request.applied_on else 'N/A'
                else:
                    value = 'N/A'
                
                if isinstance(value, date):
                    value = value.isoformat()
                approval_data[field] = value

            report_data[leave_request_id].append(approval_data)

        return [{'leave_request': lr_id, 'approvals': details} for lr_id, details in report_data.items()]
    # def generate_report_data(self, fields_to_include, generalreport):
    #     # Fetch fields from emp_master and leave_approval models
    #     emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name != 'id']
    #     leave_approval_fields = [field.name for field in LeaveApproval._meta.get_fields() if isinstance(field, Field) and field.name != 'id']

    #     report_data = []

    #     for document in generalreport:
    #         general_data = {}

    #         # Access the related leave_request object and employee object
    #         leave_request = document.leave_request
    #         employee = leave_request.employee if leave_request else None

    #         for field in fields_to_include:
    #             if field in emp_master_fields and employee:
    #                 # Get field value from employee
    #                 value = getattr(employee, field, 'N/A')
    #             elif field in leave_approval_fields:
    #                 # Get field value from leave_approval
    #                 value = getattr(document, field, 'N/A')
    #             elif field == 'leave_type' and leave_request:
    #                 # Access leave_type through leave_request
    #                 value = leave_request.leave_type.name if leave_request.leave_type else 'N/A'
    #             elif field == 'reason' and leave_request:
    #                 value = leave_request.reason
    #             elif field == 'applied_on' and leave_request:
    #                 value = leave_request.applied_on.isoformat() if leave_request.applied_on else 'N/A'
    #             else:
    #                 value = 'N/A'
    #             # Format date fields
    #             if isinstance(value, date):
    #                 value = value.isoformat()
    #             general_data[field] = value
    #         report_data.append(general_data)
    #     return report_data
    
    @action(detail=False, methods=['get'])
    def select_filter_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        selected_fields = request.session.get('selected_fields', [])
        report_id = request.GET.get('report_id')  # Get report_id from query parameters      
        return Response({
            'available_fields': available_fields,
            'selected_fields': selected_fields,
            'report_id': report_id
        })
    
    @action(detail=False, methods=['post'])
    def filter_by_date(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # Replace slashes with hyphens
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')

        # Parse and validate the date range
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date format: {str(e)}'}, status=400)

        # Fetch report data from your database
        try:
            report_instance = LeaveApprovalReport.objects.get(id=report_id)
            report_data = json.loads(report_instance.report_data.read().decode('utf-8'))
        except LeaveApprovalReport.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)

        # Filter data by date range
        date_filtered_data = [
            row for row in report_data
            if 'created_at' in row and row['created_at'] and
            start_date <= datetime.fromisoformat(row['created_at']) <= end_date
        ]

        # Save filtered data to Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        cache.set(cache_key, date_filtered_data, timeout=None)  # Set timeout as needed

        return JsonResponse({
            'date_filtered_data': date_filtered_data,
            'report_id': report_id,
        })
    

    @action(detail=False, methods=['post'])
    def approval_filter_table(self, request, *args, **kwargs):
        selected_fields = request.POST.getlist('selected_fields')
        report_id = request.data.get('report_id')

        # Save selected fields to session
        request.session['selected_fields'] = selected_fields

        # Fetch date-filtered report data from session
        date_filtered_data = request.session.get('date_filtered_data', [])
        print("previosly date filtered ",date_filtered_data)
        
        # If no date-filtered data, attempt to fetch full report
        if not date_filtered_data:
            try:
                report = LeaveApprovalReport.objects.get(id=report_id)
                report_file_path = os.path.join(settings.MEDIA_ROOT, report.report_data.name)
                with open(report_file_path, 'r') as file:
                    report_content = json.load(file)
            except LeaveApprovalReport.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Report not found'})

            date_filtered_data = report_content

        # If no fields are selected for filtration, default to all existing fields in the report
        if not selected_fields:
            if date_filtered_data:
                selected_fields = list(date_filtered_data[0].keys())  # Default to all keys in the first record
            else:
                selected_fields = []  # No data in the report
        # Get unique values for selected_fields from date-filtered data
        unique_values = self.get_unique_values_for_fields(date_filtered_data, selected_fields)

        processed_unique_values = {}
        for field, values in unique_values.items():
            processed_unique_values[field] = {
                'values': values,
            }

        return JsonResponse({
            'selected_fields': selected_fields,
            'report_id': report_id,
            'report_content': date_filtered_data,  # Pass filtered data to the frontend
            'unique_values': processed_unique_values,
        })

    def get_unique_values_for_fields(self, data, selected_fields):
        unique_values = {field: set() for field in selected_fields}
        # Extract data from the provided content
        for record in data:
            for field in selected_fields:
                if field in record:
                    unique_values[field].add(record[field])

        # Convert sets to lists
        for field in unique_values:
            unique_values[field] = list(unique_values[field])
        return unique_values

    @action(detail=False, methods=['post'])
    def approval_filter_report(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')

        # Retrieve filtered data from Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        filtered_data = cache.get(cache_key)

        if filtered_data is None:
            return JsonResponse({'status': 'error', 'message': 'No date-filtered data available'}, status=404)

        # Apply additional filtering here if needed
        # For example, based on other fields:
        additional_filters = {key: value for key, value in request.data.items() if key not in ('report_id',)}
        
        # Further filter based on additional criteria
        filtered_data = [
            row for row in filtered_data
            if all(row.get(key) == value for key, value in additional_filters.items())
        ]

        return JsonResponse({
            'filtered_data': filtered_data,
            'report_id': report_id,
        })

class AttendanceReportViewset(viewsets.ModelViewSet):
    queryset = AttendanceReport.objects.all()
    serializer_class = AttendanceReportSerializer
    
    def __init__(self, *args, **kwargs):
        super(AttendanceReportViewset, self).__init__(*args, **kwargs)
        self.attendance_standard_report_exists()
    def get_available_fields(self):
        excluded_fields = {'id', 'created_by'}
        included_emp_master_fields = { 'emp_first_name', 'emp_dept_id', 'emp_desgntn_id', 'emp_ctgry_id'}
        
        display_names = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "shift": "Shift",
            "date": "Date",
            "check_in_time":"Check In",
            "check_out_time": "Check Out",
            "total_hours":"Total Hours",
           
        }

        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name in included_emp_master_fields]
        attendance_fields = [field.name for field in Attendance._meta.get_fields() if isinstance(field, Field) and field.name not in excluded_fields]
        
        available_fields = {field: display_names.get(field, field) for field in emp_master_fields + attendance_fields}
        return available_fields

    @action(detail=False, methods=['get'])
    def select_attendancereport_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        return Response({'available_fields': available_fields})
       
    @action(detail=False, methods=['post'])
    def generate_leave_report(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                file_name = request.POST.get('file_name', 'report')
                fields_to_include = request.POST.getlist('fields', [])
                # from_date = parse_date(request.POST.get('from_date'))
                # to_date = parse_date(request.POST.get('to_date'))
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
            if not fields_to_include:
                fields_to_include = list(self.get_available_fields().keys())
            
            attendancereport = Attendance.objects.all()
            # documents = self.filter_documents_by_date_range(documents)

            report_data = self.generate_report_data(fields_to_include,attendancereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)  # Serialize dates to string format


            AttendanceReport.objects.create(file_name=file_name, report_data=file_name + '.json')
            return JsonResponse({'status': 'success', 'file_path': file_path,'selected_fields_data': fields_to_include,})
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

   
    def attendance_standard_report_exists(self):
        # Update the standard report if it exists, otherwise create a new one
        if AttendanceReport.objects.filter(file_name='attendance_std_report').exists():
            self.generate_standard_report()
        else:
            self.generate_standard_report()
    
    def generate_standard_report(self):
        try:
            file_name = 'attendance_std_report'
            fields_to_include = self.get_available_fields().keys()
            attendancereport = Attendance.objects.all()

            report_data = self.generate_report_data(fields_to_include, attendancereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')

            # Save report data to a file
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)

            # Update or create the standard report entry in the database
            AttendanceReport.objects.update_or_create(
                file_name=file_name,
                defaults={'report_data': file_name + '.json'}
            )

            print("Standard report generated successfully.")

        except Exception as e:
            print(f"Error generating standard report: {str(e)}")

    @action(detail=False, methods=['get'])
    def std_report(self, request, *args, **kwargs):
        try:
            # Ensure the standard report is up-to-date
            self.generate_standard_report()
            report = AttendanceReport.objects.get(file_name='attendance_std_report')
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        except AttendanceReport.DoesNotExist:
            return Response({"error": "Standard report not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def generate_report_data(self, fields_to_include,generalreport):
        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name != 'id']
        leave_request_fields = [field.name for field in Attendance._meta.get_fields() if isinstance(field, Field) and field.name != 'id']

        report_data = []
        for document in generalreport:
            general_data = {}
            for field in fields_to_include:
                if field in emp_master_fields:
                    value = getattr(document.employee, field, 'N/A')
                    if isinstance(value, date):
                        value = value.isoformat()
                elif field in leave_request_fields:
                    value = getattr(document, field, 'N/A')
                else:
                    value = 'N/A'
                general_data[field] = value
            report_data.append(general_data)
        return report_data
   
    @action(detail=False, methods=['get'])
    def select_filter_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        selected_fields = request.session.get('selected_fields', [])
        report_id = request.GET.get('report_id')
        
        return Response({
            'available_fields': available_fields,
            'selected_fields': selected_fields,
            'report_id': report_id
        })
    
    @action(detail=False, methods=['post'])
    def filter_by_date(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # Replace slashes with hyphens
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')

        # Parse and validate the date range
        try:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date format: {str(e)}'}, status=400)

        # Fetch report data from your database
        try:
            report_instance = AttendanceReport.objects.get(id=report_id)
            report_data = json.loads(report_instance.report_data.read().decode('utf-8'))
        except AttendanceReport.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)

        # Filter data by date range
        date_filtered_data = [
            row for row in report_data
            if 'date' in row and row['date'] and
            start_date <= datetime.fromisoformat(row['date']) <= end_date
        ]

        # Save filtered data to Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        cache.set(cache_key, date_filtered_data, timeout=None)  # Set timeout as needed

        return JsonResponse({
            'date_filtered_data': date_filtered_data,
            'report_id': report_id,
        })
    

    @action(detail=False, methods=['post'])
    def attendance_filter_table(self, request, *args, **kwargs):
        selected_fields = request.POST.getlist('selected_fields')
        report_id = request.data.get('report_id')

        # Save selected fields to session
        request.session['selected_fields'] = selected_fields

        # Fetch date-filtered report data from session
        date_filtered_data = request.session.get('date_filtered_data', [])
        print("previosly date filtered ",date_filtered_data)
        
        # If no date-filtered data, attempt to fetch full report
        if not date_filtered_data:
            try:
                report = AttendanceReport.objects.get(id=report_id)
                report_file_path = os.path.join(settings.MEDIA_ROOT, report.report_data.name)
                with open(report_file_path, 'r') as file:
                    report_content = json.load(file)
            except AttendanceReport.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Report not found'})

            date_filtered_data = report_content

        # If no fields are selected for filtration, default to all existing fields in the report
        if not selected_fields:
            if date_filtered_data:
                selected_fields = list(date_filtered_data[0].keys())  # Default to all keys in the first record
            else:
                selected_fields = []  # No data in the report
        # Get unique values for selected_fields from date-filtered data
        unique_values = self.get_unique_values_for_fields(date_filtered_data, selected_fields)

        processed_unique_values = {}
        for field, values in unique_values.items():
            processed_unique_values[field] = {
                'values': values,
            }

        return JsonResponse({
            'selected_fields': selected_fields,
            'report_id': report_id,
            'report_content': date_filtered_data,  # Pass filtered data to the frontend
            'unique_values': processed_unique_values,
        })

    def get_unique_values_for_fields(self, data, selected_fields):
        unique_values = {field: set() for field in selected_fields}
        # Extract data from the provided content
        for record in data:
            for field in selected_fields:
                if field in record:
                    unique_values[field].add(record[field])

        # Convert sets to lists
        for field in unique_values:
            unique_values[field] = list(unique_values[field])
        return unique_values

    @action(detail=False, methods=['post'])
    def approval_filter_report(self, request, *args, **kwargs):
        tenant_id = request.tenant.schema_name
        report_id = request.data.get('report_id')

        # Retrieve filtered data from Redis cache
        cache_key = f"{tenant_id}_{report_id}_date_filtered_data"
        filtered_data = cache.get(cache_key)

        if filtered_data is None:
            return JsonResponse({'status': 'error', 'message': 'No date-filtered data available'}, status=404)

        # Apply additional filtering here if needed
        # For example, based on other fields:
        additional_filters = {key: value for key, value in request.data.items() if key not in ('report_id',)}
        
        # Further filter based on additional criteria
        filtered_data = [
            row for row in filtered_data
            if all(row.get(key) == value for key, value in additional_filters.items())
        ]

        return JsonResponse({
            'filtered_data': filtered_data,
            'report_id': report_id,
        })
class LvBalanceReportViewset(viewsets.ModelViewSet):
    queryset = lvBalanceReport.objects.all()
    serializer_class = lvBalanceReportSerializer

    def __init__(self, *args, **kwargs):
        super(LvBalanceReportViewset, self).__init__(*args, **kwargs)
        self.lvbalance_standard_report_exists()
    def get_available_fields(self):
        excluded_fields = {'id', 'created_by'}
        included_emp_master_fields = { 'emp_first_name', 'emp_dept_id', 'emp_desgntn_id', 'emp_ctgry_id'}
        
        display_names = {
            "employee": "Employee Code",
            "emp_first_name": "First Name",
            "emp_branch_id":"Branches",
            "emp_dept_id": "Department",
            "emp_desgntn_id": "Designation",
            "emp_ctgry_id": "Category",
            "leave_type": "Leave Type",
            "balance": "Balance",
            "openings":"Openings",
            
           
        }

        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name in included_emp_master_fields]
        leave_balance = [field.name for field in emp_leave_balance._meta.get_fields() if isinstance(field, Field) and field.name not in excluded_fields]
        
        available_fields = {field: display_names.get(field, field) for field in emp_master_fields + leave_balance}
        return available_fields

    @action(detail=False, methods=['get'])
    def select_attendancereport_fields(self, request, *args, **kwargs):
        available_fields = self.get_available_fields()
        return Response({'available_fields': available_fields})
       
    @action(detail=False, methods=['post'])
    def generate_leave_report(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                file_name = request.POST.get('file_name', 'report')
                fields_to_include = request.POST.getlist('fields', [])
                # from_date = parse_date(request.POST.get('from_date'))
                # to_date = parse_date(request.POST.get('to_date'))
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
            if not fields_to_include:
                fields_to_include = list(self.get_available_fields().keys())
            
            attendancereport = emp_leave_balance.objects.all()
            # documents = self.filter_documents_by_date_range(documents)

            report_data = self.generate_report_data(fields_to_include,attendancereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)  # Serialize dates to string format


            lvBalanceReport.objects.create(file_name=file_name, report_data=file_name + '.json')
            return JsonResponse({'status': 'success', 'file_path': file_path,'selected_fields_data': fields_to_include,})
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

   
    def lvbalance_standard_report_exists(self):
        # Update the standard report if it exists, otherwise create a new one
        if lvBalanceReport.objects.filter(file_name='lvbalance_std_report').exists():
            self.generate_standard_report()
        else:
            self.generate_standard_report()
    
    def generate_standard_report(self):
        try:
            file_name = 'lvbalance_std_report'
            fields_to_include = self.get_available_fields().keys()
            lvbalancereport = emp_leave_balance.objects.all()

            report_data = self.generate_report_data(fields_to_include, lvbalancereport)
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + '.json')

            # Save report data to a file
            with open(file_path, 'w') as file:
                json.dump(report_data, file, default=str)

            # Update or create the standard report entry in the database
            lvBalanceReport.objects.update_or_create(
                file_name=file_name,
                defaults={'report_data': file_name + '.json'}
            )

            print("Standard report generated successfully.")

        except Exception as e:
            print(f"Error generating standard report: {str(e)}")

    @action(detail=False, methods=['get'])
    def std_report(self, request, *args, **kwargs):
        try:
            # Ensure the standard report is up-to-date
            self.generate_standard_report()
            report = lvBalanceReport.objects.get(file_name='lvbalance_std_report')
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        except lvBalanceReport.DoesNotExist:
            return Response({"error": "Standard report not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def generate_report_data(self, fields_to_include,generalreport):
        emp_master_fields = [field.name for field in emp_master._meta.get_fields() if isinstance(field, Field) and field.name != 'id']
        leave_request_fields = [field.name for field in emp_leave_balance._meta.get_fields() if isinstance(field, Field) and field.name != 'id']

        report_data = []
        for document in generalreport:
            general_data = {}
            for field in fields_to_include:
                if field in emp_master_fields:
                    value = getattr(document.employee, field, 'N/A')
                    if isinstance(value, date):
                        value = value.isoformat()
                elif field in leave_request_fields:
                    value = getattr(document, field, 'N/A')
                else:
                    value = 'N/A'
                general_data[field] = value
            report_data.append(general_data)
        return report_data
    

