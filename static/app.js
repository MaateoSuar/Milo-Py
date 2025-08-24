document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    console.log('Setting today date:', today);
    
    // Variables globales
    let productosPorID = {}; 
    let editIndex = null;
    let ventasCache = [];
    let lastAddedIndex = -1; // Para trackear el último elemento agregado

    // ======== ELEMENTOS DOM =========
    const form = document.getElementById('ventaForm');
    const inputID = document.getElementById('id');
    const inputNombre = document.getElementById('nombre');
    const inputPrecio = document.getElementById('precio');
    const inputUnidades = document.getElementById('unidades');
    const inputPago = document.querySelector('input[name="pago"]:checked');
    const inputNotas = document.getElementById('notas');
    const fechaField = document.getElementById('fecha');
    const addBtn = document.getElementById('addBtn');
    const resetBtn = document.getElementById('resetBtn');
    const exportBtn = document.getElementById('exportBtn');
    const downloadLink = document.getElementById('downloadLink');
    const ventasTable = document.getElementById('ventasTable');
    const ventasBody = document.getElementById('ventasBody');
    const totalVentas = document.getElementById('totalVentas');
    
    // Configurar fecha inicial
    if (fechaField) {
        fechaField.value = today;
        console.log('Date field set to:', fechaField.value);
    }

    // ======== EVENTOS =========
    form.addEventListener('submit', handleSubmit);
    addBtn.addEventListener('click', handleSubmit);
    resetBtn.addEventListener('click', resetForm);
    exportBtn.addEventListener('click', exportarExcel);

    // Evento para el dropdown de IDs
    inputID.addEventListener('change', function() {
        const selectedID = this.value;
        if (selectedID && productosPorID[selectedID]) {
            inputNombre.value = productosPorID[selectedID];
            setHelper(`✅ ID seleccionado: ${selectedID}`, true);
            
            // Focus en el siguiente campo (precio)
            inputPrecio.focus();
        } else {
            inputNombre.value = '';
            setHelper('Selecciona un ID válido del catálogo.', false);
        }
    });

    // ======== CARGA INICIAL =========
    cargarCatalogo();
    cargarVentas();

    // ======== CATALOGO (Sheets vía backend) =========
    async function cargarCatalogo() {
        try {
            console.log('Cargando catálogo desde Google Sheets...');
            const res = await fetch('/api/catalogo');
            
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            
            const data = await res.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            productosPorID = data;
            console.log('Catálogo cargado:', productosPorID);

            // Llenar el dropdown de IDs
            llenarDropdownIDs();
            
        } catch (error) {
            console.error('Error cargando catálogo:', error);
            mostrarNotificacion(`Error cargando catálogo: ${error.message}`, 'error');
        }
    }

    function llenarDropdownIDs() {
        // Limpiar opciones existentes (mantener la primera opción)
        inputID.innerHTML = '<option value="">Selecciona un ID...</option>';
        
        // Agregar opciones de productos
        Object.keys(productosPorID).sort().forEach(id => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = `${id} - ${productosPorID[id]}`;
            inputID.appendChild(option);
        });
        
        console.log(`Dropdown llenado con ${Object.keys(productosPorID).length} productos`);
    }

    function setHelper(msg, ok) {
        const el = document.getElementById('idHelper');
        el.textContent = msg;
        el.className = `mt-1 text-xs ${ok ? 'text-green-600' : 'text-red-600'}`;
    }

    function resetForm() {
        form.reset();
        if (fechaField) {
            fechaField.value = today;
        }
        inputNombre.value = '';
        editIndex = null;
        setHelper('Formulario limpiado. Selecciona un ID del catálogo.', true);
        inputID.focus();
    }

    async function exportarExcel() {
        console.log('Exportando a Excel...');
        
        try {
            // Mostrar estado de carga
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Exportando...';
            
            // Llamar a la API de exportación
            const response = await fetch('/api/exportar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Respuesta de exportación:', data);
            console.log('data.success:', data.success);
            console.log('data.mensaje:', data.mensaje);
            
            // Mostrar notificación de éxito
            if (data.success) {
                const mensaje = data.mensaje || 'Exportado con éxito';
                console.log('Mostrando mensaje:', mensaje);
                mostrarNotificacion(`✅ ${mensaje}`, 'success');
            } else {
                throw new Error(data.mensaje || 'Error desconocido en la exportación');
            }
            
            // Mostrar enlace de descarga
            downloadLink.classList.remove('hidden');
            downloadLink.focus();
            
        } catch (error) {
            console.error('Error exportando a Excel:', error);
            mostrarNotificacion(`❌ Error al exportar: ${error.message}`, 'error');
        } finally {
            // Restaurar botón
            exportBtn.disabled = false;
            exportBtn.innerHTML = '<i class="fas fa-file-excel mr-2"></i> Exportar a Excel';
        }
    }

    // ======== API (ventas) =========
    async function cargarVentas() {
        const res = await fetch('/api/ventas');
        ventasCache = await res.json();
        actualizarTabla();
        actualizarEstadisticas();
        actualizarContador();
    }

    async function handleSubmit(event) {
        event.preventDefault(); // Evitar que el formulario se envíe de forma tradicional
        console.log('Intentando agregar/actualizar venta...');
        
        // Validar formulario
        if (!form.checkValidity()) {
            console.log('Formulario no válido');
            form.reportValidity();
            return;
        }

        // Obtener valores del formulario
        const fecha = document.getElementById('fecha').value;
        const id = document.getElementById('id').value.trim().toUpperCase();
        const nombre = document.getElementById('nombre').value.trim();
        const precioValue = document.getElementById('precio').value;
        const unidadesValue = document.getElementById('unidades').value;
        const pagoElement = document.querySelector('input[name="pago"]:checked');
        const notas = document.getElementById('notas').value;

        console.log('Valores del formulario:', { fecha, id, nombre, precioValue, unidadesValue, pagoElement, notas });

        // Validaciones
        if (!fecha) {
            mostrarNotificacion('❌ La fecha es requerida', 'error');
            return;
        }

        if (!id) {
            mostrarNotificacion('❌ El ID del producto es requerido', 'error');
            inputID.focus();
            return;
        }

        if (!(id in productosPorID)) {
            mostrarNotificacion('❌ El ID no existe en el catálogo. Selecciona un ID válido.', 'error');
            inputID.focus();
            return;
        }

        if (!precioValue || isNaN(parseFloat(precioValue))) {
            mostrarNotificacion('❌ El precio es requerido y debe ser un número válido', 'error');
            document.getElementById('precio').focus();
            return;
        }

        if (!unidadesValue || isNaN(parseInt(unidadesValue))) {
            mostrarNotificacion('❌ Las unidades son requeridas y deben ser un número válido', 'error');
            document.getElementById('unidades').focus();
            return;
        }

        if (!pagoElement) {
            mostrarNotificacion('❌ Selecciona una forma de pago', 'error');
            return;
        }

        const precio = parseFloat(precioValue);
        const unidades = parseInt(unidadesValue);
        const pago = pagoElement.value;

        const venta = { fecha, id, nombre, precio, unidades, pago, notas };
        console.log('Venta a enviar:', venta);

        try {
            if (editIndex === null) {
                console.log('Agregando nueva venta...');
                const res = await fetch('/api/ventas', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(venta)
                });
                
                const data = await res.json();
                console.log('Respuesta del servidor:', data);
                
                if (!res.ok) {
                    throw new Error(data.error || `Error HTTP ${res.status}`);
                }
                
                // Marcar el índice del último elemento agregado
                lastAddedIndex = ventasCache.length;
                
                mostrarNotificacion('✅ ' + data.message, 'success');
            } else {
                console.log('Actualizando venta existente...');
                const res = await fetch(`/api/ventas/${editIndex}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(venta)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Error al actualizar');
                mostrarNotificacion('✅ ' + data.message, 'success');
                salirDeEdicion();
            }

            // Recargar datos y resetear formulario
            await cargarVentas();
            form.reset();
            
            // Restablecer fecha a hoy
            const fechaField = document.getElementById('fecha');
            if (fechaField) {
                fechaField.value = today;
            }
            
            inputNombre.value = '';
            setHelper('✅ Venta agregada correctamente. Haz clic para seleccionar otro producto.', true);
            
            // Auto-scroll al último elemento agregado
            if (editIndex === null) {
                setTimeout(() => scrollToLastAdded(), 300);
            }
            
            // Focus en ID para siguiente venta
            inputID.focus();
            
        } catch (err) {
            console.error('Error al procesar venta:', err);
            mostrarNotificacion(`❌ Error: ${err.message}`, 'error');
        }
    }

    // ======== AUTO-SCROLL AL ÚLTIMO ELEMENTO =========
    function scrollToLastAdded() {
        if (lastAddedIndex >= 0 && lastAddedIndex < ventasCache.length) {
            const tableContainer = document.querySelector('.overflow-x-auto');
            const lastRow = tableContainer.querySelector(`tbody tr:nth-child(${lastAddedIndex + 1})`);
            
            if (lastRow) {
                // Resaltar temporalmente la fila
                lastRow.classList.add('bg-yellow-100', 'border-2', 'border-yellow-400');
                
                // Scroll suave a la fila
                lastRow.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                // Remover el resaltado después de 3 segundos
                setTimeout(() => {
                    lastRow.classList.remove('bg-yellow-100', 'border-2', 'border-yellow-400');
                }, 3000);
            }
        }
    }

    function entrarEnEdicion(index) {
        editIndex = index;
        const v = ventasCache[index];
        document.getElementById('fecha').value = v.fecha;
        document.getElementById('id').value = v.id;
        document.getElementById('precio').value = v.precio;
        document.getElementById('unidades').value = v.unidades;
        document.querySelector(`input[name="pago"][value="${v.pago}"]`).checked = true;
        document.getElementById('notas').value = v.notas;
        document.getElementById('nombre').value = v.nombre || (productosPorID[v.id] || '');
        addBtn.innerHTML = '<i class="fas fa-save mr-2"></i> Guardar Cambios';
        document.getElementById('ventaForm').scrollIntoView({ behavior: 'smooth' });
    }

    function salirDeEdicion() {
        editIndex = null;
        addBtn.innerHTML = '<i class="fas fa-plus-circle mr-2"></i> Agregar';
    }

    // Variables para el modal de confirmación
    let currentDeleteIndex = null;
    const confirmModal = document.getElementById('confirmModal');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    const confirmCancelBtn = document.getElementById('confirmCancel');

    // Configurar eventos del modal
    if (confirmDeleteBtn && confirmCancelBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            if (currentDeleteIndex === null) return;
            
            // Mostrar carga
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Eliminando...';
            
            const index = currentDeleteIndex;
            const res = await fetch(`/api/ventas/${index}`, { method: 'DELETE' });
            const data = await res.json();
            
            // Restaurar botón
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = 'Eliminar';
            confirmModal.classList.add('hidden');
            
            if (!res.ok) {
                mostrarNotificacion(data.error || 'Error al eliminar', 'error');
                return;
            }
            
            mostrarNotificacion('Venta eliminada correctamente', 'success');
            
            if (editIndex === index) {
                salirDeEdicion();
                form.reset();
                document.getElementById('fecha').value = today;
                inputNombre.value = '';
            }
            
            await cargarVentas();
        });
        
        confirmCancelBtn.addEventListener('click', () => {
            confirmModal.classList.add('hidden');
        });
    }

    async function eliminarVenta(index) {
        currentDeleteIndex = index;
        confirmModal.classList.remove('hidden');
    }

    // ======== TABLA / ESTADISTICAS =========
    function actualizarTabla() {
        const tbody = document.getElementById('ventasBody');
        tbody.innerHTML = '';
        let totalGeneral = 0;

        ventasCache.forEach((venta, index) => {
            totalGeneral += venta.total;
            const row = document.createElement('tr');
            row.className = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${venta.fecha}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${venta.id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700" title="${venta.nombre}">${venta.nombre || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">$${Number(venta.precio).toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${venta.unidades}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">$${Number(venta.total).toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                        ${venta.pago === 'Efectivo' ? 'bg-green-100 text-green-800' :
                          venta.pago === 'Tarjeta' ? 'bg-blue-100 text-blue-800' :
                          venta.pago === 'Transferencia' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'}">
                        ${venta.pago}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 max-w-xs truncate" title="${venta.notas}">${venta.notas || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button data-action="editar" data-index="${index}" class="text-blue-600 hover:text-blue-900">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button data-action="eliminar" data-index="${index}" class="text-red-600 hover:text-red-900">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        document.getElementById('totalGeneral').textContent = `$${totalGeneral.toFixed(2)}`;

        tbody.querySelectorAll('button[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                const idx = parseInt(e.currentTarget.getAttribute('data-index'));
                if (action === 'editar') entrarEnEdicion(idx);
                if (action === 'eliminar') eliminarVenta(idx);
            });
        });
    }

    function actualizarEstadisticas() {
        const hoy = new Date().toISOString().split('T')[0];
        const ventasHoy = ventasCache.filter(v => v.fecha === hoy);
        const cant = ventasHoy.length;
        const ingresos = ventasHoy.reduce((sum, v) => sum + Number(v.total || 0), 0);
        const prom = cant > 0 ? ingresos / cant : 0;

        document.getElementById('ventasHoy').textContent = cant;
        document.getElementById('ingresosTotales').textContent = `$${ingresos.toFixed(2)}`;
        document.getElementById('promedioVenta').textContent = `$${prom.toFixed(2)}`;
    }

    function actualizarContador() {
        const totalVentas = ventasCache.length;
        document.getElementById('totalVentas').textContent = totalVentas;
    }

    // ======== EXPORTAR =========
    async function exportarExcel() {
        try {
            const res = await fetch('/api/exportar', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Error al exportar');
            mostrarNotificacion(data.message, 'success');
            downloadLink.classList.remove('hidden');
        } catch (err) {
            mostrarNotificacion(err.message, 'error');
        }
    }
});
