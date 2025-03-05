from rest_framework import serializers
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollTransaction,Payslip,PayrollFormula,PaySlipComponent,LoanType,LoanApplication,
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
class PayrollTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollTransaction
        fields = ['transaction_id', 'employee', 'pay_period_start', 'pay_period_end',
                  'gross_pay', 'net_pay', 'payment_date', 'status']
        read_only_fields = ['transaction_id', 'gross_pay', 'net_pay']
        extra_kwargs = {
            'pay_period_start': {'style': {'placeholder': 'YYYY-MM-DD', 'autofocus': True}},
            'pay_period_end': {'style': {'placeholder': 'YYYY-MM-DD'}},
            'payment_date': {'style': {'placeholder': 'YYYY-MM-DD'}},
        }
class PaySlipComponentSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='salary_component.name')
    
    class Meta:
        model = PaySlipComponent
        fields = ['component_name', 'amount']


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