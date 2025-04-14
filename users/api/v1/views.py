import json
from django.apps import apps
from django.conf import settings
from django.forms import ValidationError
from django.contrib.auth import authenticate
from json import JSONEncoder, loads

import requests
from claims.models import ClaimRegular
from security.models import Role, Module
from common.utils import generateQr
from common.views import BaseView
from settings.middlewares import create_cookies, delete_cookies, get_request_at
from users.models import User,Account
from security.models import Role
from administration.models import Client
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.db.models import BooleanField, Case, Exists, ExpressionWrapper, F, OuterRef, Q, Value, When
from rest_framework.exceptions import APIException
from django.dispatch import receiver
# from settings.storages import FileStorage, StaticStorage
from django.db.models.signals import pre_save
from django.core.files.uploadedfile import InMemoryUploadedFile


# class GoogleLoginView(SocialLoginView): # if you want to use Authorization Code Grant, use this
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = "http://localhost:3000/"
#     client_class = OAuth2Client


# RESPONSES
def login_response(token, token_exp, refresh_token, refresh_token_exp, status=200):
    response = JsonResponse({
        'token_type': 'Bearer',
        'access_token': token,
        'expires_in': settings.JWT_ACCESS_EXP * 60 * 60,
        'expires_at': token_exp,
        'messages': [{'level': 'Debug', 'title': 'Logged in successfully', 'description': None}]
    }, status=status)
    return create_cookies(response, token, token_exp, refresh_token, refresh_token_exp)

def logout_response(status=401, console_message='Logged out successfully', error_message=None, error_description=None):

    messages = []
    if console_message:
        messages.append({'level': 'Debug', 'title': console_message, 'description': None})
    if error_message:
        messages.append({'level': 'Error', 'title': error_message, 'description': error_description})

    response = JsonResponse({'messages': messages}, status=status) \
        if messages else HttpResponse(status=status)

    return delete_cookies(response)

# LOGIN
@csrf_exempt
def login(request):
    # Check method
    if request.method != 'POST':
        return HttpResponse(status=403)

    # Get body
    request_body = loads(request.body) if request.body else None
    if not isinstance(request_body, dict):
        return HttpResponse(status=400)
    #API Key/Secret
    email = request_body.get('email').lower()
    password = request_body.get('password')
    remember_me = request_body.get('remember_me', False)
   
    
    # Check body
    if not (email and isinstance(email, str) and \
        password and isinstance(password, str) and \
        isinstance(remember_me, bool)):
        return HttpResponse(status=400)

    # Try to login
    user = authenticate(username=email, password=password)
    # Check user
   
    if not user:
        return logout_response(console_message=None,
            error_message='Invalid email or password',
            error_description='Please re-enter your password or choose "Forgot your password?" if you need assistance.')
    # Valida si el usuario es superuser
    if not user.is_superuser:
        client = Client.objects.filter(account__user=user,is_deleted=False) 
        if not client:
            return logout_response(console_message=None,
                error_message="client doesn't exists",
                error_description='Please enter a valid client.')
    
    account = Account.objects.filter(user=user).first()  
    if account:
        if not account.is_active:
            return logout_response(
                console_message=None,
                error_message='Account disabled',
                error_description='Please contact with the manager to active the account'
            )

    # Create token
    [token, token_exp] = user.create_token()

    # Create refresh_token
    # TODO: Create a refresh token for rememeber_me (user.create_refresh_token() if remember_me)
    [refresh_token, refresh_token_exp] = [None, None]
    # Update last login
    user.update_last_login()
    apps.get_model('users', 'Account').objects.filter(user=user ) \
        .update(last_login=get_request_at(),is_online=True, do_not_log=True)

    # Return login response
    return login_response(token, token_exp, refresh_token, refresh_token_exp)


# LOGOUT
def logout(request):
    """
    User logout
    API URL: auth/logout/
    Method: GET
    """
    # Check method
    if request.method != 'GET':
        return HttpResponse(status=403)
    apps.get_model('users','Account').objects.filter(uuid = request.scope.account.uuid).update(is_online = False)
    # Return logout response
    return logout_response(status=200)

    
@csrf_exempt
def forgot_password(request):

    if request.method == 'POST':
       
        data = json.loads(request.body)
        if not (('email' in data) and (isinstance(data['email'],str))):
            return HttpResponseBadRequest()
            
        user = User.objects.filter(email=data['email']).first()
        if user :
            if not user.is_active:
                  return JsonResponse(
                {
                    'messages': [{'level':'Error','title':None,'description':"The user is not active in the system"}],
                },
                status=400
            )
            account = Account.objects.filter(user__uuid=user.uuid).first()
            fields_dict = dict(full_name=account.full_name)
            user.create_reset_password_token(fields_dict)
            return JsonResponse(
                {
                'messages': [{'level': 'Success', 'title':None,'description': 'Check your email to restore the password'}],
                },
                status=200
            )
        else:
            return JsonResponse(
                {
                    'messages': [{'level':'Error', 'title':None,'description':"The email doesn't exist or is invalid"}],
                },
                status=400
            )
    else:
        return HttpResponseBadRequest()
    
@csrf_exempt
def create_password(request):
    if request.method == 'POST':
        request_body = loads(request.body) 
        reset_password_token = request_body .get('reset_password_token')
        if not (reset_password_token and (isinstance(reset_password_token,str))):
            return HttpResponseBadRequest()
        user = User.objects.filter(reset_password_token=reset_password_token,is_active = True).first()
        if user :
            new_pass = request_body.get('newPassword')
            if not (new_pass and isinstance(new_pass,str)):
                return HttpResponseBadRequest()
            try:
                 validate_password(new_pass)
            except ValidationError as err:
                return JsonResponse({'messages':[{'level': 'Error', 'title': err.messages[0], 'description': None}]},status=400)
            user.set_password(new_pass)
            user.reset_password_token_exp=None
            user.save()

            return JsonResponse(
               {
                   'messages':[{'level':'Success','title':'You have change your password successfully','description':None}],
               },
               status=200
           )
        else:
            return JsonResponse(
               {
                   'messages':[{'level':'Error','title':None, 'description':"User doesn't exist"}],
               },
               status=400
           )
    else:
        return HttpResponseBadRequest()

class AccountView(BaseView):
    model = Account
    fields = ['uuid', 'id', 'profile_image','full_name','dni', 'user','omic','support_level', 'is_active','roles','last_login','permissions','phone','created_at','comments']
    
    list_exclude = {'user__is_staff': True}
    
    extra_fields={
        'display_name':str,
        'is_active':bool,
        'roles':str,
        'email':str,
        'phone':str,
        'omic_id': [None,str],
        'support_level':str,
        'dni':str,
        'full_name':str,
        'client_id': str,
        'permissions':dict,
        'comments':str,
        'profile_image': [None, InMemoryUploadedFile]
    }

    list_fields_related = {
        'user':['display_name','email'],
        'omic':['uuid','name','responsible'],
        'roles' : ['name',],
        'permissions' :['name','mapping_key']
    }
    list_search_fields=["is_deleted","roles__name"]

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {} 
        if 'id' in kwargs:
            kwargs['uuid'] = Account.objects.filter(id=kwargs['id']).first().uuid
        return super().dispatch(request,*args,**kwargs)
    
    @staticmethod
    def get_profile_image_url(account):
        # account['profile_image_url'] = FileStorage.get_url(account['profile_image'])\
        #     if account['profile_image'] else StaticStorage.get_default_avatar_url()
        # del account['profile_image']
        return account

    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)
        for rol in data['roles']:
            rol['name'] = rol['name'].lower()
        data['permissions'] = {perm["mapping_key"]: True for perm in data["permissions"]}
        data['created_at'] = data['created_at'].strftime("%d/%m/%y")
        if data["last_login"]:
            data['last_login'] = data['last_login'].strftime("%d/%m/%y %H.%Mhs")
        else:
            data['last_login'] = "-"
        return self.get_profile_image_url(data)
    
    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        for user in data:
            user['details'] = {}
            if user["last_login"]:
                formatted_date = user["last_login"].strftime("%d/%m/%y %H.%Mhs")
            else:
                formatted_date = "-"
            user['details']['date'] = f"Ultimo acceso: {formatted_date}"
            user['details']['more_details'] = "Permisos de admin municipal por default activos"

            #TODO: Agregar la suma de los IVE
            user['details']['cant_claims_assigned'] = (ClaimRegular.objects.filter(derived_to_user__uuid=user["uuid"]).count())

        return data
    
    def annotate(self):
        if self.view_type != 'list': return {}
        can_view_module = lambda cls: Exists(Module.objects.annotate(
            all_policies=ExpressionWrapper(OuterRef('is_office_admin_or_owner'), output_field=BooleanField())
        ).filter(
            # Check if office have access to the content
            Q(
                content_types__app_label=cls._meta.app_label,
                content_types__model=cls._meta.model_name,
            ) |
            # Check if content in parent module (for view_permission)
            Q(
                parents__content_types__app_label=cls._meta.app_label,
                parents__content_types__model=cls._meta.model_name
            ),
            # Check if account is admin or office owner
            Q(all_policies=True) |
            # Check if account have policy
            Q(
                Q(policy__role__account=OuterRef('pk')) | Q(policy__account=OuterRef('pk')),
                policy__view_permission=True
            )
        ))
        return {
            'is_client_admin_or_owner': Case(
                When(is_admin=True, then=Value(True)),
                When(client__owner=F('user_id'), then=Value(True)),
                default=Value(False)
            ),
        }

    @staticmethod
    def clean_before_save_user(sender, instance, *args, **kwargs):
        instance.full_clean(exclude=('password',))


    def modify_object(self, fields_dict, *args, **kwargs):
        user = User.objects.filter(account=kwargs['uuid'],account__is_deleted=False).first()
        update_fields= {}

        if 'display_name' in fields_dict:
            if not User.objects.filter(display_name=fields_dict['display_name']).exists():
                update_fields['display_name'] = fields_dict.pop('display_name')
            else:
                return APIException("Display name already used")

        if 'email' in fields_dict:
            update_fields['email'] = fields_dict.pop('email')

        if update_fields:
            User.objects.filter(email=user.email).update(**update_fields)
        if 'permissions' in fields_dict:
            permission_uuids = [uuid for uuid, selected in fields_dict['permissions'].items() if selected]
            modules = Module.objects.filter(mapping_key__in=permission_uuids).values_list('uuid',flat=True)
            fields_dict['permissions']=modules
        if 'roles' in fields_dict:
            fields_dict['roles'] = [Role.objects.filter(name=fields_dict['roles'].lower()).first().uuid] 
        return super().modify_object(fields_dict, *args, **kwargs)
    
    def create_object(self, fields_dict, *args, **kwargs):
        # Connect the Signal to check the User
        pre_save.connect(self.clean_before_save_user, sender=User)
        # Get User
        fields_dict['user'], is_user_new = User.objects.get_or_create(email=fields_dict['email'])
        # Disconnect the Signal to check the User
        pre_save.disconnect(self.clean_before_save_user, sender=User)
        del fields_dict['email']
        # Check Display Name
        if 'display_name' in fields_dict:
            # Will only change Display Name on new users
            if is_user_new and fields_dict['display_name']:
                fields_dict['user'].display_name = fields_dict['display_name']
                duplicates = 0
                while User.objects.exclude(pk=fields_dict['user'].pk).filter(display_name=fields_dict['user'].display_name).exists():
                    duplicates =+ 1
                    fields_dict['user'].display_name = '%s %s' % (fields_dict['display_name'], duplicates)
                fields_dict['user'].save(do_not_log=True, update_fields=['display_name'])
            del fields_dict['display_name']
            # Obtener y asignar permisos usando UUIDs
        if 'permissions' in fields_dict:
            permission_uuids = [uuid for uuid, selected in fields_dict['permissions'].items() if selected]
            modules = Module.objects.filter(mapping_key__in=permission_uuids).values_list('uuid',flat=True)
            fields_dict['permissions']=modules 
        if 'roles' in fields_dict:
            fields_dict['roles'] = [Role.objects.filter(name=fields_dict['roles'].lower()).first().uuid]
        
        # If user is new
        if is_user_new:
            fields_dict['user'].create_password_token(dict(full_name=fields_dict['full_name']))
        if not 'client_id' in fields_dict:
            fields_dict['client_id'] = self.request.scope.account.client_id
        if isinstance(fields_dict['omic_id'], str) and fields_dict['omic_id'].strip().lower() in ['null', 'none', '']:
            fields_dict['omic_id'] = None
        # Creare account
        super().create_object(fields_dict, *args, **kwargs)

class ProfileView(BaseView):
    model = Account
    fields = ['uuid', 'id','user_id','omic','profile_image', 'user__display_name', 'full_name', 'user__email', 'is_active', 'is_admin', 'roles','last_login']
    extra_fields = {
        'full_name': str,
        'display_name': str,
        'is_active': bool 
    }
    list_fields_related = {
        'roles' : ['name', 'uuid'],
        'omic': ['name']
    }
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if request.scope.account:
            kwargs['uuid']= request.scope.account.uuid
        return super().dispatch(request,*args,**kwargs)
    
    def data_json(self, fields, **kwargs):
        data = super().data_json(fields, **kwargs)
        if data["last_login"]:
            formatted_date = data["last_login"].strftime("%d/%m/%y %H.%Mhs")
        else:
            formatted_date = "-"
        data["last_login"] = formatted_date
        return data

class AccountPermissionsView(BaseView):
    """ api/security/v1/permissions/ """

    model = Role
    fields = ['name','modules']
    list_fields_related = {
        'modules': ['name','mapping_key']
    }

    def data_list_json(self, query_set, fields, **kwargs):
        data = super().data_list_json(query_set, fields, **kwargs)
        data_formated = []
        for rol in data:
            info = {
                'type': rol["name"].lower(),
                'permissions': []
            }

            for permission in rol["modules"]:
                formatted_permission = {
                    "label": permission["name"].encode().decode("utf8"),
                    "value": permission["mapping_key"]
                }
                info['permissions'].append(formatted_permission)
            
            data_formated.append(info)
        
        return data_formated



@csrf_exempt
def validate_recaptcha(request):

    if request.method == 'POST':
       
        request_body = loads(request.body)
        if not (('token' in request_body) and (isinstance(request_body['token'],str))):
            return HttpResponseBadRequest()
        
        token = request_body["token"]
        url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": token,
        }
        response = requests.post(url, data=data)
        result = response.json()

        if result.get("success"):
            return JsonResponse(
                {
                'messages': [{'level': 'Success', 'title':None,'description': 'Validacion exitosa'}],
                },
                status=200
            )
        else:
            return JsonResponse(
                {
                    'messages': [{'level':'Error', 'title':None,'description':"Validación fallida"}],
                },
                status=400
            )
    else:
        return HttpResponseBadRequest()
        