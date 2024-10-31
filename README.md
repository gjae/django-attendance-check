# Introducción

Este sistema fue desarrollado para facilitar el manejo del control de asistencia del personal que labora en la empresa INPROMAR. 

# Requerimientos
- Windows / Linux / MAC
- Docker / Docker compose (recomendado para despliegue)
- Python >= 3.10
- Django >= 5.0
- PostgreSQL

# Instalación
La instalación de este sistema depende especificamente de la instalación de las dependencias ubicadas en la carpeta <roor>/repo/requirements/production.yml, más sin embargo, el uso de docker y docker composer es recomendado para mayor facilidad.
Para realizar la instalación usando docker:
primero, debe ser creadas las variables de entorno necesarias para la ejecución. Por defecto ya se incluye los archivos necesarios para dicha tarea en .envs/.local/
solo copie los archivos contenidos en la dirección .envs/.production/ 
```bash
cp -R ./.envs/.local/ ./.envs/.production/
```

## Variables necesarias
```ini
POSTGRES_HOST= HOST DE LA BD, esta puede ser un dominio o la dirección al servidor de la BD
POSTGRES_PORT=5432
POSTGRES_DB= NOMBRE DE LA BD
POSTGRES_USER= USUARIO ASIGNADO A LA BD
POSTGRES_PASSWORD= CLAVE ASIGNADA A LA BD
```

estas variables estarán ubicadas en __.envs/.production/.postgresql__, siendo las variables mas importantes de momento

ademas de éstas, existen unas variables adicionales que estan dispersadas en config/settings (base.py, production.py y test.py, cada archivo será ejecutado dependiendo del entorno en que se encuentre, por defecto base.py estará incluida en local, production y test)

### Configuración interna
```python

# Indica sí la sesión de usuario cerrará automaticamente al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Tiempo máximo sin actividad para cerrar la sesión de usuario automaticamente
SESSION_COOKIE_AGE = 600 # set just 10 seconds to test

# Actualiza la sesión de usuario cada solicitud HTTP, para evitar el efecto de la variable anterior
SESSION_SAVE_EVERY_REQUEST = True

# URL base del panel administrativo
LOGOUT_REDIRECT_URL = "/admin"
SESSION_TIMEOUT_REDIRECT  = "/admin"
```

## Ejecución del sistema

los archivos __*.yml__ ubicados en la raíz del proyecto describen un entorno de ejecución, por lo que __local.py__ describe un entorno de desarrollo y __production.yml__ describirá un entorno de producción.
Estos se apoyan de los archivos ubicados en config/settings/local.py y config/settings/local.py, en caso de ejecutar __local.yml__ este llamará a __local.py__

> **_NOTA:_** Sí desea ejecutar el sistema de forma plana directamente sobre el hardware, asegurese de crear un entorno virtual con virtualenv (o sú gestor de entornos virtuales de preferencia) e instalar el archivo de requerimiento necesario para el objetivo de la ejecuición

__EJECUTAR ENTORNO DE PRODUCCIÓN__

En la terminal de preferencia, ubiquese en la rutadel proyecto y ejecute el siguiente comando:
```bash 
$ docker compose -f production.yml build && sudo docker compose -f production up -d
```
Este comando ejecutará automaticamente todas las dependencias y servicios necesarios para que el proyecto sea ejecutado correctamente. Los parametros necesarios para personalizar aún mas la instancia en ejecución pueden ser consultadas en la documentación oficial de  
[Docker](https://docs.docker.com/) y/o [Docker Compose](https://docs.docker.com/compose/).

# Creando usuario root
El usuario root será el encargado de crear los primeros usuarios que trabajarán en el sistema ademas de tener poder absoluto sobre cada aspecto interno del sistema. Para crear un superusuario, ubiquese en la raíz del proyecto y ejecute el siguiente comando
```bash
sudo docker compose -f production.yml run --rm django python manage.py createsuperuser
```
deberá agregar un nombre de suario y una contraseña

> **_NOTA:_** Puede haber tantos superusuarios como sea requerido para organización interna


# Aspectos generales
Este proyecto fue desarrollado utilizando el framework __Django__ en sú versión 5, por lo que, para mejor documentación referente al framework, [visite su sitio web oficial](https://docs.djangoproject.com/en/5.1/)
De manera general, el sistema se divide en aplicaciones, cada aplicación representán un modulo o funcionalidad muy especifica y aislada dentro del proyecto, las aplicaciones desarrolladas se encuentran en la ruta ./src/.
