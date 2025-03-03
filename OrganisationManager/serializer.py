from .models import (brnch_mstr,dept_master,desgntn_master,DocumentNumbering,
                     ctgry_master,FiscalPeriod,FiscalYear,CompanyPolicy,AssetMaster,AssetMaster, AssetTransaction,Asset_CustomFieldValue)
from rest_framework import serializers
from tenant_users.tenants.models import UserTenantPermissions
from django.contrib.auth.models import Permission,Group
from calendars .models import assign_holiday,holiday,holiday_calendar

class CompanyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyPolicy
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    holidays = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()  # Add this field

    class Meta:
        model = brnch_mstr
        fields = '__all__'

    # def get_holidays(self, obj):
    #     from calendars.serializer import HolidaySerializer
    #     assigned_holidays = assign_holiday.objects.filter(branch=obj).values_list('holiday_model__holiday', flat=True)
    #     holidays = holiday.objects.filter(id__in=assigned_holidays)
    #     return HolidaySerializer(holidays, many=True).data

    # def get_policies(self, obj):
    #     """Fetch company policies assigned to this branch."""
    #     # from OrganisationManager.serializer import CompanyPolicySerializer  # Import the serializer
    #     policies = obj.policies.all()  # Using related_name='policies' from CompanyPolicy model
    #     return CompanyPolicySerializer(policies, many=True).data
    def get_holidays(self, obj):
        from calendars.serializer import HolidaySerializer
        """Fetch assigned holidays for the branch."""
        assigned_holidays = assign_holiday.objects.filter(branch=obj).values_list('holiday_model__id', flat=True)
        holidays = holiday.objects.filter(id__in=assigned_holidays).distinct()
        return HolidaySerializer(holidays, many=True).data

    def get_policies(self, obj):
        """Fetch company policies assigned to this branch."""
        if hasattr(obj, 'policies'):  # Ensure the related field exists
            policies = obj.policies.all()
            return CompanyPolicySerializer(policies, many=True).data
        return []
    
    # def to_representation(self, instance):
    #     rep = super(BranchSerializer, self).to_representation(instance)
    #     rep['br_state_id'] = instance.br_state_id.state_name
    #     rep['br_country'] = instance.br_country.country_name
    #     rep['br_company_id'] = instance.br_company_id.cmpny_name
    #     return rep
# class CompanySerializer(serializers.ModelSerializer):
#     cmpny_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
#     cmpny_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
#     branches = BranchSerializer(many=True, read_only=True)
#     class Meta:
#         model = cmpny_mastr
#         fields = '__all__'
#     def to_representation(self, instance):
#         rep = super(CompanySerializer, self).to_representation(instance)
#         rep['cmpny_state_id'] = instance.cmpny_state_id.state_name
#         rep['cmpny_country'] = instance.cmpny_country.country_name
#         return rep

#DEPARTMENT SERIALIZER
class DeptSerializer(serializers.ModelSerializer):
    # dept_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # dept_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = dept_master
        fields= '__all__'
    def to_representation(self, instance):
        rep = super(DeptSerializer, self).to_representation(instance)
        if instance.branch_id:
            rep['branch_id'] =instance.branch_id.branch_name
        return rep
class DeptUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = dept_master
        fields= '__all__'

#DESIGNATION SERIALIZER
class DesgSerializer(serializers.ModelSerializer):
    desgntn_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    desgntn_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = desgntn_master
        fields= '__all__'
class DesgUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = desgntn_master
        fields= '__all__'




#CATOGARY SERIALIZER
class CtgrySerializer(serializers.ModelSerializer):
    ctgry_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ctgry_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = ctgry_master
        fields= '__all__'
#CATEGARY Bulupload SERIALIZER
class CtgryUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = ctgry_master
        fields= '__all__'

class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = '__all__'

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = '__all__'

class permserializer(serializers.ModelSerializer):
    class Meta:
        model=Permission
        fields=['id','codename']

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all()
    )
    class Meta:
        model = Group
        fields='__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['permissions'] = permserializer(instance.permissions.all(), many=True).data
        return representation

class PermissionSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['groups'] = GroupSerializer(instance.groups.all(), many=True).data
        representation['user_permissions'] = permserializer(instance.user_permissions.all(), many=True).data
        return representation

    class Meta:
        model = UserTenantPermissions
        fields = '__all__'


class DocumentNumberingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DocumentNumbering
        fields = '__all__'
    def to_representation(self, instance):
        rep = super(DocumentNumberingSerializer, self).to_representation(instance)
        if instance.branch_id:  # Check if emp_state_id is not None
            rep['branch_id'] = instance.branch_id.branch_name
        # if instance.category:  # Check if emp_state_id is not None
        #     rep['category'] = instance.category.ctgry_title
        return rep
    

class AssetMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMaster
        fields = '__all__'

class AssetTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetTransaction
        fields = '__all__'

    def validate(self, data):
        asset = data.get('asset')
        transaction_type = data.get('transaction_type')
        quantity = data.get('quantity')

        if transaction_type == AssetTransaction.ISSUE and asset.available_quantity < quantity:
            raise serializers.ValidationError("Insufficient quantity available for issuance.")
        
        return data

class Asset_CustomFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset_CustomFieldValue
        fields = '__all__'   
