import base64
from datetime import datetime, timezone
import io
import json
import os
from django.utils.timezone import localtime
from babel.dates import format_datetime
from datetime import datetime
from babel import Locale
from django.conf import settings
from django.http import HttpResponseBadRequest,HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from claims.models import ClaimIVE, ClaimRegular
from common.communication.utils import send_email
from common.models import BaseModel
from common.views import BaseView
from tickets.models import File, Ticket
from users.models import Account
from django.core.files.uploadedfile import TemporaryUploadedFile


locale = Locale('es', 'AR')

status = {
    "pending_review": "Pendiente Revisión",
    "in_progress": "En curso",
    "closed": "Cerrado",
}

class TicketView(BaseView):
    model = Ticket

    fields = ["id","uuid", "claim","assigned","status","support_level","activity","problem_description","tasks","created_at"]

    list_fields_related = {
        "assigned":["uuid","full_name"],
    }

    extra_fields = {
        'claim':str,
        'problem_description':str,
        'tasks':list,
        'files': [None, TemporaryUploadedFile],
        'support_level':str,
        'status': str,
        'assigned': [None,str],
    }

    list_page_size = "all"
    
    list_search_fields=["assigned__uuid","status"]
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    
    def create_object(self, fields_dict, *args, **kwargs):
        data = super().create_object(fields_dict, *args, **kwargs)
        if fields_dict["files"]:
            for file in fields_dict["files"]:
                File.objects.create(file=file,file_name=file.name,ticket=self.object)
        if fields_dict["claim"].startswith("#RIVE-"):
            claim = ClaimIVE.objects.filter(id=fields_dict["claim"]).first()
        else:
            claim = ClaimRegular.objects.filter(id=fields_dict["claim"]).first()
        if claim:
            locale = Locale('es', 'AR')
            date = localtime(datetime.now(timezone.utc))
            custom_format = "d 'de' MMMM 'de' yyyy 'a las' HH:mm"
            activity = {
                "id": len(claim.activity)+1,
                "type": "support",
                "timestamp": format_datetime(date, format=custom_format, locale=locale),
                "user": self.request.scope.account.full_name,
                'content': f'Se genero el ticket “{self.object.id}“',
                'highlighted': False,
            }
            claim.activity.append(activity)
            claim.save()
        return data
    
    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)                    
        for ticket in data:
            ticket['created_at'] = ticket['created_at'].strftime("%d/%m/%Y")
            ticket['status'] = status[ticket["status"]]

        return data
    
    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs) 
        data["support_level"] = self.object.get_support_level_display()
        data["activity"].sort(key=lambda x: x["id"], reverse=True)
        files = File.objects.filter(ticket=self.object).all()
        data["files"] = []
        for file in files:
            new_file = {
                "uuid":file.uuid,
                "file":file.file.url,
                "file_name":file.file_name,
                "created_at":file.created_at.strftime("%d/%m/%Y")
            }
            data["files"].append(new_file)
        return data
    
class AddCommentTicketView(BaseView):
    model = Ticket

    extra_fields = {
        'id': int,
        'type': str,
        'timestamp': str,
        'user': str,
        'content': str,
        'highlighted': bool,
    }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def modify_object(self, fields_dict, *args, **kwargs):

        activity_list = self.object.activity
        
        if isinstance(fields_dict['timestamp'], str):
            fields_dict['timestamp'] = datetime.strptime(
                fields_dict['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc)

        modified_at_local = localtime(fields_dict['timestamp'])
        custom_format = "d 'de' MMMM 'de' yyyy 'a las' HH:mm"
        locale = "es_ES"
        fields_dict["timestamp"] = format_datetime(modified_at_local, format=custom_format, locale=locale)

        # Si no existe el ID, agregar un nuevo objeto con ID incremental
        new_id = max([item.get("id", 0) for item in activity_list], default=0) + 1
        fields_dict["id"] = new_id
        activity_list.append(fields_dict)

        self.object.save()
        return JsonResponse({"message": "Se agregó correctamente la actividad"}, status=200)
    
class AddAditionalInfoClaimView(BaseView):
    model = Ticket
    
    extra_fields = {
        'id': int,
        'type': str,
        'timestamp': str,
        'user': str,
        'content': str,
        'highlighted': bool,
        'ticket':str
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    
    def modify_object(self, fields_dict, *args, **kwargs):
        if self.object.claim.startswith("#RIVE-"):
            claim = ClaimIVE.objects.filter(id=self.object.claim).first()
        else:
            claim = ClaimRegular.objects.filter(id=self.object.claim).first()  
        activity_list = claim.activity
        
        if isinstance(fields_dict['timestamp'], str):
            fields_dict['timestamp'] = datetime.strptime(
                fields_dict['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc)

        modified_at_local = localtime(fields_dict['timestamp'])
        custom_format = "d 'de' MMMM 'de' yyyy 'a las' HH:mm"
        locale = "es_ES"
        fields_dict["timestamp"] = format_datetime(modified_at_local, format=custom_format, locale=locale)

        # Si no existe el ID, agregar un nuevo objeto con ID incremental
        new_id = max([item.get("id", 0) for item in activity_list], default=0) + 1
        fields_dict["id"] = new_id
        activity_list.append(fields_dict)

        claim.save()

        activity_list = self.object.activity

        new_id = max([item.get("id", 0) for item in activity_list], default=0) + 1
        fields_dict["id"] = new_id
        activity_list.append(fields_dict)
        self.object.save()

        return JsonResponse({"message": "Se agregó correctamente la actividad"}, status=200)

class AssignTicketView(BaseView):
    model = Ticket

    fields = ["id","uuid", "claim","assigned","status","support_level","activity","problem_description","tasks","created_at"]

    list_fields_related = {
        "assigned":["uuid","full_name"],
    }

    extra_fields = {
        'assigned_id':str,
    }

    list_page_size = "all"
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    
    def modify_object(self, fields_dict, *args, **kwargs):
        data = super().modify_object(fields_dict, *args, **kwargs)
        support_level = {
            "S/A":"unassigned",
            "Nivel 1 (N1)":"n1",
            "Nivel 2 (N2)":"n2",
            "Nivel 3 (N3)":"n3",
        }
        self.object.support_level = support_level.get(self.object.assigned.support_level, "unassigned")
        self.object.status="in_progress"
        self.object.save()
        return data