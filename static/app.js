document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    console.log('Setting today date:', today);
    
    // Variables globales
    let productosPorID = {}; 
    let editIndex = null;
    let ventasCache = [];
    let lastAddedIndex = -1; // Para trackear el último elemento agregado
    let rangosPrecios = {}; // Umbrales por grupo: { A: [0, 8000, 11600], AN: [0, 7600, 8000], ... }

    // ======== ELEMENTOS DOM =========
    const form = document.getElementById('ventaForm');
    const inputID = document.getElementById('id');
    const inputNombre = document.getElementById('nombre');
    const inputPrecio = document.getElementById('precio');
    const inputUnidades = document.getElementById('unidades');
    const inputPrecioFinal = document.getElementById('precioFinal');
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
    const inputDescuento = document.getElementById('descuento');
    const descuentoGroup = document.getElementById('descuentoGroup');
    const precioGroup = document.getElementById('precioGroup');
    const unidadesGroup = document.getElementById('unidadesGroup');
    const precioFinalGroup = document.getElementById('precioFinalGroup');
    const sidebarClock = document.getElementById('sidebarClock');
    const sidebarClockDate = document.getElementById('sidebarClockDate');
    const sidebarClockTime = document.getElementById('sidebarClockTime');
    // Tabs y tarjeta
    const tabVenta = document.getElementById('tabVenta');
    const tabCambio = document.getElementById('tabCambio');
    const ventaFormCard = document.getElementById('ventaFormCard');
    const formTitle = document.getElementById('formTitle');

    // Estado de pestaña actual
    let isCambio = false;
    let precioFinalTouched = false; // si el usuario editó manualmente precioFinal

    const NOTAS_PLACEHOLDER_VENTA = 'Detalles adicionales sobre la venta...';
    const NOTAS_PLACEHOLDER_CAMBIO = 'CAMBIO - ';

    function aplicarModo() {
        if (!ventaFormCard) return;
        // Estilos de pestañas
        if (isCambio) {
            tabVenta?.classList.remove('bg-gray-100');
            tabCambio?.classList.add('bg-red-100');
            tabCambio?.classList.add('text-red-700');
            tabCambio?.classList.remove('hover:bg-red-50');
            // Marco rojo/bordo
            ventaFormCard.classList.add('border-2', 'border-red-700', 'ring-2', 'ring-red-100');
            // Placeholder de notas
            if (inputNotas) inputNotas.placeholder = NOTAS_PLACEHOLDER_CAMBIO;
            // Escribir valor por defecto en notas si no existe o no empieza con el prefijo
            if (inputNotas && (!inputNotas.value || !inputNotas.value.startsWith(NOTAS_PLACEHOLDER_CAMBIO))) {
                inputNotas.value = NOTAS_PLACEHOLDER_CAMBIO;
            }
            // Ocultar descuento y precio final en Cambios y limpiar su valor
            if (descuentoGroup) descuentoGroup.classList.add('hidden');
            if (inputDescuento) inputDescuento.value = '';
            if (precioFinalGroup) precioFinalGroup.classList.add('hidden');
            // En Cambios: precioFinal = precio (si no fue tocado manualmente)
            if (!precioFinalTouched) {
                if (inputPrecio && inputPrecio.value !== '') {
                    inputPrecioFinal.value = inputPrecio.value;
                } else {
                    inputPrecioFinal.value = '';
                }
            }
            // Layout: precio más grande y unidades a la derecha
            if (precioGroup) {
                precioGroup.classList.remove('md:col-span-2');
                precioGroup.classList.add('md:col-span-3');
            }
            if (unidadesGroup) {
                unidadesGroup.classList.add('md:justify-self-end');
            }
            // Título del formulario
            if (formTitle) formTitle.textContent = 'Cambio de Venta';
        } else {
            tabCambio?.classList.remove('bg-red-100');
            tabCambio?.classList.add('hover:bg-red-50');
            tabVenta?.classList.add('bg-gray-100');
            // Quitar marco rojo/bordo
            ventaFormCard.classList.remove('border-2', 'border-red-700', 'ring-2', 'ring-red-100');
            // Placeholder de notas
            if (inputNotas) inputNotas.placeholder = NOTAS_PLACEHOLDER_VENTA;
            // Si el valor era exactamente el prefijo automático, limpiar al volver a Venta
            if (inputNotas && inputNotas.value === NOTAS_PLACEHOLDER_CAMBIO) {
                inputNotas.value = '';
            }
            // Mostrar descuento y precio final en Ventas
            if (descuentoGroup) descuentoGroup.classList.remove('hidden');
            if (precioFinalGroup) precioFinalGroup.classList.remove('hidden');
            // Recalcular precio final a partir de descuento si no fue tocado manual
            recalcularPrecioFinalSiAuto();
            // Layout: precio normal y unidades sin alineación forzada
            if (precioGroup) {
                precioGroup.classList.remove('md:col-span-3');
                precioGroup.classList.add('md:col-span-2');
            }
            if (unidadesGroup) {
                unidadesGroup.classList.remove('md:justify-self-end');
            }
            // Título del formulario
            if (formTitle) formTitle.textContent = 'Registro de Venta';
        }
    }

    // Helper: formatear fecha ISO (YYYY-MM-DD) a DD/MM/AAAA para display en tabla
    function formatFechaDisplay(iso) {
        if (!iso) return '';
        const parts = String(iso).split('-');
        if (parts.length !== 3) return iso;
        const [y, m, d] = parts;
        return `${d}/${m}/${y}`;
    }

    // Eventos de pestañas
    tabVenta?.addEventListener('click', () => { isCambio = false; aplicarModo(); });
    tabCambio?.addEventListener('click', () => { isCambio = true; aplicarModo(); });
    
    // Configurar fecha inicial
    if (fechaField) {
        fechaField.value = today;
        console.log('Date field set to:', fechaField.value);
    }
    // Aplicar estado inicial de pestañas/placeholder/borde
    aplicarModo();

    // ======== RELOJ LATERAL ========
    function updateSidebarClock() {
        if (!sidebarClock) return;
        const now = new Date();
        let fecha = now.toLocaleDateString('es-AR', { weekday: 'long', day: '2-digit', month: 'long' });
        // Capitalizar solo la PRIMERA letra del día
        const comaIdx = fecha.indexOf(',');
        if (comaIdx !== -1) {
            const dia = fecha.slice(0, comaIdx);
            const diaCap = dia.charAt(0).toUpperCase() + dia.slice(1);
            const resto = fecha.slice(comaIdx);
            fecha = `${diaCap}${resto}`;
        } else if (fecha.length > 0) {
            fecha = fecha.charAt(0).toUpperCase() + fecha.slice(1);
        }
        const hora = now.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        if (sidebarClockDate) sidebarClockDate.textContent = fecha;
        if (sidebarClockTime) sidebarClockTime.textContent = hora;
    }
    updateSidebarClock();
    setInterval(updateSidebarClock, 1000);

    // ======== EVENTOS =========
    form.addEventListener('submit', handleSubmit);
    addBtn.addEventListener('click', handleSubmit);
    resetBtn.addEventListener('click', resetForm);
    exportBtn.addEventListener('click', exportarExcel);

    // Recalcular Precio Final en tiempo real si no fue editado manualmente
    if (inputPrecio) inputPrecio.addEventListener('input', () => {
        // Al editar Precio, dejamos de fijar Precio Final manualmente
        precioFinalTouched = false;
        recalcularPrecioFinalSiAuto();
    });
    if (inputDescuento) inputDescuento.addEventListener('input', () => {
        // Clamp descuento a [0,100]
        if (typeof inputDescuento.value === 'string') {
            let d = parseFloat(inputDescuento.value.replace(',', '.'));
            if (isNaN(d)) d = 0;
            if (d < 0) d = 0;
            if (d > 100) d = 100;
            const fixed = Number.isInteger(d) ? String(d) : d.toFixed(2);
            if (inputDescuento.value !== fixed) inputDescuento.value = fixed;
        }
        // Si estamos en modo Cambio, el descuento no aplica visualmente; sincronizamos por las dudas
        if (isCambio) {
            precioFinalTouched = false;
            recalcularPrecioFinalSiAuto();
            return;
        }
        const dPct = obtenerDescuentoPct();
        // Si el usuario fijó manualmente el Precio Final, recalcular el Precio base para conservarlo
        if (precioFinalTouched && inputPrecioFinal && inputPrecioFinal.value !== '') {
            const pf = parseFloat(inputPrecioFinal.value);
            if (!isNaN(pf) && isFinite(pf)) {
                const base = calcularPrecioDesdeFinal(pf, dPct);
                if (!isNaN(base) && isFinite(base)) inputPrecio.value = base.toFixed(2);
            }
        }
        // Si no está fijado, recalcular el Precio Final a partir del Precio
        recalcularPrecioFinalSiAuto();
    });
    if (inputPrecioFinal) inputPrecioFinal.addEventListener('input', () => {
        // El usuario está fijando el Precio Final manualmente
        precioFinalTouched = true;
        const pf = parseFloat(inputPrecioFinal.value);
        if (isNaN(pf) || !isFinite(pf)) return;
        if (isCambio) {
            // En Cambios, Precio Final = Precio
            inputPrecio.value = pf.toFixed(2);
            return;
        }
        const dPct = obtenerDescuentoPct();
        const base = calcularPrecioDesdeFinal(pf, dPct);
        if (!isNaN(base) && isFinite(base)) inputPrecio.value = base.toFixed(2);
    });

    // Evento para el dropdown de IDs
    inputID.addEventListener('change', function() {
        const selectedID = this.value;
        if (selectedID && productosPorID[selectedID]) {
            const productoSel = productosPorID[selectedID];
            inputNombre.value = (productoSel && productoSel.nombre) ? productoSel.nombre : '';
            setHelper(`✅ ID seleccionado: ${selectedID}`, true);
            
            // Focus en el siguiente campo (precio)
            inputPrecio.focus();
        } else {
            inputNombre.value = '';
            setHelper('Selecciona un ID válido del catálogo.', false);
        }
    });

    // ======== CARGA INICIAL =========
    console.log('Iniciando carga inicial...');
    cargarCatalogo().then(() => {
            console.log('Catálogo cargado, cargando rangos...');
            return cargarRangos();
        }).then(() => {
            console.log('Rangos cargados, cargando ventas...');
            return cargarVentas();
    }).catch(error => {
        console.error('Error en carga inicial:', error);
        mostrarNotificacion(`Error en carga inicial: ${error.message}`, 'error');
    });

    // ======== CATALOGO (Sheets vía backend) =========
    async function cargarCatalogo() {
        try {
            console.log('Cargando catálogo desde Google Sheets...');
            const res = await fetch('/api/catalogo');
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error('Error en la respuesta del servidor:', errorText);
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            
            const data = await res.json();
            console.log('Datos recibidos del servidor:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Verificar que los datos tengan el formato esperado
            if (typeof data !== 'object' || Object.keys(data).length === 0) {
                console.warn('El catálogo está vacío o tiene un formato inesperado');
                mostrarNotificacion('El catálogo está vacío o no tiene el formato esperado', 'warning');
                return;
            }

            productosPorID = data;
            console.log('Catálogo cargado con éxito. Número de productos:', Object.keys(productosPorID).length);

            // Llenar el dropdown de IDs
            llenarDropdownIDs();
            
            return data; // Retornamos los datos para manejar la promesa
            
        } catch (error) {
            console.error('Error cargando catálogo:', error);
            mostrarNotificacion(`Error cargando catálogo: ${error.message}`, 'error');
            throw error; // Relanzamos el error para manejarlo en la cadena de promesas
        }
    }

    async function cargarRangos() {
        try {
            const res = await fetch('/api/rangos');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            rangosPrecios = (data && data.rangos && typeof data.rangos === 'object') ? data.rangos : {};
            console.log('Rangos de precios:', rangosPrecios);
        } catch (e) {
            console.warn('No se pudieron cargar rangos, se usará placeholder simple');
            rangosPrecios = {};
        }
    }

    function llenarDropdownIDs() {
        try {
            console.log('Llenando dropdown con productos...');
            
            // Limpiar opciones existentes (mantener la primera opción)
            inputID.innerHTML = '<option value="">Selecciona un ID...</option>';
            
            // Verificar que hay productos
            const ids = Object.keys(productosPorID);
            if (ids.length === 0) {
                console.warn('No hay productos para mostrar en el dropdown');
                mostrarNotificacion('No se encontraron productos en el catálogo', 'warning');
                return;
            }
            
            // Ordenar los IDs de forma "natural": prefijo alfabético + número (A1, A2, ..., AN1)
            const naturalKey = (id) => {
                const m = String(id).toUpperCase().match(/^([A-Z]+)(\d+)$/);
                if (m) {
                    return { letters: m[1], number: parseInt(m[2], 10), raw: id };
                }
                // Fallback para IDs que no siguen el patrón
                return { letters: String(id).toUpperCase(), number: Number.MAX_SAFE_INTEGER, raw: id };
            };

            const idsOrdenados = [...ids].sort((a, b) => {
                const ka = naturalKey(a);
                const kb = naturalKey(b);
                if (ka.letters < kb.letters) return -1;
                if (ka.letters > kb.letters) return 1;
                if (ka.number < kb.number) return -1;
                if (ka.number > kb.number) return 1;
                // Si empatan, ordenar por valor crudo
                return String(ka.raw).localeCompare(String(kb.raw));
            });
            
            // Establecer un placeholder simple y fijo
            inputPrecio.placeholder = "Ingresa el precio";
            
            // Agregar opciones de productos
            idsOrdenados.forEach(id => {
                try {
                    const producto = productosPorID[id];
                    const nombre = producto?.nombre || 'Sin nombre';
                    
                    const option = document.createElement('option');
                    option.value = id;
                    // Mostrar SOLO ID y nombre, sin precios ni textos extra
                    option.textContent = `${id} - ${nombre}`;
                    
                    // Tooltip sin precio
                    option.title = `ID: ${id}\nNombre: ${nombre}`;
                    
                    // No almacenar precio en dataset para evitar usos accidentales
                    
                    inputID.appendChild(option);
                } catch (error) {
                    console.error(`Error procesando producto con ID ${id}:`, error);
                }
            });
            
            console.log(`Dropdown llenado con ${idsOrdenados.length} productos`);
            
            // Configurar evento para actualizar el placeholder cuando se seleccione un ID
            inputID.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption && selectedOption.value) {
                    const producto = productosPorID[selectedOption.value];
                    if (producto) {
                        // Placeholder según rangos si existen
                        const placeholderRango = calcularPlaceholderRango(selectedOption.value);
                        inputPrecio.placeholder = placeholderRango || "Ingresa el precio";
                        inputPrecio.value = ''; // Mantener el campo vacío siempre
                        
                        // Rellenar automáticamente el nombre
                        inputNombre.value = producto.nombre || '';
                        
                        // Focus en el campo de precio
                        inputPrecio.focus();
                        
                        setHelper(`✅ ID seleccionado: ${selectedOption.value}`, true);
                    }
                } else {
                    // Restaurar el placeholder por defecto si no hay selección
                    inputPrecio.placeholder = "Ingresa el precio";
                    inputPrecio.value = '';
                    inputNombre.value = '';
                    setHelper('Selecciona un ID del catálogo', false);
                }
            });
            
        } catch (error) {
            console.error('Error al llenar el dropdown:', error);
            mostrarNotificacion('Error al cargar la lista de productos', 'error');
            
            // Establecer un placeholder por defecto en caso de error
            inputPrecio.placeholder = "Ingresa el precio";
        }
    }

    function calcularPlaceholderRango(idSeleccionado) {
        // Rango por grupo: usar solo IDs con el mismo prefijo de letras
        const parseId = (id) => {
            const m = String(id).toUpperCase().match(/^([A-Z]+)(\d+)$/);
            return m ? { letters: m[1], number: parseInt(m[2], 10), raw: id } : { letters: '', number: 0, raw: id };
        };
        const sel = parseId(idSeleccionado);
        const umbralesGrupo = rangosPrecios[sel.letters];
        if (!Array.isArray(umbralesGrupo) || umbralesGrupo.length < 2) {
            // Sin rangos suficientes, no mostrar sugerencia
            return '';
        }
        const options = Array.from(inputID.options).filter(o => o.value);
        const grupoOptions = options.filter(o => parseId(o.value).letters === sel.letters);
        const idsGrupo = grupoOptions.map(o => o.value);

        // Índice dentro del grupo
        const idx = idsGrupo.indexOf(idSeleccionado);
        if (idx === -1) return '';

        // Usar el índice del grupo para mapear umbrales del grupo
        const lower = umbralesGrupo[Math.min(idx, umbralesGrupo.length - 1)] ?? 0;
        const upper = umbralesGrupo[idx + 1];

        const fmt = (n) => {
            if (typeof n !== 'number' || isNaN(n)) return '-';
            return `$${n.toLocaleString('es-CL')}`;
        };

        const left = fmt(lower);
        const right = (typeof upper === 'number') ? fmt(upper) : '-';
        return `Precio sugerido: ${left} a ${right}`;
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
        if (inputDescuento) inputDescuento.value = '';
        if (inputPrecioFinal) inputPrecioFinal.value = '';
        precioFinalTouched = false;
        editIndex = null;
        setHelper('Formulario limpiado. Selecciona un ID del catálogo.', true);
        inputID.focus();
        // Ajustar notas según modo actual
        if (inputNotas) {
            if (isCambio) {
                inputNotas.value = NOTAS_PLACEHOLDER_CAMBIO;
                inputNotas.placeholder = NOTAS_PLACEHOLDER_CAMBIO;
            } else {
                inputNotas.value = '';
                inputNotas.placeholder = NOTAS_PLACEHOLDER_VENTA;
            }
        }
    }

    let isExporting = false;
    async function exportarExcel() {
        try {
            if (isExporting) return; // evitar doble exportación
            isExporting = true;
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Exportando...';
            
            const res = await fetch('/api/exportar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            try {
                const data = await res.json();
                if (res.ok && data && data.success !== false) {
                    if (typeof mostrarNotificacion === 'function') {
                        mostrarNotificacion('✅ Exportación completada. Historial actualizado.', 'success');
                    }
                    // Vaciar inmediatamente la tabla en UI
                    ventasCache = [];
                    actualizarTabla();
                    actualizarEstadisticas();
                    actualizarContador();
                    // Forzar limpieza en backend por si hubo condiciones de carrera
                    try { await fetch('/api/ventas', { method: 'DELETE' }); } catch (_) {}
                    // Recargar ventas para reflejar limpieza
                    try { await cargarVentas(); } catch (_) {}
                    // Invalidar/actualizar historial (SPA)
                    window.dispatchEvent(new Event('historial:invalidate'));
                    // Redirigir al historial para que el usuario valide la exportación
                    setTimeout(() => { window.location.href = '/historial'; }, 300);
                } else {
                    if (typeof mostrarNotificacion === 'function') {
                        mostrarNotificacion('❌ Falló la exportación', 'error');
                    }
                }
            } catch (_) {
                // Si no se puede parsear JSON, igual disparamos invalidación por si el backend ya guardó
                window.dispatchEvent(new Event('historial:invalidate'));
            }
            
        } catch (error) {
            alert('ERROR AL EXPORTAR');
        } finally {
            isExporting = false;
            exportBtn.disabled = false;
            exportBtn.innerHTML = '<i class="fas fa-file-excel mr-2"></i> Exportar a Google Sheets';
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

    // ======== Modal de límite de exportación ========
    function cerrarModalLimit() {
        const modal = document.getElementById('exportLimitModal');
        if (modal) modal.remove();
    }

    function mostrarModalLimiteExport() {
        // Evitar múltiples modales
        if (document.getElementById('exportLimitModal')) return;
        const overlay = document.createElement('div');
        overlay.id = 'exportLimitModal';
        overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40';

        const box = document.createElement('div');
        box.className = 'bg-white rounded-lg shadow-xl w-11/12 max-w-md p-6';
        box.innerHTML = `
            <h3 class="text-lg font-semibold mb-3">Límite alcanzado</h3>
            <p class="text-sm text-gray-700 mb-5">Has alcanzado 20 artículos en la tabla. Para continuar, exporta las ventas actuales.</p>
            <div class="flex justify-end gap-3">
                <button id="btnCancelLimit" class="px-4 py-2 rounded border border-gray-300 text-gray-700 hover:bg-gray-50">Cancelar</button>
                <button id="btnExportLimit" class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700"><i class="fas fa-file-excel mr-2"></i>Exportar</button>
            </div>
        `;
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        document.getElementById('btnCancelLimit').addEventListener('click', cerrarModalLimit);
        document.getElementById('btnExportLimit').addEventListener('click', async () => {
            try {
                cerrarModalLimit();
                await exportarExcel();
            } catch (_) {
                // noop
            }
        });
    }

    async function handleSubmit(event) {
        event.preventDefault(); // Evitar que el formulario se envíe de forma tradicional
        console.log('Intentando agregar/actualizar venta...');
        // Límite de 20 artículos: no permitir agregar más -> abrir modal Exportar/Cancelar
        if (editIndex === null && Array.isArray(ventasCache) && ventasCache.length >= 20) {
            mostrarModalLimiteExport();
            return;
        }
        
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

        let precio = parseFloat(precioValue);
        let unidades = parseInt(unidadesValue);
        // Determinar precio unitario final a enviar: usar Precio Final si está, si no calcular a partir de descuento
        let precioFinalUnit = null;
        const descuentoPct = (() => {
            if (isCambio) return 0;
            if (inputDescuento && inputDescuento.value !== '') {
                const d = parseFloat(inputDescuento.value);
                if (!isNaN(d) && isFinite(d)) return Math.min(100, Math.max(0, d));
            }
            return 0;
        })();

        if (inputPrecioFinal && inputPrecioFinal.value !== '') {
            const pf = parseFloat(inputPrecioFinal.value);
            if (!isNaN(pf) && isFinite(pf)) {
                precioFinalUnit = pf;
            }
        }
        if (precioFinalUnit === null) {
            if (!isNaN(precio) && isFinite(precio)) {
                precioFinalUnit = +(precio * (1 - (descuentoPct / 100))).toFixed(2);
            } else {
                mostrarNotificacion('❌ El precio es inválido', 'error');
                document.getElementById('precio').focus();
                return;
            }
        }
        // Usar precio final como precio unitario enviado al backend
        precio = precioFinalUnit;
        if (isCambio) {
            unidades = -Math.abs(unidades);
        }
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
        if (inputPrecioFinal) {
            inputPrecioFinal.value = v.precio; // el precio almacenado es el unitario final
            precioFinalTouched = true;
        }
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

    // ======== PRECIO FINAL: Cálculo automático ========
    function calcularPrecioFinalUnit() {
        const precioVal = parseFloat(inputPrecio?.value || '');
        if (isNaN(precioVal) || !isFinite(precioVal)) return '';
        if (isCambio) return precioVal.toFixed(2);
        const dStr = inputDescuento?.value || '';
        const d = parseFloat(dStr);
        const descuentoPct = (!isNaN(d) && isFinite(d)) ? Math.min(100, Math.max(0, d)) : 0;
        const pf = +(precioVal * (1 - (descuentoPct / 100))).toFixed(2);
        return pf.toFixed(2);
    }

    function recalcularPrecioFinalSiAuto() {
        if (!inputPrecioFinal) return;
        if (precioFinalTouched) return; // respetar edición manual
        const val = calcularPrecioFinalUnit();
        inputPrecioFinal.value = val;
    }

    // ======== Helpers para bidireccionalidad Precio <-> Precio Final ========
    function obtenerDescuentoPct() {
        if (isCambio) return 0;
        const dStr = inputDescuento?.value || '';
        const d = parseFloat(dStr);
        if (isNaN(d) || !isFinite(d)) return 0;
        return Math.min(100, Math.max(0, d));
    }

    function calcularPrecioDesdeFinal(precioFinal, descuentoPct) {
        // precioFinal = precio * (1 - d/100) => precio = precioFinal / (1 - d/100)
        const denom = 1 - (descuentoPct / 100);
        if (denom <= 0) return precioFinal; // Evitar división por cero o negativa; tomar base = final
        return +(precioFinal / denom).toFixed(2);
    }

    // Variables para el modal de confirmación
    let currentDeleteIndex = null;
    const confirmModal = document.getElementById('confirmModal');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    const confirmCancelBtn = document.getElementById('confirmCancel');
    const clearAllBtn = document.getElementById('clearAllBtn');

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

    // Vaciar todas las ventas con confirmación
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', async () => {
            try {
                const confirmado = await confirmarAccionJSON({
                    titulo: '¿Vaciar todas las ventas?',
                    mensaje: 'Esta acción eliminará todas las ventas en memoria. No se puede deshacer.',
                    confirmarTexto: 'Sí, vaciar',
                    cancelarTexto: 'Cancelar'
                });
                if (!confirmado) return;

                clearAllBtn.disabled = true;
                clearAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Vaciando...';

                const res = await fetch('/api/ventas', { method: 'DELETE' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Error al vaciar ventas');

                mostrarNotificacion('✅ ' + (data.message || 'Ventas vaciadas'), 'success');
                await cargarVentas();
            } catch (e) {
                mostrarNotificacion(`❌ ${e.message}`, 'error');
            } finally {
                clearAllBtn.disabled = false;
                clearAllBtn.innerHTML = '<i class="fas fa-trash mr-2"></i> Vaciar ventas';
            }
        });
    }

    // Pequeño helper de confirmación tipo JSON
    async function confirmarAccionJSON({ titulo, mensaje, confirmarTexto = 'Confirmar', cancelarTexto = 'Cancelar' }) {
        return new Promise((resolve) => {
            // Reutilizamos el modal existente con textos dinámicos
            const modal = document.getElementById('confirmModal');
            if (!modal) { resolve(confirm(mensaje)); return; }

            const titleEl = modal.querySelector('h3');
            const msgEl = modal.querySelector('p');
            const btnConfirm = document.getElementById('confirmDelete');
            const btnCancel = document.getElementById('confirmCancel');

            const oldTitle = titleEl.textContent;
            const oldMsg = msgEl.textContent;
            const oldConfirmText = btnConfirm.textContent;
            const oldCancelText = btnCancel.textContent;

            titleEl.textContent = titulo;
            msgEl.textContent = mensaje;
            btnConfirm.textContent = confirmarTexto;
            btnCancel.textContent = cancelarTexto;

            modal.classList.remove('hidden');

            const onConfirm = () => {
                cleanup();
                resolve(true);
            };
            const onCancel = () => {
                cleanup();
                resolve(false);
            };

            function cleanup() {
                modal.classList.add('hidden');
                btnConfirm.removeEventListener('click', onConfirm);
                btnCancel.removeEventListener('click', onCancel);
                // Restaurar textos originales
                titleEl.textContent = oldTitle;
                msgEl.textContent = oldMsg;
                btnConfirm.textContent = oldConfirmText;
                btnCancel.textContent = oldCancelText;
            }

            btnConfirm.addEventListener('click', onConfirm, { once: true });
            btnCancel.addEventListener('click', onCancel, { once: true });
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
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${formatFechaDisplay(venta.fecha)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${venta.id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700" title="${venta.nombre}">${venta.nombre || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">$${Number(venta.precio).toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${venta.unidades}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">$${Number(venta.total).toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                        ${venta.pago === 'Efectivo' ? 'bg-green-100 text-green-800' :
                          venta.pago === 'Debito' ? 'bg-blue-100 text-blue-800' :
                          venta.pago === 'Credito' ? 'bg-purple-100 text-purple-800' :
                          venta.pago === 'Transferencia' ? 'bg-gray-100 text-gray-800' :
                          'bg-yellow-100 text-yellow-800'}">
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

    
    const watermark = document.getElementById('watermark');
    function updateWatermarkVisibility() {
        if (!watermark) return;
        // Mostrar watermark SOLO en Registro de Venta (cuando existe la tarjeta del formulario)
        const isRegistroVenta = !!document.getElementById('ventaFormCard');
        if (!isRegistroVenta) {
            watermark.style.opacity = '0';
            watermark.style.display = 'none';
            return;
        }
        watermark.style.display = '';
        const doc = document.documentElement;
        const atBottom = Math.ceil(window.innerHeight + window.scrollY) >= (doc.scrollHeight - 2);
        watermark.style.opacity = atBottom ? '0.3' : '0';
    }
    window.addEventListener('scroll', updateWatermarkVisibility, { passive: true });
    window.addEventListener('resize', updateWatermarkVisibility);
    updateWatermarkVisibility();
});
