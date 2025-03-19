import re
from decimal import Decimal
from django.db import transaction
from .models import PayrollRun, Payslip, PayslipComponent, EmployeeSalaryStructure
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .models import Payslip, PayslipComponent
import io

def process_payroll(payroll_run_id):
    payroll_run = PayrollRun.objects.get(id=payroll_run_id)  # Use 'id' as the field name    # Fetch employees based on branch (and optionally dept/category)
    employees = payroll_run.branch.emp_master_set.all()  # Assuming emp_master has a related_name to branch
    
    with transaction.atomic():  # Ensure atomicity
        for employee in employees:
            # Get employee's salary structure
            salary_structures = EmployeeSalaryStructure.objects.filter(employee=employee, is_active=True)
            
            # Initialize totals
            total_additions = Decimal('0.00')
            total_deductions = Decimal('0.00')
            basic_salary = None
            
            # Create payslip
            payslip = Payslip.objects.create(
                payroll_run=payroll_run,
                employee=employee,
                status='pending'
            )
            
            # Process each component
            for structure in salary_structures:
                component = structure.component
                amount = structure.amount or Decimal('0.00')
                
                # Save to PayslipComponent
                PayslipComponent.objects.create(
                    payslip=payslip,
                    component=component,
                    amount=amount
                )
                
                # Categorize amounts
                if component.component_type == 'addition':
                    total_additions += amount
                    if component.name.lower() == 'basic':  # Assuming 'Basic' is the basic salary component
                        basic_salary = amount
                elif component.component_type == 'deduction':
                    total_deductions += amount
            
            # Calculate gross and net salary
            gross_salary = total_additions
            net_salary = total_additions - total_deductions
            
            # Apply formula (basic parsing for now)
            formula = payroll_run.pay_formula.formula_text
            components_dict = {s.component.name: s.amount for s in salary_structures}
            try:
                net_salary = eval_formula(formula, components_dict)
            except Exception as e:
                raise ValueError(f"Error evaluating formula: {e}")
            
            # Update payslip
            payslip.basic_salary = basic_salary
            payslip.gross_salary = gross_salary
            payslip.net_salary = net_salary
            payslip.total_additions = total_additions
            payslip.total_deductions = total_deductions
            payslip.save()
        
        # Mark payroll as processed
        payroll_run.status = 'processed'
        payroll_run.save()

def eval_formula(formula, components_dict):
    # Replace component names with their values in the formula
    for name, value in components_dict.items():
        formula = formula.replace(name, str(value or 0))
    return Decimal(eval(formula))  # Use with caution; consider a safer parser


def generate_payslip_pdf(payslip):
    """Generate a PDF payslip for the given Payslip instance."""
    # Create a buffer to hold the PDF data
    buffer = io.BytesIO()

    # Create the PDF object using ReportLab
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Styles for text
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']

    # Add company header (customize as needed)
    elements.append(Paragraph("Company Name: ZEO HRMS", title_style))
    elements.append(Paragraph(f"Payslip for {payslip.employee.emp_first_name} {payslip.employee.emp_last_name or ''}", normal_style))
    elements.append(Paragraph(f"Payroll Period: {payslip.payroll_run.get_month_display()} {payslip.payroll_run.year}", normal_style))
    elements.append(Spacer(1, 12))

    # Employee details
    employee_details = [
        ["Employee Code", payslip.employee.emp_code],
        ["Department", payslip.employee.emp_dept_id.dept_name if payslip.employee.emp_dept_id else "N/A"],
        ["Branch", payslip.employee.emp_branch_id.branch_name if payslip.employee.emp_branch_id else "N/A"],
    ]
    employee_table = Table(employee_details, colWidths=[200, 200])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 12))

    # Salary components table
    components = PayslipComponent.objects.filter(payslip=payslip)
    data = [["Component", "Amount"]]
    for component in components:
        data.append([component.component.name, f"{component.amount:.2f}"])

    # Add totals
    data.append(["", ""])
    data.append(["Gross Salary", f"{payslip.gross_salary:.2f}"])
    data.append(["Total Deductions", f"{payslip.total_deductions:.2f}"])
    data.append(["Net Salary", f"{payslip.net_salary:.2f}"])

    salary_table = Table(data, colWidths=[200, 200])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Right-align amounts
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 12))

    # Footer
    elements.append(Paragraph("Generated by ZEO HRMS", normal_style))

    # Build the PDF
    pdf.build(elements)

    # Get the PDF data from the buffer
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    # Return the PDF as an HTTP response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.employee.emp_code}_{payslip.payroll_run.month}_{payslip.payroll_run.year}.pdf"'
    return response