from django.conf import settings
from django.core.exceptions import ValidationError, FieldError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import F, Q, RestrictedError, ProtectedError
from django.db.models.fields.files import ImageFieldFile
from django.db.models.fields.related_descriptors import ManyToManyDescriptor, ReverseManyToOneDescriptor
from django.db.models.manager import Manager
from django.db.models.signals import pre_save
from django.http import JsonResponse, HttpResponse
from django.http.multipartparser import MultiPartParser
from django.utils.dateparse import parse_datetime, parse_date, parse_time, parse_duration
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, time, timedelta
from phonenumber_field.modelfields import PhoneNumber
from json import loads
from uuid import UUID
from .utils import to_title
import logging
from common.models import BaseModel

logger = logging.getLogger(__name__)


# MESSAGES
def message_success_created(model):

    return '%s successfully created' % (to_title(model._meta.object_name))

def message_success_duplicated(model):

    return '%s successfully duplicated' % (to_title(model._meta.object_name))

def message_success_updated(model):

   return '%s successfully updated' % (to_title(model._meta.object_name))

def message_success_deleted(model):

   return '%s successfully deleted' % (to_title(model._meta.object_name))

def message_error_conflict(model, err):
    try:
        # Read errors
        errors = []
        [keys, values] = [t.split(')')[0] for t in err.__cause__.diag.message_detail.split('(')[1:]]
        keys = keys.split(', ')
        values = values.split(', ')
        for i, key in enumerate(keys):
            try:
                errors.append('%s "%s"' % (
                    model._meta.get_field(key).verbose_name,
                    model._meta.get_field(key).related_model.objects.get(pk=values[i]) if key.endswith('_id') else values[i]
                ))
            except: pass
        # Transform into one string
        error = ''
        for i, e in enumerate(errors):
            if i == 0:
                error += 'the %s' % (e)
            elif i + 1 == len(errors):
                error += ' and the %s' % (e)
            else:
                error += ', the %s' % (e)
        # Return custom error
        if error:
            return {
                'title': "The data you're trying to apply is causing a conflict",
                'description': 'There is another %s with %s.' % (to_title(model._meta.object_name), error)
            }
    except: pass
    # Return generic error
    return {
        'title': "The data you're trying to apply is causing a conflict with another %s in the database" \
            % (to_title(model._meta.object_name)),
        'description': None
    }

def message_error_protected(model, by):

   return "You can't delete this %s as it is in use by at least one %s" % \
       (to_title(model._meta.object_name), to_title(by._meta.object_name))


# BAD REQUEST RESPONSES
def reponse_bad_body():
    if settings.DEBUG:
        return JsonResponse({'messages': [{
            'level': 'debug',
            'title': 'Bad Request',
            'description': 'Unreadable body'
        }]}, status=400)

    return HttpResponse(status=400)

def reponse_required_field(field):
    if settings.DEBUG:
        return JsonResponse({'messages': [{
            'level': 'debug',
            'title': 'Bad Request',
            'description': "The field '%s' is required" % (field)
        }]}, status=400)

    return HttpResponse(status=400)

def reponse_bad_field(field, type):
    if settings.DEBUG:
        type_str = ''
        if isinstance(type, list):
            type_str = []
            for type_n in type:
                type_str.append('null' if type_n is None else getattr(type_n, '__name__', str(type_n)))
            type_str = ' or '.join(type_str)
        else:
            type_str = 'null' if type is None else getattr(type, '__name__', str(type))
        return JsonResponse({'messages': [{
            'level': 'debug',
            'title': 'Bad Request',
            'description': "The field '%s' should be an instance of %s" % (field, type_str)
        }]}, status=400)

    return HttpResponse(status=400)

def reponse_bad_data(err=None):
    if settings.DEBUG:
        return JsonResponse({'messages': [{
            'level': 'debug',
            'title': 'Bad Request',
            'description': str(err) if err else 'Unhandled error while trying to save the data'
        }]}, status=400)

    return HttpResponse(status=400)

# TEMP SIGNAL
def clean_before_save(sender, instance, *args, **kwargs):
    """ This Signal will be connect for the View model on every POST or PATCH request """

    instance.full_clean(
        exclude=(f.name for f in instance._meta.fields if f.name not in kwargs['update_fields']) \
            if kwargs.get('update_fields') else None
    )

class BaseView(View):

    http_method_names = ['get', 'post', 'patch', 'delete']
    model = None # Object model class

    foreign_keys = { } # Dict to translate URL parameters. Ex: { <object_field>: {
    #     'model': <ForeignKeyToModel>,
    #     'filters': {
    #         <ForeignKeyToModel_field>: <request_parameter>,
    #     }
    # } }

    DANGEROUSLY_PUBLIC = False # Take care with this option. Needs custom permissions check to work.

    # View Props
    annotate = { }
    fields = [ ] # List of fields to be returned by APIs. By default, m2m will be hiden on list results.

    # Modify Props
    update_on_conflict = False # If True, will not throw error on conflict (POST only)
    unique_fields = [] # Required if update_on_conflict is True
    update_fields = [] # Will update all fields if True, only fields on list if list, set or tuple, or none if anything else.
    required_fields = { } # Ex { <object_field>: str }
    extra_fields = { } # Ex { <object_field>: str }

    # List View Props
    list_get_fields = { } # Dict to translate URL parameters. Ex: { <object_field>: <request_parameter> }
    list_page_size = 50 # Default page
    list_filters = { }
    list_exclude = { }
    list_order_by = None
    list_search_fields = [ ]
    list_search_lookup = 'icontains'
    list_fields = [ ]
    list_fields_related = {}

    # Instance View Props
    instance_filters = { }
    instance_exclude = { }
    instance_get_fields = { 'pk': 'uuid' } # Dict to translate URL parameters. Ex: { <object_field>: <request_parameter> }
    instance_select_related = [ ] # Array of related fields to select
    instance_prefetch_related = [ ] # Array of related fields to prefetch
    instance_fields = [ ]

    # Variables
    view_type = None
    user = None
    account = None
    query_set = None
    object = None
    permissions = { }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):

        # Clear data
        self.view_type = None
        self.user = request.scope.user
        self.account = request.scope.account
        self.query_set = None
        self.object = None
        self.permissions = {}

        # Check if authenticated
        if not self.user and not self.DANGEROUSLY_PUBLIC:
            return HttpResponse(status=401)
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def read_body(request):
        if request.content_type == 'multipart/form-data':
            parameters, files = MultiPartParser(request.META, request, request.upload_handlers).parse()
            return {**{key: parameters[key] for key in parameters}, **{key: files[key] for key in files}}
        if request.content_type == 'application/x-www-form-urlencoded':
            return {key: request.POST.get(key) for key in request.POST}
        return loads(request.body) if request.body else {}

    def clean_body(self, request_body, force_required=False, ignore_foreign_keys=False, **kwargs):
        cleaned_body = {}
        # Read required fields
        for field in self.required_fields:
            if field in request_body:
                if request_body[field] == '' or request_body[field] is None:
                    return [None, reponse_required_field(field)]
                cleaned_body[field], is_field_valid = self.read_field(request_body[field], self.required_fields[field])
                if not is_field_valid:
                    return [None, reponse_bad_field(field, self.required_fields[field])]
            elif force_required: # Use force_required for POST and PUT
                return [None, reponse_required_field(field)]
        # Read extra fields
        for field in self.extra_fields:
            if field in request_body:
                cleaned_body[field], is_field_valid = self.read_field(request_body[field], self.extra_fields[field])
                if not is_field_valid:
                    return [None, reponse_bad_field(field, self.extra_fields[field])]
        # Add foreign keys
        if not ignore_foreign_keys: # Use ignore_foreign_keys for PATCH and DELETE
            # Set Other ForeignKeys
            for f_key in self.foreign_keys:
                filters = {}
                for kw in self.foreign_keys[f_key]['filters']:
                    if self.foreign_keys[f_key]['filters'][kw] not in kwargs:
                        # All keys in filters need to come in kwargs. If not, the View and/or the URL are not set correctly.
                        return [None, HttpResponse(status=500)]
                    filters[kw] = kwargs[self.foreign_keys[f_key]['filters'][kw]]
                # Get foreign object
                f_key_obj = self.foreign_keys[f_key]['model'].objects.filter(**filters).first()
                if not f_key_obj:
                    # Could not find the foreign key by values in kwargs.
                    return [None, HttpResponse(status=404)]
                cleaned_body[f_key] = f_key_obj
        return [cleaned_body, False]

    def get_cleaned_body(self, request, force_required=False, ignore_foreign_keys=False, **kwargs):
        # Get body
        try:
            request_body = self.read_body(request)
        except:
            return [None, reponse_bad_body()]
        # Check body
        if not isinstance(request_body, dict):
            return [None, reponse_bad_body()]
        # Clean body
        force_required = force_required or self.view_type == 'list'
        ignore_foreign_keys = ignore_foreign_keys or self.view_type == 'instance'
        return self.clean_body(request_body, force_required, ignore_foreign_keys, **kwargs)

    @staticmethod
    def read_field(value, types):
        if not isinstance(types, list):
            types = [types]
        for type in types:
            # READ VALUE
            # None
            if type is None:
                if value is None or value == '':
                    return None, True
                continue
            # Datetimes
            if type == datetime:
                if isinstance(value, str):
                    try:
                        value = parse_datetime(value)
                    except: pass
            elif type == date:
                if isinstance(value, str):
                    try:
                        value = parse_date(value)
                    except: pass
            elif type == time:
                if isinstance(value, str):
                    try:
                        value = parse_time(value)
                    except: pass
            elif type == timedelta:
                if isinstance(value, str):
                    try:
                        value = parse_duration(value)
                    except: pass
            # Integers
            elif type == int:
                if value == '':
                    return 0, True
                try:
                    return int(value), True
                except: pass
            # Floats
            elif type == float:
                if value == '':
                    return 0.0, True
                try:
                    return float(value), True
                except: pass
            # Booleans
            elif type == bool:
                if isinstance(value, bool):
                    return value, True
                if isinstance(value, str):
                    if value.lower() == 'true':
                        return True, True
                    if value.lower() == 'false':
                        return False, True
                return value, False
            # Objects
            elif type in [list, dict]:
                if isinstance(value, str):
                    try:
                        return loads(value), True
                    except: pass
            # CHECK TYPE
            if isinstance(value, type):
                return value, True
        return value, False

    def get_object(self, scope, **kwargs):
        # Create filters
        filters = self.instance_filters() if callable(self.instance_filters) else self.instance_filters.copy()
        exclude = self.instance_exclude() if callable(self.instance_exclude) else self.instance_exclude.copy()
        for kw in self.instance_get_fields:
            filters[kw] = kwargs[self.instance_get_fields[kw]]
        # Get QuerySet
        self.query_set = self.model.objects \
            .annotate(
                **(self.model.annotate() if callable(getattr(self.model, 'annotate', {})) else getattr(self.model, 'annotate', {})),
                **(self.annotate() if callable(self.annotate) else self.annotate)
            ) \
            .exclude(**exclude) \
            .filter(**filters) \
            .prefetch_related(*self.instance_prefetch_related) \
            .select_related(*self.instance_select_related)
        # Get object
        self.object = self.query_set.first()

    def create_object(self, fields_dict, *args, **kwargs):
        # Get ManyToManyFields
        m2m_fields = [field for field in fields_dict if isinstance(getattr(self.model, field), ManyToManyDescriptor)]
        # Get ReverseManyToOne
        rev_m2o_fields = [field for field in fields_dict if isinstance(getattr(self.model, field), ReverseManyToOneDescriptor)]
        # Create instance
        if self.update_on_conflict and self.unique_fields:
            self.object = self.model.objects.update_or_create(
                **{field: fields_dict[field] for field in self.unique_fields if field not in [*m2m_fields, *rev_m2o_fields]},
                defaults={field: fields_dict[field] for field in fields_dict if field not in [*m2m_fields, *rev_m2o_fields] \
                    # Field is not on unique fields list
                    and field not in self.unique_fields \
                    # Will update all fields is update_fields is True or only the fields on update_fields list
                    and (self.update_fields is True or field in self.update_fields)} \
                    # Will not update any field if update_fields is anything but True or a list (list, set and tuple)
                    if self.update_fields is True or isinstance(self.update_fields, (list, set, tuple)) else {}
            )[0]
        else:
            self.object = self.model.objects.create(**{field: fields_dict[field] for field in fields_dict \
                if field not in [*m2m_fields, *rev_m2o_fields]})
        # Set QuerySet
        self.query_set = self.model.objects \
            .filter(pk=self.object.pk) \
            .annotate(
                **(self.model.annotate() if callable(getattr(self.model, 'annotate', {})) else getattr(self.model, 'annotate', {})),
                **(self.annotate() if callable(self.annotate) else self.annotate)
            )
        # Set ManyToManyFields
        for field in m2m_fields:
            getattr(self.object, field).set(fields_dict[field])

    def modify_object(self, fields_dict, *args, **kwargs):
        modified_fields = []
        for field in fields_dict:
            # ManyToMany fields
            if isinstance(getattr(self.model, field), ManyToManyDescriptor):
                getattr(self.object, field).set(fields_dict[field])
            # ReverseManyToOne fields
            elif isinstance(getattr(self.model, field), ReverseManyToOneDescriptor):
                getattr(self.object, field).clear()
                getattr(self.object, field).model.objects.filter(pk__in=fields_dict[field]).update(
                    **{getattr(self.object, field).field.name: self.object}
                )
            # Others
            else:
                modified_fields.append(field)
                setattr(self.object, field, fields_dict[field])
        self.object.save(update_fields=modified_fields)

    # Responses
    def data_json(self, fields, **kwargs):
        related_fields = [field for field in fields if '__' in field]

        def read_field(field,field_related):
            value = getattr(self.object, field, None)
            return (
                # UUID or PhoneNumber fields
                str(value) if isinstance(value, (UUID, PhoneNumber)) else \
                # Image Files
                getattr(self.object, f'{field}_url', None) or (value.url if value else None) if isinstance(value, ImageFieldFile) else \
                # ManyToMany fields
                list(value.values(*field_related[field] if field in field_related else ['uuid'])) if isinstance(value, (ManyToManyDescriptor,Manager)) else \
                # Model and ForeignKey
                ({field: getattr(value, field) for field in field_related[field]} if field in field_related else str(value.uuid)) if (isinstance(value, (BaseModel))) else \
                # Others
                value
            )
        if fields:
            if not 'uuid' in fields:
                fields = ['uuid', *fields]
        return {
            **{field: read_field(field,self.list_fields_related) for field in (fields or (f.attname for f in self.object._meta.fields)) if field not in related_fields},
            **(self.query_set.values(*[field for field in related_fields]).first() if related_fields else {})
        }

    def data_list_json(self, query_set, fields, **kwargs):

        query = []
        for obj in query_set:
            values = {}
            for field in fields:
                value = getattr(obj, field, None)
                values[field]=(
                    # UUID or PhoneNumber fields
                    str(value) if isinstance(value, (UUID, PhoneNumber)) else \
                    # Image Files
                    getattr(obj, f'{field}_url', None) or (value.url if value else None) if isinstance(value, ImageFieldFile) else \
                    # ManyToMany fields
                    list(value.values(*self.list_fields_related[field] if field in self.list_fields_related else ['uuid'])) if isinstance(value, (ManyToManyDescriptor,Manager)) else \
                    # Model and ForeignKey
                    ({field: getattr(value, field) for field in self.list_fields_related[field]} if field in self.list_fields_related else str(value.uuid)) if (isinstance(value, (BaseModel))) else \
                    # Others
                    value)
            query.append(values)
        return query

    # - Messages
    def message_success_created(self):

        return message_success_created(self.model)

    def message_success_duplicated(self):

        return message_success_duplicated(self.model)

    def message_success_updated(self):

       return message_success_updated(self.model)

    def message_success_deleted(self):

       return message_success_deleted(self.model)

    def message_error_conflict(self, err):

        return message_error_conflict(self.model, err)

    def message_error_protected(self, by):

       return message_error_protected(self.model, by)

    # Permissions
    def get_permissions(self, request, *args, **kwargs):
        
        self.permissions = self.model.get_permissions(self.account, kwargs.get('uuid'))

    # Methods
    # - Get
    def get_list(self, request, *args, **kwargs):
        self.view_type = 'list'
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('view_permission'):
            return HttpResponse(status=403)
        # Read query in request
        page = 1
        page_size = self.list_page_size
        order_by = self.list_order_by
        query_include = Q()
        query_exclude = Q()
        for parameter in request.GET:
            # Search
            if parameter == 'search':
                if self.list_search_fields:
                    query_search = Q()
                    for search in request.GET.getlist('search'):
                        for field in self.list_search_fields:
                            query_search |= Q((f'{field}__{self.list_search_lookup}', search))
                        # If search have multiple words
                        if ' ' in search:
                            sub_query_search = Q()
                            # Each word must matches a field value
                            # Ex. ((first=Michael OR first=Scott) AND (last=Michael OR last=Scott)) OR first=Michael Scott OR last=Michael Scott
                            for sub_search in search.split():
                                sub_query_field_search = Q()
                                for field in self.list_search_fields:
                                    sub_query_field_search |= Q((f'{field}__{self.list_search_lookup}', sub_search))
                                sub_query_search &= sub_query_field_search
                            query_search |= sub_query_search
                    query_include &= query_search
            # Page
            elif parameter == 'page':
                try: page = int(request.GET['page'])
                except: pass
            # Page Size
            elif parameter == 'page_size':
                try: page_size = int(request.GET['page_size'])
                except:
                    if request.GET['page_size'] == 'all':
                        page_size = 'all'
            # Order By
            elif parameter == 'order_by':
                order_by = [F(field.lstrip('-')).desc(nulls_last=True) if field.startswith('-') \
                    else F(field) for field in request.GET.getlist('order_by')]
            # Other Filters
            else:
                sub_query = Q()
                for value in request.GET.getlist(parameter):
                    if value == 'true':
                        value = True
                    elif value == 'false':
                        value = False
                    elif value == 'null':
                        value = None
                    sub_query |= Q((parameter.lstrip('-'), value))
                if parameter.startswith('-'):
                    query_exclude &= sub_query
                else:
                    query_include &= sub_query
        # Create filters
        filters = self.list_filters() if callable(self.list_filters) else self.list_filters.copy()
        exclude = self.list_exclude() if callable(self.list_exclude) else self.list_exclude.copy()
        for kw in self.list_get_fields:
            if kw.startswith('-'):
                exclude[kw.lstrip('-')] = kwargs[self.list_get_fields[kw]]
            else:
                filters[kw] = kwargs[self.list_get_fields[kw]]
        # Get QuerySet
        try:
            self.query_set = self.model.objects.annotate(
                    **(self.model.annotate() if callable(getattr(self.model, 'annotate', {})) else getattr(self.model, 'annotate', {})),
                    **(self.annotate() if callable(self.annotate) else self.annotate)
                ) \
                .filter(query_include, **filters) \
                .exclude(query_exclude, **exclude) \
                .distinct() \
                .order_by(*(order_by or self.model._meta.ordering))
        except Exception as err:
            logger.error(str(err))
            return JsonResponse({'messages': [{'level': 'error', 'title': str(err), 'description': None}]}, status=400)
        # If requested all item
        if page_size == 'all':
            data = self.data_list_json(self.query_set, set([*self.fields, *self.list_fields]), **kwargs)
            if isinstance(data, (JsonResponse, HttpResponse)):
                return data
            try: data_size = len(data)
            except: data_size = self.query_set.count()
            # Return Data
            return JsonResponse({
                'data': data,
                'data_size': data_size,
                'page': 1,
                'page_size': data_size,
                'permissions': self.permissions
            })
        # Create Pages
        paginator = Paginator(self.query_set, page_size)
        # Return Data
        data = self.data_list_json(paginator.get_page(page).object_list, set([*self.fields, *self.list_fields]), **kwargs)
        if isinstance(data, (JsonResponse, HttpResponse)):
            return data
        return JsonResponse({
            'data': data,
            'data_size': paginator.count,
            'page': max(1, min(page, paginator.num_pages)),
            'page_size': page_size,
            'permissions': self.permissions
        })

    def get_instance(self, request, *args, **kwargs):
        self.view_type = 'instance'
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('view_permission'):
            return HttpResponse(status=403)
        # Get object
        try:
            self.get_object(request.scope, **kwargs)
        except Exception as err:
            logger.error(str(err))
            return JsonResponse({'messages': [{'level': 'error', 'title': str(err), 'description': None}]}, status=400)
        # Check Object
        if not self.object:
            return HttpResponse(status=404)
        # Return Data
        data = self.data_json(set([*self.fields, *self.instance_fields]), **kwargs)
        if isinstance(data, (JsonResponse, HttpResponse)):
            return data
        return JsonResponse({
            'data': data,
            'permissions': self.permissions,
        })

    def get(self, request, *args, **kwargs):

        if all([field in kwargs for field in self.instance_get_fields.values()]):
            return self.get_instance(request, *args, **kwargs)

        if all([field in kwargs for field in self.list_get_fields.values()]):
            return self.get_list(request, *args, **kwargs)

        return HttpResponse(status=404)

    # - Post
    def create(self, request, *args, **kwargs):
        self.view_type = 'list'
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('add_permission'):
            return HttpResponse(status=403)
        # Get cleaned body
        [cleaned_body, bad_response] = self.get_cleaned_body(request, **kwargs)
        if bad_response: return bad_response
        # Connect the Signal to check the obj
        pre_save.connect(clean_before_save, sender=self.model)
        # Create Object
        try:
            self.create_object(cleaned_body, *args, **kwargs)
            if self.annotate or getattr(self.model, 'annotate', {}): # Need to get object again, to get annotations values
                self.get_object(request.scope, uuid=self.object.pk, **kwargs)
        except IntegrityError as err:
            logger.warning(str(err))
            if 'UNIQUE constraint failed' in str(err):
                return JsonResponse({'messages': [{
                    'level': 'error', **self.message_error_conflict(err)
                }]}, status=409)
            return reponse_bad_data(err)
        except ValidationError as err:
            logger.warning(str(err))
            # return JsonResponse({'messages':[{'level': 'error', 'title': message, 'description': None} \
            #     for message in err.messages]}, status=400) if len(err.messages) else HttpResponse(status=400)
            if err.message_dict:
                response_data = {
                    'messages': [
                        {'level': 'error', 'field': field, 'description': str(error[0])}
                        for field, error in err.message_dict.items()
                    ]
                }
            else:
                response_data = {
                    'messages': [
                        {'level': 'error', 'description': message}
                        for message in err.messages
                    ]
                }

            return JsonResponse(response_data, status=400) if response_data['messages'] else HttpResponse(status=400)
        except Exception as err:
            logger.error(str(err))
            return reponse_bad_data(err)
        # Disconnect the Signal to check the obj
        pre_save.disconnect(clean_before_save, sender=self.model)
        # Return Data
        data = self.data_json(set([*self.fields, *self.instance_fields]), **kwargs)
        if isinstance(data, (JsonResponse, HttpResponse)):
            return data
        return JsonResponse({
            'messages': [{'level': 'success', 'title': self.message_success_created(), 'description': None}],
            'data': data,
            'permissions': self.permissions,
        }, status=201)

    def duplicate(self, request, *args, **kwargs):
        self.view_type = 'instance'
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('add_permission'):
            return HttpResponse(status=403)
        # Get object
        try:
            self.get_object(request.scope, **kwargs)
        except Exception as err:
            logger.error(str(err))
            return JsonResponse({'messages': [{'level': 'error', 'title': str(err), 'description': None}]}, status=400)
        # Check Object
        if not self.object:
            return HttpResponse(status=404)
        # Get cleaned body
        [cleaned_body, bad_response] = self.get_cleaned_body(request, **kwargs)
        if bad_response: return bad_response
        # Connect the Signal to check the obj
        pre_save.connect(clean_before_save, sender=self.model)
        # Duplicate Object
        try:
            self.object.duplicate(**cleaned_body)
            if 'uuid' in kwargs:
                kwargs['uuid'] = str(self.object.pk)
            if self.annotate or getattr(self.model, 'annotate', {}): # Need to get object again, to get annotations values
                self.get_object(request.scope, **kwargs)
        except IntegrityError as err:
            logger.warning(str(err))
            if 'UNIQUE constraint failed' in str(err):
                return JsonResponse({'messages': [{
                    'level': 'error', **self.message_error_conflict(err)
                }]}, status=409)
            return reponse_bad_data(err)
        except ValidationError as err:
            logger.warning(str(err))
            return JsonResponse({'messages':[{'level': 'error', 'title': message, 'description': None} \
                for message in err.messages]}, status=400) if len(err.messages) else HttpResponse(status=400)
        except Exception as err:
            logger.error(str(err))
            return reponse_bad_data(err)
        # Disconnect the Signal to check the obj
        pre_save.disconnect(clean_before_save, sender=self.model)
        # Return Data
        data = self.data_json(set([*self.fields, *self.instance_fields]), **kwargs)
        if isinstance(data, (JsonResponse, HttpResponse)):
            return data
        return JsonResponse({
            'messages': [{'level': 'success', 'title': self.message_success_duplicated(), 'description': None}],
            'data': data,
            'permissions': self.permissions,
        }, status=201)

    def post(self, request, *args, **kwargs):

        if all([field in kwargs for field in self.instance_get_fields.values()]):
            return self.duplicate(request, *args, **kwargs)

        if all([field in kwargs for field in self.list_get_fields.values()]):
            return self.create(request, *args, **kwargs)

        return HttpResponse(status=404)

    # - Patch
    def patch(self, request, *args, **kwargs):
        self.view_type = 'instance'
        # Check kwargs
        if any([field not in kwargs for field in self.instance_get_fields.values()]):
            return HttpResponse(status=404)
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('modify_permission'):
            return HttpResponse(status=403)
        # Get object
        try:
            self.get_object(request.scope, **kwargs)
        except Exception as err:
            logger.error(str(err))
            return JsonResponse({'messages': [{'level': 'error', 'title': str(err), 'description': None}]}, status=400)
        if not self.object:
            return HttpResponse(status=404)
        # Get cleaned body
        [cleaned_body, bad_response] = self.get_cleaned_body(request, **kwargs)
        if bad_response: return bad_response
        # Connect the Signal to check the obj
        pre_save.connect(clean_before_save, sender=self.model)
        # Save obj
        try:
            self.modify_object(cleaned_body, *args, **kwargs)
            if self.annotate or getattr(self.model, 'annotate', {}): # Need to get object again, as annotations values could change with the patched values
                self.get_object(request.scope, **kwargs)
        except IntegrityError as err:
            logger.warning(str(err))
            if 'UNIQUE constraint failed' in str(err):
                return JsonResponse({'messages': [{
                    'level': 'error', **self.message_error_conflict(err)
                }]}, status=409)
            return reponse_bad_data(err)
        except ValidationError as err:
            logger.warning(str(err))
            return JsonResponse({'messages':[{'level': 'error', 'title': message, 'description': None} \
                for message in err.messages]}, status=400) if len(err.messages) else HttpResponse(status=400)
        except Exception as err:
            logger.error(str(err))
            return reponse_bad_data(err)
        # Disconnect the Signal to check the obj
        pre_save.disconnect(clean_before_save, sender=self.model)
        # Return Data
        data = self.data_json(set([*self.fields, *self.instance_fields]), **kwargs)
        if isinstance(data, (JsonResponse, HttpResponse)):
            return data
        return JsonResponse({
            'messages': [{'level': 'success', 'title': self.message_success_updated(), 'description': None}],
            'data': data,
            'permissions': self.permissions,
        }, status=200)

    # - Delete
    def delete(self, request, *args, **kwargs):
        self.view_type = 'instance'
        # Check kwargs
        if any([field not in kwargs for field in self.instance_get_fields.values()]):
            return HttpResponse(status=404)
        # Get permissions
        self.get_permissions(request, *args, **kwargs)
        if not self.permissions.get('delete_permission'):
            return HttpResponse(status=403)
        # Get object
        try:
            self.get_object(request.scope, **kwargs)
        except Exception as err:
            logger.error(str(err))
            return JsonResponse({'messages': [{'level': 'error', 'title': str(err), 'description': None}]}, status=400)
        # Check Object
        if not self.object:
            return HttpResponse(status=404)
        # Delete obj
        instance_uuid = self.object.pk.__str__()
        try:
            self.object.delete()
        except (RestrictedError, ProtectedError) as err:
            logger.warning(str(err))
            try:
                return JsonResponse({'messages': [{
                    'level': 'error',
                    'title': self.message_error_protected(list(err.args[1])[0]),
                    'description': None
                }]}, status=409)
            except:
                return reponse_bad_data(err)
        except Exception as err:
            logger.error(str(err))
            return reponse_bad_data(err)
        # Return Data
        return JsonResponse({
            'messages': [{'level': 'success', 'title':  self.message_success_deleted(), 'description': None}],
            'data': { 'uuid': instance_uuid },
            'permissions': self.permissions,
        }, status=200)
    
    def generate_response(
        success: str,
        status: int,
        title: str = "Error",
        permissions: dict = {},
        data: dict = {},
        description: str = None,
    ):
        """Helper method to generate a response with the given data, status, and type of response info."""
        response = {
            "messages": [{"level": success, "title": title, "description": description}],
            "data": data,
            "permissions": permissions,
        }
        return JsonResponse(response, status=status)