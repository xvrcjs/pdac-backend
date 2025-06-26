# BaseModel

`BaseModel` es la base para todos los modelos del sistema y se implementa en
[`common/models.py`](../common/models.py). Para un repaso general de la
arquitectura consulta también [system.md](./system.md) y la distribución de
archivos en [Project Root Overview](./project-root-overview.md).

## Ubicación
```
common/models.py
```

## Propiedades principales
- `uuid`: campo `UUIDField` usado como clave primaria.
- `created_at`, `created_by`, `created_from`: datos de auditoría de creación.
- `modified_at`, `modified_by`, `modified_from`: datos de auditoría de modificación.
- `_old`: referencia interna para conservar el estado previo.
- `objects`: manager basado en `BaseQuerySet` con operaciones auditables.

## Métodos destacados
- `save(by_system=False, do_not_log=False, *args, **kwargs)`: guarda la instancia registrando auditoría.
- Propiedad `is_new`: indica si la instancia aún no fue persistida.
- Propiedad `old`: recupera la versión previa almacenada.
- `duplicate(by_system=False, do_not_log=False, *args, **kwargs)`: clona la instancia asignando nuevo UUID.
- `_get_permissions(account)`: calcula permisos en base a módulos y políticas.
- `get_permissions(account, pk=None)`: retorna los permisos efectivos.

### Tabla de métodos
| Método | Propósito | Ejemplo |
|-------|-----------|---------|
|`save(by_system=False, do_not_log=False, *args, **kwargs)`|Guarda la instancia registrando auditoría.|`obj.save()`|
|`duplicate(by_system=False, do_not_log=False, **campos)`|Crea una copia con nuevo UUID.|`obj.duplicate(cuil="20-...")`|
|`is_new`|Indica si la instancia aún no existe en base de datos.|`if obj.is_new:`|
|`old`|Devuelve la versión almacenada antes de modificar.|`print(obj.old)`|
|`get_permissions(account, pk=None)`|Obtiene permisos para un usuario.|`BaseModel.get_permissions(account)`|

## Fragmento de código
```python
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
```

## Ejemplo de uso
```python
from common.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _

class Supplier(BaseModel):
    fullname = models.CharField(_('Fullname'), max_length=255)
    cuil = models.CharField(_('Cuil'), max_length=50)
    address = models.CharField(_('Address'), max_length=255)
```
Al heredar de `BaseModel`, `Supplier` cuenta automáticamente con campos de auditoría y sistema de permisos.

## Ejemplos avanzados

Duplicar un registro existente modificando algunos campos:
```python
supplier = Supplier.objects.get(uuid="<uuid>")
supplier.duplicate(fullname="Copia de " + supplier.fullname)
```
El método `duplicate()` genera un nuevo `uuid` y guarda el registro sin afectar el original.

## Extensibilidad

`BaseModel` puede heredarse en cualquier app. Para personalizar comportamientos
se recomienda:

- Sobrescribir `save()` cuando se requiera lógica adicional antes o después del
  guardado.
- Definir managers propios extendiendo de `BaseQuerySet` para reutilizar las
  operaciones de auditoría.
- Agregar campos adicionales en los modelos hijos sin modificar la clase base.

## Documentos relacionados
- [Project Root Overview](./project-root-overview.md)
- [System](./system.md)
- [BaseView](./base-view.md)
