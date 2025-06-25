from storages.backends.s3boto3 import S3StaticStorage,S3Boto3Storage
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class StaticStorage(S3StaticStorage):
    location = settings.STATIC_LOCATION
    default_acl = 'public-read'

    @classmethod
    def get_url(cls, name='', *args, **kwargs):

        return cls().url(name, *args, **kwargs)

    @classmethod
    def get_default_logo_url(cls, *args, **kwargs):

        return cls().url('logo.png', *args, **kwargs)


    @classmethod
    def get_default_avatar_url(cls, *args, **kwargs):
        local_storage = FileSystemStorage()
        file_url = local_storage.url('dummyAvatar.png')
        return file_url
        # return cls().url('dummyAvatar.png', *args, **kwargs)

class FileStorage(S3Boto3Storage):
    location = settings.MEDIA_LOCATION
    default_acl = 'private'
    custom_domain = False

    @classmethod
    def get_url(cls, name='', *args, **kwargs):

        return cls().url(name, *args, **kwargs)