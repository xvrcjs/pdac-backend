from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.db.models.utils import resolve_callables
from django.forms import MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _

from typing import Any, Dict, Tuple, Union
from copy import deepcopy
from functools import reduce
from operator import or_
from uuid import uuid4

from settings.middlewares import get_request_at, get_request_by, get_request_from
from django.db.models import Exists, OuterRef, Q,Value

# FIELDS
class CaseInsensitiveCharField(models.CharField):
    ''' A case insensitive CharField '''

    LOOKUP_CONVERSIONS = {
        'exact': 'iexact',
        'contains': 'icontains',
        'startswith': 'istartswith',
        'endswith': 'iendswith',
        'regex': 'iregex',
    }

    def get_lookup(self, lookup_name):
        converted = self.LOOKUP_CONVERSIONS.get(lookup_name, lookup_name)
        return super().get_lookup(converted)

class ArrayWithChoicesFormField(MultipleChoiceField):

    def __init__(self, *args, **kwargs):
        kwargs.pop('base_field', None)
        kwargs.pop('max_length', None)
        super().__init__(*args, **kwargs)
    
# QUERYSET
class BaseQuerySet(models.QuerySet):
    # Overwritten method to store original obj (old)
    def get(self, *args, **kwargs):
        """
        Perform the query and return a single object matching the given
        keyword arguments.
        """
        obj = super().get(*args, **kwargs)
        if isinstance(obj, self.model):
            obj._old = deepcopy(obj)
        return obj

    # Overwritten method to store original obj (old)
    def first(self):
        """Return the first object of a query or None if no match is found."""
        obj = super().first()
        if isinstance(obj, self.model):
            obj._old = deepcopy(obj)
        return obj

    # Overwritten method to allow adding logging data
    def create(self, by_system=False, do_not_log=False, *args, **kwargs):
        
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(do_not_log=do_not_log, force_insert=True, using=self.db)
        return obj

    # Overwritten method to allow adding logging data
    def get_or_create(self, defaults=None, by_system=False, do_not_log=False, **kwargs):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        self._for_write = True
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            params = self._extract_model_params(defaults, **kwargs)
            # Try to create an object using passed params.
            try:
                with transaction.atomic(using=self.db):
                    params = dict(resolve_callables(params))
                    return self.create(by_system=by_system, do_not_log=do_not_log, **params), True
                   
            except IntegrityError:
                try:
                    return self.get(**kwargs), False
                except self.model.DoesNotExist:
                    pass
                raise

    # Overwritten method to allow adding logging data
    def update(self, by_system=False, do_not_log=False, **kwargs):
        """
        Update all elements in the current QuerySet, setting all the given
        fields to the appropriate values.
        """
        if not do_not_log:
            # Get log data
            at_now = get_request_at()
            if by_system:
                by_user_id = settings.SYSTEM_USER_UUID
                from_ip = '127.0.0.1'
            else:
                by_user_id = get_request_by().uuid if get_request_by() else settings.ANONYMOUS_USER_UUID
                from_ip = get_request_from()
            # Save log data
            kwargs['modified_at'] = at_now
            kwargs['modified_by_id'] = by_user_id
            kwargs['modified_from'] = from_ip

        return super().update(**kwargs)

    # Overwritten method to allow adding logging data
    def bulk_create(
        self, objs, batch_size=None, ignore_conflicts=False,
        update_conflicts=False, update_fields=None, unique_fields=None,
        by_system=False, do_not_log=False
    ):
        """
        Insert each of the instances into the database. Do *not* call
        save() on each of the instances, do not send any pre/post_save
        signals, and do not set the primary key attribute if it is an
        autoincrement field (except if features.can_return_rows_from_bulk_insert=True).
        Multi-table models are not supported.
        """
        if not do_not_log and objs:
            # Get log data
            at_now = get_request_at()
            if by_system:
                by_user_id = settings.SYSTEM_USER_UUID
                from_ip = '127.0.0.1'
            else:
                by_user_id = get_request_by().uuid if get_request_by() else settings.ANONYMOUS_USER_UUID
                from_ip = get_request_from()
            # Save log data
            for obj in objs:
                obj.created_at = at_now
                obj.created_by_id = by_user_id
                obj.created_from = from_ip
                obj.modified_at = at_now
                obj.modified_by_id = by_user_id
                obj.modified_from = from_ip

        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields, unique_fields=unique_fields
        )

    # Overwritten method to allow adding logging data
    def bulk_update(self, objs, fields, batch_size=None, by_system=False, do_not_log=False):
        """
        Update the given fields in each of the given objects in the database.
        """
        if not do_not_log and objs:
            # Get log data
            at_now = get_request_at()
            if by_system:
                by_user_id = settings.SYSTEM_USER_UUID
                from_ip = '127.0.0.1'
            else:
                by_user_id = get_request_by().uuid if get_request_by() else settings.ANONYMOUS_USER_UUID
                from_ip = get_request_from()
            # Save log data
            for obj in objs:
                obj.modified_at = at_now
                obj.modified_by_id = by_user_id
                obj.modified_from = from_ip
            # Extend to fields
            if fields:
                fields.extend([field for field in ['modified_at', 'modified_by_id', 'modified_from'] if field not in fields])

        return super().bulk_update(objs, fields, batch_size=batch_size)

    # Overwritten method to allow adding logging data
    def bulk_update_or_create(self, objs, update_fields, unique_fields, batch_size=None, by_system=False, do_not_log=False):
        """
        A combination of bulk_update and bulk_create.
        Related fields in unique_fields must be IDs, and not instances.
        """

        # Check if any obj, otherwise return empty lists
        if not objs:
            return []

        # Map objects
        get_unique_key = lambda obj: reduce(
            lambda result, field: (result + '|' if result else '') + str(getattr(obj, field)),
            unique_fields
        )
        objs_dict = {get_unique_key(obj): obj for obj in objs}
        objs_in_db_filter = reduce(
            or_,
            [Q(**{field: getattr(obj, field) for field in unique_fields}) for obj in objs]
        )
        objs_in_db_dict = {get_unique_key(obj): obj for obj in self.filter(objs_in_db_filter)}
        # Prepare objects to update
        def get_updated_obj(key):
            obj = objs_in_db_dict[key]
            for field in update_fields:
                setattr(obj, field, getattr(objs_dict[key], field))
            return obj
        objs_to_update = [get_updated_obj(key) for key in objs_in_db_dict]
        # Prepare objects to create
        objs_to_create = [objs_dict[key] for key in objs_dict if key not in objs_in_db_dict]
        with transaction.atomic(using=self.db):
            # Update
            self.bulk_update(
                objs_to_update, fields=update_fields, batch_size=batch_size,
                by_system=by_system, do_not_log=do_not_log
            )
            # Create
            objs_to_create = self.bulk_create(
                objs_to_create, batch_size=batch_size,
                by_system=by_system, do_not_log=do_not_log
            )

        return [*objs_to_update, *objs_to_create]


# MODELS
class BaseModel(models.Model):
    uuid = models.UUIDField(_('Unique identifier'), primary_key=True, default=uuid4, editable=False)

    created_at = models.DateTimeField(_('Created at (UTC)'), blank=True, null=True)
    created_by = models.ForeignKey('users.User', models.SET_NULL, \
        'created_%(app_label)s_%(class)s', verbose_name=_('Created By'), null=True)
    created_from = models.CharField(_('Created from (IP)'), max_length=50, default='', null=True, blank=True)
    modified_at = models.DateTimeField(_('Modified at (UTC)'), blank=True, null=True)
    modified_by = models.ForeignKey('users.User', models.SET_NULL, \
        'modified_%(app_label)s_%(class)s', verbose_name=_('Modified By'), null=True)
    modified_from = models.CharField(_('Modified from (IP)'), max_length=50, default='', null=True, blank=True)

    # Instance variables
    _old = None

    objects: Union[BaseQuerySet, models.Manager] = models.Manager.from_queryset(BaseQuerySet)()

    class Meta:
        abstract = True
    

    def save(self, by_system=False, do_not_log=False, *args, **kwargs):
        if not do_not_log:
            # Get log data
            at_now = get_request_at()
            if by_system:              
                by_user_id = settings.SYSTEM_USER_UUID
                from_ip = '127.0.0.1'
            else:
                by_user_id = get_request_by().uuid if get_request_by() else settings.ANONYMOUS_USER_UUID
                from_ip = get_request_from()
            # Save log data
            if not self.created_at or self.is_new:
                self.created_at = at_now
                self.created_by_id = by_user_id
                self.created_from = from_ip
            self.modified_at = at_now
            self.modified_by_id = by_user_id
            self.modified_from = from_ip
            # Check update fields
            if 'update_fields' in kwargs:
                kwargs['update_fields'].extend(['created_at', 'created_by', 'created_from', 'modified_at', 'modified_by', 'modified_from'])
        super().save(*args, **kwargs)

    @property
    def is_new(self):
        return self._state.adding == True

    @property
    def old(self):
        if self.is_new:
            self._old = None
        elif not self._old:
            self._old = self.__class__.objects.filter(pk=self.pk).first()

        return self._old

    def duplicate(self, by_system=False, do_not_log=False, *args, **kwargs):
        self.uuid = uuid4()
        self.created_at = None
        self._state.adding = True
        for key, value in list(kwargs.items()):
            if hasattr(self, key):
                setattr(self, key, value)
                del kwargs[key]
        self.save(by_system, do_not_log, *args, **kwargs)

    # PERMISSIONS
    @classmethod
    def _get_permissions(cls, account):
        from security.models import Module
        from users.models import ContentType
        def get_permission(level):
            return Exists(Module.objects.annotate(
                is_admin=Value(True if (account.client.owner == account.user_id or account.is_admin) else False)
            ).filter(
                # Check if client have access to the content
                Q(content_types=OuterRef('pk'), client=account.client) |
                # Check if content in parent module (for view_permission)
                (Q(parents__content_types=OuterRef('pk')) if level == 'view' else Q()),
                # Check if account is admin or client owner
                Q(is_admin=True) |
                # Check if account have policy
                Q(Q(policy__role__account=account) | Q(policy__account=account), **{'policy__%s_permission' % level: True})
        ))
        return ContentType.objects.filter(
            app_label=cls._meta.app_label, model=cls._meta.model_name
        ).annotate(
            view_permission=get_permission('view'),
            add_permission=get_permission('add'),
            modify_permission=get_permission('modify'),
            delete_permission=get_permission('delete')
        ).values('view_permission', 'add_permission', 'modify_permission', 'delete_permission').first()

    @classmethod
    def get_permissions(cls, account, pk=None):

        # Check user
        if not account:
            return {
                'view_permission': False,
                'add_permission': False,
                'modify_permission': False,
                'delete_permission': False
            }
        if account.user.is_superuser:
            return {
                'view_permission': True,
                'add_permission': True,
                'modify_permission': True,
                'delete_permission': True
            }
        # Get permissions
        if not hasattr(account, '_permissions'):
            account._permissions = {}
        
        permissions = account._permissions.get(f'{cls._meta.app_label}.{cls._meta.model_name}')
        if not permissions:
            if account.client:
                permissions = cls._get_permissions(account)
                account._permissions[f'{cls._meta.app_label}.{cls._meta.model_name}'] = permissions
        # Return permissions
        return permissions or {
            'view_permission': False,
            'add_permission': False,
            'modify_permission': False,
            'delete_permission': False
        }