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

class TrafficLightSystemTimes(BaseModel):

    greenToYellow_c = models.IntegerField(_('Green To Yellow Common'),default=0, blank=True)
    yellowToRed_c = models.IntegerField(_('Yellow to Red Common'),default=0, blank=True)
    greenToYellow_ive_hv = models.IntegerField(_('Green To Yellow IVE and HV'),default=0, blank=True)
    yellowToRed_ive_hv = models.IntegerField(_('Yellow to Red IVE and HV'),default=0, blank=True)

    class Meta:
        verbose_name = _('TrafficLightSystemTime')
        verbose_name_plural = _('TrafficLightSystemTimes')


class Omic(BaseModel):

    name = models.CharField(_('Name'),max_length=255)
    responsible = models.CharField(_('Responsible'),max_length=255)
    opening_hours = models.CharField(_('Opening Hours'),max_length=255, blank=True)
    phone = models.CharField(_('Phone'),max_length=255, blank=True,null=True)
    address = models.CharField(_('Address'),max_length=255, blank=True,null=True)
    email = models.CharField(_('Email'),max_length=255)

    class Meta:
        verbose_name = _('Omic')
        verbose_name_plural = _('Omics')
      
def site_config(request):
    return {
        'TITLE_FROM_ENVIRONMENT': getenv('TITLE_FROM_ENVIRONMENT', default='Default Title'),
        'LOGO_ALT_TEXT': getenv('LOGO_ALT_TEXT', default='Default Alt Text'),
        'LOGO_URL': getenv('LOGO_URL', default='https://default-logo-url.com'),
        'SITE_NAME': getenv('SITE_NAME', default='Default Site Name'),
        'FAVICON_URL': getenv('FAVICON_URL', default='https://default-favicon-url.com'),
    }
    