from common.views import BaseView
from security.models import Role, Module
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
 
    
class ModuleView(BaseView):
    model = Module
    fields = ['uuid', 'name','mapping_key']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        return super().dispatch(request,*args,**kwargs)

class RoleView(BaseView):
    model = Role
    fields = ['uuid', 'name','description']
