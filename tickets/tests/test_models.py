import pytest
from tickets.models import Ticket, File
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_ticket_crud():
    ticket = Ticket.objects.create(problem_description='desc')
    ticket.refresh_from_db()
    ticket.problem_description = 'new'
    ticket.save()
    assert Ticket.objects.get(pk=ticket.pk).problem_description == 'new'
    file = File.objects.create(file=SimpleUploadedFile('f.txt', b'1'), file_name='f.txt', ticket=ticket)
    assert file.ticket == ticket
    file.delete()
    ticket.delete()
    assert not Ticket.objects.filter(pk=ticket.pk).exists()
