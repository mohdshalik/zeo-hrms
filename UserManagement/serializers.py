from django.contrib.auth.models import Group,Permission
from rest_framework import serializers
from .models import CustomUser,company,Domain
from OrganisationManager.models import  brnch_mstr
from OrganisationManager.serializer import BranchSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from EmpManagement.models import Approval
from EmpManagement.serializer import ApprovalSerializer

class CompanySerializer(serializers.ModelSerializer):
    # user = serializers.SerializerMethodField()
    class Meta:
        model = company
        fields = '__all__'

class DomainSerializer(serializers.ModelSerializer):
    # user = serializers.SerializerMethodField()
    class Meta:
        model = Domain
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    # approvals = serializers.SerializerMethodField()
    # approvals=ApprovalSerializer(many=True, read_only=True)
    # created_by = serializers.HiddenField(default=serializers.CurrentUserDefault(), required=False)
    # user_permissions = PermissionSerializer(many=True, read_only=True)
    tenants = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = '__all__'
        queryset = CustomUser.objects.none()
        extra_kwargs = {'password': {'write_only': True}}
    def get_tenants(self, obj):
        tenants = obj.tenants.all()
        return CompanySerializer(tenants, many=True).data

    def to_representation(self, instance):
        rep = super(UserSerializer, self).to_representation(instance)
        return rep
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)
    
    # def get_approvals(self, obj):
    #     approvals = obj.get_approvals()
    #     return ApprovalSerializer(approvals, many=True).data


#         rep = super().to_representation(instance)
#         rep['groups'] = [{
#             'name': group.name,
#             'permissions': list(group.permissions.all().values('codename'))
#         } for group in instance.groups.all()]
#         return rep
# # class CustomUserSerializer(UserSerializer):
#     companies = serializers.PrimaryKeyRelatedField(many=True, queryset=cmpny_mastr.objects.all(), required=False)
#     branches = serializers.PrimaryKeyRelatedField(many=True, queryset=brnch_mstr.objects.all(), required=False)
#     branches = BranchSerializer(many=True, read_only=True)

#     def init(self, *args, **kwargs):
#         super().init(*args, **kwargs)
        
#         if 'request' in self.context and self.context['request'].user.is_authenticated:
#             self.fields['companies'] = serializers.PrimaryKeyRelatedField(many=True, queryset=cmpny_mastr.objects.all(), required=False)
#             self.fields['branches'] = serializers.PrimaryKeyRelatedField(many=True, queryset=brnch_mstr.objects.all(), required=False)
#         else:
#             self.fields.pop('companies')
#             self.fields.pop('branches')
        
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
    
        # Add custom claims
        token["custom_field"] = "Custom value"
    
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
    
        user = self.user
        data["user_id"] = user.id
        data["username"] = user.username
            # ... add other user information as needed
    
        return data
    
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_ess', 'is_staff', 'is_superuser', 'tenants']