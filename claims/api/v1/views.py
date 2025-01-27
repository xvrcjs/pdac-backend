import json
import os
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common.communication.utils import send_email
from common.views import BaseView

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


    

