# PDAC Backend

PDAC es un backend modular desarrollado con **Django**, **Docker** y **Django REST Framework**. Centraliza la gestión de tickets y reclamos, ofreciendo un conjunto de APIs y herramientas listas para desplegarse en entornos productivos o de desarrollo. La documentación completa se encuentra en la carpeta [docs/](./docs/).

## Tabla de contenidos
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación y configuración](#instalación-y-configuración)
- [Visión general](#visión-general)
- [Configuración avanzada](#configuración-avanzada)
- [Documentación detallada](#documentación-detallada)
- [Uso y comandos frecuentes](#uso-y-comandos-frecuentes)
- [Contribuir](#contribuir)
- [Recursos adicionales](#recursos-adicionales)

## Estructura del proyecto
```text
.
├── README.md
├── administration
│   ├── __init__.py
│   ├── admin.py
│   ├── api
│   ├── apps.py
│   ├── migrations
│   ├── models.py
│   └── tests.py
├── claims
│   ├── __init__.py
│   ├── admin.py
│   ├── api
│   ├── apps.py
│   ├── migrations
│   └── models.py
├── common
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── communication
│   ├── fixtures
│   ├── forms.py
│   ├── migrations
│   ├── models.py
│   ├── static
│   ├── templates
│   ├── utils.py
│   └── views.py
├── docker
│   ├── Dockerfile
│   └── scripts
├── docker-compose.yml
├── docs
│   ├── administration-api-v1.md
│   ├── base-model.md
│   ├── base-view.md
│   ├── claims-api-v1.md
│   ├── project-root-overview.md
│   ├── security-api-v1.md
│   ├── setup.md
│   ├── system.md
│   ├── tickets-api-v1.md
│   └── users-api-v1.md
├── log
├── manage.py
├── media
├── requirements.txt
├── security
│   ├── __init__.py
│   ├── admin.py
│   ├── api
│   ├── apps.py
│   ├── migrations
│   └── models.py
├── settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── cache.py
│   ├── celery.py
│   ├── middlewares.py
│   ├── settings.py
│   ├── storages.py
│   ├── urls.py
│   └── wsgi.py
├── tickets
│   ├── __init__.py
│   ├── admin.py
│   ├── api
│   ├── apps.py
│   ├── migrations
│   ├── models.py
│   └── tests.py
└── users
    ├── __init__.py
    ├── admin.py
    ├── api
    ├── apps.py
    ├── exceptions.py
    ├── management
    ├── migrations
    ├── models.py
    └── tests.py
```

## Instalación y configuración
1. Copia `.env.template` como `.env` y actualiza los valores secretos.
2. Construye las imágenes:
   ```bash
   docker compose build
   ```
3. Levanta los servicios:
   ```bash
   docker compose up
   ```
4. Ejecuta migraciones y crea datos iniciales:
   ```bash
   docker compose exec pdac-web python manage.py migrate
   docker compose exec pdac-web python manage.py loaddata db
   docker compose exec pdac-web python manage.py create_admin
   ```
Consulta [docs/setup.md](docs/setup.md) para más detalles.

## Visión general
Los documentos [Project Root Overview](docs/project-root-overview.md) y [System Architecture](docs/system.md) describen en profundidad la estructura del repositorio y la arquitectura general del sistema.

## Configuración avanzada
Variables de entorno clave tomadas de `.env`:
- `DEBUG`
- `JWT_SECRET`
- `SECRET_KEY`
- `STORAGE_ENVIRONMENT`
- `LOG_FILENAME`
- `API_URL`
- `FRONT_URL`
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `TRUSTED_ORIGINS`, `SERVER_URL`
- `REDIS_ENDPOINT`, `REDIS_ENABLED`
- `SECURE_COOKIES`
- `EMAIL_SENDER_ENABLED`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- `RESET_PASSWORD_LINK`

Las tareas en segundo plano se definen en [`settings/celery.py`](settings/celery.py) y se describen en [docs/system.md#tareas-en-segundo-plano](docs/system.md#tareas-en-segundo-plano). Los middlewares personalizados y la cache se configuran en [`settings/middlewares.py`](settings/middlewares.py) y [`settings/cache.py`](settings/cache.py).

## Documentación detallada
- **Modelos base y vistas base**
  - [BaseModel](docs/base-model.md)
  - [BaseView](docs/base-view.md)
- **APIs v1**
  - [Administración](docs/administration-api-v1.md)
  - [Reclamos](docs/claims-api-v1.md)
  - [Tickets](docs/tickets-api-v1.md)
  - [Usuarios](docs/users-api-v1.md)
  - [Seguridad](docs/security-api-v1.md)

## Uso y comandos frecuentes
- Desarrollo local:
  ```bash
  docker compose exec pdac-web bash
  ```
- Migraciones y pruebas:
  ```bash
  docker compose exec pdac-web python manage.py makemigrations
  docker compose exec pdac-web python manage.py migrate
  docker compose exec pdac-web python manage.py test
  ```
- Recolección de estáticos y debugging:
  ```bash
  docker compose exec pdac-web python manage.py collectstatic
  ```

## Contribuir
1. Ejecuta los tests antes de enviar cambios: `python manage.py test`.
2. Sigue el estilo de código definido en `flake8` y `isort` (si están configurados).
3. Abre una Pull Request describiendo claramente los cambios realizados.

## Recursos adicionales
- [Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery](https://docs.celeryq.dev/)