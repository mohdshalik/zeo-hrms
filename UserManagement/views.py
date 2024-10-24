from django.shortcuts import render
from django.contrib.auth.models import User,Group,Permission
from .serializers import CompanySerializer,DomainSerializer,UserSerializer,CustomTokenObtainPairSerializer,UserListSerializer
from . models import company,CustomUser,Domain
from . permissions import (IsOwnerOrReadOnly,IsSuperUser,IsEssUserOrReadOnly)
from rest_framework.response import Response
from rest_framework import status,generics,viewsets,permissions
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly,IsAdminUser
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from EmpManagement.serializer import Emp_qf_Serializer,EmpFamSerializer,EmpJobHistorySerializer,EmpLeaveRequestSerializer,DocumentSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from tenant_users.tenants.models import UserTenantPermissions
from OrganisationManager.serializer import PermissionSerializer
from .signals import add_company_to_superusers
from rest_framework.views import APIView
from EmpManagement.models import Approval
from rest_framework.exceptions import NotFound
from EmpManagement .serializer import ApprovalSerializer,ReqNotifySerializer
from LeaveManagement.serializer import LvApprovalSerializer
from LeaveManagement.models import LeaveApproval
# Create your views here.
#usergroups or roles
class RegisterUserAPIView(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

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


        
    # authentication_classes = [JWTAuthentication]  # Add JWTAuthentication for token decoding

    # def perform_create(self, serializer):
    #     # Extract user ID from the decoded token
    #     user_id = self.request.user.id
    #     # Perform any action with the user ID, for example:
    #     serializer.save(created_by_id=user_id)
    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=True, methods=['get'])
    def approvals(self, request, pk=None):
        user = self.get_object()
        approvals = user.get_approvals()
        serializer = ApprovalSerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def approvalnotification(self, request, pk=None):
        user = self.get_object()
        approvals = user.get_requestsnotification()
        serializer = ReqNotifySerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    # @action(detail=True, methods=['get'])
    # def lvapprovals(self, request, pk=None):
    #     user = self.get_object()  # Assuming this gets the user object
    #     approvals = LeaveApproval.objects.filter(approver=user)  # Correct queryset
    #     serializer = LvApprovalSerializer(approvals, many=True)  # Serialize the queryset
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=['get'])
    def lvapprovals(self, request, pk=None):
        user = self.get_object()
        approvals = user.get_lv_approvals()
        serializer = LvApprovalSerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
     

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = company.objects.all()
    serializer_class = CompanySerializer
    def perform_create(self, serializer):
        # Call the super's perform_create to save the instance
        instance = serializer.save()


        # Trigger the signal manually after the instance is saved
        add_company_to_superusers(sender=company, instance=instance, created=True)
    # permission_classes = [IsAuthenticated]
    
class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer



# class UserRolesViewSet(viewsets.ModelViewSet):
#     queryset = Group.objects.all()
#     serializer_class = RoleSerializer
#     permission_classes = [IsSuperUser]


# # # user grouping with permissions

# class UserandPermissionGrouping(viewsets.ModelViewSet):
#     queryset = CustomUserGroup.objects.all()
#     serializer_class = CustomUserGroupSerializer
#     permission_classes = [IsSuperUser]
    


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class TenantUserListView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated]

    serializer_class = UserListSerializer

    def get_queryset(self):
        schema_name = self.request.tenant.schema_name  # Assuming you have multi-tenancy setup
        return CustomUser.objects.filter(tenants__schema_name=schema_name)
    
