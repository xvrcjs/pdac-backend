from django.conf import settings
from django.core.management.base import BaseCommand
from os import getenv
from users.models import User


class Command(BaseCommand):
    help = 'Create inital System Administrator user.'

    def handle(self, *args, **kwargs):
        display_name = getenv('ADMIN_USERNAME')
        password = getenv('ADMIN_PASSWORD')
        if not (display_name and password):
            self.stdout.write('Failed to create System Administrator user. ADMIN_USERNAME and ADMIN_PASSWORD are required.')
        elif User.objects.filter(pk=settings.ADMIN_USER_UUID).exists():
            self.stdout.write('System Administrator user alredy exists.')
        else:
            try:
                User.objects.create_superuser(
                    pk=settings.ADMIN_USER_UUID,
                    display_name="System Administrator",
                    email=display_name,
                    password=password
                )
                self.stdout.write('System Administrator user successfully created.')
            except Exception as err:
                self.stdout.write('Failed to create System Administrator user. %s' % err)

