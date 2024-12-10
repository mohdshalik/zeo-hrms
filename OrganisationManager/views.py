from django.shortcuts import render
from rest_framework.response import Response
from django.http import FileResponse, Http404
from rest_framework import status,generics,viewsets,permissions
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view
from django.http import FileResponse
from openpyxl import load_workbook
from docx import Document
from django_tenants.utils import schema_context
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import (brnch_mstr,dept_master,document_numbering,
                     desgntn_master,ctgry_master,FiscalPeriod,FiscalYear,CompanyPolicy,AssetMaster, AssetTransaction,Asset_CustomFieldValue)

from . serializer import (BranchSerializer,PermissionSerializer,GroupSerializer,permserializer,DocumentNumberingSerializer,
                          CtgrySerializer,DeptSerializer,DesgSerializer,FiscalYearSerializer,PeriodSerializer,DeptUploadSerializer,
                          DesgUploadSerializer,CompanyPolicySerializer,AssetMasterSerializer,AssetTransactionSerializer,Asset_CustomFieldValueSerializer)
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly,IsAdminUser
from .resource import (DepartmentResource,DesignationResource,DesgtnReportResource,DeptReportResource)
from EmpManagement.models import emp_master
from UserManagement.permissions import IsAdminUser,IsSuperUser
from datetime import timedelta
from rest_framework.views import APIView
from openpyxl import Workbook
from django.http import JsonResponse
from tablib import Dataset
from openpyxl.styles import PatternFill,Alignment,Font
from django.http import HttpResponse
from io import BytesIO
from UserManagement.permissions import BranchPermission,DepartmentPermission,DesignationPermission,CategoryPermission
# Create your views here.
from django.contrib.auth.models import Permission,Group
from django.core.exceptions import PermissionDenied
from tenant_users.tenants.models import UserTenantPermissions
from rest_framework.decorators import action
import subprocess
import os
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

def get_model_permissions(model):
    content_type = ContentType.objects.get_for_model(model)
    permissions = Permission.objects.filter(
        Q(content_type=content_type)
    )
    return permissions
class BranchViewSet(viewsets.ModelViewSet):
    queryset = brnch_mstr.objects.all()
    serializer_class = BranchSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['tenant_id'] = self.request.query_params.get('tenant_id')
        return context  
    
    @action(detail=True, methods=['POST', 'GET'])
    def policies(self, request, pk=None):
        employee = self.get_object()
        if request.method == 'GET':
            family_members = employee.policies.all()
            serializer = CompanyPolicySerializer(family_members, many=True)
            return Response(serializer.data)
#DEPARTMENT 
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = dept_master.objects.all()
    serializer_class = DeptSerializer
    # authentication_classes = [SessionAuthentication,]
    # permission_classes = [DepartmentPermission]
    def get_queryset(self):
        queryset = super().get_queryset()

        # Retrieve the branch_id from the query parameters
        branch_id = self.request.query_params.get('branch_id')

        # Filter departments based on the provided branch_id
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        return queryset  

    @action(detail=False, methods=['get'])
    def department_report(self, request):
        queryset = dept_master.objects.all()
        resource = DeptReportResource()
        dataset = resource.export(queryset)

        # Get the fields from the resource
        fields = [field.column_name for field in resource.get_fields()]

        # Prepare JSON response
        data = [
            {field: row[field] if field != 'dept_is_active' else (True if row[field] else False)
            for field in fields}
            for row in dataset.dict
        ]
        
        return JsonResponse(data, safe=False)
        
    
    @action(detail=False, methods=['get'])
    def deparment_excel_report(self,request):
        if request.method == 'GET':
            queryset = dept_master.objects.all()
            resource = DeptReportResource()
            dataset = resource.export(queryset)

            fields = [field.column_name for field in resource.get_fields()]
            # Create an Excel workbook
            wb = Workbook()
            ws = wb.active

            # Define default cell formats
            default_fill = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')  # pink background color
            default_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

            # Apply default styles to headings
            for col_num, field_name in enumerate(dataset.headers):
                ws.cell(row=1, column=col_num + 1, value=field_name)
                ws.cell(row=1, column=col_num + 1).fill = default_fill
                ws.cell(row=1, column=col_num + 1).alignment = default_alignment

            # Write data to the Excel file with boolean conversion
            for row_num, row in enumerate(dataset.dict, start=2):
                for col_num, field_name in enumerate(fields, start=1):
                    value = row[field_name]
                    if field_name == 'dept_is_active':
                        value = 'True' if value else 'False'
                    ws.cell(row=row_num, column=col_num, value=value)
                    ws.cell(row=row_num, column=col_num).alignment = default_alignment

            # Auto-size columns
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[col[0].column_letter].width = adjusted_width

            # Save the workbook to an in-memory buffer
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            # Prepare response
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="deparment_Report.xlsx"'
            return response
    @action(detail=True, methods=['POST', 'GET'])
    def policies(self, request, pk=None):
        employee = self.get_object()
        if request.method == 'GET':
            family_members = employee.policies.all()
            serializer = CompanyPolicySerializer(family_members, many=True)
            return Response(serializer.data)
@api_view(['POST'])
def save_notification_settings(request):
    selected_departments = request.data.get('departments', [])
    branch_id = request.data.get('branch_id')

    try:
        branch = brnch_mstr.objects.get(id=branch_id)
    except brnch_mstr.DoesNotExist:
        return Response({"error": "Branch not found"}, status=404)

    # Assuming you store department notification settings per branch
    branch.departments.set(selected_departments)
    branch.save()

    return Response({"status": "success"})

 #Dept BulkUpload       
class DeptBulkUploadViewSet(viewsets.ModelViewSet):
    queryset = dept_master.objects.all()
    serializer_class = DeptUploadSerializer
    

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            excel_file = request.FILES['file']
            if excel_file.name.endswith('.xlsx'):
                try:
                    # Load data from the Excel file into a Dataset
                    dataset = Dataset()
                    dataset.load(excel_file.read(), format='xlsx')

                    # Create a resource instance
                    resource = DepartmentResource()

                    # Import data into the model using the resource
                    result = resource.import_data(dataset, dry_run=False, raise_errors=True)

                    return Response({"message": f"{result.total_rows} records created successfully"})
                except Exception as e:
                    return Response({"error": str(e)}, status=400)
            else:
                return Response({"error": "Invalid file format. Only Excel files (.xlsx) are supported."}, status=400)
        else:
            return Response({"error": "Please provide an Excel file."}, status=400)

#DESIGNATION 
class DesignationViewSet(viewsets.ModelViewSet):
    queryset = desgntn_master.objects.all()
    serializer_class = DesgSerializer
    # authentication_classes = [SessionAuthentication,]
    # permission_classes = [DesignationPermission,] 
    
    @action(detail=False, methods=['get'])
    def designation_report(self, request):
        queryset = desgntn_master.objects.all()
        resource = DesgtnReportResource()
        dataset = resource.export(queryset)

        # Get the fields from the resource
        fields = [field.column_name for field in resource.get_fields()]

        # Prepare JSON response
        data = [
            {field: row[field] if field != 'desgntn_is_active' else (True if row[field] else False)
            for field in fields}
            for row in dataset.dict
        ]
        print(data)
        return JsonResponse(data, safe=False)

    @action(detail=True, methods=['POST', 'GET'])
    def policies(self, request, pk=None):
        employee = self.get_object()
        if request.method == 'GET':
            family_members = employee.policies.all()
            serializer = CompanyPolicySerializer(family_members, many=True)
            return Response(serializer.data)   
    
    @action(detail=False, methods=['get'])
    def designation_excel_report(self,request):
        if request.method == 'GET':
            queryset = desgntn_master.objects.all()
            resource = DesgtnReportResource()
            dataset = resource.export(queryset)

            fields = [field.column_name for field in resource.get_fields()]
            # Create an Excel workbook
            wb = Workbook()
            ws = wb.active

            # Define default cell formats
            default_fill = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')  # pink background color
            default_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

            # Apply default styles to headings
            for col_num, field_name in enumerate(dataset.headers):
                ws.cell(row=1, column=col_num + 1, value=field_name)
                ws.cell(row=1, column=col_num + 1).fill = default_fill
                ws.cell(row=1, column=col_num + 1).alignment = default_alignment

            # Write data to the Excel file with boolean conversion
            for row_num, row in enumerate(dataset.dict, start=2):
                for col_num, field_name in enumerate(fields, start=1):
                    value = row[field_name]
                    if field_name == 'desgntn_is_active':
                        value = 'True' if value else 'False'
                    ws.cell(row=row_num, column=col_num, value=value)
                    ws.cell(row=row_num, column=col_num).alignment = default_alignment

            # Auto-size columns
            for col in ws.columns:
                max_length = 0
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                ws.column_dimensions[col[0].column_letter].width = adjusted_width

            # Save the workbook to an in-memory buffer
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            # Prepare response
            response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="designtn_Report.xlsx"'
            return response

    

#Designation BulkUpload
class DesignationBulkUploadViewSet(viewsets.ModelViewSet):
    queryset = desgntn_master.objects.all()
    serializer_class = DesgUploadSerializer
   
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            excel_file = request.FILES['file']
            if excel_file.name.endswith('.xlsx'):
                try:
                    # Load data from the Excel file into a Dataset
                    dataset = Dataset()
                    dataset.load(excel_file.read(), format='xlsx')

                    # Create a resource instance
                    resource = DesignationResource()

                    # Import data into the model using the resource
                    result = resource.import_data(dataset, dry_run=False, raise_errors=True)

                    return Response({"message": f"{result.total_rows} records created successfully"})
                except Exception as e:
                    return Response({"error": str(e)}, status=400)
            else:
                return Response({"error": "Invalid file format. Only Excel files (.xlsx) are supported."}, status=400)
        else:
            return Response({"error": "Please provide an Excel file."}, status=400)

#CATOGARY CRUD
class CatogoryViewSet(viewsets.ModelViewSet):
    queryset = ctgry_master.objects.all()
    serializer_class = CtgrySerializer
    # authentication_classes = [SessionAuthentication,]
    permission_classes = [CategoryPermission,] 
    

class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the FiscalYear instance
        self.perform_create(serializer)
        
        # Automatically create 12 FiscalPeriod instances with a gap of 30 days
        fiscal_year = serializer.instance
        start_date = fiscal_year.start_date
        for period_number in range(1, 13):
            period_start_date = start_date + timedelta(days=(period_number - 1) * 30)
            period_end_date = period_start_date + timedelta(days=29)
            FiscalPeriod.objects.create(
                fiscal_year=fiscal_year,
                period_number=period_number,
                start_date=period_start_date,
                end_date=period_end_date,
                branch=fiscal_year.branch_id
            )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = FiscalPeriod.objects.all()
    serializer_class = PeriodSerializer

class CompanyFiscalData(APIView):
    def get(self, request, company_id):
        try:
            fiscal_years = FiscalYear.objects.filter(company_id=company_id)
            fiscal_years_serializer = FiscalYearSerializer(fiscal_years, many=True)
            
            fiscal_periods = FiscalPeriod.objects.filter(company_id=company_id)
            fiscal_periods_serializer = PeriodSerializer(fiscal_periods, many=True)
            
            return Response({
                'fiscal_years': fiscal_years_serializer.data,
                'fiscal_periods': fiscal_periods_serializer.data
            })
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        

class permissionviewset(viewsets.ModelViewSet):
    queryset = UserTenantPermissions.objects.all()
    serializer_class = PermissionSerializer
    def get_serializer_class(self):
        return PermissionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Filter queryset based on authenticated user's profile ID
            return UserTenantPermissions.objects.filter(profile_id=user.id)
        return UserTenantPermissions.objects.none() 
    # def get_queryset(self):
    # def get_queryset(self):
    #     user = self.request.user
    #     return UserTenantPermissions.objects.filter(profile=user)  # Optional filtering

    # serializer_class = PermissionSerializer

class Groupviewset(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class permviewset(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class=permserializer

class DocNumberingviewset(viewsets.ModelViewSet):
    queryset = document_numbering.objects.all()
    serializer_class = DocumentNumberingSerializer
    def create(self, request, *args, **kwargs):
        branch_id = request.data.get('branch_id')
        category = request.data.get('category')

        if document_numbering.objects.filter(branch_id=branch_id, category=category).exists():
            raise ValidationError({'error': 'A document numbering record already exists for this branch and category.'})

        return super().create(request, *args, **kwargs)


from django.shortcuts import get_object_or_404
    
class FiscalYearDatesView(APIView):
    def get(self, request, fiscal_year_id):
        try:
            fiscal_year = FiscalYear.objects.get(id=fiscal_year_id)
        except FiscalYear.DoesNotExist:
            return Response({"error": "Fiscal year not found."}, status=status.HTTP_404_NOT_FOUND)

        start_date = fiscal_year.start_date
        end_date = fiscal_year.end_date

        if start_date is None or end_date is None:
            return Response({"error": "Fiscal year does not have valid start and end dates."}, status=status.HTTP_400_BAD_REQUEST)

        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        return Response({
            "fiscal_year": fiscal_year.id,
            "branch": fiscal_year.branch_id.id,
            "dates": date_list
        })
    
class FiscalPeriodDatesView(APIView):
    def get(self, request, fiscal_year_id, period_number):
        try:
            fiscal_period = FiscalPeriod.objects.get(fiscal_year_id=fiscal_year_id, period_number=period_number)
        except FiscalPeriod.DoesNotExist:
            return Response({"error": "Fiscal period not found."}, status=404)

        start_date = fiscal_period.start_date
        end_date = fiscal_period.end_date

        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        return Response({
            "fiscal_year": fiscal_period.fiscal_year.id,
            "period_number": fiscal_period.period_number,
            "branch": fiscal_period.branch.id,
            "dates": date_list
        })
    
class CompanyPolicyViewSet(viewsets.ModelViewSet):
    queryset = CompanyPolicy.objects.all()
    serializer_class = CompanyPolicySerializer
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                return self.queryset

            # Check if user is listed in `specific_users`
            if self.queryset.filter(specific_users=user).exists():
                return self.queryset.filter(specific_users=user)

            # Get the employee's branch, department, and category if the user is an ESS user
            if user.is_ess:
                emp_branch = user.emp_master.emp_branch_id
                emp_dept = user.emp_master.emp_dept_id
                emp_category = user.emp_master.emp_ctgry_id

                # Filter policies by matching the branch, department, and category
                return self.queryset.filter(
                    branch=emp_branch,
                    department=emp_dept,
                    category=emp_category
                )
        
        return CompanyPolicy.objects.none()
    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         if user.is_superuser:
    #             return self.queryset
    #         # Get the employee's branch, department, and category
    #         emp_branch = user.emp_master.emp_branch_id
    #         emp_dept = user.emp_master.emp_dept_id
    #         emp_category = user.emp_master.emp_ctgry_id

    #         # Filter policies by matching the branch, department, and category
    #         return self.queryset.filter(
    #             branch=emp_branch,
    #             department=emp_dept,
    #             category=emp_category
    #         )
    #     return CompanyPolicy.objects.none()
    
    @action(detail=True, methods=['get'], url_path='download', url_name='download_policy')
    def download_policy(self, request, pk=None):
        policy = self.get_object()

        if not policy.policy_file:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        file_extension = os.path.splitext(policy.policy_file.name)[1].lower()

        if file_extension == '.docx':
            return self.convert_docx_to_pdf(policy)

        elif file_extension == '.xlsx':
            return self.convert_xlsx_to_pdf(policy)
        elif file_extension == '.txt':
            return self.convert_txt_to_pdf(policy)

        elif file_extension == '.pdf':
            try:
                response = FileResponse(policy.policy_file.open(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{policy.title}.pdf"'
                return response
            except FileNotFoundError:
                raise Http404("File not found")

        else:
            return Response({'error': 'Unsupported file format'}, status=status.HTTP_400_BAD_REQUEST)

    def convert_docx_to_pdf(self, policy):
        """
        Convert .docx content to a readable paragraph format in a PDF.
        """
        doc = Document(policy.policy_file)
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y_position = height - 50  # Starting position for text
        
        # Read each paragraph and add it as text to the PDF
        for para in doc.paragraphs:
            if y_position < 50:  # Check if page needs to be advanced
                pdf_canvas.showPage()
                y_position = height - 50
            text = para.text
            pdf_canvas.drawString(50, y_position, text)
            y_position -= 20  # Move down for the next line

        pdf_canvas.save()

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'{policy.title}.pdf')

    def convert_xlsx_to_pdf(self, policy):
        """
        Convert .xlsx content to a paragraph-like format in a PDF.
        """
        policy.policy_file.open()
        workbook = load_workbook(policy.policy_file)
        sheet = workbook.active

        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y_position = height - 50  # Starting position for text

        # Iterate over rows and columns to format as paragraph-like text
        for row in sheet.iter_rows(values_only=True):
            row_text = ', '.join([str(cell) for cell in row if cell is not None])  # Join all cells with a comma
            if y_position < 50:  # Check if page needs to be advanced
                pdf_canvas.showPage()
                y_position = height - 50

            pdf_canvas.drawString(50, y_position, row_text)
            y_position -= 20  # Move down for the next line

        pdf_canvas.save()

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'{policy.title}.pdf')

    def convert_txt_to_pdf(self, policy):
        """
        Convert .txt content to a readable paragraph format in a PDF.
        """
        policy.policy_file.open()
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y_position = height - 50  # Starting position for text

        # Read the .txt file line by line and write it to the PDF
        for line in policy.policy_file:
            if y_position < 50:  # Check if page needs to be advanced
                pdf_canvas.showPage()
                y_position = height - 50

            # Decode if it's a binary file (bytes) to text
            text = line.decode('utf-8').strip()
            pdf_canvas.drawString(50, y_position, text)
            y_position -= 20  # Move down for the next line

        pdf_canvas.save()

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'{policy.title}.pdf')
    
def list_data_in_schema(request):
    schema_name = request.tenant.schema_name  # This gets the current tenant's schema name

    # Use schema_context to switch to the tenant's schema
    with schema_context(schema_name):
        # Fetch branches, departments, and designations within the schema
        branches = brnch_mstr.objects.all()
        departments = dept_master.objects.all()
        designations = desgntn_master.objects.all()
        categories=ctgry_master.objects.all()

        # Structure the data to send in the response
        data = {
            'branches': [
                {'id': branch.id, 'name': branch.branch_name} for branch in branches
            ],
            'departments': [
                {'id': dept.id, 'name': dept.dept_name} for dept in departments
            ],
            'designations': [
                {'id': desig.id, 'name': desig.desgntn_job_title} for desig in designations
            ],
            'categories': [
                {'id': cat.id, 'name': cat.ctgry_title} for cat in categories
            ]
        }

        # Return the data as a JSON response
        return JsonResponse(data)

class AssetMasterViewSet(viewsets.ModelViewSet):
    queryset = AssetMaster.objects.all()
    serializer_class = AssetMasterSerializer

class AssetTransactionViewSet(viewsets.ModelViewSet):
    queryset = AssetTransaction.objects.all()
    serializer_class = AssetTransactionSerializer
    
class Asset_CustomFieldValueViewSet(viewsets.ModelViewSet):
    queryset = Asset_CustomFieldValue.objects.all()
    serializer_class = Asset_CustomFieldValueSerializer
