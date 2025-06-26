import pytest
from django.test import Client
from security.api.v1.views import ModuleView

@pytest.mark.django_db
def test_module_view_get(monkeypatch):
    monkeypatch.setattr(ModuleView, 'DANGEROUSLY_PUBLIC', True)
    client = Client()
    response = client.get('/api/v1/module/')
    assert response.status_code in [200, 204]
