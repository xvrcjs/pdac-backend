# Estrategia de Pruebas Unitarias

Este proyecto utiliza **pytest** junto con las utilidades de prueba de Django. Cada aplicación cuenta con un paquete `tests/` que agrupa los archivos de prueba.

## Estructura Generada

```
<app>/
 └── tests/
     ├── __init__.py
     ├── test_models.py
     ├── test_views.py
     ├── test_forms.py (si aplica)
     └── test_urls.py
```

En la raíz existe un `pytest.ini` configurado para detectar todos los tests ubicados dentro de estas carpetas.

## Configuración para Tests

Se añadió `settings/settings_test.py` para aislar la configuración durante la ejecución de las pruebas. Utiliza una base de datos SQLite en memoria y desactiva configuraciones de logging y contraseñas costosas.

## Ejecución de Tests

Ejemplos de comandos:

```bash
pytest           # Ejecuta toda la batería de pruebas
pytest app/tests # Ejecuta las pruebas de una app específica
```

## Buenas Prácticas

- Nombrar los archivos de prueba con el prefijo `test_`.
- Utilizar `pytest.mark.django_db` cuando se interactúa con la base de datos.
- Mantener los tests independientes y reproducibles.
- Emplear el cliente de Django para simular peticiones a vistas.

## Requisitos Previos

- Instalación de `pytest` y `pytest-django`.
- Dependencias listadas en `requirements.txt`.
