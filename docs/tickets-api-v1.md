# Tickets API v1

La siguiente documentación describe los archivos `urls.py` y `views.py` ubicados en `tickets/api/v1/`.

## 1. Archivo `urls.py`

**Ruta relativa:** `tickets/api/v1/urls.py`

**Propósito:** Registrar las rutas de la versión 1 del API de tickets.

### Rutas definidas

| URL | Método HTTP | Vista | Nombre de URL | Descripción |
| --- | --- | --- | --- | --- |
| `^ticket`+`regex_for_optional_uuid` | GET, POST, PATCH, DELETE | `TicketView` | `create_ticket` | Operaciones de listado, creación y modificación de tickets. |
| `^ticket/comment`+`regex_for_optional_uuid` | PATCH | `AddCommentTicketView` | `comment_ticket` | Agrega comentarios a un ticket existente. |
| `^ticket/aditional-info`+`regex_for_optional_uuid` | PATCH | `AddAditionalInfoClaimView` | `comment_ticket` | Registra información adicional de un ticket o de su reclamo relacionado. |
| `^ticket/assign`+`regex_for_optional_uuid` | PATCH | `AssignTicketView` | `assign_ticket` | Asigna un ticket a un usuario determinado. |

## 2. Archivo `views.py`

**Ruta relativa:** `tickets/api/v1/views.py`

**Propósito:** Implementar las vistas que gestionan la lógica de cada endpoint.

A continuación se resumen las vistas y los decoradores relevantes.

### 2.1 `TicketView`
- Hereda de `BaseView` y maneja la creación y modificación de tickets.
- Atributo `list_page_size = "all"` para obtener la lista completa sin paginación.
- Usa `@csrf_exempt` en `dispatch` y limpia `required_fields` cuando se recibe un `uuid`.
- `data_list_json` formatea `created_at` y calcula si hay nueva información en `status`.
- `data_json` ordena la actividad, incluye archivos asociados y marca la última entrada de tipo `user_add_info` como vista.
- `modify_object` permite actualizar `tasks` y adjuntar archivos subidos.

**Ejemplo de petición**
```json
POST /ticket/
{
  "claim": "#R-0000001",
  "problem_description": "Detalle del problema",
  "tasks": []
}
```
**Respuesta**
```json
{
  "data": {"uuid": "<uuid>"},
  "messages": [{"level": "success", "title": "Created"}],
  "permissions": {}
}
```

### 2.2 `AddCommentTicketView`
- Extiende `BaseView` y añade objetos al campo `activity` del ticket.
- Usa `@csrf_exempt` en `dispatch` para aceptar solicitudes sin token CSRF.
- Convierte `timestamp` a zona horaria local y lo formatea con `babel` antes de almacenarlo.
- El ID se incrementa automáticamente tomando el máximo de la lista.

### 2.3 `AddAditionalInfoClaimView`
- Similar a `AddCommentTicketView` pero con el campo extra `ticket`.
- Si el tipo es `support_add_info` también sincroniza la actividad con el reclamo (modelo `ClaimRegular` o `ClaimIVE`).
- Devuelve un mensaje JSON de confirmación.

### 2.4 `AssignTicketView`
- Permite asignar un ticket a un usuario (`Account`).
- Usa `@csrf_exempt` y limpia `required_fields` cuando se pasa el `uuid`.
- Al modificar, actualiza el `support_level` según el nivel del usuario asignado y cambia el estado a `in_progress`.

## 3. Integración con el sistema
- Las vistas interactúan con los modelos `Ticket` y `File` (`tickets/models.py`), y con `Account` (`users/models.py`).
- Para algunos tipos se consultan los modelos `ClaimRegular` y `ClaimIVE` (`claims/models.py`).
- Todas heredan de `common.views.BaseView`, que maneja validación y permisos.
- No existen tests automáticos en `tickets/tests.py` (solo contiene un placeholder).

## Gdeba

**Ruta:** `gdeba/`

**Propósito:** Integración con GEDO BA para generar documentos a partir de los reclamos.

**Archivos:** [`gdeba/api/v1/urls.py`](../gdeba/api/v1/urls.py) y [`gdeba/api/v1/views.py`](../gdeba/api/v1/views.py)
