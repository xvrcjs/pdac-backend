import pytest
from security.models import Module, Role

@pytest.mark.django_db
def test_module_crud():
    module = Module.objects.create(name='Module', mapping_key='module_key')
    module.refresh_from_db()
    module.name = 'Updated'
    module.save()
    assert Module.objects.get(pk=module.pk).name == 'Updated'
    module.delete()
    assert not Module.objects.filter(pk=module.pk).exists()

@pytest.mark.django_db
def test_role_crud():
    role = Role.objects.create(name='Role')
    role.description = 'desc'
    role.save()
    assert Role.objects.filter(name='Role').exists()
    role.delete()
    assert not Role.objects.filter(pk=role.pk).exists()
