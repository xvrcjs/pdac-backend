from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'claims'

urlpatterns = [
   re_path(r'^ticket'+regex_for_optional_uuid, TicketView.as_view(), name='create_ticket'),
   re_path(r'^ticket/comment'+regex_for_optional_uuid, AddCommentTicketView.as_view(), name='comment_ticket'),
   re_path(r'^ticket/aditional-info'+regex_for_optional_uuid, AddAditionalInfoClaimView.as_view(), name='comment_ticket'),
   re_path(r'^ticket/assign'+regex_for_optional_uuid, AssignTicketView.as_view(), name='assign_ticket'),
]