from django.urls import resolve
from reports.api.v1.views import ReportClaims


def test_report_claims_url():
    match = resolve('/api/v1/reports/')
    assert match.func.view_class is ReportClaims
