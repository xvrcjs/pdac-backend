from common.views import BaseView
from security.models import Role, Module
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
 
    
    
class ModuleView(BaseView):
    model = Module

class RoleView(BaseView):
    model = Role
    fields = ['uuid', 'name','description']
