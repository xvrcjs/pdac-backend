import pytest
from users.models import User, Account

@pytest.mark.django_db
def test_user_account_crud():
    user = User.objects.create_user(email='u@example.com', password='pass')
    acc = Account.objects.create(user=user)
    user.display_name = 'Updated'
    user.save()
    assert User.objects.get(pk=user.pk).display_name == 'Updated'
    acc.delete()
    user.delete()
    assert not User.objects.filter(pk=user.pk).exists()
