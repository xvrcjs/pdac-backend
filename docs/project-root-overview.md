# Project Root Overview

Este documento describe los archivos principales en la raíz del proyecto backend y su impacto en los flujos de desarrollo y despliegue. Se detallan las rutas, propósitos, configuraciones relevantes y ejemplos de comandos útiles.

## 1. `README.md`

**Ruta:** `README.md`

**Propósito:** Manual inicial para levantar el entorno local. Explica los prerequisitos y el uso básico de Docker.

**Secciones clave:**
- Requerimientos de Docker y hardware.
- Pasos de instalación: creación de `.env`, `docker compose build` y `docker compose up`.
- Cómo entrar al contenedor y ejecutar migraciones con `manage.py`.
- Creación del usuario administrador utilizando variables `ADMIN_USERNAME` y `ADMIN_PASSWORD` definidas en `.env`.
- Tabla de variables de entorno con descripción de cada una.

**Impacto:** Proporciona la base para que cualquier desarrollador pueda montar el proyecto localmente.

**Ejemplo de comandos:**
```bash
# Construir imágenes
$ docker compose build
# Levantar contenedores
$ docker compose up
# Ejecutar migraciones
$ docker compose exec pdac-web python manage.py migrate
```

## 2. `docker-compose.yml`

**Ruta:** `docker-compose.yml`

**Propósito:** Orquestar los servicios necesarios (base de datos, web y redis) y definir redes y volúmenes.

**Explicación:**
- **pdac-db**: servicio `mariadb:10.5` que lee variables de la base de datos desde `.env` (`DB_ROOT_PASSWORD`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). Expone el puerto 3306 y monta el volumen `pdac-data`.
- **pdac-web**: construye la imagen usando `docker/Dockerfile` con el target `django-develop`. Mapea el puerto `8000`, monta el código y la carpeta `media`. Ejecuta `/start` y carga variables del archivo `.env`. Depende de `pdac-db` y se conecta a las redes `default` y `nginx-proxy`.
- **pdac-redis**: servicio Redis que expone el puerto `6379`.
- Volúmenes: `pdac-data` (para la base) y `media` (archivos subidos).
- Red externa `nginx-proxy` para integrarse con un proxy inverso.

**Impacto:** Define cómo se levantan los servicios en desarrollo y producción. Permite reproducir el entorno de manera consistente.

**Comando típico:**
```bash
$ docker compose up
```

## 3. Carpeta `docker/`

**Ruta:** `docker/`

### Dockerfile

- **Base (`django-base`)**: parte de `python:3.8`, instala dependencias de sistema (compiladores, libs de mysql, locales, etc.), copia `requirements.txt` y las instala. Copia los scripts de inicio y el código.
- **Target `django-develop`**: ajusta variables para desarrollo, crea la carpeta `media` con permisos para el usuario `django` y ejecuta con dicho usuario.
- **Target `django-production`**: usa `start.prod` para iniciar con Daphne en producción.
- Expone el puerto 8000 y define el comando `/start`.

### Scripts
- **scripts/start**: ejecuta las migraciones, verifica datos iniciales con `loaddata`, permite cargar ejemplos si `LOAD_EXAMPLES=true`, e inicia el servidor de desarrollo `python manage.py runserver 0.0.0.0:8000`.
- **scripts/start.prod**: ejecuta migraciones y levanta `daphne settings.asgi:application`.

**Impacto:** Establecen cómo se construye y se inicia la aplicación en cada entorno. Permiten la carga automática de datos iniciales y simplifican la ejecución en contenedores.

## 4. `manage.py`

**Ruta:** `manage.py`

**Propósito:** Entrada de línea de comandos para las tareas administrativas de Django. Configura la variable `DJANGO_SETTINGS_MODULE` apuntando a `settings.settings`.

**Uso típico:**
```bash
$ docker compose exec pdac-web python manage.py migrate
$ docker compose exec pdac-web python manage.py createsuperuser
```

## 5. `requirements.txt`

**Ruta:** `requirements.txt`

**Propósito:** Lista de dependencias de Python para el proyecto. Incluye paquetes de Django, Celery, almacenamiento en S3, autenticación JWT y otros utilitarios (pandas, reportlab, etc.).

**Impacto:** Se utilizan durante la construcción de la imagen Docker para instalar todas las dependencias necesarias.

## 6. `settings/`

**Ruta:** `settings/`

Contiene todos los archivos de configuración de Django.

### Archivos principales
- `__init__.py`: importa la configuración de Celery para que esté disponible al iniciar el proyecto.
- `asgi.py` y `wsgi.py`: puntos de entrada para servidores ASGI/WSGI. Ambos establecen la variable `DJANGO_SETTINGS_MODULE`.
- `celery.py`: configura la instancia de Celery usando `REDIS_ENDPOINT` como backend y broker. Define una tarea programada (`transcript_perfom_daily`).
- `cache.py`: funciones utilitarias para limpiar la cache de Redis cuando está habilitada.
- `middlewares.py`: middleware personalizado que maneja autenticación vía token, gestión de cookies y control de caché de usuario.
- `storages.py`: define clases de almacenamiento en S3 o sistema de archivos local para archivos estáticos y media.
- `settings.py`: configuración principal de Django (instalación de apps, base de datos, JWT, logging, email, etc.).
- `urls.py`: rutas principales del proyecto, incluye los módulos de la API y la documentación Swagger.

### Variables de entorno relevantes
Las variables se cargan desde `.env` y se acceden con `os.getenv` o `getenv()` en `settings.py` y `celery.py`. Entre las más importantes se encuentran:
- `SECRET_KEY`, `DEBUG`, `ENV_STAGE`, `ENV_VERSION`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `TRUSTED_ORIGINS`, `SERVER_URL`
- `REDIS_ENDPOINT`, `REDIS_ENABLED`
- `JWT_SECRET`, `SECURE_COOKIES`, `RESET_PASSWORD_LINK`
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`

Estas variables son definidas en `.env` (ejemplo en `.env.template`). Controlan aspectos críticos como la conexión a la base de datos, el uso de Redis, los parámetros de seguridad y el envío de emails.

### Impacto
- **Desarrollo:** permite levantar un entorno completo con Docker usando las variables por defecto de `.env.template`.
- **Build:** el Dockerfile lee `requirements.txt` y la configuración de `settings/` para generar las imágenes con las dependencias y rutas correctas.
- **Producción:** el script `start.prod` usa `daphne` para servir la aplicación y las variables definen el entorno productivo (por ejemplo, `DEBUG=False`, `SECURE_COOKIES=True`).

### Ejemplos de comandos
```bash
# Ejecutar collectstatic en el contenedor
$ docker compose exec pdac-web python manage.py collectstatic
# Ejecutar pruebas (si existieran)
$ docker compose exec pdac-web python manage.py test
```

## 7. Archivo `.env.template`

Contiene todas las variables de entorno que deben copiarse a un archivo `.env` para configurar la aplicación. Cada variable controla aspectos como credenciales de base de datos, almacenamiento, credenciales de email y opciones de seguridad.

Ejemplo de creación de archivo `.env`:
```bash
$ cp .env.template .env
$ nano .env  # Editar valores secretos
```

## 8. `gdeba/`

**Ruta:** `gdeba/`

**Propósito:** Integrar PDAC con GEDO BA para generar documentos en formato electrónico.

**Archivos relevantes:** [`gdeba/api/v1/urls.py`](../gdeba/api/v1/urls.py), [`gdeba/api/v1/views.py`](../gdeba/api/v1/views.py)

---
Con esta información cualquier desarrollador puede comprender la estructura de la raíz del proyecto, cómo se configuran los servicios Docker y qué variables de entorno son necesarias para ejecutar la aplicación en los distintos entornos.

