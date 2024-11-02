from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

urlpatterns = [
    re_path(r'^role'+regex_for_optional_uuid, RoleView.as_view(), name='auth_v1_account'),
    re_path(r'^policy/?$', PolicyView.as_view(), name='auth_v1_account'),  
]