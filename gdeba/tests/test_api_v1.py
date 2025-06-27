from gdeba.api.v1 import urls


def test_app_name():
    assert urls.app_name == 'gdeba'
