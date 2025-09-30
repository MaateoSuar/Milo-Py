# 🏪 Milo Store ERP - Sistema de Gestión de Ventas

Sistema web completo para la gestión de ventas de Milo Store, con sincronización automática de catálogo desde Google Sheets y exportación a Excel.

## ✨ Características Principales

- 📊 **Gestión completa de ventas** con interfaz moderna
- 🔄 **Sincronización automática** con Google Sheets para el catálogo
- 📋 **Autocompletado inteligente** de productos por ID
- 📈 **Estadísticas en tiempo real** (ventas del día, ingresos, promedio)
- 📤 **Exportación a Excel** con pandas
- 🎨 **Interfaz responsive** con Tailwind CSS
- 🔍 **Búsqueda y filtrado** de productos
- 📱 **Diseño mobile-friendly**

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd milo-store-erp
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Google Sheets / Apps Script
- Opción A (API de Sheets via gspread):
  - Configura `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_SHEETS_SHEET_ID`, `GOOGLE_SHEETS_SHEET_NAME`
  - Comparte la hoja con la cuenta de servicio.
- Opción B (Apps Script Web App - recomendado si ves errores 409/429):
  - Crea un proyecto GAS y copia `apps_script/Code.gs` y `apps_script/appsscript.json`.
  - En Propiedades del Script define `SHEET_ID`, `SHEET_NAME` y opcional `API_KEY`.
  - Publica como Aplicación web (Ejecutar como tú; Acceso: cualquiera con el enlace).
  - En la app define `GAS_URL` (URL del Web App) y opcional `GAS_API_KEY`.
  - La app usará AppsScript automáticamente si `GAS_URL` está presente.

### 4. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

Para verificar Apps Script: `GET /test_gas`. Para Sheets API: `GET /test_sheets`.

## 📁 Estructura del Proyecto

```
milo-store-erp/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración centralizada
├── requirements.txt      # Dependencias Python
├── services/            # Servicios de negocio
│   ├── catalog_service.py    # Gestión del catálogo
│   ├── sales_service.py      # Gestión de ventas
│   └── export_service.py     # Exportación a Excel
├── static/              # Archivos estáticos
│   ├── app.js          # Lógica principal de la aplicación
│   └── notifications.js # Sistema de notificaciones
├── templates/           # Plantillas HTML
│   └── index.html      # Interfaz principal
└── data/               # Archivos generados (Excel)
```

## 🔧 Configuración

### Variables de Entorno
Puedes configurar las siguientes variables en `config.py`:

- `GOOGLE_SHEETS_CONFIG`: Configuración de Google Sheets
- `APP_CONFIG`: Configuración de la aplicación Flask
- `FILE_CONFIG`: Configuración de archivos y directorios
- `LOGGING_CONFIG`: Configuración de logging

### Google Sheets
La aplicación se conecta automáticamente a tu Google Sheet usando la API pública. Asegúrate de que:

1. El archivo esté público o compartido con permisos de lectura
2. Las columnas tengan los nombres correctos: `ID` y `Nombre del Elemento`
3. Los IDs sean únicos y consistentes

## 📱 Uso de la Aplicación

### 1. **Registro de Venta**
- La fecha se establece automáticamente en "hoy"
- Escribe un ID o haz clic en el campo para ver todos los IDs disponibles
- El nombre del producto se autocompleta automáticamente
- Completa precio, unidades, forma de pago y notas

### 2. **Gestión de Ventas**
- Ver todas las ventas en la tabla
- Editar ventas existentes haciendo clic en el ícono de editar
- Eliminar ventas con confirmación
- Ver estadísticas en tiempo real

### 3. **Exportación**
- Exportar todas las ventas a Excel
- Descargar el archivo generado
- El archivo se guarda en la carpeta `data/`

## 🎯 Funcionalidades Destacadas

### **Dropdown Inteligente de IDs**
- Al hacer clic en el campo ID se despliega un dropdown con todos los productos
- Muestra ID y nombre del producto
- Búsqueda automática y filtrado
- Selección rápida con un clic

### **Auto-scroll al Último Elemento**
- Después de agregar una venta, la tabla se desplaza automáticamente
- El último elemento se resalta temporalmente
- Navegación fluida entre ventas

### **Validación en Tiempo Real**
- Verificación automática de IDs válidos
- Mensajes de ayuda contextuales
- Prevención de errores de entrada

## 🔍 API Endpoints

### Ventas
- `GET /api/ventas` - Listar todas las ventas
- `POST /api/ventas` - Agregar nueva venta
- `PUT /api/ventas/<index>` - Actualizar venta existente
- `DELETE /api/ventas/<index>` - Eliminar venta

### Catálogo
- `GET /api/catalogo` - Obtener catálogo desde Google Sheets

### Exportación
- `POST /api/exportar` - Exportar ventas a Excel
- `GET /download/excel` - Descargar archivo Excel

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python Flask
- **Frontend**: HTML5, JavaScript ES6+, Tailwind CSS
- **Base de Datos**: Almacenamiento en memoria (se reinicia al reiniciar)
- **Exportación**: Pandas + OpenPyXL
- **Catálogo**: Google Sheets API
- **UI/UX**: Font Awesome, Tailwind CSS

## 🚧 Próximas Mejoras

- [ ] **Persistencia de datos** con SQLite/PostgreSQL
- [ ] **Sistema de usuarios** y autenticación
- [ ] **Backup automático** de datos
- [ ] **Reportes avanzados** y gráficos
- [ ] **Notificaciones push** en tiempo real
- [ ] **API REST** completa para integraciones
- [ ] **Docker** para deployment
- [ ] **Tests automatizados**

## 🐛 Solución de Problemas

### Error de Conexión a Google Sheets
- Verifica que el archivo esté público
- Revisa los logs en la consola
- Confirma que el SHEET_ID y GID sean correctos

### Error de Exportación
- Asegúrate de que la carpeta `data/` tenga permisos de escritura
- Verifica que pandas y openpyxl estén instalados

### Problemas de Rendimiento
- La aplicación usa almacenamiento en memoria
- Para grandes volúmenes, considera migrar a base de datos

## 📞 Soporte

Si tienes problemas o sugerencias:

1. Revisa los logs en la consola
2. Verifica la configuración en `config.py`
3. Asegúrate de que todas las dependencias estén instaladas
4. Confirma que Google Sheets esté configurado correctamente

## 📄 Licencia

Este proyecto está desarrollado para Milo Store. Todos los derechos reservados.

---

**Desarrollado con ❤️ para Milo Store** 