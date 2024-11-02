
from secrets import token_urlsafe
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
   PermissionsMixin, Group as BaseGroup, Permission as BasePermission
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from common.utils import  to_title
from settings.middlewares import get_request_at,  get_request_origin
from common.models import BaseQuerySet, BaseModel, CaseInsensitiveCharField
from datetime import timedelta
from jwt import encode
from common.communication.utils import send_email
from django.contrib.contenttypes.models import ContentType as BaseContentType 
from django.apps import apps  
from phonenumber_field.modelfields import PhoneNumberField
from common.communication.templates import user_create_password_message, user_reset_password_message


class ContentType(BaseContentType):

    # BaseContentType:
    # - app_label (models.CharField, max_length=100)
    # - model (models.CharField, max_length=100)

    class Meta:
        proxy = True
        verbose_name = _('Content Type')
        verbose_name_plural = _('Content Types')
        ordering = ['app_label', 'model']

    def __str__(self):
        try:
            model = apps.get_model(self.app_label, self.model)
            return model._meta.app_config.verbose_name.__str__() + " | " + model._meta.verbose_name.__str__()
        except LookupError:
            return self.app_label + " | " + self.model + " (NOT VALID)"

class UserManager(BaseUserManager):
    def get_queryset(self):

        return BaseQuerySet(self.model, using=self._db)

    def _create_user(self, email, password, by_system=False, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email.lower())

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db, by_system=by_system)

        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('by_system', False)

        if extra_fields['is_superuser'] is True and extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('by_system', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


# USERS
def get_profile_image_path(user, filename):

    timestamp = int(get_request_at().timestamp() * 1000)

    return 'user/%s/img/profile.%s.%s' % (user.uuid, timestamp, filename.split('.')[-1])

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    REQUIRED_FIELDS = ['display_name']
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'

    # Profile
    display_name = CaseInsensitiveCharField(_('Display Name'), unique=True, max_length=150, \
        help_text=_('Uniqueness for this field is case-insensitive.'),default='')
    email = models.EmailField(_('Email Address'), unique=True, max_length=255)

    # Settings
    is_active = models.BooleanField(_('Active'), default=True, \
        help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    is_staff = models.BooleanField(_('Staff Status'), default=False, \
        help_text=_('Designates whether the user can log into this admin site.'))
    last_access = models.DateTimeField(_('Last Access (UTC)'), blank=True, null=True)
    last_login = models.DateTimeField(_('Last Login (UTC)'), blank=True, null=True)
    
    # Tokens
    reset_password_token = models.CharField(_('Reset Password Token'), max_length=100, default='', blank=True)
    reset_password_token_exp = models.DateTimeField(_('Reset Password Expiration (UTC)'), blank=True, null=True)

    # AbstractBaseUser:
    # - password (models.CharField, max_length=128)
    # PermissionsMixin:
    # - is_superuser (models.BooleanField, default=False)
    # - groups (models.ManyToManyField(Group), related_name="user_set", related_query_name="user")
    # - user_permissions (models.ManyToManyField(Permission), related_name="user_set", related_query_name="user")

    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['email'], name='user_email_idx'),
            models.Index(fields=['display_name'], name='user_displayname_idx'),
            models.Index(fields=['uuid', 'email'], name='user_auth_idx'),
            models.Index(fields=[
                'reset_password_token', 'reset_password_token_exp'], name='user_resetpassword_idx')
        ]

    def __str__(self):
        return '%s' % (self.email)
    
    
    def validate(self):
        if self.display_name.lower().strip() in ['anonymous', 'system', 'admin', 'administrator', 'system admin', 'system administrator'] \
            and str(self.pk) not in [settings.ADMIN_USER_UUID, settings.SYSTEM_USER_UUID, settings.ANONYMOUS_USER_UUID]:
                raise ValidationError('"%s" %s' % (self.display_name, _('is not a valid Display Name.')))


    def clean(self):

        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def create_display_name(self, first=None, last=None, email=None):
        return to_title((email if email is not None else self.email).split('@')[0])
    
    def save(self, *args, **kwargs):
        # Check Display Name
        if not self.display_name:
            self.display_name = self.create_display_name()
            duplicates = 0
            while User.objects.exclude(pk=self.pk).filter(display_name=self.display_name).exists():
                duplicates =+ 1
                self.display_name = '%s %s' % (self.create_display_name(), duplicates)
            if 'update_fields' in kwargs and 'display_name' not in kwargs['update_fields']:
                kwargs['update_fields'] = [*kwargs['update_fields'], 'display_name']
        # Validate
        self.validate()
        # Check if staff
        if not self.is_staff:
            if self.is_superuser:
                self.is_superuser = False
                if 'update_fields' in kwargs and 'is_superuser' not in kwargs['update_fields']:
                    kwargs['update_fields'] = [*kwargs['update_fields'], 'is_superuser']
            self.groups.clear()
            self.user_permissions.all().delete()

        super().save(*args, **kwargs)
    
    # DATETIMES
    def update_last_login(self):
        self.last_login = get_request_at()
        super().save(do_not_log=True, update_fields=['last_login'])

    def update_last_access(self):
        self.last_access = get_request_at()
        super().save(do_not_log=True, update_fields=['last_access'])

   # TOKENS
    def create_token(self, aud=None):
        token_exp = get_request_at() + timedelta(hours=settings.JWT_ACCESS_EXP)
        token_data = {
            'type': 'user',
            **({'aud': aud or get_request_origin()} if settings.JWT_AUD_CHECK else {}),
            'sub': self.uuid.__str__(),
            'email': self.email,
            'display_name': self.display_name,
            'iat': get_request_at(),
            'exp': token_exp,
        }
        token = encode(token_data, settings.JWT_SECRET, algorithm="HS256")
        return [token, token_exp]
    
    # MESSAGES
    def send_email(self,fields_dict, subject, message, parameters={}, ignore_preferences=False):
        """Send an email to this user."""

        # Check if should submit
        if not (self.is_active):
            return (False, '')
        # Replace parameters
        for key in parameters:
            subject = subject.replace('{{' + key + '}}', parameters[key])
            message = message.replace('{{' + key + '}}', parameters[key])
        subject = subject.replace('{{display_name}}', self.display_name) \
                         .replace('{{first_or_display_name}}', fields_dict['full_name'] or self.display_name)
        message = message.replace('{{display_name}}', self.display_name) \
                         .replace('{{first_or_display_name}}', fields_dict['full_name'] or self.display_name)
        # Submit
        return send_email(self.email, subject, message)

    def create_reset_password_token(self, fields_dict):
        is_unique = False
        while not is_unique:
            self.reset_password_token = token_urlsafe(64)
            is_unique = not User.objects.filter(reset_password_token=self.reset_password_token).exists()   
        self.reset_password_token_exp = get_request_at() + timedelta(hours=settings.RESET_PASSWORD_EXP)
        
        if self.password:
            message = user_reset_password_message.html_message
        else:
            message = user_create_password_message.html_message
        
        link = settings.RESET_PASSWORD_LINK + '?reset_password_token=' + self.reset_password_token     

        self.send_email(
            fields_dict,
            user_create_password_message.subject,
            message,
            {'link': link, 'url_image': ''},
            True
        )
        super().save(do_not_log=True, update_fields=['reset_password_token', 'reset_password_token_exp'])   

class Account(BaseModel):

    id = models.IntegerField(unique=True, null=False, blank=False,verbose_name=_('User ID'))
    user = models.OneToOneField('User',on_delete=models.CASCADE, verbose_name=_('User'))
    
    #Details
    full_name = models.CharField(_('Full Name'), max_length=70, default='', blank=True)
    phone = PhoneNumberField(_('Phone'),blank=True)    
    profile_image = models.ImageField(_('Profile Image'), upload_to=get_profile_image_path, null=True, blank=True)
    
    #Administration
    client = models.ForeignKey('administration.Client',models.CASCADE,'accounts','account',verbose_name=_('Client'),null=True, blank=True)

    roles = models.ManyToManyField('security.Role', 'accounts', 'account', verbose_name=_('Roles'),blank=True)
    
    #Settings
    last_login = models.DateTimeField(_('Last Login'),blank=True,null=True)
    is_active = models.BooleanField(_('Is Active'),default=True)
    is_admin = models.BooleanField(_('Is Admin'),default=False)
    is_online = models.BooleanField(_('Is Online'), default=False)
    policies = models.ManyToManyField('security.Policy','accounts', 'account', verbose_name=_('Policies'),blank=True)
    is_deleted = models.BooleanField(_('Is Deleted'), default=False)


    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        ordering = ['user__display_name']
        indexes = [
            models.Index(fields=['client'], name='account_client_idx'),
            models.Index(fields=['client', 'user'], name='account_client_user_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['client', 'user'], name='account_client_user_unq'),
        ]
    def __str__(self):

        return '%s' % (self.user)


    @staticmethod
    def get_last_id():
        last_account = Account.objects.order_by('-id').first()
        if last_account:
            return last_account.id + 1
        return 1

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.get_last_id()
        super().save(*args, **kwargs)

    def get_profile_path(account, filename):
        timestamp = int(get_request_at().timestamp()*1000)

        return 'profiles/%s/img/img.%s.%s' % (account.uuid,timestamp,filename.split('.')[-1]) 
    

    