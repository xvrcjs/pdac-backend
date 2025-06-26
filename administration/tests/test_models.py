import pytest
from administration.models import Client, TrafficLightSystemTimes, Omic, StandardsAndProtocols
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_client_crud():
    client = Client.objects.create(name='Test Client')
    client.refresh_from_db()
    client.name = 'Updated'
    client.save()
    assert Client.objects.get(pk=client.pk).name == 'Updated'
    client.delete()
    assert not Client.objects.filter(pk=client.pk).exists()

@pytest.mark.django_db
def test_traffic_light_system_times_crud():
    tls = TrafficLightSystemTimes.objects.create()
    tls.greenToYellow_c = 5
    tls.save()
    assert TrafficLightSystemTimes.objects.get(pk=tls.pk).greenToYellow_c == 5
    tls.delete()
    assert not TrafficLightSystemTimes.objects.filter(pk=tls.pk).exists()

@pytest.mark.django_db
def test_omic_crud():
    omic = Omic.objects.create(name='Omic', responsible='Resp', email='omic@example.com')
    omic.refresh_from_db()
    omic.phone = '123'
    omic.save()
    assert Omic.objects.get(pk=omic.pk).phone == '123'
    omic.delete()
    assert not Omic.objects.filter(pk=omic.pk).exists()

@pytest.mark.django_db
def test_standards_and_protocols_crud(tmp_path):
    file = SimpleUploadedFile('test.txt', b'content')
    sap = StandardsAndProtocols.objects.create(title='Doc', description='Desc', file=file)
    sap.refresh_from_db()
    sap.title = 'Updated'
    sap.save()
    assert StandardsAndProtocols.objects.get(pk=sap.pk).title == 'Updated'
    sap.delete()
    assert not StandardsAndProtocols.objects.filter(pk=sap.pk).exists()
