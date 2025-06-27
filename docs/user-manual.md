# Manual de Usuario de PDAC

## Portada

**Versión:** 1.0.0  
**Fecha:** 2025-06-27

---

## Tabla de Contenidos
1. [Introducción](#1-introducción)
2. [Requisitos](#2-requisitos)
3. [Instalación](#3-instalación)
4. [Configuración](#4-configuración)
5. [Uso básico](#5-uso-básico)
6. [Casos de uso avanzados](#6-casos-de-uso-avanzados)
7. [Resolución de problemas y FAQs](#7-resolución-de-problemas-y-faqs)
8. [Glosario y referencias](#8-glosario-y-referencias)

---

## 1. Introducción
PDAC es un backend modular desarrollado con **Django**, **Docker** y **Django REST Framework**. Centraliza la gestión de tickets y reclamos y ofrece un conjunto de APIs listas para desplegar en entornos productivos o de desarrollo.

## 2. Requisitos
Según el documento de instalación se recomienda:

| Recurso | Versión/Valor |
|---------|---------------|
| Docker | 27.2.0 |
| Docker compose | v2.29.7 |
| Memoria RAM | 16 GB |
| Procesadores | 4 núcleos |
| Espacio en disco | 1 TB |
| Sistema Operativo | Ubuntu 22.04 |
| Conectividad mínima | 1 Gbps |

## 3. Instalación
1. Copie `.env.template` como `.env` y edite las variables necesarias.
2. Construya las imágenes:
   ```bash
   docker compose build
   ```
3. Inicie los servicios:
   ```bash
   docker compose up
   ```
4. Ejecute migraciones y cargue los datos iniciales:
   ```bash
   docker compose exec pdac-web python manage.py migrate
   docker compose exec pdac-web python manage.py loaddata db
   docker compose exec pdac-web python manage.py create_admin
   ```

Para más detalles consulte [docs/setup.md](setup.md).

## 4. Configuración
El archivo `.env` define todas las variables del sistema. A continuación se listan las más relevantes:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DEBUG` | Modo debug de Django. | `TRUE` |
| `JWT_SECRET` | Secreto para autenticación JWT. | - |
| `SECRET_KEY` | Clave secreta de Django. | - |
| `STORAGE_ENVIRONMENT` | Destino para archivos multimedia. | `Local` |
| `LOG_FILENAME` | Ruta del log principal. | `log/debug.log` |
| `API_URL` | URL del backend. | `http://localhost:8000` |
| `FRONT_URL` | URL del frontend. | `http://localhost:3000` |
| `ADMIN_USERNAME` | Usuario admin por defecto. | `admin@admin.com` |
| `ADMIN_PASSWORD` | Contraseña admin por defecto. | `admin` |
| `DB_NAME` | Nombre de la base de datos. | `postgres` |
| `DB_USER` | Usuario de base de datos. | `postgres` |
| `DB_PASSWORD` | Contraseña de base de datos. | `postgres` |
| `DB_HOST` | Servicio de la base de datos. | `postgres` |
| `DB_PORT` | Puerto de la base. | `5432` |
| `TRUSTED_ORIGINS` | Orígenes permitidos para CORS. | `http://localhost:3000, http://localhost` |
| `SERVER_URL` | URL de acceso al backend. | `localhost,*` |
| `REDIS_ENDPOINT` | Endpoint de Redis. | `redis://redis:6379` |
| `REDIS_ENABLED` | Activar uso de Redis. | `True` |
| `SECURE_COOKIES` | Control de cookies seguras. | `False` |
| `EMAIL_SENDER_ENABLED` | Envío real de emails. | `True` |
| `EMAIL_HOST_USER` | Cuenta emisora de emails. | - |
| `EMAIL_HOST_PASSWORD` | Contraseña del email. | - |
| `DEFAULT_FROM_EMAIL` | Email por defecto si no se envía. | `prueba@prueba.com` |
| `RESET_PASSWORD_LINK` | Enlace de recuperación para usuarios. | `http://localhost:3000/create-password` |

## 5. Uso básico
Una vez configurado el entorno:

- Acceda al contenedor para ejecutar comandos de Django:
  ```bash
  docker compose exec pdac-web bash
  ```
- Cree nuevas migraciones y aplíquelas:
  ```bash
  docker compose exec pdac-web python manage.py makemigrations
  docker compose exec pdac-web python manage.py migrate
  ```
- Ejecute pruebas unitarias:
  ```bash
  docker compose exec pdac-web pytest
  ```
- Recolecte archivos estáticos cuando sea necesario:
  ```bash
  docker compose exec pdac-web python manage.py collectstatic
  ```

## 6. Casos de uso avanzados
- **APIs**: el proyecto expone endpoints REST para administración, reclamos, tickets, usuarios y seguridad. Consulte los documentos:
  - [administration-api-v1.md](administration-api-v1.md)
  - [claims-api-v1.md](claims-api-v1.md)
  - [tickets-api-v1.md](tickets-api-v1.md)
  - [users-api-v1.md](users-api-v1.md)
  - [security-api-v1.md](security-api-v1.md)
- **Modelos base**: `BaseModel` y `BaseView` simplifican la creación de nuevas apps y el manejo de permisos.
- **Tareas en segundo plano**: se ejecutan con Celery y Redis según se define en `settings/celery.py`.
- **Extensibilidad**: agregue nuevas apps heredando de `BaseModel` y exponiendo vistas de `BaseView`. Consulte [system.md](system.md) para más detalles arquitectónicos.

## 7. Resolución de problemas y FAQs
- **Las imágenes no construyen**: verifique su versión de Docker y que las variables del `.env` estén completas.
- **No puedo conectarme a la base de datos**: revise los parámetros `DB_HOST`, `DB_USER`, `DB_PASSWORD` y que el servicio `pdac-db` esté en ejecución.
- **Error de permisos**: asegúrese de haber ejecutado `create_admin` y de contar con los módulos y roles configurados correctamente.
- **Correos no enviados**: confirme las variables `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y `EMAIL_SENDER_ENABLED`.

## 8. Glosario y referencias
- **PDAC**: Plataforma de Gestión de Tickets y Reclamos.
- **Claim**: Reclamo ingresado por un usuario o ciudadano.
- **Ticket**: Incidencia o solicitud de soporte derivada de un reclamo.
- **Module/Role**: Elementos del sistema de permisos que definen qué acciones puede realizar cada usuario.

Documentación adicional en la carpeta [docs/](./) y en los archivos de referencia:
- [Project Root Overview](project-root-overview.md)
- [System](system.md)
- [Data Models](data-models.md)
- [Estrategia de pruebas](unit-test.md)
- [Resumen de tests](tests-reports/test-summary.md)

