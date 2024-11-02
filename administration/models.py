from django.db import models
from common.models import BaseModel
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from os import getenv

# from settings.storages import StaticStorage
    
def get_logo_path(office, file_name):
    pass 

class Client(BaseModel):

    #Details
    name = models.CharField(_('Name'), unique=True ,max_length=255)
    logo = models.ImageField(_('Logo'),upload_to=get_logo_path, null=True, blank=True)
    phone = PhoneNumberField(_('Phone'),blank=True)
    address = models.TextField(_(' Address'), default='', blank=True)

    #Administration
    owner = models.OneToOneField('users.Account',on_delete=models.CASCADE,verbose_name=_('Owner'),null=False, related_name="client_owner")
    modules = models.ManyToManyField('security.Module', verbose_name=_('Modules'), blank=True)
    cant_students = models.IntegerField(_('Cant Students'), default=0, blank=True)

    #Settings
    is_deleted = models.BooleanField(_('Is Deleted'), default=False)
            
    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    # @property
    # def profile_image_url(self):
    #     return self.logo.url if self.logo else StaticStorage.get_default_avatar_url()

def site_config(request):
    return {
        'TITLE_FROM_ENVIRONMENT': getenv('TITLE_FROM_ENVIRONMENT', default='Default Title'),
        'LOGO_ALT_TEXT': getenv('LOGO_ALT_TEXT', default='Default Alt Text'),
        'LOGO_URL': getenv('LOGO_URL', default='https://default-logo-url.com'),
        'SITE_NAME': getenv('SITE_NAME', default='Default Site Name'),
        'FAVICON_URL': getenv('FAVICON_URL', default='https://default-favicon-url.com'),
    }
    