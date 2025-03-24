from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'claims'

urlpatterns = [
   re_path(r'^create-claim-ive/?$', CreateClaimIveView.as_view(), name='create_claim_ive'),
   re_path(r'^create_claim/?$', CreateClaimView.as_view(), name='claim'),
   re_path(r'^claim'+regex_for_optional_uuid, ClaimView.as_view(), name='get_claim'),
   # Permite el control de los reclamos ive en su vista
   re_path(r'^claim-ive'+regex_for_optional_uuid, ClaimIVEView.as_view(), name='get_claim_ive'),
   # Devuelve la cantidad de reclamos HV e IVE sin tener un asignado
   re_path(r'^cant-claim-hv', CantClaimHVView.as_view(), name='get_cant_claim_hv'),

   #Descarga el reclamo comun en formato PDF
   re_path(r'^download_claim'+regex_for_optional_uuid, GenerateClaimPdf.as_view(), name='download_claim'),
   #Descarga el los archivos de un reclamo en un zip
   re_path(r'^zip_files_claim'+regex_for_optional_uuid, GenerateClaimFileZip.as_view(), name='download_claim'),
   #Permite el agregar comentarios al reclamo y tambien fijar y desfijar comentarios
   re_path(r'^comment'+regex_for_optional_uuid, CommentToClaim.as_view(), name='comment_to_claim'),
   re_path(r'^comment-ive'+regex_for_optional_uuid, CommentToClaimIVE.as_view(), name='comment_to_claim_ive'),
   #Asignar una omic o un usuario especifico a un reclamo
   re_path(r'^assign_claim'+regex_for_optional_uuid, AssignClaim.as_view(), name='assign_claim'),
   re_path(r'^assign-claim-ive'+regex_for_optional_uuid, AssignClaimIVE.as_view(), name='assign_claim'),
]