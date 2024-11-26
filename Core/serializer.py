from rest_framework import serializers
from .models import(state_mstr,cntry_mstr,crncy_mstr,document_type,LanguageMaster,Nationality)
#STATE SERIALIZER
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = state_mstr
        fields = '__all__'
    # def create(self, validated_data):
    #     country_name = validated_data.pop('country_name')  # Extract country name
    #     country_name, created = cntry_mstr.objects.get(name=country_name)  # Get the Country object by name
    #     state = state_mstr.objects.create(country_name=country_name, **validated_data)
    #     return state

#COUNTRY SERIALIZER
class CountrySerializer(serializers.ModelSerializer):
    states_set = StateSerializer(many=True, read_only=True)  # 
    # br_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # br_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = cntry_mstr
        fields = '__all__'

class CntryBulkUploadSerializer(serializers.ModelSerializer):  
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = cntry_mstr
        fields = '__all__'

 #ntionality bulk upload
class NationalityBlkUpldSerializer(serializers.ModelSerializer):  
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = Nationality
        fields = '__all__'

#CURRENCY SERIALIZER
class CurrencySerializer(serializers.ModelSerializer):
    # br_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # br_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = crncy_mstr
        fields = '__all__'

class Document_type(serializers.ModelSerializer):
    class Meta:
        model = document_type
        fields = '__all__'



# LANGUAGES
class LanguageMasterSerializer(serializers.ModelSerializer):
    # br_created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # br_updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model= LanguageMaster
        fields = '__all__'