# Security API v1

La siguiente documentación describe los archivos `urls.py` y `views.py` ubicados en `security/api/v1/`.

## 1. Archivo `urls.py`

**Ruta relativa:** `security/api/v1/urls.py`

**Propósito:** Registrar las rutas de la versión 1 del API de seguridad (gestión de roles y módulos).

### Rutas definidas

| URL | Método HTTP | Vista | Nombre de URL | Descripción |
| --- | --- | --- | --- | --- |
| `^role(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `RoleView` | `auth_v1_account` | CRUD de roles. |
| `^module/?$` | GET, POST | `ModuleView` | `auth_v1_account` | Listado y creación de módulos. |

## 2. Archivo `views.py`

**Ruta relativa:** `security/api/v1/views.py`

**Propósito:** Implementar las vistas que gestionan la lógica de roles y módulos.

### 2.1 `ModuleView`
- Hereda de `BaseView` y opera sobre el modelo `Module`.
- Campos expuestos: `uuid`, `name`, `mapping_key`.
- Decorador `@csrf_exempt` en `dispatch` para omitir CSRF.
- Cuando se recibe un `uuid` se limpian los `required_fields`.

### 2.2 `RoleView`
- Hereda de `BaseView` y administra el modelo `Role`.
- Campos expuestos: `uuid`, `name`, `description`.
- No redefine `dispatch`; utiliza el de `BaseView`.

### 2.3 Ejemplo de petición y respuesta

**Listado de roles**
```http
GET /role/
```
```json
{
  "data": [
    {"uuid": "1", "name": "Admin"}
  ],
  "data_size": 1,
  "page": 1,
  "page_size": 50,
  "permissions": {}
}
```

**Detalle de módulos**
```http
GET /module/
```
```json
{
  "data": [
    {"uuid": "1", "name": "security", "mapping_key": "SECURITY"}
  ],
  "data_size": 1,
  "page": 1,
  "page_size": 50,
  "permissions": {}
}
```

## 3. Integración con el sistema
- Los modelos `Module` y `Role` están definidos en `security/models.py`.
- Todas las vistas se basan en `common.views.BaseView` para validar datos y permisos.
- Actualmente no existen serializers ni pruebas unitarias específicas para esta app.
