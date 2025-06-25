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
from administration.models import Omic, TrafficLightSystemTimes
from claims.models import ClaimIVE, ClaimRegular, Claimer, File, Supplier
from tickets.models import Ticket
from common.communication.utils import send_email
from common.models import BaseModel
from common.views import BaseView
from users.models import Account
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db import transaction

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap  # Para dividir texto largo en líneas

locale = Locale('es', 'AR')

class CreateClaimIveView(BaseView):
    model = ClaimIVE

    extra_fields = {
        'fullname': str,
        'dni': str,
        'birthdate': str,
        'email': str,
        'phone': str,
        'street':str,
        'number':str,
        'between_streets':str,
        'province':str,
        'city':str,
        'has_social_work': bool,
        'social_work_or_company': str,
        'establishment': str,
        'other': str,
        'reasons': list
    }

    DANGEROUSLY_PUBLIC = True

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        if (request.user):
            self.request.scope.account = Account.objects.filter(user_id=settings.ANONYMOUS_USER_UUID).first()
        return super().dispatch(request,*args,**kwargs)

    def create_object(self, fields_dict, *args, **kwargs):
        with transaction.atomic():
            try:
                fields_dict["birthdate"] = datetime.strptime(fields_dict["birthdate"], "%d/%m/%Y").strftime("%Y-%m-%d")
                super().create_object(fields_dict, *args, **kwargs)
                
                self.model.send_notification(self.object)
                return self.object

            except Exception as e:
                print(f"Error: {e}")
                raise 

class CreateClaimView(BaseView):
    model = ClaimRegular
    extra_fields = {
        'claimer': str,
        'suppliers': str,
        'problem_description': str,
        'files': [None, TemporaryUploadedFile],
    }

    DANGEROUSLY_PUBLIC = True

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        if (request.user):
            self.request.scope.account = Account.objects.filter(user_id=settings.ANONYMOUS_USER_UUID).first()
        return super().dispatch(request,*args,**kwargs)

    def create_object(self, fields_dict, *args, **kwargs):
        # Inicia una transacción
        with transaction.atomic():
            try:
                #Proceso los datos del Claimer
                claimer_data = json.loads(fields_dict["claimer"])
                del fields_dict["claimer"]
                fields_dict["claimer"] = Claimer.objects.create(**claimer_data)

                #Proceso los datos de los Suppliers
                supplier_data = json.loads(fields_dict["suppliers"])
                fields_dict["suppliers"] = []
                for supplier in supplier_data:
                    transformed_supplier_data = {
                        key[:-3] if key.endswith("_sp") else key: value
                        for key, value in supplier.items()
                    }
                    if "has_cuil" in transformed_supplier_data:
                        del transformed_supplier_data["has_cuil"]

                    supplier_obj = Supplier.objects.create(**transformed_supplier_data)
                    fields_dict["suppliers"].append(supplier_obj)

                # Guardo los archivos para procesarlos despues
                files = fields_dict["files"]
                del fields_dict["files"]

                super().create_object(fields_dict, *args, **kwargs)
                if files:
                    for file in files:
                        file_created = File.objects.create(file=file,file_name=file.name,claim=self.object.id)
                        self.object.files.add(file_created)

                self.object.save()

                self.model.send_notification(self.object)
                return self.object

            except Exception as e:
                print(f"Error: {e}")
                raise

class ClaimView(BaseView):
    model = ClaimRegular

    fields = ["id","uuid", "claimer","suppliers","problem_description","files","activity","claim_access","type_of_claim","claim_status","category","heading","subheading","transfer_to_company","derived_to_omic","derived_to_user","transfer_to_the_consumer","conciliation_hearing","imputation","resolution","monetary_agreement","created_at"]

    list_fields_related = {
        "suppliers":["fullname","cuil"],
        "claimer":["fullname","dni","cuit","email","gender","street","number","between_streets","province","city"],
        "files":["uuid","file","file_name"],
        "derived_to_omic":["uuid","name","responsible"],
    }

    extra_fields = {
        'claim_access':str,
        'type_of_claim':str,
        'claim_status':str,
        'category':str,
        'heading':str,
        'subheading':str,
        'transfer_to_company':str,
        'derived_to_omic':[None,str],
        'transfer_to_the_consumer':str,
        'conciliation_hearing':str,
        'imputation':str,
        'resolution':str,
        'monetary_agreement':str
    }

    list_page_size = 10

    list_search_fields=["derived_to_user__uuid"]
    list_order_by = ["-id"]

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)

        #Obtengo las url de los archivos
        for file in data['files']:
            file_instance = File.objects.get(uuid=file["uuid"])
            file["file"] = file_instance.file.url

        #Obtengo los ultimos 3 comentarios destacados
        highlighted_comments = [item for item in data["activity"] if item.get("highlighted")]
        highlighted_comments.sort(key=lambda x: x["timestamp"], reverse=True)
        data["featured_comments"] = highlighted_comments[:3]

        #Obtengo el nombre del usuario asignado
        if data["derived_to_user"]:
            account = Account.objects.filter(uuid=data["derived_to_user"]).first()
            data["assigned"] = account.full_name if account else "S/A"
        else:
            data["assigned"] = f"{data['derived_to_omic']['name']} - {data['derived_to_omic']['responsible']}" if data["derived_to_omic"] else "S/A"
        
        #Ordeno las actividades en base a las mas nuevas primero
        data["activity"].sort(key=lambda x: x["id"], reverse=True)

        #Calculo el tiempo transcurrido desde la creacion del reclamo hasta hoy
        status_activities = [entry for entry in self.object.activity if entry.get("type") == "status_activity"]

        data["last_status"] = max(status_activities, key=lambda x: x["id"]) if status_activities else None

        #Logica para tipo de reclamo y estado de reclamo
        trafic_config = TrafficLightSystemTimes.objects.values("greenToYellow_c","yellowToRed_c","greenToYellow_ive_hv","yellowToRed_ive_hv").first()
        if data["type_of_claim"] != "S/A":
            elapsed_time = ((datetime.now(timezone.utc)-data["created_at"]).total_seconds())//3600
            if data["type_of_claim"][:2] != "HV": # RECLAMO COMUN
                if elapsed_time < trafic_config["greenToYellow_c"]:
                    data["status_claim"] = "verde"
                else:
                    if elapsed_time < (trafic_config["yellowToRed_c"]+trafic_config["greenToYellow_c"]):
                        data["status_claim"] = "amarillo"
                    else:
                        data["status_claim"] = "rojo"
            else:
                if elapsed_time < trafic_config["greenToYellow_c"]:
                    data["status_claim"] = "hv_verde"
                else:
                    if elapsed_time < (trafic_config["yellowToRed_c"]+trafic_config["greenToYellow_c"]):
                        data["status_claim"] = "hv_amarillo"
                    else:
                        data["status_claim"] = "hv_rojo" 
        else:
            data["status_claim"] =  "verde"

        #Devuelvo la fecha de creacion formateada
        locale = Locale('es', 'AR')
        modified_at_local = localtime(data['created_at'])
        custom_format = "dd/MM/yyyy 'a las' HH.mm'hs'"
        data['created_at'] = format_datetime(modified_at_local, format=custom_format, locale=locale)
        data['has_ticket'] = Ticket.objects.filter(claim=data['id']).exclude(status="closed").exists()

        return data

    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        data_new = []

        for claim in data:
            claim_data = {}
            claim_data["uuid"]= claim["uuid"]
            claim_data["id"] = claim["id"]
            if claim["derived_to_omic"]:
                claim_data["assigned"] = f"{claim['derived_to_omic']['name']} - {claim['derived_to_omic']['responsible']}" if claim["derived_to_omic"] else "S/A"
            else:
                account = Account.objects.filter(uuid=claim["derived_to_user"]).first()
                claim_data["assigned"] = account.full_name if account else "S/A"
            claim_data["status"] = claim["claim_status"]

            #Logica para tipo de reclamo y estado de reclamo
            trafic_config = TrafficLightSystemTimes.objects.values("greenToYellow_c","yellowToRed_c","greenToYellow_ive_hv","yellowToRed_ive_hv").first()
            if claim["type_of_claim"] != "S/A":
                elapsed_time = ((datetime.now(timezone.utc)-claim["created_at"]).total_seconds())//3600
                if claim["type_of_claim"][:2] != "HV": # RECLAMO COMUN
                    if elapsed_time < trafic_config["greenToYellow_c"]:
                        claim_data["type_of_claim"] = "verde"
                    else:
                        if elapsed_time < (trafic_config["yellowToRed_c"]+trafic_config["greenToYellow_c"]):
                            claim_data["type_of_claim"] = "amarillo"
                        else:
                            claim_data["type_of_claim"] = "rojo"
                else:
                    if elapsed_time < trafic_config["greenToYellow_c"]:
                        claim_data["type_of_claim"] = "hv_verde"
                    else:
                        if elapsed_time < (trafic_config["yellowToRed_c"]+trafic_config["greenToYellow_c"]):
                            claim_data["type_of_claim"] = "hv_amarillo"
                        else:
                            claim_data["type_of_claim"] = "hv_rojo" 
            else:
                claim_data["type_of_claim"] =  "verde"

            data_new.append(claim_data)
        return data_new
    def modify_object(self, fields_dict, *args, **kwargs):
        if fields_dict["claim_status"] != self.object.claim_status:
            locale = Locale('es', 'AR')
            date = localtime(datetime.now(timezone.utc))
            custom_format = "d 'de' MMMM 'de' yyyy 'a las' HH:mm"
            activity = {
                "id": len(self.object.activity)+1,
                "type": "status_activity",
                "timestamp": format_datetime(date, format=custom_format, locale=locale),
                "user": self.request.scope.account.full_name,
                'content': f'Realizó cambio de estado de “{self.object.claim_status}“ a “{fields_dict["claim_status"]}“',
                'highlighted': False,
            }
            self.object.activity.append(activity)
            self.object.save()

        return super().modify_object(fields_dict, *args, **kwargs)
class ClaimIVEView(BaseView):
    model = ClaimIVE

    fields = ["id","uuid", "fullname","dni","birthdate","email","phone","has_social_work","establishment","other""reasons","problem_description","activity","claim_access","type_of_claim","claim_status","category","heading","subheading","transfer_to_company","derived_to_omic","derived_to_user","transfer_to_the_consumer","conciliation_hearing","imputation","resolution","monetary_agreement","created_at"]

    list_fields_related = {
        "derived_to_omic":["uuid","name","responsible"],
    }

    extra_fields = {
        'claim_access':str,
        'type_of_claim':str,
        'claim_status':str,
        'category':str,
        'heading':str,
        'subheading':str,
        'transfer_to_company':str,
        'derived_to_omic':[None,str],
        'transfer_to_the_consumer':str,
        'conciliation_hearing':str,
        'imputation':str,
        'resolution':str,
        'monetary_agreement':str
    }
    list_page_size = "all"

    list_search_fields=["derived_to_user__uuid"]

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)

        #Obtengo los ultimos 3 comentarios destacados
        highlighted_comments = [item for item in data["activity"] if item.get("highlighted")]
        highlighted_comments.sort(key=lambda x: x["timestamp"], reverse=True)
        data["featured_comments"] = highlighted_comments[:3]

        #Ordeno las actividades en base a las mas nuevas primero
        data["activity"].sort(key=lambda x: x["id"], reverse=True)

        #Calculo el tiempo transcurrido desde la creacion del reclamo hasta hoy
        status_activities = [entry for entry in self.object.activity if entry.get("type") == "status_activity"]

        data["last_status"] = max(status_activities, key=lambda x: x["id"]) if status_activities else None

        #Logica para tipo de reclamo y estado de reclamo
        trafic_config = TrafficLightSystemTimes.objects.values("greenToYellow_ive_hv","yellowToRed_ive_hv").first()
        elapsed_time = ((datetime.now(timezone.utc)-data["created_at"]).total_seconds())//3600
        if elapsed_time < trafic_config["greenToYellow_ive_hv"]:
            data["status_claim"] = "hv_ive_v"
        else:
            if elapsed_time < (trafic_config["yellowToRed_ive_hv"]+trafic_config["greenToYellow_ive_hv"]):
                data["status_claim"] = "hv_ive_a"
            else:
                data["status_claim"] = "hv_ive_r" 

        #Devuelvo la fecha de creacion formateada
        locale = Locale('es', 'AR')
        modified_at_local = localtime(data['created_at'])
        custom_format = "dd/MM/yyyy 'a las' HH.mm'hs'"
        data['created_at'] = format_datetime(modified_at_local, format=custom_format, locale=locale)

        data["birthdate"] = format_datetime(data["birthdate"], format="dd/MM/yyyy")
        return data
    
    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        data_new = []

        for claim in data:
            claim_data = {}
            claim_data["uuid"]= claim["uuid"]
            claim_data["id"] = claim["id"]
            if claim["derived_to_user"]:
                account = Account.objects.filter(uuid=claim["derived_to_user"]).first()
                claim_data["assigned"] = account.full_name if account else "S/A"
            else:
                claim_data["assigned"] = f"{claim['derived_to_omic']['name']} - {claim['derived_to_omic']['responsible']}" if claim["derived_to_omic"] else "S/A"
            claim_data["status"] = claim["claim_status"]

            #Logica para tipo de reclamo y estado de reclamo
            trafic_config = TrafficLightSystemTimes.objects.values("greenToYellow_ive_hv","yellowToRed_ive_hv").first()
            elapsed_time = ((datetime.now(timezone.utc)-claim["created_at"]).total_seconds())//3600
            if elapsed_time < trafic_config["greenToYellow_ive_hv"]:
                claim_data["type_of_claim"] = "hv_ive_v"
            else:
                if elapsed_time < (trafic_config["yellowToRed_ive_hv"]+trafic_config["greenToYellow_ive_hv"]):
                    claim_data["type_of_claim"] = "hv_ive_a"
                else:
                    claim_data["type_of_claim"] = "hv_ive_r" 

            data_new.append(claim_data)

        has_admin_role = "Admin" in self.account.roles.values_list("name", flat=True)
        if has_admin_role:
            claim_hv = ClaimRegular.objects.filter(type_of_claim__icontains="HV").values('uuid','id','derived_to_user','derived_to_omic__name','derived_to_omic__responsible','claim_status','created_at')
        else:
            claim_hv = ClaimRegular.objects.filter(derived_to_user=self.account.uuid, type_of_claim__icontains="HV").values('uuid','id','derived_to_user','derived_to_omic__name','derived_to_omic__responsible','claim_status','created_at')
        for claim in claim_hv:
            claim_data = {}
            claim_data["uuid"]= claim["uuid"]
            claim_data["id"] = claim["id"]
            if claim["derived_to_user"]:
                account = Account.objects.filter(uuid=claim["derived_to_user"]).first()
                claim_data["assigned"] = account.full_name if account else "S/A"
            else:
                claim_data["assigned"] = f"{claim['derived_to_omic__name']} - {claim['derived_to_omic__responsible']}" if claim['derived_to_omic__name'] else "S/A"
            claim_data["status"] = claim["claim_status"]

            #Logica para tipo de reclamo y estado de reclamo
            trafic_config = TrafficLightSystemTimes.objects.values("greenToYellow_ive_hv","yellowToRed_ive_hv").first()
            elapsed_time = ((datetime.now(timezone.utc)-claim["created_at"]).total_seconds())//3600
            if elapsed_time < trafic_config["greenToYellow_ive_hv"]:
                claim_data["type_of_claim"] = "hv_verde"
            else:
                if elapsed_time < (trafic_config["yellowToRed_ive_hv"]+trafic_config["greenToYellow_ive_hv"]):
                    claim_data["type_of_claim"] = "hv_amarillo"
                else:
                    claim_data["type_of_claim"] = "hv_rojo" 
            data_new.append(claim_data)
        return data_new
    
class CommentToClaimIVE(BaseView):

    model = ClaimIVE

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
        # Si existe el ID en lo field debe modificar solo el estado de destacado
        if "id" in fields_dict:
            for item in activity_list:
                if item.get("id") == fields_dict["id"]:
                    item["highlighted"] = not item.get("highlighted", False)
                    self.object.save()
                    return JsonResponse({"message": "Se actualizó correctamente la actividad"}, status=200)
        
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
    
class CantClaimHVView(BaseView):
    model = ClaimIVE

    fields = ["derived_to_omic","derived_to_user"]

    list_fields_related = {
        "derived_to_omic":["uuid","name","responsible"],
        "derived_to_user":["uuid","full_name"]
    }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    
    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        data_new = {}
        has_admin_role = "Admin" in self.account.roles.values_list("name", flat=True)
        if has_admin_role:
            data_new["total_claims_hv"] = sum(1 for item in data if item['derived_to_user'] is None)
        else:
            data_new["total_claims_hv"] = 0

        return data_new

class GenerateClaimPdf(BaseView):
    model = ClaimRegular

    fields = ["id","uuid", "claimer","suppliers","problem_description","files","claim_access","type_of_claim","claim_status","category","heading","subheading","transfer_to_company","derived_to_omic","derived_to_user","transfer_to_the_consumer","conciliation_hearing","imputation","resolution","monetary_agreement","created_at","activity"]

    list_fields_related = {
        "suppliers":["fullname","cuil","address","num_address","city","zip_code"],
        "claimer":["fullname","dni","cuit","email","gender","street","number","between_streets","province","city"],
        "files":["uuid","file","file_name"]
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_json(self, fields, **kwargs):
        claim = super().data_json(fields, **kwargs)

        #Para testear como se ve sin tener que descargar el archivo continuamente descomentar esto
        # response = HttpResponse(content_type="application/pdf")
        # response["Content-Disposition"] = f'attachment; filename="{claim["id"]}.pdf"'
        # pdf = canvas.Canvas(response, pagesize=A4)

        pdf_buffer = io.BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        pdf.drawImage("common/templates/claim/reclamo-comun-1.png", 0, 0, width=width, height=height)

        margin_top = 50  # Margen desde la parte superior
        y_position = height - margin_top  # Posición inicial de escritura

        def draw_input_label(x, y, value,fontSize):
            """Dibuja etiquetas y cuadros de texto para simular inputs"""
            pdf.setFont("Helvetica", fontSize)
            pdf.drawString(x + 5, y - 7, value)  

        # Datos de reclamo
        #ID
        pdf.setFont("Helvetica", 8)
        pdf.drawString(440, y_position-2, claim["id"])  
        #Fecha de creación
        pdf.drawString(473, y_position-11, format_datetime(claim["created_at"],format="dd/MM/yyyy"))

        y_position-=28
        # Datos del solicitante
        draw_input_label(45, y_position-58, claim["claimer"]["fullname"],10)
        draw_input_label(45, y_position - 106, claim["claimer"]["dni"],10)
        draw_input_label(45, y_position - 151, claim["claimer"]["cuit"],10)
        draw_input_label(45, y_position - 198, claim["claimer"]["email"],10)
        GENDER_CHOICES = {
            "female": "Femenino",
            "male": "Masculino",
            "x": "X",
            "other": "Otro",
            "none": "Prefiero no decirlo",
        }
        draw_input_label(45, y_position - 243, GENDER_CHOICES.get(claim["claimer"]["gender"]),10)

        y_position = 763
        #Datos de domicilio
        draw_input_label(350, y_position - 58, claim["claimer"]["street"],10)
        draw_input_label(350, y_position - 106, claim["claimer"]["between_streets"],10)
        draw_input_label(350, y_position - 151, claim["claimer"]["number"],10)
        draw_input_label(350, y_position - 198, claim["claimer"]["province"],10)
        draw_input_label(350, y_position - 243, claim["claimer"]["city"],10)

        # Datos del proveedor
        y_position -= 343
        x_base_supplier = 45
        for i in range(3):
            supplier = claim["suppliers"][i] if i < len(claim["suppliers"]) else {} 
            draw_input_label(x_base_supplier, y_position - 20, supplier.get("cuil", "-"),8)
            draw_input_label(x_base_supplier, y_position - 81, supplier.get("fullname", "-"),8)
            draw_input_label(x_base_supplier, y_position - 140, supplier.get("address", "-"),8)
            draw_input_label(x_base_supplier, y_position - 187, supplier.get("city", "-"),8)
            draw_input_label(x_base_supplier, y_position - 233, supplier.get("num_address", "-"),8)
            draw_input_label(x_base_supplier, y_position - 280, supplier.get("zip_code", "-"),8)
            x_base_supplier += 173
        y_position -= 340

        # Espacio disponible en la página
        available_space = y_position - 30  

        wrapped_text = wrap(claim["problem_description"], 100)

        # Nueva pagina
        pdf.showPage()
        pdf.setFont("Helvetica", 10)
        y_position = height - 120  # Reiniciar posición en la nueva página
        available_space = y_position - 50
        pdf.drawImage("common/templates/claim/reclamo-comun-2.png", 0, 0, width=width, height=height)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(440, y_position+68, claim["id"])  
        #Fecha de creación
        pdf.drawString(473, y_position+58, format_datetime(claim["created_at"],format="dd/MM/yyyy"))
        for line in wrapped_text:
            draw_input_label(50,y_position,line,10)
            y_position -= 15  # Moverse a la siguiente línea
            available_space -= 15  # Reducir el espacio disponible

        pdf.showPage()
        pdf.save()

        pdf_buffer.seek(0)
        encoded_pdf = base64.b64encode(pdf_buffer.read()).decode("utf-8")
        return JsonResponse({"pdf_base64": encoded_pdf, "filename": f"{claim['id']}.pdf"})

        # return response
class CommentToClaim(BaseView):

    model = ClaimRegular

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
        # Si existe el ID en lo field debe modificar solo el estado de destacado
        if "id" in fields_dict:
            for item in activity_list:
                if item.get("id") == fields_dict["id"]:
                    item["highlighted"] = not item.get("highlighted", False)
                    self.object.save()
                    return JsonResponse({"message": "Se actualizó correctamente la actividad"}, status=200)
        
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
    
class GenerateClaimFileZip(BaseView):
    model = ClaimRegular

    fields = ["id","uuid", "files"]

    list_fields_related = {
        "files":["uuid","file","file_name"]
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    
    def data_json(self, fields, **kwargs):
        import zipfile 

        claim = super().data_json(fields,**kwargs)
        # Creamos un archivo ZIP en memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in claim["files"]:
                file_instance = File.objects.get(uuid=file["uuid"])
                zip_file.write(settings.MEDIA_ROOT+"/"+file["file"], arcname=file["file_name"].split("/")[-1])

        # Convertimos el archivo ZIP a base64
        zip_buffer.seek(0)  # Volvemos al inicio del buffer
        zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')

        return JsonResponse({
            "zip_file": zip_base64,
        })
    
class AssignClaim(BaseView):
    model = ClaimRegular

    extra_fields = {
        'type': str,
        'assigned_id': str,
    }
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def modify_object(self, fields_dict, *args, **kwargs):
        if(fields_dict["type"] == "omic"):
            omic = Omic.objects.filter(uuid=fields_dict["assigned_id"]).first()
            fields_dict["derived_to_omic"] = omic
            fields_dict["derived_to_user"] = Account.objects.filter(omic=omic).first()
        else:
            fields_dict["derived_to_user"] =  Account.objects.filter(uuid=fields_dict["assigned_id"]).first()
            fields_dict["derived_to_omic"] = None
        del fields_dict["assigned_id"]
        del fields_dict["type"]
        return super().modify_object(fields_dict, *args, **kwargs)
    
class AssignClaimIVE(BaseView):
    model = ClaimIVE

    extra_fields = {
        'type': str,
        'assigned_id': str,
    }
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def modify_object(self, fields_dict, *args, **kwargs):
        if(fields_dict["type"] == "omic"):
            fields_dict["derived_to_omic"] = Omic.objects.filter(uuid=fields_dict["assigned_id"]).first()
        else:
            fields_dict["derived_to_user"] =  Account.objects.filter(uuid=fields_dict["assigned_id"]).first()

        del fields_dict["assigned_id"]
        del fields_dict["type"]
        return super().modify_object(fields_dict, *args, **kwargs)

class RejectClaim(BaseView):
    model = ClaimRegular
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
        locale = Locale('es', 'AR')
        date = localtime(datetime.now(timezone.utc))
        custom_format = "d 'de' MMMM 'de' yyyy 'a las' HH:mm"
        activity = {
            "id": len(self.object.activity)+1,
            "type": "status_activity",
            "timestamp": format_datetime(date, format=custom_format, locale=locale),
            "user": self.request.scope.account.full_name,
            'content': f'Realizó cambio de estado de “{self.object.claim_status}“ a “Rechazado“ por motivo: “{fields_dict["content"]}“',
            'highlighted': False,
        }
        self.object.activity.append(activity)
        self.object.claim_status = "Rechazado"
        self.object.save()

        self.model.send_notification_rejected(self.object,fields_dict["content"])

        return JsonResponse({"message": "Se agregó correctamente la actividad"}, status=200)