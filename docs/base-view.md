# BaseView

`BaseView` se define en `common/views.py` y provee un conjunto completo de operaciones CRUD sobre modelos que extienden `BaseModel`.

## Ruta
```
common/views.py
```

## Propósito
Expone vistas genéricas para listar, crear, duplicar, modificar y eliminar instancias. Gestiona permisos y validación de datos.

## Endpoints principales
| URL | Método | Acción |
|-----|--------|--------|
| `/api/<recurso>/` | GET | Listar objetos |
| `/api/<recurso>/` | POST | Crear nuevo objeto |
| `/api/<recurso>/<uuid>/` | GET | Obtener detalle |
| `/api/<recurso>/<uuid>/` | PATCH | Modificar objeto |
| `/api/<recurso>/<uuid>/` | DELETE | Eliminar objeto |
| `/api/<recurso>/<uuid>/` | POST | Duplicar (cuando existe `uuid` en la ruta) |

## Fragmento de definición
```python
class BaseView(View):

    # Métodos HTTP permitidos en la vista
    http_method_names = ['get', 'post', 'patch', 'delete']

    # Modelo base que esta vista va a gestionar
    model = None  # Debe ser una subclase de BaseModel

    # Configuración de claves foráneas y sus relaciones
    foreign_keys = { }  # Diccionario para manejar relaciones foráneas
                       # Ejemplo:
                       # {
                       #     'usuario': {                    # Campo en el modelo actual
                       #         'model': Usuario,           # Modelo relacionado
                       #         'filters': {                # Filtros adicionales
                       #             'activo': 'is_active'   # Campo modelo -> parámetro URL
                       #         }
                       #     }
                       # }

    # ¡PRECAUCIÓN! Permite acceso público sin autenticación
    DANGEROUSLY_PUBLIC = False    # Si es True, la vista será accesible sin autenticación
                                 # Requiere implementar verificación de permisos personalizada

    # Propiedades generales de la vista
    annotate = { }               # Anotaciones para agregar campos calculados
                                # Ejemplo: {'total_ventas': Sum('ventas__monto')}
    
    fields = [ ]                # Campos a incluir en todas las respuestas
                               # Si está vacío, incluye todos los campos
                               # Las relaciones many-to-many se ocultan por defecto en listas

    # Propiedades para modificación de datos
    update_on_conflict = False  # Si es True, actualiza en vez de error en conflictos (POST)
    unique_fields = []          # Campos únicos para identificar duplicados
                               # Requerido si update_on_conflict es True
    
    update_fields = []          # Control de campos actualizables:
                               # - True: actualiza todos los campos
                               # - Lista/Set/Tupla: solo actualiza los campos listados
                               # - Otro valor: no actualiza ningún campo
    
    required_fields = { }       # Campos requeridos adicionales
                               # Ejemplo: {'email': 'correo electrónico'}
    
    extra_fields = { }         # Campos adicionales no presentes en el modelo
                               # Ejemplo: {'password_confirm': 'str'}

    # Propiedades para vista de lista
    list_get_fields = { }      # Mapeo de parámetros URL a campos del modelo
                               # Ejemplo: {'user_id': 'usuario__id'}
    
    list_page_size = 50        # Tamaño de página para paginación
    
    list_filters = { }         # Filtros predeterminados para la lista
                               # Ejemplo: {'activo': True}
    
    list_exclude = { }         # Exclusiones predeterminadas para la lista
                               # Ejemplo: {'eliminado': True}
    list_order_by = None          # Campo por el cual ordenar la lista. Ej: '-created_at' para orden descendente
    list_search_fields = [ ]      # Lista de campos en los que se realizará la búsqueda. Ej: ['nombre', 'descripcion']
    list_search_lookup = 'icontains'  # Tipo de búsqueda a realizar. 'icontains' = case-insensitive, contiene el texto
    list_fields = [ ]             # Campos a incluir en la respuesta de la lista. Si está vacío, se usan todos
    list_fields_related = {}      # Campos a incluir de relaciones. Ej: {'usuario': ['nombre', 'email']}
    instance_filters = { }        # Filtros adicionales para obtener una instancia. Ej: {'activo': True}
    instance_exclude = { }        # Exclusiones para obtener una instancia. Ej: {'eliminado': True}
    instance_get_fields = {       # Mapeo entre parámetros URL y campos del modelo
        'pk': 'uuid'             # Ej: 'uuid' en URL se mapea a 'pk' en el modelo
    }
    instance_select_related = [ ] # Optimización: Trae relaciones en una sola consulta
                                 # Ej: ['usuario', 'categoria']
    instance_prefetch_related = [ ] # Optimización: Trae relaciones many-to-many en una sola consulta
                                   # Ej: ['tags', 'permisos']
    instance_fields = [ ]         # Campos adicionales a incluir solo en vista detalle
                                 # Ej: ['historial', 'estadisticas']

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
```

## Flujo de un POST
```text
Cliente -> BaseView.clean_body -> BaseView.create_object -> modelo.save -> respuesta JSON
```

El proceso se resume así:
1. Se lee y valida el cuerpo de la petición (`clean_body`).
2. Se conecta la señal `clean_before_save` para ejecutar `full_clean` en el modelo.
3. Se crea o duplica la instancia (`create_object` / `duplicate`).
4. Tras guardar, se desconecta la señal y se construye la respuesta.

## Diagrama simplificado
```
[Request] -> dispatch -> permisos -> clean_body -> (create/duplicate/patch/delete) -> JsonResponse
```
