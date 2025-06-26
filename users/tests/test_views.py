from django.test import Client


def test_login_view_get():
    client = Client()
    response = client.get('/api/v1/login/')
    assert response.status_code == 403
