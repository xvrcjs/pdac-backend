from datetime import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from users.models import Account


  
def get_ticket_file_path(instance,file_name):
    return 'tickets/%s/%s' % (instance.ticket.id,file_name)

class File(BaseModel):
    file = models.FileField(upload_to=get_ticket_file_path)
    file_name = models.CharField(max_length=255)
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='files')
    def __str__(self):
        return f"{self.file.name}"
    
class Ticket(BaseModel):
    STATUS = [
        ("pending_review", "Pendiente Revisión"),
        ("in_progress", "En curso"),
        ("closed", "Cerrado"),
    ]
    SUPPORT_LEVEL = [
        ("unassigned", "S/A"),
        ("n1", "Nivel 1 (N1)"),
        ("n2", "Nivel 2 (N2)"),
        ("n3", "Nivel 3 (N3)"),
    ]
    #Information Base
    id = models.CharField(_('Id'),max_length=255,unique=True)
    claim = models.CharField(_('Claim'),max_length=255,blank=True,null=True)
    assigned = models.ForeignKey(Account,on_delete=models.CASCADE, related_name='assigned',null=True,blank=True)
    status = models.CharField(_('Status'),max_length=30, choices=STATUS,default="pending_review",blank=True)
    support_level = models.CharField(_('Support Level'), max_length=30,choices=SUPPORT_LEVEL,default="unassigned",blank=True)
    #Activity and status changes
    activity = models.JSONField(default=list,blank=True,null=True)
    problem_description = models.TextField(blank=True)
    tasks = models.JSONField(default=list,blank=True,null=True)


    def __str__(self):
        return f"{self.uuid}"
    @staticmethod
    def get_year_letter(year):
        # Asignar letra según el año (A=2025, B=2026, etc.)
        return chr(65 + (year - 2025))  # 'A' es 65 en ASCII
    
    @staticmethod
    def get_last_ticket_number(year):
        # Obtener el último número de reclamo en el año actual
        last_ticket = Ticket.objects.filter(id__startswith=f"#T-{Ticket.get_year_letter(year)}").order_by('-id').first()
        if last_ticket:
            # Extraer el número y agregar 1
            last_number = int(last_ticket.id.split('-')[-1])
            return last_number + 1
        return 1
    
    def save(self, *args, **kwargs):
        if not self.id:
            year = datetime.now().year
            letter = self.get_year_letter(year)  # Letra del año
            claim_number = self.get_last_ticket_number(year)  # Número secuencial

            # Formatear el número con ceros a la izquierda
            formatted_number = f"{claim_number:07d}"
            self.id = f"#T-{letter}-{formatted_number}"
        
        super().save(*args, **kwargs)