# Despliegue en Railway

Esta guía te ayudará a desplegar la aplicación Milo Store ERP en Railway.

## Requisitos previos

1. Una cuenta en [Railway](https://railway.app/)
2. Un repositorio Git con el código de la aplicación
3. Una cuenta de servicio de Google Cloud Platform con las credenciales de Google Sheets API

## Pasos para el despliegue

### 1. Crear un nuevo proyecto en Railway

1. Inicia sesión en [Railway](https://railway.app/)
2. Haz clic en "New Project"
3. Selecciona "Deploy from GitHub repo"
4. Si es la primera vez, autoriza a Railway a acceder a tu cuenta de GitHub
5. Selecciona el repositorio de Milo-Py

### 2. Configurar variables de entorno

Después de desplegar el proyecto, ve a la pestaña "Variables" y configura las siguientes variables de entorno:

- `FLASK_APP`: `app.py`
- `FLASK_ENV`: `production`
- `SECRET_KEY`: Una clave secreta segura para la aplicación
- `GOOGLE_SHEETS_SHEET_ID`: El ID de tu hoja de Google Sheets (ya configurado por defecto)
- `GOOGLE_SHEETS_SHEET_NAME`: El nombre de la hoja (por defecto "Ingreso Diario")
- `GOOGLE_SHEETS_CATALOG_GID`: El ID de la hoja del catálogo (ya configurado por defecto)
- `GOOGLE_SHEETS_CREDENTIALS`: Las credenciales de la cuenta de servicio de Google en formato JSON (ver abajo)

### 3. Configurar credenciales de Google Sheets

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Sheets
4. Crea una cuenta de servicio y descarga el archivo JSON de credenciales
5. Copia el contenido del archivo JSON y configúralo como valor de la variable de entorno `GOOGLE_SHEETS_CREDENTIALS` en Railway

### 4. Iniciar el despliegue

Una vez configuradas las variables de entorno, Railway comenzará automáticamente a desplegar la aplicación. Puedes ver el progreso en la pestaña "Deployments".

### 5. Acceder a la aplicación

Una vez completado el despliegue, haz clic en la pestaña "Settings" y luego en "Generate Domain" para obtener la URL de tu aplicación.

## Solución de problemas

- **Error al conectar con Google Sheets**: Verifica que las credenciales de la API de Google Sheets sean correctas y que la cuenta de servicio tenga permisos para editar la hoja de cálculo.
- **La aplicación no se inicia**: Revisa los logs en la pestaña "Logs" de Railway para ver los mensajes de error.
- **Problemas con las dependencias**: Asegúrate de que todas las dependencias estén correctamente especificadas en `requirements.txt`.

## Actualizar la aplicación

Para actualizar la aplicación, simplemente haz push a tu repositorio de GitHub y Railway desplegará automáticamente los cambios.
