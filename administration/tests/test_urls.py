from django.urls import resolve
from administration.api.v1.views import ClientView


def test_client_url_resolves():
    match = resolve('/api/v1/client/')
    assert match.func.view_class is ClientView
