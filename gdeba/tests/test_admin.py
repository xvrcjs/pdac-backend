from django.apps import apps
from django.contrib import admin


def test_no_models_registered():
    app_config = apps.get_app_config('gdeba')
    registered = [m for m in app_config.get_models() if m in admin.site._registry]
    assert registered == []
