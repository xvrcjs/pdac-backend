# Users API v1

La siguiente documentación describe los archivos `urls.py` y `views.py` ubicados en `users/api/v1/`.

## 1. Archivo `urls.py`

**Ruta relativa:** `users/api/v1/urls.py`

**Propósito:** Registrar las rutas de la versión 1 del API de usuarios.

### Rutas definidas

| URL | Método HTTP | Vista | Nombre de URL | Descripción |
| --- | --- | --- | --- | --- |
| `^login/?$` | POST | `login` | - | Autenticación de un usuario y generación de tokens. |
| `^logout/?$` | GET | `logout` | - | Cierre de sesión y eliminación de cookies. |
| `^forgot-password/?$` | POST | `forgot_password` | - | Envía email con enlace para restablecer contraseña. |
| `^create-password/?$` | POST | `create_password` | - | Define una nueva contraseña a partir del token enviado por email. |
| `^account(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `AccountView` | `auth_v1_account` | Gestión de cuentas de usuario. |
| `^account(/(?P<id>\w+))?/$` | GET, POST, PATCH, DELETE | `AccountView` | `api_v1_account_edit` | Edición por identificador numérico. |
| `^profile(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, PATCH | `ProfileView` | - | Perfil del usuario autenticado. |
| `^permissions(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET | `AccountPermissionsView` | `auth_v1_permissions` | Consulta de permisos disponibles por rol. |
| `^validate-recaptcha/?$` | POST | `validate_recaptcha` | - | Valida el token de reCAPTCHA de Google. |
| `^supports(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET | `SupportView` | `api_v1_support` | Listado de usuarios con rol de soporte. |

## 2. Archivo `views.py`

**Ruta relativa:** `users/api/v1/views.py`

**Propósito:** Implementar las vistas que gestionan la lógica de cada endpoint.

A continuación se resumen las vistas y los decoradores empleados.

### 2.1 `login`
- Función que autentica al usuario usando `authenticate` y devuelve un token JWT.
- Decorador `@csrf_exempt` para permitir solicitudes sin CSRF.
- Almacena cookies con `create_cookies` y registra el último login.

### 2.2 `logout`
- Elimina las cookies de autenticación usando `delete_cookies`.
- Solo acepta método `GET` y devuelve un mensaje de cierre de sesión.

### 2.3 `forgot_password`
- Recibe un email y, si existe un usuario activo, genera un token de recuperación.
- Responde con mensajes JSON indicando éxito o error.
- Decorado con `@csrf_exempt`.

### 2.4 `create_password`
- Valida el token de recuperación y la nueva contraseña.
- Usa `validate_password` de Django para verificar reglas.
- Devuelve mensajes JSON con el resultado.

### 2.5 `AccountView`
- Hereda de `BaseView` para operaciones CRUD sobre `Account`.
- Decorador `@csrf_exempt` en `dispatch` para omitir CSRF y ajustar `required_fields`.
- Métodos `data_json` y `data_list_json` formatean fechas y roles.
- `create_object` y `modify_object` gestionan la creación de `User` relacionado y asignación de permisos.

### 2.6 `ProfileView`
- También extiende `BaseView` y muestra el perfil del usuario autenticado.
- `dispatch` captura el `uuid` desde `request.scope.account`.
- Devuelve la fecha de último acceso formateada.

### 2.7 `AccountPermissionsView`
- Lista los módulos disponibles para cada rol.
- Los permisos se devuelven agrupados por tipo y mapping key.

### 2.8 `validate_recaptcha`
- Función pública que envía el token a la API de Google reCAPTCHA.
- Decorada con `@csrf_exempt` y responde con éxito o error según la verificación.

### 2.9 `SupportView`
- Vista de solo lectura para usuarios de soporte.
- Usa `@csrf_exempt` y en `data_list_json` agrega la cantidad de tickets asignados.

## 3. Integración con el sistema
- Las vistas interactúan con los modelos `User` y `Account` de `users/models.py`.
- Se apoyan en `common.views.BaseView` para validar datos y permisos.
- También consultan `Module`, `Role` y `Ticket` para permisos y estadísticas.
- Actualmente no existen pruebas automatizadas específicas para este módulo.
