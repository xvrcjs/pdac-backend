from django.urls import resolve
from tickets.api.v1.views import TicketView


def test_ticket_url_resolves():
    match = resolve('/api/v1/ticket/')
    assert match.func.view_class is TicketView
