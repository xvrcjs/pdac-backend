from django.urls import path, re_path
from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import GenerateGedoView

app_name = 'gdeba'

urlpatterns = [
    re_path(r'^gdeba/generate-gedo'+regex_for_optional_uuid, GenerateGedoView.as_view(), name='generate_gedo'),
]