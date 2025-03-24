import base64
import io
from json import loads
import json
import mimetypes
import os
import shutil
from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from administration.models import Client, StandardsAndProtocols, TrafficLightSystemTimes,Omic
from common.views import BaseView
from users.models import Account
from babel import Locale
from babel.dates import format_datetime
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from datetime import datetime, timezone

class ClientView(BaseView):
    model = Client
    fields = ['name','owner','image_url']
    required_fields = {}

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        return super().dispatch(request,*args,**kwargs)
        
class TrafficLightSystemTimesConfigView(BaseView):
    model = TrafficLightSystemTimes
    fields = ['greenToYellow_c','yellowToRed_c','greenToYellow_ive_hv','yellowToRed_ive_hv','modified_by','modified_at']
    extra_fields={
        'greenToYellow_c':int,
        'yellowToRed_c':int,
        'greenToYellow_ive_hv':int,
        'yellowToRed_ive_hv':int,
        'modified_by':str,
        'modified_at':str
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        if request.method == 'GET':
            first_record = TrafficLightSystemTimes.objects.first()
            if first_record:
                kwargs['uuid']= first_record.uuid
            else:
                first_record = TrafficLightSystemTimes.objects.create(greenToYellow_c=8,
                yellowToRed_c=24,
                greenToYellow_ive_hv=8,
                yellowToRed_ive_hv=24)
                kwargs['uuid']= first_record.uuid
        if request.method == 'PATCH':
            first_record = TrafficLightSystemTimes.objects.first()
            if first_record:
                kwargs['uuid']= first_record.uuid
        return super().dispatch(request,*args,**kwargs)
    
    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)
        locale = Locale('es', 'AR')
        
        if data:
            userInfo = Account.objects.filter(user_id=data['modified_by']).first()
            data['modified_by'] = userInfo.full_name
            modified_at_local = localtime(data['modified_at'])
            custom_format = "EEEE dd/MM/yyyy 'a las' HH.mm'hs'"
            data['modified_at'] = format_datetime(modified_at_local, format=custom_format, locale=locale)

        return data
    
    def modify_object(self, fields_dict, *args, **kwargs):
        fields_dict['modified_at'] = datetime.now()
        fields_dict['modified_by'] = self.request.scope.user
        return super().modify_object(fields_dict, *args, **kwargs)
    
class OmicView(BaseView):
    model = Omic
    fields = ['uuid','name','responsible','opening_hours','phone','address','email']
    
    extra_fields = {
        'name':str,
        'responsible':str,
        'opening_hours':str,
        'phone':str,
        'address':str,
        'email':str
    }
    list_page_size = "all"

    list_order_by = ["name"]
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        return super().dispatch(request,*args,**kwargs)
    
@csrf_exempt
def OmicMassiveView(request):
    if request.method == 'POST':
        request_body = loads(request.body) 
        if request_body:
            for omic in request_body:
               Omic.objects.create(name=omic["name"],address=omic["address"],email=omic["email"],phone=omic["phone"],opening_hours=omic["opening_hours"],responsible=omic["responsible"])

            return JsonResponse(
                {
                    'response':'Se crearon correctamente las omics',
                },
                status=200
            )
        
        
    else:
        return HttpResponseBadRequest()
    
class StandardsAndProtocolsView(BaseView):
    model = StandardsAndProtocols
    fields = ['uuid','title','description','file','last_modified']
    
    extra_fields = {
        'title':str,
        'description':str,
        'file':[None,InMemoryUploadedFile],
    }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        return super().dispatch(request,*args,**kwargs)
    
    def create_object(self, fields_dict, *args, **kwargs):
        with transaction.atomic():
            try:
                fields_dict["file"]=fields_dict["file"][0]
                super().create_object(fields_dict, *args, **kwargs)
                return self.object
            except Exception as e:
                print(f"Error: {e}")
                raise
    def data_json(self, fields, **kwargs):
        data =  super().data_json(fields, **kwargs)
        del data["file"]
        return data
    
    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        for item in data:
            file_name = item.get("file").name if item.get("file") else None
            item["type_file"] = os.path.splitext(file_name)[-1].lstrip(".").lower() if file_name else "desconocido"
            locale = Locale('es', 'AR')
            custom_format = "dd/MM/yyyy"
            item["last_modified"] =  format_datetime(item["last_modified"], format=custom_format, locale=locale)
            item["url"]=item["file"].url              
            del item["file"]    
        return data
    
    def delete(self, request, *args, **kwargs):
        data = StandardsAndProtocols.objects.filter(uuid=kwargs["uuid"]).first()
        file_path = data.file.path.replace("/api", "/src")
        
        if os.path.exists(file_path):
            folder_path = os.path.dirname(file_path)
            shutil.rmtree(folder_path) 
            
        return super().delete(request, *args, **kwargs)
    
class StandardsAndProtocolsDownloadView(BaseView):
    model = StandardsAndProtocols
    fields = ['file']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)
    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)
        file_path = data["file"].path.replace("/api", "/src")

        if not os.path.exists(file_path):
            return HttpResponse("Archivo no encontrado", status=404)

        mime_type, _ = mimetypes.guess_type(file_path)

        response = FileResponse(open(file_path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        
        return response
        return super().data_json(fields, **kwargs)
    
class StandardsAndProtocolsZipView(BaseView):
    model = StandardsAndProtocols

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        response = self.create_zip(request.body)
        return response
    def create_zip(self, fields_dict):
        data = json.loads(fields_dict)

        if not data:
            return JsonResponse({"error": "No se proporcionaron UUIDs válidos"}, status=400)
        import zipfile 

        zip_buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for uuid in data:
                    instance = StandardsAndProtocols.objects.filter(uuid=uuid).first()
                    if not instance or not instance.file:
                        continue  
                    file_path = instance.file.path.replace("/api", "/src")
                    if not os.path.exists(file_path):
                        continue  
                    zip_file.write(file_path, arcname=instance.file.name.split("/")[-1])  

            if len(zip_file.filelist) == 0:
                return JsonResponse({"error": "No se encontraron archivos válidos"}, status=400)

            zip_buffer.seek(0)  
            zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')

            return JsonResponse({
                "zip_file": zip_base64,
            })

        except Exception as e:
            return JsonResponse({"error": f"Error al generar el ZIP: {str(e)}"}, status=500)