from rest_framework import serializers
from .models import(state_mstr,cntry_mstr,TaxSystem,crncy_mstr,document_type,LanguageMaster,Nationality,LanguageSkill,MarketingSkill,ProgrammingLanguageSkill,
                    ReligionMaster)
#STATE SERIALIZER
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = state_mstr
        fields = '__all__'
    def to_representation(self, instance):
        rep = super(StateSerializer, self).to_representation(instance)
        if instance.country:  # Check if emp_state_id is not None
            rep['country'] = instance.country.country_name
       
        return rep
#CURRENCY SERIALIZER
class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = crncy_mstr
        fields = '__all__'
#COUNTRY SERIALIZER
class CountrySerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(read_only=True)
    states_set = StateSerializer(many=True, read_only=True)  # 
    state_label = serializers.SerializerMethodField()  # Dynamic label field
    class Meta:
        model = cntry_mstr
        fields = '__all__'
    def get_state_label(self, obj):
        """Return dynamic name for 'states' based on country selection."""
        custom_labels = {
        "Afghanistan": "Provinces",
        "Albania": "Counties",
        "Algeria": "Provinces",
        "American Samoa": "Districts",
        "Andorra": "Parishes",
        "Angola": "Provinces",
        "Anguilla": "Districts",
        "Antarctica": "Territories",
        "Antigua and Barbuda": "Parishes",
        "Argentina": "Provinces",
        "Armenia": "Marzes",
        "Aruba": "Regions",
        "Australia": "Territories",
        "Austria": "States",
        "Azerbaijan": "Economic Regions",
        "Bahamas": "Districts",
        "Bahrain": "Governorates",
        "Bangladesh": "Divisions",
        "Barbados": "Parishes",
        "Belarus": "Regions",
        "Belgium": "Regions",
        "Belize": "Districts",
        "Benin": "Departments",
        "Bermuda": "Parishes",
        "Bhutan": "Dzongkhags",
        "Bolivia": "Departments",
        "Bonaire, Sint Eustatius and Saba": "Municipalities",
        "Bosnia and Herzegovina": "Entities",
        "Botswana": "Districts",
        "Bouvet Island": "Territory",
        "Brazil": "States",
        "British Indian Ocean Territory": "Atolls",
        "Brunei Darussalam": "Districts",
        "Bulgaria": "Provinces",
        "Burundi": "Provinces",
        "Cabo Verde": "Islands",
        "Cambodia": "Provinces",
        "Cameroon": "Regions",
        "Canada": "Provinces",
        "Cayman Islands": "Districts",
        "Central African Republic": "Prefectures",
        "Chad": "Regions",
        "Chile": "Regions",
        "China": "Provinces",
        "Christmas Island": "Shires",
        "Cocos (Keeling) Islands": "Territory",
        "Colombia": "Departments",
        "Comoros": "Islands",
        "Congo (Republic of the)": "Departments",
        "Congo (Democratic Republic of the)": "Provinces",
        "Cook Islands": "Islands",
        "Costa Rica": "Provinces",
        "Côte d'Ivoire": "Districts",
        "Croatia": "Counties",
        "Cuba": "Provinces",
        "Curaçao": "Districts",
        "Cyprus": "Districts",
        "Czech Republic": "Regions",
        "Denmark": "Regions",
        "Djibouti": "Regions",
        "Dominica": "Parishes",
        "Dominican Republic": "Provinces",
        "Ecuador": "Provinces",
        "Egypt": "Governorates",
        "El Salvador": "Departments",
        "Equatorial Guinea": "Provinces",
        "Eritrea": "Regions",
        "Estonia": "Counties",
        "Ethiopia": "Regions",
        "Falkland Islands (Malvinas)": "Islands",
        "Faroe Islands": "Regions",
        "Fiji": "Divisions",
        "Finland": "Regions",
        "France": "Regions",
        "French Guiana": "Regions",
        "French Polynesia": "Islands",
        "French Southern Territories": "Districts",
        "Gabon": "Provinces",
        "Gambia": "Divisions",
        "Georgia": "Regions",
        "Germany": "States",
        "Ghana": "Regions",
        "Gibraltar": "Territory",
        "Greece": "Regions",
        "Greenland": "Municipalities",
        "Grenada": "Parishes",
        "Guadeloupe": "Departments",
        "Guam": "Villages",
        "Guatemala": "Departments",
        "Guernsey": "Parishes",
        "Guinea": "Regions",
        "Guinea-Bissau": "Regions",
        "Guyana": "Regions",
        "Haiti": "Departments",
        "Honduras": "Departments",
        "Hong Kong": "Districts",
        "Hungary": "Counties",
        "Iceland": "Regions",
        "India": "States",
        "Indonesia": "Provinces",
        "Iran": "Provinces",
        "Iraq": "Governorates",
        "Ireland": "Counties",
        "Isle of Man": "Parishes",
        "Israel": "Districts",
        "Italy": "Regions",
        "Jamaica": "Parishes",
        "Japan": "Prefectures",
        "Jersey": "Parishes",
        "Jordan": "Governorates",
        "Kazakhstan": "Regions",
        "Kenya": "Counties",
        "Kiribati": "Islands",
        "Korea (Democratic People's Republic of)": "Provinces",
        "Korea (Republic of)": "Provinces",
        "Kuwait": "Governorates",
        "Kyrgyzstan": "Regions",
        "Lao People's Democratic Republic": "Provinces",
        "Latvia": "Regions",
        "Lebanon": "Governorates",
        "Lesotho": "Districts",
        "Liberia": "Counties",
        "Libya": "Districts",
        "Liechtenstein": "Municipalities",
        "Lithuania": "Counties",
        "Luxembourg": "Districts",
        "Macao": "Regions",
        "Macedonia": "Regions",
        "Madagascar": "Regions",
        "Malawi": "Districts",
        "Malaysia": "States",
        "Maldives": "Atolls",
        "Mali": "Regions",
        "Malta": "Regions",
        "Marshall Islands": "Atolls",
        "Martinique": "Regions",
        "Mauritania": "Regions",
        "Mauritius": "Districts",
        "Mexico": "States",
        "Micronesia (Federated States of)": "States",
        "Moldova": "Districts",
        "Mongolia": "Aimags",
        "Montenegro": "Municipalities",
        "Montserrat": "Parishes",
        "Morocco": "Regions",
        "Mozambique": "Provinces",
        "Myanmar": "States and Regions",
        "Namibia": "Regions",
        "Nauru": "Districts",
        "Nepal": "Provinces",
        "Netherlands": "Provinces",
        "New Caledonia": "Provinces",
        "New Zealand": "Regions",
        "Nicaragua": "Departments",
        "Niger": "Regions",
        "Nigeria": "States",
        "Norway": "Counties",
        "Oman": "Governorates",
        "Pakistan": "Provinces",
        "Palau": "States",
        "Panama": "Provinces",
        "Papua New Guinea": "Provinces",
        "Paraguay": "Departments",
        "Peru": "Regions",
        "Philippines": "Regions",
        "Poland": "Voivodeships",
        "Portugal": "Districts",
        "Puerto Rico": "Municipalities",
        "Qatar": "Municipalities",
        "Romania": "Counties",
        "Russian Federation": "Federal Subjects",
        "Rwanda": "Provinces",
        "Saint Kitts and Nevis": "Parishes",
        "Saudi Arabia": "Regions",
        "Senegal": "Regions",
        "Serbia": "Districts",
        "Seychelles": "Districts",
        "Sierra Leone": "Provinces",
        "Singapore": "Planning Areas",
        "Slovakia": "Regions",
        "Slovenia": "Regions",
        "Solomon Islands": "Provinces",
        "South Africa": "Provinces",
        "Spain": "Autonomous Communities",
        "Sri Lanka": "Provinces",
        "Sudan": "States",
        "Sweden": "Counties",
        "Switzerland": "Cantons",
        "Thailand": "Provinces",
        "Turkey": "Provinces",
        "Ukraine": "Oblasts",
        "United Arab Emirates": "Emirates",
        "United Kingdom": "Counties",
        "United States": "States","Uruguay": "Departments","Venezuela": "States","Vietnam": "Provinces","Zambia": "Provinces", "Zimbabwe": "Provinces",
    }

        return custom_labels.get(obj.country_name)  # No default value

class CntryBulkUploadSerializer(serializers.ModelSerializer):  
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = cntry_mstr
        fields = '__all__'

class NationalitySerializer(serializers.ModelSerializer):  
    class Meta:
        model = Nationality
        fields = '__all__'
 
 #ntionality bulk upload
class NationalityBlkUpldSerializer(serializers.ModelSerializer):  
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = Nationality
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

class LanguageSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageSkill
        fields = '__all__'

class MarketingSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingSkill
        fields = '__all__'

class ProgrammingLanguageSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguageSkill
        fields = '__all__'
class LanguageBlkupldSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = LanguageSkill
        fields = '__all__'

class MarketingBlkupldSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = MarketingSkill
        fields = '__all__'

class ProLangBlkupldSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = ProgrammingLanguageSkill
        fields = '__all__'

class TaxSystemSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.country_name", read_only=True)
    class Meta:
        model = TaxSystem
        # fields = '__all__'
        fields = ['id', 'country', 'country_name', 'tax_name', 'tax_percentage', 'is_active']

class ReligionMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReligionMaster
        fields = '__all__'
        
class ReligionMasterBlkupldSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True) 
    class Meta:
        model = ReligionMaster
        fields = '__all__'