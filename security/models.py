
from typing import Any, Dict, Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from common.utils import is_valid_mapping_key

from django.db import models
from common.models import  BaseModel, CaseInsensitiveCharField
from phonenumber_field.modelfields import PhoneNumberField

from settings.middlewares import get_request_at



# Create your models here.


class Module(BaseModel):
    parents = models.ManyToManyField('self', 'children', 'child', verbose_name=_('Parents Modules'),symmetrical=False,blank=True)
    name = models.CharField(_('Name'), max_length=255, unique=True)
    mapping_key = CaseInsensitiveCharField(_('Mapping Key'), unique=True, max_length=50, help_text=_('Uniqueness for this field is case-insensitive.'))

    #Settings
    content_types = models.ManyToManyField('users.ContentType', 'modules','module',verbose_name=_('Content Types'))

    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['name']
        indexes = [
            models.Index(fields=['mapping_key'], name='module_mappingkey_idx'),
        ]
        constraints = []

    def __str__(self):

        return self.name

    def validate(self):
        if not is_valid_mapping_key(self.mapping_key):
            raise ValidationError('"%s" %s' % (self.mapping_key, _('is not a valid mapping key.')))

    def clean(self):
        self.validate()

        super().clean()

    def save(self, *args, **kwargs):
        self.validate()
        if not self.name:
            self.name = ' '.join(self.mapping_key.split('_')).title()

        super().save(*args, **kwargs)

# class Policy(BaseModel):

#     name = models.CharField(_('Policy'),max_length=255)
#     module = models.ForeignKey('Module', verbose_name=_('Module'), on_delete=models.CASCADE)
    
#     #Settings
#     view_permission = models.BooleanField(_('View Permission'), default=True)
#     add_permission = models.BooleanField(_('Add Permission'), default=True)
#     delete_permission = models.BooleanField(_('Delete Permission'), default=False)
#     modify_permission = models.BooleanField(_('Modify Permission'), default=True)

#     class Meta:
#         verbose_name = _('Policy')
#         verbose_name_plural = _('Policies')
#         ordering = ['name']
#         indexes = [
#             models.Index(fields=['module'], name='policy_module_idx'),
#         ]

#     def __str__(self):

#         return self.name


class Role(BaseModel): 

    name = models.CharField(_('Name'),max_length=255)
    description = models.TextField(_('Description'), default='', blank=True)

    #Settings
    modules = models.ManyToManyField('Module', verbose_name=_('Modules'))

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        ordering = ['name']

    def __str__(self):

        return self.name
def get_profile_image_path(user, filename):

    timestamp = int(get_request_at().timestamp() * 1000)

    return 'user/%s/img/profile.%s.%s' % (user.uuid, timestamp, filename.split('.')[-1])



    






