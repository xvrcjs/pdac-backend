from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'administration'

urlpatterns = [
    re_path(r'^client'+regex_for_optional_uuid, ClientView.as_view(), name='auth_v1_client'),
]