from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'claims'

urlpatterns = [
#    re_path(r'^send-claim-ive'+regex_for_optional_uuid, SendClaimIVE.as_view(), name='send_claim_ive'),
   re_path(r'^send-claim-ive/?$', SendClaimIVE),
   re_path(r'^create_claim/?$', CreateClaimView.as_view(), name='claim'),
   re_path(r'^claim'+regex_for_optional_uuid, ClaimView.as_view(), name='get_claim'),
   re_path(r'^download_claim'+regex_for_optional_uuid, GenerateClaimPdf.as_view(), name='download_claim'),
]