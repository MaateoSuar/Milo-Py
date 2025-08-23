# 🚀 Uso Rápido - Milo Store ERP

## ⚡ Inicio Inmediato

### Opción 1: Script Automático (Recomendado)
```bash
py start.py
```
- ✅ Verifica dependencias automáticamente
- ✅ Abre el navegador automáticamente
- ✅ Inicia la aplicación Flask

### Opción 2: Manual
```bash
py app.py
```
Luego abre: http://localhost:5000

## 🎯 Funcionalidades Principales

### 1. **Dropdown de IDs Inteligente**
- **Haz clic** en el campo "ID de Producto"
- Se despliegan **todos los IDs** del catálogo
- **Selecciona** con un clic
- El nombre se **autocompleta** automáticamente

### 2. **Fecha Automática**
- La fecha se establece **automáticamente** en "hoy"
- **No necesitas** cambiarla manualmente

### 3. **Auto-scroll al Último Elemento**
- Al agregar una venta, la tabla se **desplaza automáticamente**
- El último elemento se **resalta** temporalmente
- **Navegación fluida** entre ventas

## 📱 Interfaz de Usuario

### **Panel Izquierdo - Estadísticas**
- 📊 Ventas del día
- 💰 Ingresos totales
- 📈 Promedio por venta

### **Formulario Principal**
- 📅 Fecha (automática)
- 🆔 ID de Producto (con dropdown)
- 🏷️ Nombre (autocompletado)
- 💵 Precio
- 📦 Unidades
- 💳 Forma de Pago
- 📝 Notas

### **Tabla de Ventas**
- 📋 Lista de todas las ventas
- ✏️ Botón editar (ícono azul)
- 🗑️ Botón eliminar (ícono rojo)
- 📊 Total general en el pie

## 🔧 Comandos Útiles

### **Verificar Funcionamiento**
```bash
py demo.py
```

### **Probar Catálogo**
```bash
py test_catalog.py
```

### **Instalar Dependencias**
```bash
py -m pip install -r requirements.txt
```

## 🚨 Solución de Problemas

### **Error: "No module named 'flask'"**
```bash
py -m pip install flask
```

### **Error: "No module named 'openpyxl'"**
```bash
py -m pip install openpyxl
```

### **Error de Conexión a Google Sheets**
- Verifica que el archivo esté **público**
- Confirma el **SHEET_ID** y **GID** en `config.py`
- Revisa los logs en la consola

### **La aplicación no inicia**
1. Verifica que Python esté instalado: `py --version`
2. Instala dependencias: `py -m pip install -r requirements.txt`
3. Ejecuta: `py start.py`

## 📞 Soporte Rápido

### **Verificar Estado**
```bash
py demo.py
```

### **Logs de Error**
- Revisa la consola donde ejecutaste `py app.py`
- Los errores aparecen en tiempo real

### **Archivos Importantes**
- `config.py` - Configuración principal
- `services/catalog_service.py` - Conexión Google Sheets
- `services/sales_service.py` - Gestión de ventas
- `services/export_service.py` - Exportación Excel

---

**💡 Consejo**: Usa `py start.py` para el inicio más fácil y automático! 