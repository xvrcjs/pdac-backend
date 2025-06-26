import pytest
from django.test import Client
from reports.api.v1.views import ReportClaims

@pytest.mark.django_db
def test_report_claims_view(monkeypatch):
    monkeypatch.setattr(ReportClaims, 'DANGEROUSLY_PUBLIC', True)
    client = Client()
    response = client.get('/api/v1/reports/')
    assert response.status_code in [200, 204]
