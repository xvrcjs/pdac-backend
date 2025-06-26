## Requerimientos

Para levantarlo se necesita:

|| Main version (dev)       |  
|:---:|:---:|
| Docker     | 27.2.0                     |
| Docker compose     | v2.29.7                    |
| Memoria RAM| 16 GB 
| Procesadores| 4 núcleos de CPU |
| Espacio en disco| 1TR |
| Sistema Operativo| Ubuntu 22.04 |
| Conectividad mínima| 1gbps|
  
## Instalación

Crear un archivo `.env` o cambiar el nombre del archivo `.env.template` que se encuentra en la raiz del proyecto. Este archivo contiene todas las variables de entornos que van a servir para la configuración del sistema, mas adelante hay una tabla con las variables y su funcionalidad.

Una vez que tenemos el archivo .env configurado con los datos correspondientes continuamos con generar las imagenes del sistema.

Para crear/descargar las imágenes requeridas:
```bash
# Docker version < 20.10
$ docker-compose build
# Docker version > 20.10
$ docker compose build
```

Para iniciar el entorno:
```bash
# Docker version < 20.10
$ docker-compose up
# Docker version > 20.10
$ docker compose up
```

### Cómo comunicarse con el contenedor

Solo envía lo que necesitas usando:
```bash
$ docker compose exec pdac-web bash
```

### Cómo generar migraciones y ejecutarlas

Para identificar los cambios generados y crear las migraciones:
```bash
$ docker compose exec pdac-web python manage.py makemigrations
```

Para aplicar las migraciones:
```bash
$ docker compose exec pdac-web python manage.py migrate
```

### Cómo crear el usuario administrador


Debe tener las siguientes variables creadas en el archivo `.env`
```env
ADMIN_USERNAME=admin@admin.com
ADMIN_PASSWORD=admin
# ejemplos, puedes cambiar los valores
```

Ahora puede ejecutar los siguientes comandos:
```bash
docker compose exec pdac-web python manage.py loaddata db
docker compose exec pdac-web python manage.py create_admin
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
`EMAIL_SENDER_ENABLED` | Variable que controla si los email salen del sistema o son generados en forma de pdf dentro del sistema | `True`|
`EMAIL_HOST_USER`| Email con el cual se envian todos los correos del sistema|
`EMAIL_HOST_PASSWORD`| Contraseña del correo | 
`DEFAULT_FROM_EMAIL`| Correo por defecto con el cual se generan los archivos pdf en caso de que el servicio de email esta deshabilitado|  `prueba@prueba.com`
`RESET_PASSWORD_LINK`|Url del frontend por el cual se solicita al sistema la restauración de la contraseña de usuario, es usado enviar la url en los emails | `http://localhost:3000/create-password`
