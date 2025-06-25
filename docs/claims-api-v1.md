# Claims API v1

La siguiente documentación describe los archivos `urls.py` y `views.py` ubicados en `claims/api/v1/`.

## 1. Archivo `urls.py`

**Ruta relativa:** `claims/api/v1/urls.py`

**Propósito:** Registrar las rutas de la versión 1 del API de reclamos.

### Rutas definidas

| URL | Método HTTP | Vista | Nombre de URL | Descripción |
| --- | --- | --- | --- | --- |
| `^create-claim-ive/?$` | POST | `CreateClaimIveView` | `create_claim_ive` | Crea un reclamo IVE de forma anónima. |
| `^create_claim/?$` | POST | `CreateClaimView` | `claim` | Crea un reclamo común. |
| `^claim`+`regex_for_optional_uuid` | GET, POST, PATCH, DELETE | `ClaimView` | `get_claim` | Listado o gestión de un reclamo común. |
| `^claim-ive`+`regex_for_optional_uuid` | GET, POST, PATCH, DELETE | `ClaimIVEView` | `get_claim_ive` | Listado o gestión de un reclamo IVE. |
| `^cant-claim-hv` | GET | `CantClaimHVView` | `get_cant_claim_hv` | Devuelve la cantidad de reclamos HV/IVE sin asignar. |
| `^download_claim`+`regex_for_optional_uuid` | GET | `GenerateClaimPdf` | `download_claim` | Descarga un reclamo en PDF codificado en base64. |
| `^zip_files_claim`+`regex_for_optional_uuid` | GET | `GenerateClaimFileZip` | `download_claim` | Descarga los archivos de un reclamo en un ZIP. |
| `^comment`+`regex_for_optional_uuid` | PATCH | `CommentToClaim` | `comment_to_claim` | Agrega o destaca comentarios en un reclamo común. |
| `^comment-ive`+`regex_for_optional_uuid` | PATCH | `CommentToClaimIVE` | `comment_to_claim_ive` | Agrega o destaca comentarios en un reclamo IVE. |
| `^assign_claim`+`regex_for_optional_uuid` | PATCH | `AssignClaim` | `assign_claim` | Asigna un reclamo común a una OMIC o usuario. |
| `^assign-claim-ive`+`regex_for_optional_uuid` | PATCH | `AssignClaimIVE` | `assign_claim` | Asigna un reclamo IVE a una OMIC o usuario. |
| `^claim-rejected`+`regex_for_optional_uuid` | PATCH | `RejectClaim` | `claim_rejected` | Marca un reclamo común como rechazado. |

## 2. Archivo `views.py`

**Ruta relativa:** `claims/api/v1/views.py`

**Propósito:** Implementar las vistas que gestionan la lógica de cada endpoint.

A continuación se describen brevemente las vistas más relevantes y los decoradores utilizados.

### 2.1 `CreateClaimIveView`
- Hereda de `BaseView` y permite crear reclamos IVE.
- Atributo `DANGEROUSLY_PUBLIC = True` para permitir acceso sin autenticación.
- Uso de `@csrf_exempt` en `dispatch`.
- Convierte `birthdate` al formato `YYYY-MM-DD` y envía notificación.

**Ejemplo de petición**
```json
POST /create-claim-ive/
{
  "fullname": "Ana",
  "dni": "12345678",
  "birthdate": "01/01/1990",
  "email": "ana@example.com",
  "phone": "1234",
  "reasons": ["me_negaron_la_practica"]
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

### 2.2 `CreateClaimView`
- Similar a la anterior pero para reclamos comunes.
- Procesa datos de `Claimer` y `Supplier` desde JSON.
- Guarda archivos adjuntos y envía notificación.

### 2.3 `ClaimView`
- Permite listar, crear, actualizar o eliminar un reclamo común.
- En `data_json` agrega URLs de archivos, comentarios destacados y estado semáforo.

### 2.4 `ClaimIVEView`
- Versión para reclamos IVE con lógica de semáforo específica.
- No usa paginación (`list_page_size = "all"`).

### 2.5 `CommentToClaim` y `CommentToClaimIVE`
- Agregan o modifican comentarios en los reclamos.
- El ID incrementa automáticamente y se permite fijar o desfijar un comentario.

### 2.6 `GenerateClaimPdf` y `GenerateClaimFileZip`
- Generan un PDF o un ZIP codificado en base64 a partir de los archivos del reclamo.

### 2.7 `AssignClaim` y `AssignClaimIVE`
- Asignan el reclamo a una OMIC o a un usuario concreto según el tipo indicado.

### 2.8 `RejectClaim`
- Cambia el estado del reclamo a "Rechazado" y registra la actividad.

## 3. Integración con el sistema
- Las vistas utilizan los modelos `ClaimRegular`, `ClaimIVE`, `Claimer`, `Supplier` y `File` de `claims/models.py`.
- También interactúan con `Omic` y `TrafficLightSystemTimes` (`administration`), `Account` (`users`) y `Ticket` (`tickets`).
- No existen pruebas automatizadas para este módulo.
- Todo el flujo se apoya en la clase base `common.views.BaseView` para validar datos y manejar permisos.
