from django.shortcuts import render
from .models import (state_mstr,crncy_mstr,cntry_mstr,document_type,LanguageMaster,Nationality)
from .serializer import (CountrySerializer,StateSerializer,LanguageMasterSerializer,
                         CurrencySerializer,Document_type,CntryBulkUploadSerializer,NationalityBlkUpldSerializer)
from . permissions import LanguageMasterPermission
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status,generics,viewsets,permissions
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly,IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
import csv
from UserManagement.permissions import CountryPermission,StatePermission,DocTypePermission

# Create your views here.

#STATE CRUD
class StateViewSet(viewsets.ModelViewSet):
    queryset = state_mstr.objects.all()
    serializer_class = StateSerializer
    # authentication_classes = [SessionAuthentication,]
    # permission_classes = [StatePermission,] 

    # def list(self, request):
    #     country_id = request.query_params.get('country_id')
    #     if country_id:
    #         states = self.queryset.filter(country_id=country_id)
    #         serializer = self.serializer_class(states, many=True)
    #         return Response(serializer.data)
    #     else:
    #         return Response({"error": "Country ID is required"})
#COUNTRY CRUD
class CountryViewSet(viewsets.ModelViewSet):
    queryset = cntry_mstr.objects.all()
    serializer_class = CountrySerializer
    # authentication_classes = [SessionAuthentication,]
    # permission_classes = [CountryPermission,]

    # Custom action to get states for a specific country
    @action(detail=True, methods=['get'])
    def states(self, request, pk=None):
        country = self.get_object()
        states = country.state_mstr_set.all()  # Use the correct related_name
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data)

class CountryBulkuploadViewSet(viewsets.ModelViewSet):
    queryset = cntry_mstr.objects.all()
    serializer_class = CntryBulkUploadSerializer
    # permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('latin-1').splitlines()  # Decode using 'latin-1'
            reader = csv.DictReader(decoded_file)

            success_count = 0
            error_count = 0
            errors = []

            for row_number, row in enumerate(reader, start=1):
                country_code = row.get('country_code', '')[:50]  # Get country_code, truncate if too long
                country_name = row.get('country_name', '')[:50]  # Get country_name, truncate if too long

                if not country_code or not country_name:
                    errors.append(f"Missing required fields in row {row_number}")
                    error_count += 1
                    continue  # Skip this row and proceed to the next one

                try:
                    cntry_mstr.objects.create(
                        country_code=country_code,
                        country_name=country_name
                    )
                    success_count += 1
                except Exception as e:
                    errors.append(f"Error in row {row_number}: {str(e)}")
                    error_count += 1

            if error_count > 0:
                return Response({'error': errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': f'Bulk upload successful. {success_count} rows added.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'No file found'}, status=status.HTTP_400_BAD_REQUEST)

#nationality bulkupload
class NationalityBlkupldViewSet(viewsets.ModelViewSet):
    queryset = Nationality.objects.all()
    serializer_class = NationalityBlkUpldSerializer
    # permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            try:
                for row in reader:
                    Nationality.objects.create(
                        N_name=row['N_name'],
                        
                    )
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'message': 'Bulk upload successful'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'No file found'}, status=status.HTTP_400_BAD_REQUEST)


#CURRENCY CRUD+
class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = crncy_mstr.objects.all()
    serializer_class = CurrencySerializer
    # authentication_classes = [SessionAuthentication,]
    

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = document_type.objects.all()
    serializer_class = Document_type
    # permission_classes = [DocTypePermission,] 

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = LanguageMaster.objects.all()
    serializer_class = LanguageMasterSerializer
    permission_classes = [LanguageMasterPermission]
    def get_serializer_context(self):
        return {'request': self.request}