from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'claims'

urlpatterns = [
#    re_path(r'^send-claim-ive'+regex_for_optional_uuid, SendClaimIVE.as_view(), name='send_claim_ive'),
   re_path(r'^send-claim-ive/?$', SendClaimIVE),
]