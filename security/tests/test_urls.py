from django.urls import resolve
from security.api.v1.views import ModuleView


def test_module_url_resolves():
    match = resolve('/api/v1/module/')
    assert match.func.view_class is ModuleView
