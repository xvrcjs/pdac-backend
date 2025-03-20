from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'administration'

urlpatterns = [
    re_path(r'^client'+regex_for_optional_uuid, ClientView.as_view(), name='administration_v1_client'),
    re_path(r'^traffic-light-system-config'+regex_for_optional_uuid, TrafficLightSystemTimesConfigView.as_view(), name='administration_v1_client'),
    re_path(r'^omic'+regex_for_optional_uuid, OmicView.as_view(), name='administration_v1_omic'),
    re_path(r'^omic-massive',OmicMassiveView, name='administration_v1_omic_massive'),
    re_path(r'^standards-and-protocols'+regex_for_optional_uuid,StandardsAndProtocolsView.as_view(), name='administration_v1_standars_and_protocolos'),
    re_path(r'^standards-and-protocols/download'+regex_for_optional_uuid,StandardsAndProtocolsDownloadView.as_view(), name='administration_v1_standars_and_protocolos'),
    re_path(r'^standards-and-protocols/zip',StandardsAndProtocolsZipView.as_view(), name='administration_v1_standars_and_protocolos_zip'),

]