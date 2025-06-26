import pytest
from django.test import Client
from tickets.api.v1.views import TicketView

@pytest.mark.django_db
def test_ticket_view_get(monkeypatch):
    monkeypatch.setattr(TicketView, 'DANGEROUSLY_PUBLIC', True)
    client = Client()
    response = client.get('/api/v1/ticket/')
    assert response.status_code in [200, 204]
