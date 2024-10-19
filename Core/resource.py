from import_export import resources,fields
from .models import cntry_mstr,Nationality



class CountryResource(resources.ModelResource):
    class Meta:
        model = cntry_mstr
        fields = ('id','country_code','country_name')

class NationalityResource(resources.ModelResource):
    class Meta:
        model = Nationality
        fields = ('id','N_name')