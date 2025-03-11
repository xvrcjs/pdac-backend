from json import loads
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from administration.models import Client, TrafficLightSystemTimes,Omic
from common.views import BaseView
from users.models import Account
from babel import Locale
from babel.dates import format_datetime
from datetime import datetime

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