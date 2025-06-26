import pytest
from claims.models import Supplier, Claimer, File, ClaimRegular, ClaimIVE
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_claim_models_crud():
    supplier = Supplier.objects.create(fullname='Supp', cuil='20-12345678-9', address='Addr', num_address='1', city='City', zip_code='1234')
    claimer = Claimer.objects.create(fullname='Person', dni='12345678', cuit='20-12345678-9', email='p@example.com', gender='other')
    file = File.objects.create(file=SimpleUploadedFile('test.txt', b'1'), file_name='test.txt')
    claim = ClaimRegular.objects.create(claimer=claimer, problem_description='desc')
    claim.suppliers.add(supplier)
    claim.files.add(file)
    claim.claim_status = 'Updated'
    claim.save()
    assert ClaimRegular.objects.get(pk=claim.pk).claim_status == 'Updated'
    claim.delete()
    assert not ClaimRegular.objects.filter(pk=claim.pk).exists()
    ive = ClaimIVE.objects.create(fullname='Test', dni='1', birthdate='2023-01-01', email='e@e.com', phone='1', social_work_or_company='None', reasons=['otra'])
    ive.phone='2'
    ive.save()
    assert ClaimIVE.objects.get(pk=ive.pk).phone == '2'
    ive.delete()
    assert not ClaimIVE.objects.filter(pk=ive.pk).exists()
