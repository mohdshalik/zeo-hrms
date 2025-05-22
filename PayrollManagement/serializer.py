from rest_framework import serializers
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollRun,Payslip,PayslipComponent,LoanType,LoanApplication,
                    LoanRepayment,LoanApprovalLevels,LoanApproval)



class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'


class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    emp_code = serializers.SerializerMethodField()  # Field for emp_code from emp_master
    component_name = serializers.SerializerMethodField()  # Field for name from SalaryComponent

    class Meta:
        model = EmployeeSalaryStructure
        fields = '__all__'  # Include all fields from the model
        # Optionally, explicitly list fields to include emp_code and component_name
        # fields = ['id', 'employee', 'component', 'amount', 'is_active', 'date_created', 'date_updated', 'emp_code', 'component_name']

    def get_emp_code(self, obj):
        return obj.employee.emp_code  # Fetch emp_code from the related emp_master

    def get_component_name(self, obj):
        return obj.component.name  # Fetch name from the related SalaryComponent

    def to_representation(self, instance):
        """
        Customize the output to replace employee and component IDs with emp_code and component_name.
        """
        rep = super().to_representation(instance)
        rep['employee'] = self.get_emp_code(instance)  # Replace employee ID with emp_code
        rep['component'] = self.get_component_name(instance)  # Replace component ID with name
        return rep
class EmpBulkuploadSalaryStructureSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = EmployeeSalaryStructure
        fields = '__all__'

# class PayrollFormulaSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PayrollFormula
#         fields = '__all__'
class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'
class PaySlipComponentSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)
    component_type = serializers.CharField(source='component.get_component_type_display', read_only=True)

    class Meta:
        model = PayslipComponent
        fields = ['id', 'component_name', 'component_type', 'amount']


class PayslipSerializer(serializers.ModelSerializer):
    payroll_run = PayrollRunSerializer(read_only=True)
    employee = serializers.StringRelatedField()  # Displays employee's string representation
    components = PaySlipComponentSerializer(many=True, read_only=True)
    class Meta:
        model = Payslip
        fields = '__all__'




class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = '__all__'
class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = '__all__'
class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = '__all__'
class LoanApprovalLevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApprovalLevels
        fields = '__all__'
class LoanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApproval
        fields = '__all__'