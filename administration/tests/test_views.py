import pytest
from django.test import Client
from administration.api.v1.views import ClientView

@pytest.mark.django_db
def test_client_view_get(monkeypatch):
    monkeypatch.setattr(ClientView, 'DANGEROUSLY_PUBLIC', True)
    client = Client()
    response = client.get('/api/v1/client/')
    assert response.status_code in [200, 204]
