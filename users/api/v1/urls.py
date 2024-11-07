from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *


urlpatterns = [
    #Login/Logout
    re_path(r'^login/?$', login),
    re_path(r'^logout/?$', logout),
    re_path(r'^forgot-password/?$', forgot_password),
    re_path(r'^create-password/?$', create_password),  
      
    re_path(r'^account'+regex_for_optional_uuid, AccountView.as_view(), name='auth_v1_account'),
    re_path(r'^account(/(?P<id>\w+))?/$', AccountView.as_view(), name='api_v1_account_edit'),
    re_path(r'^profile'+regex_for_optional_uuid, ProfileView.as_view()),  
    re_path(r'^permissions'+regex_for_optional_uuid, AccountPermissionsView.as_view(), name='auth_v1_permissions'),

]