# Administration API v1

La siguiente documentación describe los archivos `urls.py` y `views.py` ubicados en `administration/api/v1/`.

## 1. Archivo `urls.py`

**Ruta relativa:** `administration/api/v1/urls.py`

**Propósito:** Registrar las rutas de la versión 1 del API de administración.

### Rutas definidas

| URL | Método HTTP | Vista | Nombre de URL | Descripción |
| --- | --- | --- | --- | --- |
| `^client(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `ClientView` | `administration_v1_client` | Gestión de clientes. Con `uuid` opera sobre un cliente específico. |
| `^traffic-light-system-config(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `TrafficLightSystemTimesConfigView` | `administration_v1_client` | Configuración de semáforo de tiempos. |
| `^omic(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `OmicView` | `administration_v1_omic` | Gestión de oficinas OMIC. |
| `^omic-massive/?$` | POST | `OmicMassiveView` | `administration_v1_omic_massive` | Creación masiva de OMICs. |
| `^standards-and-protocols(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET, POST, PATCH, DELETE | `StandardsAndProtocolsView` | `administration_v1_standars_and_protocolos` | Documentos de estándares y protocolos. |
| `^standards-and-protocols/download(/(?P<uuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})/)?/?$` | GET | `StandardsAndProtocolsDownloadView` | `administration_v1_standars_and_protocolos` | Descarga de un documento. |
| `^standards-and-protocols/zip/?$` | POST | `StandardsAndProtocolsZipView` | `administration_v1_standars_and_protocolos_zip` | Descarga múltiple de documentos en un ZIP. |

## 2. Archivo `views.py`

**Ruta relativa:** `administration/api/v1/views.py`

**Propósito:** Implementar las vistas que gestionan la lógica de cada endpoint.

A continuación se resume cada vista y los decoradores de importancia.

### 2.1 `ClientView`
- Hereda de `BaseView`.
- Permite CRUD completo sobre el modelo `Client`.
- Uso de `@csrf_exempt` en `dispatch` para desactivar CSRF.
- `required_fields` se limpia cuando se pasa un `uuid`, permitiendo actualizaciones parciales.

**Ejemplo de petición de creación**
```json
POST /client/
{
  "name": "Empresa Ejemplo",
  "owner": "uuid-del-usuario",
  "image_url": "https://..."
}
```
**Respuesta**
```json
{
  "messages": [{"level": "success", "title": "Client successfully created", "description": null}],
  "data": {"uuid": "<uuid-generado>"},
  "permissions": {}
}
```

### 2.2 `TrafficLightSystemTimesConfigView`
- Mantiene la configuración global de tiempos del sistema de semáforo.
- En `dispatch` asegura que siempre exista un registro único; en GET y PATCH carga el primero.
- `modify_object` actualiza `modified_by` y `modified_at` con el usuario autenticado.
- `data_json` devuelve los nombres y fechas formateadas.

### 2.3 `OmicView`
- Maneja oficinas OMIC con paginación deshabilitada (`list_page_size = "all"`).
- Ordena por el campo `name` en listados.
- Permite CRUD completo. La vista de creación masiva se encuentra en `OmicMassiveView`.

**Ejemplo de petición masiva**
```json
POST /omic-massive/
[
  {"name": "OMIC 1", "address": "Dir 1", "email": "a@b.com", "phone": "123", "opening_hours": "8-16", "responsible": "Juan"},
  {"name": "OMIC 2", "address": "Dir 2", "email": "c@d.com", "phone": "456", "opening_hours": "9-17", "responsible": "Ana"}
]
```
**Respuesta**
```json
{"response": "Se crearon correctamente las omics"}
```

### 2.4 `StandardsAndProtocolsView`
- Gestiona documentos asociados a estándares y protocolos.
- Usa transacciones en `create_object` para guardar archivos de forma segura.
- `delete` elimina el directorio físico del archivo además del registro.
- `data_list_json` añade el tipo de archivo y fecha formateada.

### 2.5 `StandardsAndProtocolsDownloadView`
- Devuelve el archivo asociado a un registro mediante `FileResponse`.
- Verifica la existencia del archivo y establece la cabecera `Content-Disposition`.

### 2.6 `StandardsAndProtocolsZipView`
- Recibe una lista de UUIDs y genera un ZIP codificado en base64.
- Si no se encuentran archivos válidos, responde con mensaje de error JSON.

## 3. Integración con el sistema
- Todas las vistas dependen de los modelos definidos en `administration/models.py`.
- Heredan de `common.views.BaseView`, que maneja permisos y respuestas estándar.
- Actualmente no existen tests específicos (`administration/tests.py` contiene solo un placeholder).

