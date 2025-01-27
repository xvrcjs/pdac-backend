from django.db import models
from common.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Supplier(BaseModel):
    fullname = models.CharField(_('Fullname'),max_length=255)
    cuil = models.CharField(_('Cuil'),max_length=20)
    address = models.CharField(_('Address'),max_length=255)
    num_address = models.CharField(_('Num Address'),max_length=10, blank=True)
    city_name = models.CharField(_('City/Provincie'),max_length=255)
    zip_code = models.CharField(_('Zip Code'),max_length=10)

    def __str__(self):
        return f"{self.fullname} ({self.cuil})"
    
class Claimer(BaseModel):

    genders = {
        ("female", "Femenino"),
        ("male", "Masculino"),
        ("x", "X"),
        ("other", "Otro"),
        ("none", "Prefiero no decirlo"),
    }

    fullname = models.CharField(_('Fullname'),max_length=255)
    dni = models.CharField(_('Dni'),max_length=15)
    cuit = models.CharField(_('Cuit/Cuil'),max_length=20)
    email = models.EmailField(_('Email'))
    gender = models.CharField(_('Gender'),max_length=10, choices=genders)

    def __str__(self):
        return self.fullname
class File(BaseModel):
    file = models.FileField(upload_to='uploads/')
    file_name = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.file.name}"
    
class ClaimRegular(BaseModel):
    claimer = models.ForeignKey(Claimer, on_delete=models.CASCADE, related_name='claimer')
    supplier = models.ManyToManyField(Supplier)
    comments = models.TextField(blank=True)
    files = models.ManyToManyField(File)

    def __str__(self):
        return f"{self.uuid}"

# class ClaimIVE(BaseModel):
#     claimer = models.ForeignKey(Claimer, on_delete=models.CASCADE, related_name='claimer')

