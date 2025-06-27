import pytest
from django.test import Client
from gdeba.api.v1.views import GenerateGedoView
from claims.models import ClaimRegular


@pytest.mark.django_db
def test_generate_gedo_view_not_found(monkeypatch):
    monkeypatch.setattr(GenerateGedoView, 'DANGEROUSLY_PUBLIC', True)
    def fake_get(*args, **kwargs):
        raise ClaimRegular.DoesNotExist
    monkeypatch.setattr(ClaimRegular.objects, 'get', fake_get)
    client = Client()
    response = client.post('/api/v1/gdeba/generate-gedo/123e4567-e89b-12d3-a456-426614174000/')
    assert response.status_code == 404
