# BaseView

`BaseView` se implementa en [`common/views.py`](../common/views.py) y provee un conjunto completo de operaciones CRUD sobre modelos que extienden [BaseModel](./base-model.md). Para ejemplos prácticos revisa los documentos [`administration-api-v1.md`](./administration-api-v1.md), [`claims-api-v1.md`](./claims-api-v1.md), [`tickets-api-v1.md`](./tickets-api-v1.md) y [`users-api-v1.md`](./users-api-v1.md).

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

    # Modelo que la vista gestionará
    model = None  # Subclase de BaseModel

    # Configuración opcional de relaciones
    foreign_keys = {}

    def get_permissions(self, request, *args, **kwargs):
        """Obtiene los permisos del usuario actual."""
        self.permissions = self.model.get_permissions(self.account, kwargs.get('uuid'))

    def get_list(self, request, *args, **kwargs):
        """Procesa filtros, búsqueda y paginación."""
        ...
```

## Ejemplo de petición y respuesta

### Listado
```http
GET /api/ejemplo/?page=1&page_size=2
```
```json
{
  "data": [{"uuid": "1"}, {"uuid": "2"}],
  "data_size": 10,
  "page": 1,
  "page_size": 2,
  "permissions": {}
}
```

### Detalle
```http
GET /api/ejemplo/1/
```
```json
{
  "data": {"uuid": "1", "nombre": "ejemplo"},
  "permissions": {}
}
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

## Personalización avanzada

`BaseView` puede extenderse con mixins para agregar comportamientos (paginación personalizada, autenticación extra, etc.). Es común sobrescribir métodos como `get_permissions` o `data_json` para adaptar la respuesta a cada proyecto.

## Notas sobre rendimiento

- Utiliza `instance_select_related` y `instance_prefetch_related` para optimizar consultas.
- Define `annotate` cuando debas incluir campos calculados, evitando consultas adicionales.
- Ajusta `list_page_size` de acuerdo con el volumen esperado para no saturar la memoria.

## Documentos relacionados
- [BaseModel](./base-model.md)
- [System](./system.md)
