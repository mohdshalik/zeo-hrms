from django.contrib.auth.models import Group,Permission
from rest_framework import serializers
from .models import CustomUser,company,Domain
from OrganisationManager.models import  brnch_mstr
# from OrganisationManager.serializer import BranchSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from EmpManagement.models import emp_master
# from OrganisationManager.serializer import GroupSerializer
# from .models import company
from django.contrib.contenttypes.models import ContentType
from django_tenants.utils import schema_context
       
class CustomUserSerializer(serializers.ModelSerializer):
    tenants = serializers.PrimaryKeyRelatedField(queryset=company.objects.all(), many=True, write_only=True)
    allocated_tenants = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def get_allocated_tenants(self, obj):
        tenants = obj.tenants.all()
        return CompanySerializer(tenants, many=True).data

    def to_representation(self, instance):
        rep = super(CustomUserSerializer, self).to_representation(instance)
        rep['allocated_tenants'] = self.get_allocated_tenants(instance)
        return rep

    def create(self, validated_data):
        tenants_data = validated_data.pop('tenants', [])
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        
        # Add tenants to user
        user.tenants.set(tenants_data)

        return user

    def update(self, instance, validated_data):
        tenants_data = validated_data.pop('tenants', None)
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        instance = super().update(instance, validated_data)
        
        # Update tenants
        if tenants_data is not None:
            instance.tenants.set(tenants_data)

        return instance
    
# class CustomUserSerializer(UserSerializer):
# from oauth2_provider.models import AccessToken
from django.utils import timezone
import uuid
from datetime import timedelta




class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Determine if the user is attempting to authenticate with username or email
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        # Check if username_or_email is a valid email format
        if "@" in username_or_email:
            user = CustomUser.objects.filter(email=username_or_email).first()
        else:
            user = CustomUser.objects.filter(username=username_or_email).first()

        if user:
            # Check if the user is active, if not, prevent login
            if not user.is_active:
                raise serializers.ValidationError("Your account is deactivated. Please contact support.")

            # Validate the user based on the is_ess field
            if (user.is_ess and user.username == username_or_email) or (
                    not user.is_ess and user.email == username_or_email):
                if user.check_password(password):
                    self.user = user
                    data = super().validate(attrs)
                    data["user_id"] = user.id
                    data["username"] = user.username
                    data["tenants"] = [
                        {
                            "id": tenant.id,
                            "name": tenant.name,
                            "schema_name": tenant.schema_name
                        }
                        for tenant in user.tenants.all()
                    ]
                    data["tenant_id"] = [tenant.schema_name for tenant in user.tenants.all()]
                    return data
                else:
                    raise serializers.ValidationError("Invalid password")
            else:
                if user.is_ess:
                    raise serializers.ValidationError("ESS users must authenticate with their username")
                else:
                    raise serializers.ValidationError("Non-ESS users must authenticate with their email")
        else:
            raise serializers.ValidationError("User not found")

        return super().validate(attrs)
    
class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = company
        fields = '__all__'
        
    
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_ess', 'is_staff', 'is_superuser', 'tenants']

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model=Domain
        fields = '__all__'


