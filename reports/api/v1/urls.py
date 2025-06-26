from django.urls import path, re_path

from common.utils import regex_for_uuid_of, regex_for_optional_uuid
from .views import *

app_name = 'reports'

urlpatterns = [
   re_path(r'^reports/?$', ReportClaims.as_view(), name='report_claims'),
   re_path(r'^reports/generate/?$', ReportGenerateClaims.as_view(), name='report_generate_claims'),
   re_path(r'^reports/generate-charts/?$', ReportGenerateCharts.as_view(), name='report_generate_charts'),
   re_path(r'^reports/generate-suppliers-charts/?$', ReportGenerateSuppliersCharts.as_view(), name='report_generate_suppliers_charts'),
   re_path(r'^reports/generate-ive-charts/?$', ReportGenerateIveCharts.as_view(), name='report_generate_ive_charts'),
   re_path(r'^reports/suppliers/?$', ReportGetSuppliers.as_view(), name='report_get_suppliers'),
   re_path(r'^reports/generate-csv/?$', ReportGenerateCSV.as_view(), name='report_generate_csv'),
]