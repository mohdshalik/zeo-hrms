from django.db import models


class cntry_mstr(models.Model):
    country_code  =  models.CharField(max_length=150,unique=True,null=True)
    timezone      =  models.CharField(max_length=100, help_text="Set timezone as per IANA timezone database format, e.g., 'America/New_York'",null=True)
    country_name  =  models.CharField(max_length=50,unique=True)
    is_active     = models.BooleanField(default=True)
    
    def __str__(self):
        return self.country_name
#STATE MODEL
class state_mstr(models.Model):

    state_name  = models.CharField(max_length=50)
    is_active   = models.BooleanField(default=True)
    country     = models.ForeignKey('cntry_mstr',on_delete=models.CASCADE)
    def __str__(self):
        return self.state_name

#CURRENCY MODEL
class crncy_mstr(models.Model):
    currency_name    = models.CharField(max_length=50,unique=True)
    currency_code    = models.CharField(max_length=3, unique=True)
    symbol           = models.CharField(max_length=5, blank=True, null=True)
    country = models.OneToOneField(cntry_mstr, on_delete=models.CASCADE, related_name='currency',null=True,blank=True)
    
    def __str__(self):
        return self.currency_name

# document master
class document_type(models.Model):
    type_name   = models.CharField(max_length=50,unique=True)
    description = models.CharField(max_length=200)
    def __str__(self):
        return self.type_name
    
#LANGUAGE MASTER 
class LanguageMaster(models.Model):
    language = models.CharField(max_length=100)
    def __str__(self):
        return self.language
    
#Nationality
class Nationality(models.Model):
    N_name = models.CharField(max_length=200,null=True)

    def str(self):
        return self.N_name

class LanguageSkill(models.Model):
    language = models.CharField(max_length=100,null=True,blank =True,default=None)
    
    def __str__(self):
        return f"{self.language }"

class MarketingSkill(models.Model):
    marketing = models.CharField(max_length=100,null=True,blank =True,default=None)

    def __str__(self):
        return f"{self.marketing }"

class ProgrammingLanguageSkill(models.Model):
    programming_language = models.CharField(max_length=100,null=True,blank =True,default=None)

    def __str__(self):
        return f"{self.programming_language }"

class TaxSystem(models.Model):
    country = models.OneToOneField(cntry_mstr, on_delete=models.CASCADE)
    tax_name = models.CharField(max_length=100)  # e.g., VAT, GST
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 5.00 for 5%
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.country.country_name} - {self.tax_name} ({self.tax_percentage}%)"