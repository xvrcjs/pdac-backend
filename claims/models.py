from datetime import datetime
from django.db import models
from administration.models import Omic
from common.models import BaseModel
from django.utils.translation import gettext_lazy as _

from users.models import Account

class Supplier(BaseModel):
    fullname = models.CharField(_('Fullname'),max_length=255)
    cuil = models.CharField(_('Cuil'),max_length=50)
    address = models.CharField(_('Address'),max_length=255)
    num_address = models.CharField(_('Num Address'),max_length=10, blank=True)
    city = models.CharField(_('City/Provincie'),max_length=255)
    zip_code = models.CharField(_('Zip Code'),max_length=10)

    def __str__(self):
        return f"{self.fullname} ({self.cuil})"
    
class Claimer(BaseModel):

    GENDER_CHOICES = [
        ("female", "Femenino"),
        ("male", "Masculino"),
        ("x", "X"),
        ("other", "Otro"),
        ("none", "Prefiero no decirlo"),
    ]

    fullname = models.CharField(_('Fullname'),max_length=255)
    dni = models.CharField(_('Dni'),max_length=15)
    cuit = models.CharField(_('Cuit/Cuil'),max_length=20)
    email = models.EmailField(_('Email'))
    gender = models.CharField(_('Gender'),max_length=10, choices=GENDER_CHOICES)

    def __str__(self):
        return self.fullname
    def get_gender_display(self):
        return dict(self.GENDER_CHOICES).get(self.gender, "Desconocido")
    
def get_claim_image_path(instance,file_name):
    return 'claim/%s/%s' % (instance.claim,file_name)

class File(BaseModel):
    file = models.FileField(upload_to=get_claim_image_path)
    file_name = models.CharField(max_length=255)
    claim = models.TextField(max_length=255,blank=True,null=True)
    def __str__(self):
        return f"{self.file.name}"
    
class ClaimRegular(BaseModel):
    #Information Base
    id = models.CharField(_('Id'),max_length=255,unique=True)
    claimer = models.ForeignKey(Claimer, on_delete=models.CASCADE, related_name='claims')
    suppliers = models.ManyToManyField(Supplier)
    problem_description = models.TextField(blank=True)
    #Comments, activity and status changes
    activity = models.JSONField(default=list,blank=True,null=True)
    files = models.ManyToManyField(File)


    #Information General
    claim_access = models.CharField(_('Claim Access'),max_length=255,blank=True,null=True)
    type_of_claim = models.CharField(_('Type of Claim'),max_length=255,blank=True,null=True,default="S/A")
    claim_status = models.CharField(_('Claim Status'),max_length=255,blank=True,null=True,default="En análisis")
    category = models.CharField(_('Category'),max_length=255,blank=True,null=True)
    heading = models.CharField(_('Heading'),max_length=255,blank=True,null=True)
    subheading = models.CharField(_('Subheading'),max_length=255,blank=True,null=True)
    
    transfer_to_company = models.CharField(_('Transfer to company'),max_length=255,blank=True,null=True)
    derived_to_omic = models.ForeignKey(Omic,on_delete=models.CASCADE,blank=True,null=True,related_name='derived_omic')
    derived_to_user = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='account',null=True,blank=True)
    transfer_to_the_consumer = models.CharField(_('Transfer to the consumer'),max_length=255,blank=True,null=True)
    conciliation_hearing = models.CharField(_('Conciliation hearing'),max_length=255,blank=True,null=True)
    imputation = models.CharField(_('Imputation'),max_length=255,blank=True,null=True)
    resolution = models.CharField(_('Resolution'),max_length=255,blank=True,null=True)
    monetary_agreement = models.CharField(_('Monetary Agreement'),max_length=255,blank=True,null=True)

    def __str__(self):
        return f"{self.uuid}"
    
    @staticmethod
    def get_year_letter(year):
        # Asignar letra según el año (A=2025, B=2026, etc.)
        return chr(65 + (year - 2025))  # 'A' es 65 en ASCII
    
    @staticmethod
    def get_last_claim_number(year):
        # Obtener el último número de reclamo en el año actual
        last_claim = ClaimRegular.objects.filter(id__startswith=f"#RC-{ClaimRegular.get_year_letter(year)}").order_by('-id').first()
        if last_claim:
            # Extraer el número y agregar 1
            last_number = int(last_claim.id.split('-')[-1])
            return last_number + 1
        return 1
    def save(self, *args, **kwargs):
        if not self.id:
            year = datetime.now().year
            letter = self.get_year_letter(year)  # Letra del año
            claim_number = self.get_last_claim_number(year)  # Número secuencial

            # Formatear el número con ceros a la izquierda
            formatted_number = f"{claim_number:07d}"
            self.id = f"#RC-{letter}-{formatted_number}"
        
        super().save(*args, **kwargs)

# class ClaimIVE(BaseModel):
#     claimer = models.ForeignKey(Claimer, on_delete=models.CASCADE, related_name='claimer')

