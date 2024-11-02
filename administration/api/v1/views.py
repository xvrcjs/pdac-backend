from django.views.decorators.csrf import csrf_exempt
from administration.models import Client
from common.views import BaseView


class ClientView(BaseView):
    model = Client
    fields = ['name','owner','image_url']
    required_fields = {}

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        return super().dispatch(request,*args,**kwargs)
        


    

