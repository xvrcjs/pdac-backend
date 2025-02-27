from datetime import datetime, timezone
import json
import os
from django.utils.timezone import localtime
from babel.dates import format_datetime
from datetime import datetime
from babel import Locale
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from administration.models import TrafficLightSystemTimes
from claims.models import ClaimRegular, Claimer, File, Supplier
from common.communication.utils import send_email
from common.views import BaseView
from users.models import Account
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db import transaction

@csrf_exempt
def SendClaimIVE(request):

    if request.method == 'POST':

        data = json.loads(request.body)
        if not (('email' in data) and (isinstance(data['email'],str))):
            return HttpResponseBadRequest()

        template_path = os.path.join('/src/common/communication/claimIVE.html')

        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()

        message = template

        send_email(data["email"], "Subject title", message)
        return JsonResponse({'message': 'Email sent successfully'})
    else:
        return HttpResponseBadRequest()    

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
                return self.object

            except Exception as e:
                print(f"Error: {e}")
                raise

class ClaimView(BaseView):
    model = ClaimRegular

    fields = ["id","uuid", "claimer","suppliers","problem_description","files","activity","claim_access","type_of_claim","claim_status","category","heading","subheading","transfer_to_company","derived_to_omic","derived_to_user","transfer_to_the_consumer","conciliation_hearing","imputation","resolution","monetary_agreement","created_at"]

    list_fields_related = {
        "suppliers":["fullname","cuil"],
        "claimer":["fullname","dni","cuit","email","gender"],
        "files":["uuid","file","file_name"]
    }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)

        locale = Locale('es', 'AR')
        modified_at_local = localtime(data['created_at'])
        custom_format = "dd/MM/yyyy 'a las' HH.mm'hs'"
        data['created_at'] = format_datetime(modified_at_local, format=custom_format, locale=locale)
        for file in data['files']:
            file_instance = File.objects.get(uuid=file["uuid"])
            file["file"] = file_instance.file.url

        return data

    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        data_new = []

        for claim in data:
            claim_data = {}
            claim_data["uuid"]= claim["uuid"]
            claim_data["id"] = claim["id"]
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
                        if elapsed_time < trafic_config["yellowToRed_c"]:
                            claim_data["type_of_claim"] = "amarillo"
                        else:
                            claim_data["type_of_claim"] = "rojo"
                else:
                    if elapsed_time < trafic_config["greenToYellow_c"]:
                        claim_data["type_of_claim"] = "hv_verde"
                    else:
                        if elapsed_time < trafic_config["yellowToRed_c"]:
                            claim_data["type_of_claim"] = "hv_amarillo"
                        else:
                            claim_data["type_of_claim"] = "hv_rojo" 
            else:
                claim_data["type_of_claim"] =  "verde"

            data_new.append(claim_data)
        return data_new

class GenerateClaimPdf(BaseView):
    model = ClaimRegular

    fields = ["id","uuid", "claimer","suppliers","problem_description","files","claim_access","type_of_claim","claim_status","category","heading","subheading","transfer_to_company","derived_to_omic","derived_to_user","transfer_to_the_consumer","conciliation_hearing","imputation","resolution","monetary_agreement","created_at","activity"]

    list_fields_related = {
        "suppliers":["fullname","cuil","address","num_address","city","zip_code"],
        "claimer":["fullname","dni","cuit","email","gender"],
        "files":["uuid","file","file_name"]
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_json(self, fields, **kwargs):
        claim = super().data_json(fields, **kwargs)

        from django.http import HttpResponse
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from textwrap import wrap  # Para dividir texto largo en líneas

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{claim["id"]}.pdf"'
        pdf = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        pdf.drawImage("common/templates/claim/reclamo.png", 0, 0, width=width, height=height)

        margin_top = 50  # Margen desde la parte superior
        y_position = height - margin_top  # Posición inicial de escritura

        def draw_input_label(x, y, value):
            """Dibuja etiquetas y cuadros de texto para simular inputs"""
            pdf.setFont("Helvetica", 10)
            pdf.drawString(x + 5, y - 7, value)  

        # Datos de reclamo
        #ID
        pdf.setFont("Helvetica", 8)
        pdf.drawString(505, y_position+26, claim["id"])  
        #Fecha de creación
        pdf.drawString(540, y_position+15, format_datetime(claim["created_at"],format="dd/MM/yyyy"))

        y_position-=28
        # Datos del solicitante
        draw_input_label(28, y_position, claim["claimer"]["fullname"])
        draw_input_label(28, y_position - 48, claim["claimer"]["dni"])
        draw_input_label(28, y_position - 93, claim["claimer"]["cuit"])
        draw_input_label(28, y_position - 140, claim["claimer"]["email"])
        GENDER_CHOICES = {
            "female": "Femenino",
            "male": "Masculino",
            "x": "X",
            "other": "Otro",
            "none": "Prefiero no decirlo",
        }
        draw_input_label(28, y_position - 185, GENDER_CHOICES.get(claim["claimer"]["gender"]))

        # Datos del proveedor
        y_position -= 250
        x_base_supplier = 28
        for i in range(3):
            supplier = claim["suppliers"][i] if i < len(claim["suppliers"]) else {}  
            draw_input_label(x_base_supplier, y_position - 20, supplier.get("cuil", "-"))
            draw_input_label(x_base_supplier, y_position - 83, supplier.get("fullname", "-"))
            draw_input_label(x_base_supplier, y_position - 140, supplier.get("address", "-"))
            draw_input_label(x_base_supplier, y_position - 187, supplier.get("city", "-"))
            draw_input_label(x_base_supplier, y_position - 235, supplier.get("num_address", "-"))
            draw_input_label(x_base_supplier, y_position - 280, supplier.get("zip_code", "-"))
            x_base_supplier += 185
        y_position -= 340

        # Espacio disponible en la página
        available_space = y_position - 30  

        wrapped_text = wrap(claim["problem_description"], 110)

        for line in wrapped_text:
            if available_space < 40:  # Si no hay espacio, saltar de página
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = height - 50  # Reiniciar posición en la nueva página
                available_space = y_position - 50  
            draw_input_label(28,y_position,line)
            # pdf.drawString(55, y_position, line)
            y_position -= 15  # Moverse a la siguiente línea
            available_space -= 15  # Reducir el espacio disponible

        pdf.showPage()
        pdf.save()
        return response