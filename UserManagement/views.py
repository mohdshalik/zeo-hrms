from django.shortcuts import render
from django.contrib.auth.models import User,Group,Permission
from .serializers import CustomUserSerializer,CustomTokenObtainPairSerializer,CompanySerializer,DomainSerializer,UserListSerializer
from . models import CustomUser,company,Domain
from . permissions import (IsSuperAdminUser,IsSelfOrSuperAdmin,IsOwnerOrReadOnly,
                           IsOwnerOrHRAdminOrReadOnly,IsSuperUser,IsEssUserOrReadOnly,HasSchemaAccess)
from OrganisationManager.serializer import PermissionSerializer,GroupSerializer
# from . custom_auth import GlobalJWTAuthentication
from rest_framework.response import Response
from rest_framework import status,generics,viewsets,permissions
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly,IsAdminUser

from rest_framework.decorators import action
from EmpManagement .serializer import ApprovalSerializer,ReqNotifySerializer
from LeaveManagement.serializer import LvApprovalSerializer,LvApprovalNotifySerializer
from LeaveManagement.models import LeaveApproval,LvApprovalNotify
from EmpManagement.models import Approval,RequestNotification
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework import viewsets, filters
from .signals import add_company_to_superusers
from tenant_users.tenants.models import UserTenantPermissions
from OrganisationManager .models import CompanyPolicy
from OrganisationManager .serializer import CompanyPolicySerializer

# from .permissions import CompanyPermission
from django.http import Http404
# Create your views here.

#usergroups or roles
class RegisterUserAPIView(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    
    @action(detail=True, methods=['get'])
    def user_permissions(self, request, pk=None):
        user = self.get_object()
        permissions = UserTenantPermissions.objects.filter(profile_id=user.id)
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['get'])
    def tenants(self, request, pk=None):
        user_profile = self.get_object()
        tenants = user_profile.tenants.all()
        serializer = CompanySerializer(tenants, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['get'])
    def approvals(self, request, pk=None):
        user = self.get_object()
        approvals = Approval.objects.filter(approver=user).order_by('-created_at')
        serializer = ApprovalSerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def approvalnotification(self, request, pk=None):
        user = self.get_object()
        approvals = RequestNotification.objects.filter(recipient_user=user).order_by('-created_at')
        serializer = ReqNotifySerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def lvapprovals(self, request, pk=None):
        user = self.get_object()  # Assuming this gets the user object
        approvals = LeaveApproval.objects.filter(approver=user).order_by('-created_at')  
        serializer = LvApprovalSerializer(approvals, many=True)  
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def lvapprovalnotification(self, request, pk=None):
        user = self.get_object()
        approvals = LvApprovalNotify.objects.filter(recipient_user=user).order_by('-created_at')
        serializer = LvApprovalNotifySerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=['get'])
    def companypolicy(self, request, pk=None):
        user = self.get_object()
        approvals = CompanyPolicy.objects.filter(specific_users=user.id).order_by('-created_at')
        serializer = CompanyPolicySerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class TenantUserListView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated]

    serializer_class = UserListSerializer

    def get_queryset(self):
        schema_name = self.request.user.tenants.schema_name  # Assuming you have multi-tenancy setup
        return CustomUser.objects.filter(tenants__schema_name=schema_name)
from django.contrib.auth import login

# from .authentication import CentralizedJWTAuthentication
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = company.objects.all()
    serializer_class = CompanySerializer
    def perform_create(self, serializer):
        # Call the super's perform_create to save the instance
        instance = serializer.save()

        # Trigger the signal manually after the instance is saved
        add_company_to_superusers(sender=company, instance=instance, created=True)
    # permission_classes = [IsAuthenticated]

   

class DomainViewset(viewsets.ModelViewSet):
    queryset=Domain.objects.all()
    serializer_class = DomainSerializer



class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tenant_id):
        # Ensure the user is part of the tenant
        try:
            tenant = company.objects.get(schema_name=tenant_id)
            user = CustomUser.objects.get(id=request.user.id, tenants=tenant)
        except (company.DoesNotExist, CustomUser.DoesNotExist):
            return Response({"detail": "Not found."}, status=404)

        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

