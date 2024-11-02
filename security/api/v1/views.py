from common.views import BaseView
from security.models import Role, Policy
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
 
    
    
class PolicyView(BaseView):
    model = Policy

class RoleView(BaseView):
    model = Role
    fields = ['uuid', 'name','description']
