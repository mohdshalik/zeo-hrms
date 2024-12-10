from rest_framework import serializers
from django.utils import timezone
from .models import (leave_type,leave_entitlement,emp_leave_balance,leave_accrual_transaction,employee_leave_request,
                     applicablity_critirea,leave_reset_transaction,Attendance,Shift,ShiftPattern,EmployeeShiftSchedule,
                    ShiftOverride,WeekPatternAssignment,EmployeeMachineMapping,LeaveReport,
                     LeaveApprovalLevels,LeaveApproval,LvApprovalNotify,LvEmailTemplate,LvCommonWorkflow,LvRejectionReason,LeaveApprovalReport,
                    AttendanceReport,lvBalanceReport,CompensatoryLeaveRequest,CompensatoryLeaveBalance,CompensatoryLeaveTransaction,EmployeeYearlyCalendar

                     )

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = leave_type
        fields = '__all__'

class ApplicableSerializer(serializers.ModelSerializer):
    class Meta:
        model = applicablity_critirea
        fields = '__all__'
        
class AccrualSerializer(serializers.ModelSerializer):
    class Meta:
        model = leave_accrual_transaction
        fields = '__all__'


class ResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = leave_reset_transaction
        fields = '__all__'


class LeaveEntitlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = leave_entitlement
        fields = '__all__'


# class LeavePolicySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = emp_leave_balance
#         fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = employee_leave_request
        fields = '__all__'
    def to_representation(self, instance):
        rep = super(LeaveRequestSerializer, self).to_representation(instance)
        if instance.employee:  
            rep['employee'] = instance.employee.emp_first_name
        if instance.leave_type:  
            rep['leave_type'] = instance.leave_type.name
        
        return rep
    def validate(self, data):
        leave_type = data['leave_type']
        is_half_day = data.get('is_half_day', False)
        half_day_period = data.get('half_day_period')

        # Validate leave duration based on the unit
        if leave_type.unit == 'hours' and (data['leave_duration'] > 8 or data['leave_duration'] <= 0):
            raise serializers.ValidationError("For hourly leave types, duration must be between 0 and 8 hours.")
        
        if leave_type.unit == 'days':
            if is_half_day:
                if data['start_date'] != data['end_date']:
                    raise serializers.ValidationError("For half-day leave, start date and end date must be the same.")
                if not half_day_period:
                    raise serializers.ValidationError("Please specify whether the half-day is in the first or second half.")
            # elif data['leave_duration'] != 1:
            #     raise serializers.ValidationError("For daily leave types, duration must be a full day (1 day).")
        
        return data

class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type = serializers.PrimaryKeyRelatedField(queryset=leave_type.objects.none())

    class Meta:
        model = emp_leave_balance
        fields = '__all__'
#         extra_fields = ['applicable_leave_types']
#     def __init__(self, *args, **kwargs):
#         employee_id = kwargs.pop('employee_id', None)
#         super().__init__(*args, **kwargs)
#         if employee_id:
#             try:
#                 employee = emp_master.objects.get(id=employee_id)
#             except emp_master.DoesNotExist:
#                 raise serializers.ValidationError("Employee not found")
#             self.fields['leave_type'].queryset = leave_type.objects.filter(
#                 id__in=emp_leave_balance.objects.filter(employee=employee).values_list('leave_type_id', flat=True)
#             )


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields ='__all__'
    def to_representation(self, instance):
        rep = super(AttendanceSerializer, self).to_representation(instance)
        if instance.shift:  
            rep['shift'] = instance.shift.name
        if instance.employee:  
            rep['employee'] = instance.employee.emp_code
        return rep
    def update(self, instance, validated_data):
        # Detect if the date has been updated
        new_date = validated_data.get('date', instance.date)
        if new_date != instance.date:
            # Recalculate the shift if the date is updated
            schedule = EmployeeShiftSchedule.objects.filter(employee=instance.employee).first()
            if schedule:
                new_shift = schedule.get_shift_for_date(instance.employee, new_date)
                validated_data['shift'] = new_shift
        else:
            # If the date is not updated, retain the current shift
            validated_data['shift'] = instance.shift  # Keep the existing shift

        # Update fields
        instance.shift = validated_data.get('shift', instance.shift)
        instance.date = new_date
        instance.check_in_time = validated_data.get('check_in_time', instance.check_in_time)
        instance.check_out_time = validated_data.get('check_out_time', instance.check_out_time)

        # Calculate total hours if check-out time is updated
        if instance.check_in_time and instance.check_out_time:
            instance.calculate_total_hours()
        instance.save()
        return instance
    
class ImportAttendanceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = Attendance
        fields ='__all__'

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'
class ShiftPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftPattern
        fields = '__all__'
        
class ShiftOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftOverride
        fields = '__all__'

class EmployeeShiftScheduleSerializer(serializers.ModelSerializer):
    # week_patterns = ShiftPatternSerializer(many=True, read_only=True)
    start_date = serializers.DateField(default=timezone.now().date)
    class Meta:
        model = EmployeeShiftSchedule
        fields = '__all__'
    
class WeekPatternAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekPatternAssignment
        fields = '__all__'
class EmployeeMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeMachineMapping
        fields = '__all__'
class LeaveReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveReport
        fields = '__all__'

class LvApprovalLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApprovalLevels
        fields = '__all__'
    def to_representation(self, instance):
        rep = super(LvApprovalLevelSerializer, self).to_representation(instance)
        if instance.request_type:  
            rep['request_type'] = instance.request_type.name
        if instance.approver:  
            rep['approver'] = instance.approver.username    
        return rep
class LvApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApproval
        fields = '__all__'
    def to_representation(self, instance):
        rep = super(LvApprovalSerializer, self).to_representation(instance)
        if instance.approver:
            rep['approver'] = instance.approver.username   
        if instance.leave_request:
            rep['leave_request'] = instance.leave_request.leave_type.name  
        return rep
   

class LvEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LvEmailTemplate
        fields = '__all__'
class LvApprovalNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = LvApprovalNotify
        fields = '__all__'

class LvCommonWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = LvCommonWorkflow
        fields = '__all__'
class LvRejectionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LvRejectionReason
        fields = '__all__'
class LvApprovalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApprovalReport
        fields = '__all__'

class AttendanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceReport
        fields = '__all__'
class lvBalanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = lvBalanceReport
        fields = '__all__'

class CompensatoryLeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompensatoryLeaveRequest
        fields ='__all__'
    

class CompensatoryLeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompensatoryLeaveBalance
        fields = '__all__'

class CompensatoryLeaveTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompensatoryLeaveTransaction
        fields = '__all__'

class EmployeeYearlyCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeYearlyCalendar
        fields = '__all__'