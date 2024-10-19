from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import company
from .serializers import CompanySerializer
from django.db.models.signals import post_save
from .models import CustomUser

@api_view(['POST'])
def create_company(request):
    serializer = CompanySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# Signal handler function to update superuser tenants
def add_company_to_superusers(sender, instance, created, **kwargs):
    if created:  # Only process newly created companies
        superusers = CustomUser.objects.filter(is_superuser=True)
        for user in superusers:
            user.tenants.add(instance)
            user.save()

post_save.connect(add_company_to_superusers, sender=company)