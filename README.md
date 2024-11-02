<div align="center">
<p align="center">
<img alt="SowTic Logo" height="50px" src="./common/static/logo-dark.svg"/>
</a>
</p>

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://gitlab.com/sas-devp/duty/remote-assistance/backend-django/blob/develop/README.en.md)
![python](https://img.shields.io/badge/python-v3.8-blue) ![django](https://img.shields.io/badge/django-v4.2.1-yellow) ![postgres](https://img.shields.io/badge/postgres-v15.1-green)
</div>

### Tabla de contenido

- [Instalación](#instalación)
  - [Cómo comunicarse con el contenedor](#cómo-comunicarse-con-el-contenedor)
  - [Cómo hacer migraciones y migrar](#cómo-hacer-migraciones-y-migrar)
  - [Cómo crear el usuario administrador](#cómo-crear-el-usuario-administrador)
- [Configuración global](#configuración-global)
  
## Instalación

Para crear/descargar las imágenes requeridas:
```bash
$ docker-compose build
```

Para iniciar el entorno:
```bash
$ docker-compose up
```

### Cómo comunicarse con el contenedor

Solo envía lo que necesitas usando:
```bash
$ docker-compose exec web bash
```

### Cómo hacer migraciones y migrar

Para identificar los cambios generados y crear las migraciones:
```bash
$ docker-compose exec web python manage.py makemigrations
```

Para aplicar las migraciones:
```bash
$ docker-compose exec web python manage.py migrate
```


### Cómo crear el usuario administrador


Debe tener las siguientes variables creadas en el archivo .env
```env
ADMIN_USERNAME=admin@admin.com
ADMIN_PASSWORD=admin
# ejemplos, puedes cambiar los valores
```

Ahora puede ejecutar los siguientes comandos:
```bash
docker-compose exec web python manage.py loaddata db
docker-compose exec web python manage.py create_admin
```

## Configuración global

El proyecto usa algunas configuraciones definidas en el archivo `.env`.
| Nombre                  | Descripción                                                                                                                                                                                                             | Valor predeterminado        |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `DEBUG`               |  Si su aplicación genera una excepción cuando DEBUG es TRUE, Django mostrará un seguimiento detallado, que incluye una gran cantidad de metadatos sobre su entorno, como todas las configuraciones de Django definidas actualmente (de settings.py). | `TRUE`                |
|`JWT_SECRET`|Secret para la autenticacion con el sistema, es necesario generarle uno hasheado |
|`SECRET_KEY`|Secret para la validacion del sistema con terceros, necesario genearlo hasheado|
| `STORAGE_ENVIRONMENT` | Le permite configurar dónde se almacenan los archivos multimedia                                                                                                                                                           | `Local`               |
| `LOG_FILENAME`        | Indica en qué directorio se genera el archivo de registro con todos los registros                                                                                                                                         | `log/debug.log`       |
| `API_URL`             | La URL del backend, el puerto debe ser el mismo que el definido en docker-compose en caso de que se cambie, debe modificarse puerto                                                                                                                                                                                                         | http://localhost:8000 |
| `FRONT_URL`           | La URL del frontend, el puerto debe ser el mismo que el definido en docker-compose en caso de que se cambie, debe modificarse puerto                                                                                                                                                                                                        | http://localhost:3000 |
| `ADMIN_USERNAME`               |  El usuario con el cual se va a poder logear al backend del sistema, es necesario para poder ejecutar el comando de creacion de usuario | `admin@admin.com` |             
| `ADMIN_PASSWORD`               |  La contraseña del usuario del sistema | `admin` |                |
| `DB_NAME`| Nombre con el cual se va a crear la base de datos del sistema |`postgres`
`DB_USER`| Nombre con el cual se va a conectar a la base de datos |`postgres`
`DB_PASSWORD`| Contraseña para conectarse a la base de datos |`postgres`
`DB_HOST`| Nombre del servicio de docker de la base de datos |`postgres`
`DB_PORT`               |  Puerto por defecto por el cual se expone la base de datos | `5432`                |
`TRUSTED_ORIGINS` | Urls a las que se les permite solicitar datos al backend, en este caso hay que colocar la url del frontend |http://localhost:3000, http://localhost|
`SERVER_URL` | Url que controla el acceso del backend, en este caso poner la url del backend productivo|localhost,*|
`REDIS_ENDPOINT` | Url que controla por donde se accede al servicio de redis| redis://redis:6379|
`REDIS_ENABLED`| Variable de control booleana para validar la existencia de conexión con redis | `True`
`SECURE_COOKIES`|Controla la creación de cookies dentro del sistema, el valor falso permite que se cree por afuera del sistema cookies compo por ejemplo en postman| `False`
`QDRANT_KEY`|Key para conectarse al servicio externo de qdrant|
`QDRANT_ENDPOINT`|Endpoint generado en el servicio de qdrant|
`OPENAI_API_KEY`|Api-key generada en el servicio de OpenAi|
`AWS_ACCESS_KEY_ID`| Key-id obtenido al generar el servicio de AWS |
`AWS_SECRET_ACCESS_KEY`| Access-key obtenido al generar el servicio de AWS|
`AWS_DEFAULT_REGION`|Region por defecto donde se genero el servicio AWS|
`AWS_STORAGE_BUCKET_NAME`|Nombre del bucket generado en el servicio s3 de AWS|
`EMAIL_SENDER_ENABLED` | Variable que controla si los email salen del sistema o son generados en forma de pdf dentro del sistema | `True`|
`EMAIL_HOST_USER`| Email con el cual se envian todos los correos del sistema|
`EMAIL_HOST_PASSWORD`| Contraseña del correo | 
`DEFAULT_FROM_EMAIL`| Correo por defecto con el cual se generan los archivos pdf en caso de que el servicio de email esta deshabilitado|  `prueba@prueba.com`
`RESET_PASSWORD_LINK`|Url del frontend por el cual se solicita al sistema la restauración de la contraseña de usuario, es usado enviar la url en los emails | `http://localhost:3000/create-password`