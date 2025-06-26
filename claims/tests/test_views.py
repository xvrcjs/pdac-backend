import pytest
from django.test import Client
from claims.api.v1.views import CantClaimHVView

@pytest.mark.django_db
def test_cant_claim_hv_view(monkeypatch):
    monkeypatch.setattr(CantClaimHVView, 'DANGEROUSLY_PUBLIC', True)
    client = Client()
    response = client.get('/api/v1/cant-claim-hv')
    assert response.status_code in [200, 204]
