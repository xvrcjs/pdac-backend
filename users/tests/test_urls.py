from django.urls import resolve
from users.api.v1.views import login


def test_login_url():
    match = resolve('/api/v1/login/')
    assert match.func is login
