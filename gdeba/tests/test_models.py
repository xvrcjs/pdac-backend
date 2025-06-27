import pytest
from django.apps import apps


def test_gdeba_has_no_models():
    app_config = apps.get_app_config('gdeba')
    assert list(app_config.get_models()) == []
