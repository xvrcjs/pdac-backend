from django.urls import resolve
from gdeba.api.v1.views import GenerateGedoView


def test_generate_gedo_url():
    match = resolve('/api/v1/gdeba/generate-gedo/')
    assert match.func.view_class is GenerateGedoView
