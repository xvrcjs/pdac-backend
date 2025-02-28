from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'claims'

urlpatterns = [
#    re_path(r'^send-claim-ive'+regex_for_optional_uuid, SendClaimIVE.as_view(), name='send_claim_ive'),
   re_path(r'^send-claim-ive/?$', SendClaimIVE),
   re_path(r'^create_claim/?$', CreateClaimView.as_view(), name='claim'),
   re_path(r'^claim'+regex_for_optional_uuid, ClaimView.as_view(), name='get_claim'),
   #Descarga el reclamo comun en formato PDF
   re_path(r'^download_claim'+regex_for_optional_uuid, GenerateClaimPdf.as_view(), name='download_claim'),
   #Descarga el los archivos de un reclamo en un zip
   re_path(r'^zip_files_claim'+regex_for_optional_uuid, GenerateClaimFileZip.as_view(), name='download_claim'),
   #Permite el agregar comentarios al reclamo y tambien fijar y desfijar comentarios
   re_path(r'^comment'+regex_for_optional_uuid, CommentToClaim.as_view(), name='comment_to_claim'),
]