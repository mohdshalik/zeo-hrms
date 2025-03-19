from rest_framework import serializers
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollRun,Payslip,PayrollFormula,PayslipComponent,LoanType,LoanApplication,
                    LoanRepayment,LoanApprovalLevels,LoanApproval)



class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'


class EmployeeSalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSalaryStructure
        fields = '__all__'

class PayrollFormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollFormula
        fields = '__all__'
class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'
class PaySlipComponentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PayslipComponent
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
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