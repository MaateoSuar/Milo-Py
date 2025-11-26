document.addEventListener('DOMContentLoaded', () => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const today = `${yyyy}-${mm}-${dd}`;
    console.log('Setting today date:', today);

    // Diagnóstico manual: activar con ?debugDate=1
    function runDateDiagnostics() {
        const now = new Date();
        const offsetMin = now.getTimezoneOffset();
        const localToday = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const utcToday = new Date().toISOString().split('T')[0];

        // Simulación de 22:30 locales del día actual
        const sim = new Date(now);
        sim.setHours(22, 30, 0, 0);
        const simLocal = `${sim.getFullYear()}-${String(sim.getMonth() + 1).padStart(2, '0')}-${String(sim.getDate()).padStart(2, '0')}`;
        const simUtc = sim.toISOString().split('T')[0];

        console.group('[Fecha] Diagnóstico Local vs UTC');
        console.log('Ahora (local):', now.toString());
        console.log('Ahora (UTC ISO):', now.toISOString());
        console.log('Timezone offset (min):', offsetMin);
        console.log('Hoy (local):', localToday);
        console.log('Hoy (UTC ISO->date):', utcToday);
        if (localToday !== utcToday) {
            console.warn('⚠ Diferencia detectada: localToday != utcToday');
        }

    // ======== STOCK INGRESO & STOCK ACTUAL =========
    const stockIngresoForm = document.getElementById('stockIngresoForm');
    const stFecha = document.getElementById('st_fecha');
    const stIdArticulo = document.getElementById('st_id_articulo');
    const stTipo = document.getElementById('st_tipo');
    const stPrecioIndividual = document.getElementById('st_precio_individual');
    const stCostoIndividual = document.getElementById('st_costo_individual');
    const stCantidad = document.getElementById('st_cantidad');
    const stCostoTotal = document.getElementById('st_costo_total');
    const stNotas = document.getElementById('st_notas');
    const stockIngresoBody = document.getElementById('stockIngresoBody');
    const stockActualBody = document.getElementById('stockActualBody');

    let stockEditId = null;

    // Fecha por defecto: hoy
    if (stockIngresoForm && stFecha && !stFecha.value) {
        stFecha.value = today;
    }

    // Formateo y cálculo de costo total
    if (stCostoIndividual) attachThousandsFormatter(stCostoIndividual);
    if (stPrecioIndividual) attachThousandsFormatter(stPrecioIndividual);

    function actualizarCostoTotalStock(){
        if (!stCostoIndividual || !stCantidad || !stCostoTotal) return;
        const costo = parseMoneyEs(stCostoIndividual.value || '');
        const cant = parseInt(stCantidad.value || '0', 10) || 0;
        if (!isFinite(costo) || cant <= 0){
            stCostoTotal.value = '';
            return;
        }
        const total = +(costo * cant).toFixed(2);
        // Mostrar como texto plano con coma
        let val = total.toFixed(2).replace('.', ',');
        stCostoTotal.value = formatThousandsEs(val);
    }

    if (stCostoIndividual){
        stCostoIndividual.addEventListener('input', actualizarCostoTotalStock);
    }
    if (stCantidad){
        stCantidad.addEventListener('input', actualizarCostoTotalStock);
    }

    function resetStockIngresoForm(){
        if (!stockIngresoForm) return;
        stockIngresoForm.reset();
        stockEditId = null;
        if (stFecha) stFecha.value = today;
    }

    async function cargarStockIngresos(){
        if (!stockIngresoBody) return;
        try {
            const res = await fetch('/api/stock/ingresos');
            const data = await res.json();
            if (!res.ok || data.success === false){
                stockIngresoBody.innerHTML = '';
                return;
            }
            const rows = Array.isArray(data.rows) ? data.rows : [];
            stockIngresoBody.innerHTML = '';
            if (!rows.length){
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="8" class="px-4 py-3 text-sm text-gray-500 text-center">No hay ingresos de stock registrados aún.</td>';
                stockIngresoBody.appendChild(tr);
                return;
            }
            rows.forEach((r) => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                const costoInd = Number(r.costo_individual || 0);
                const cant = Number(r.cantidad || 0);
                const costoTot = Number(r.costo_total || (costoInd * cant));
                const fechaDisp = formatFechaDisplay(r.fecha);
                const notasTxt = r.notas || '';
                tr.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${fechaDisp}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">${r.id_articulo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${r.tipo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">$${formatMoney(costoInd)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">${cant}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right font-semibold text-gray-900">$${formatMoney(costoTot)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-600 max-w-[8rem] md:max-w-xs truncate">
                        ${notasTxt ? `<span class="truncate inline-block cursor-pointer" data-note="${encodeURIComponent(String(notasTxt))}" title="${notasTxt}">${notasTxt}</span>` : ''}
                    </td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right">
                        <button type="button" class="inline-flex items-center justify-center h-8 w-8 rounded hover:bg-blue-50 text-blue-600 hover:text-blue-800 mr-1" data-action="st-edit" data-id="${r.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="inline-flex items-center justify-center h-8 w-8 rounded hover:bg-red-50 text-red-600 hover:text-red-800" data-action="st-delete" data-id="${r.id}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                `;
                stockIngresoBody.appendChild(tr);
            });
        } catch(_){
            // noop
        }
    }

    async function guardarStockIngreso(e){
        if (!stockIngresoForm) return;
        e.preventDefault();
        if (!stFecha || !stIdArticulo || !stCostoIndividual || !stCantidad) return;

        const fecha = stFecha.value || today;
        const id_articulo = (stIdArticulo.value || '').trim().toUpperCase();
        const tipo = (stTipo?.value || '').trim();
        const precio_individual = stPrecioIndividual ? parseMoneyEs(stPrecioIndividual.value || '') : NaN;
        const costo_individual = parseMoneyEs(stCostoIndividual.value || '');
        const cantidad = parseInt(stCantidad.value || '0', 10) || 0;
        const notas = (stNotas?.value || '').trim();

        if (!fecha || !id_articulo || !isFinite(costo_individual) || cantidad <= 0){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('❌ Completa fecha, ID, costo individual y cantidad (>0)', 'error');
            }
            return;
        }

        const costo_total_num = (() => {
            const v = parseMoneyEs(stCostoTotal?.value || '');
            if (isFinite(v) && v > 0) return v;
            return +(costo_individual * cantidad).toFixed(2);
        })();

        const payload = {
            fecha,
            id_articulo,
            tipo,
            precio_individual: isFinite(precio_individual) ? precio_individual : null,
            costo_individual,
            cantidad,
            costo_total: costo_total_num,
            notas,
        };

        try {
            const url = stockEditId != null ? `/api/stock/ingresos/${stockEditId}` : '/api/stock/ingresos';
            const method = stockEditId != null ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || data.success === false){
                throw new Error(data.error || 'Error guardando ingreso de stock');
            }
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('✅ Ingreso de stock guardado', 'success');
            }
            resetStockIngresoForm();
            await cargarStockIngresos();
        } catch(err){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion(`❌ ${err.message || err}`, 'error');
            }
        }
    }

    async function eliminarStockIngreso(id){
        if (!id) return;
        try {
            const confirmado = await confirmarAccionJSON({
                titulo: '¿Eliminar ingreso de stock?',
                mensaje: 'Esta acción eliminará el ingreso de stock de la base de datos. No se puede deshacer.',
                confirmarTexto: 'Eliminar',
                cancelarTexto: 'Cancelar',
            });
            if (!confirmado) return;
            const res = await fetch(`/api/stock/ingresos/${id}`, { method: 'DELETE' });
            const data = await res.json().catch(()=>({}));
            if (!res.ok || data.success === false){
                throw new Error(data.error || 'Error al eliminar ingreso');
            }
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('✅ Ingreso de stock eliminado', 'success');
            }
            await cargarStockIngresos();
        } catch(err){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion(`❌ ${err.message || err}`, 'error');
            }
        }
    }

    function entrarEdicionStockIngreso(id){
        if (!stockIngresoBody || !stockIngresoForm) return;
        stockEditId = id;
        // Buscar la fila en caché no existe, así que recargamos data desde tabla DOM
        const btn = stockIngresoBody.querySelector(`[data-action="st-edit"][data-id="${id}"]`);
        if (!btn) return;
        const tr = btn.closest('tr');
        if (!tr) return;
        const tds = tr.querySelectorAll('td');
        if (tds.length < 6) return;
        const fechaDisp = tds[0].textContent.trim();
        const idArt = tds[1].textContent.trim();
        const tipo = tds[2].textContent.trim();
        const costoIndTxt = tds[3].textContent.replace(/[^0-9.,-]/g, '');
        const cantTxt = tds[4].textContent.trim();
        const notasSpan = tds[6].querySelector('[data-note]');
        const notasRaw = notasSpan ? notasSpan.getAttribute('title') || '' : '';

        // Parse fecha DD/MM/AAAA -> YYYY-MM-DD
        let fechaISO = today;
        const m = fechaDisp.match(/(\d{2})\/(\d{2})\/(\d{4})/);
        if (m){
            fechaISO = `${m[3]}-${m[2]}-${m[1]}`;
        }

        if (stFecha) stFecha.value = fechaISO;
        if (stIdArticulo) stIdArticulo.value = idArt;
        if (stTipo) stTipo.value = tipo;
        if (stCostoIndividual) stCostoIndividual.value = costoIndTxt;
        if (stCantidad) stCantidad.value = cantTxt;
        if (stNotas) stNotas.value = notasRaw;
        actualizarCostoTotalStock();
        if (stIdArticulo) stIdArticulo.focus();
    }

    if (stockIngresoForm){
        if (stFecha && !stFecha.value) stFecha.value = today;
        stockIngresoForm.addEventListener('submit', guardarStockIngreso);
        // Delegación de acciones en la tabla
        if (stockIngresoBody){
            stockIngresoBody.addEventListener('click', (ev)=>{
                const btn = ev.target.closest('button[data-action]');
                if (!btn) return;
                const id = Number(btn.getAttribute('data-id') || '0') || 0;
                const action = btn.getAttribute('data-action');
                if (action === 'st-edit'){
                    entrarEdicionStockIngreso(id);
                } else if (action === 'st-delete'){
                    eliminarStockIngreso(id);
                }
            });
        }
    }

    // STOCK ACTUAL
    function getPuntoPedido(id){
        try {
            const raw = localStorage.getItem(`stock:reorder:${id}`);
            if (!raw) return 0;
            const n = parseInt(raw, 10);
            return isNaN(n) ? 0 : n;
        } catch(_){ return 0; }
    }
    function setPuntoPedido(id, val){
        try {
            const n = parseInt(val, 10);
            if (!isNaN(n) && n >= 0){
                localStorage.setItem(`stock:reorder:${id}`, String(n));
            }
        } catch(_){ /*noop*/ }
    }

    function calcularEstadoStock(cantidad, punto){
        const q = Number(cantidad || 0);
        const p = Number(punto || 0);
        if (q <= 0) return 'AGOTADO';
        if (q > 0 && q <= p) return 'NECESARIO';
        return 'OK';
    }

    function estadoToBadge(estado){
        if (estado === 'AGOTADO'){
            return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Agotado</span>';
        }
        if (estado === 'NECESARIO'){
            return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Necesario volver a comprar</span>';
        }
        return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">En stock</span>';
    }

    async function cargarStockActual(){
        if (!stockActualBody) return;
        try {
            const res = await fetch('/api/stock/actual');
            const data = await res.json();
            if (!res.ok || data.success === false){
                stockActualBody.innerHTML = '';
                return;
            }
            const rows = Array.isArray(data.rows) ? data.rows : [];
            stockActualBody.innerHTML = '';

            // Mapear stock recibido por ID de artículo
            const stockPorID = {};
            rows.forEach((r)=>{
                const id = r.id_articulo || '';
                if (!id) return;
                stockPorID[id] = r;
            });

            // Asegurar catálogo cargado si aún no existe
            let idsCatalogo = productosPorID ? Object.keys(productosPorID) : [];
            if (!idsCatalogo.length){
                try {
                    const resCat = await fetch('/api/catalogo');
                    const dataCat = await resCat.json();
                    if (resCat.ok && dataCat && typeof dataCat === 'object'){
                        if (dataCat.productos_por_id && typeof dataCat.productos_por_id === 'object'){
                            window.productosPorID = dataCat.productos_por_id;
                        } else if (dataCat.catalogo && typeof dataCat.catalogo === 'object'){
                            window.productosPorID = dataCat.catalogo;
                        }
                        // Sincronizar variable local
                        productosPorID = window.productosPorID || {};
                        idsCatalogo = Object.keys(productosPorID);
                    }
                } catch(_){/*noop*/}
            }

            if (!idsCatalogo.length && !rows.length){
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="7" class="px-4 py-3 text-sm text-gray-500 text-center">No hay datos de stock aún.</td>';
                stockActualBody.appendChild(tr);
                return;
            }

            const idsOrdenados = idsCatalogo.length ? idsCatalogo.slice().sort() : Object.keys(stockPorID).sort();

            idsOrdenados.forEach((id)=>{
                const infoStock = stockPorID[id] || {};
                const prod = (productosPorID && productosPorID[id]) || {};
                const nombre = prod.nombre || '';
                const cantidad = Number(infoStock.cantidad_total || 0);
                const costoProm = Number(infoStock.costo_promedio || 0);
                const tipo = infoStock.tipo || (prod.tipo || '');
                const punto = getPuntoPedido(id);
                const estado = calcularEstadoStock(cantidad, punto);

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">${id}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700" title="${nombre}">${nombre || '-'}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${tipo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">${cantidad}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">$${formatMoney(costoProm)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">
                        <input type="number" min="0" step="1" value="${punto}" data-pp-id="${id}" class="w-20 px-2 py-1 border border-gray-300 rounded text-right text-sm" />
                    </td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-center">${estadoToBadge(estado)}</td>
                `;
                stockActualBody.appendChild(tr);
            });

            // Delegación para cambios de punto de pedido (escuchar todos los cambios)
            stockActualBody.addEventListener('change', (ev)=>{
                const input = ev.target.closest('input[data-pp-id]');
                if (!input) return;
                const id = input.getAttribute('data-pp-id');
                const val = input.value;
                setPuntoPedido(id, val);
                // Recalcular estado solo de esa fila
                const tr = input.closest('tr');
                if (!tr) return;
                const cantTd = tr.querySelectorAll('td')[3];
                const estadoTd = tr.querySelectorAll('td')[6];
                if (!cantTd || !estadoTd) return;
                const cantidad = parseInt(cantTd.textContent.trim() || '0', 10) || 0;
                const estado = calcularEstadoStock(cantidad, parseInt(val || '0', 10) || 0);
                estadoTd.innerHTML = estadoToBadge(estado);
            });
        } catch(_){
            // noop
        }
    }

    // Exponer renderizadores para el SPA
    try {
        window.renderStockIngreso = async function(){
            // Asegurar fecha por defecto al abrir la vista
            if (stFecha && !stFecha.value) {
                stFecha.value = today;
            }
            // Asegurar combo de IDs cargado cuando se abre la vista
            llenarDropdownStockIDs();
            await cargarStockIngresos();
        };
        window.renderStockActual = async function(){
            // Asegurar que el catálogo está cargado (productosPorID)
            await cargarStockActual();
        };
    } catch(_){/*noop*/}
        console.log('--- Simulación 22:30 locales ---');
        console.log('Sim (local):', sim.toString());
        console.log('Sim (UTC ISO):', sim.toISOString());
        console.log('Sim Hoy (local):', simLocal);
        console.log('Sim Hoy (UTC ISO->date):', simUtc);
        if (simLocal !== simUtc) {
            console.warn('⚠ A las ~22:30, UTC y local pueden divergir. Con lógica local, usamos:', simLocal);
        }
        console.groupEnd();
    }

    const params = new URLSearchParams(window.location.search);
    if (params.has('debugDate')) {
        runDateDiagnostics();
    }

    // ======== STOCK INGRESO & STOCK ACTUAL (nivel principal) =========
    const stockIngresoForm = document.getElementById('stockIngresoForm');
    const stFecha = document.getElementById('st_fecha');
    const stIdArticulo = document.getElementById('st_id_articulo');
    const stTipo = document.getElementById('st_tipo');
    const stPrecioIndividual = document.getElementById('st_precio_individual');
    const stCostoIndividual = document.getElementById('st_costo_individual');
    const stCantidad = document.getElementById('st_cantidad');
    const stCostoTotal = document.getElementById('st_costo_total');
    const stNotas = document.getElementById('st_notas');
    const stockIngresoBody = document.getElementById('stockIngresoBody');
    const stockActualBody = document.getElementById('stockActualBody');

    let stockEditId = null;

    // Fecha por defecto: hoy
    if (stockIngresoForm && stFecha && !stFecha.value) {
        stFecha.value = today;
    }

    // Formateo y cálculo de costo total
    if (stCostoIndividual) attachThousandsFormatter(stCostoIndividual);
    if (stPrecioIndividual) attachThousandsFormatter(stPrecioIndividual);

    function actualizarCostoTotalStock(){
        if (!stCostoIndividual || !stCantidad || !stCostoTotal) return;
        const costo = parseMoneyEs(stCostoIndividual.value || '');
        const cant = parseInt(stCantidad.value || '0', 10) || 0;
        if (!isFinite(costo) || cant <= 0){
            stCostoTotal.value = '';
            return;
        }
        const total = +(costo * cant).toFixed(2);
        let val = total.toFixed(2).replace('.', ',');
        stCostoTotal.value = formatThousandsEs(val);
    }

    if (stCostoIndividual){
        stCostoIndividual.addEventListener('input', actualizarCostoTotalStock);
    }
    if (stCantidad){
        stCantidad.addEventListener('input', actualizarCostoTotalStock);
    }

    function resetStockIngresoForm(){
        if (!stockIngresoForm) return;
        stockIngresoForm.reset();
        stockEditId = null;
        if (stFecha) stFecha.value = today;
    }

    async function cargarStockIngresos(){
        if (!stockIngresoBody) return;
        try {
            const res = await fetch('/api/stock/ingresos');
            const data = await res.json();
            if (!res.ok || data.success === false){
                stockIngresoBody.innerHTML = '';
                return;
            }
            const rows = Array.isArray(data.rows) ? data.rows : [];
            stockIngresoBody.innerHTML = '';
            if (!rows.length){
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="8" class="px-4 py-3 text-sm text-gray-500 text-center">No hay ingresos de stock registrados aún.</td>';
                stockIngresoBody.appendChild(tr);
                return;
            }
            rows.forEach((r) => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                const costoInd = Number(r.costo_individual || 0);
                const cant = Number(r.cantidad || 0);
                const costoTot = Number(r.costo_total || (costoInd * cant));
                const fechaDisp = formatFechaDisplay(r.fecha);
                const notasTxt = r.notas || '';
                tr.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${fechaDisp}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">${r.id_articulo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${r.tipo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">$${formatMoney(costoInd)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">${cant}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right font-semibold text-gray-900">$${formatMoney(costoTot)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-600 max-w-[8rem] md:max-w-xs truncate">
                        ${notasTxt ? `<span class="truncate inline-block cursor-pointer" data-note="${encodeURIComponent(String(notasTxt))}" title="${notasTxt}">${notasTxt}</span>` : ''}
                    </td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right">
                        <button type="button" class="inline-flex items-center justify-center h-8 w-8 rounded hover:bg-blue-50 text-blue-600 hover:text-blue-800 mr-1" data-action="st-edit" data-id="${r.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="inline-flex items-center justify-center h-8 w-8 rounded hover:bg-red-50 text-red-600 hover:text-red-800" data-action="st-delete" data-id="${r.id}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                `;
                stockIngresoBody.appendChild(tr);
            });
        } catch(_){
            // noop
        }
    }

    async function guardarStockIngreso(e){
        if (!stockIngresoForm) return;
        e.preventDefault();
        if (!stFecha || !stIdArticulo || !stCostoIndividual || !stCantidad) return;

        const fecha = stFecha.value || today;
        const id_articulo = (stIdArticulo.value || '').trim().toUpperCase();
        const tipo = (stTipo?.value || '').trim();
        const precio_individual = stPrecioIndividual ? parseMoneyEs(stPrecioIndividual.value || '') : NaN;
        const costo_individual = parseMoneyEs(stCostoIndividual.value || '');
        const cantidad = parseInt(stCantidad.value || '0', 10) || 0;
        const notas = (stNotas?.value || '').trim();

        if (!fecha || !id_articulo || !isFinite(costo_individual) || cantidad <= 0){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('❌ Completa fecha, ID, costo individual y cantidad (>0)', 'error');
            }
            return;
        }

        const costo_total_num = (() => {
            const v = parseMoneyEs(stCostoTotal?.value || '');
            if (isFinite(v) && v > 0) return v;
            return +(costo_individual * cantidad).toFixed(2);
        })();

        const payload = {
            fecha,
            id_articulo,
            tipo,
            precio_individual: isFinite(precio_individual) ? precio_individual : null,
            costo_individual,
            cantidad,
            costo_total: costo_total_num,
            notas,
        };

        try {
            const url = stockEditId != null ? `/api/stock/ingresos/${stockEditId}` : '/api/stock/ingresos';
            const method = stockEditId != null ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || data.success === false){
                throw new Error(data.error || 'Error guardando ingreso de stock');
            }
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('✅ Ingreso de stock guardado', 'success');
            }
            resetStockIngresoForm();
            await cargarStockIngresos();
        } catch(err){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion(`❌ ${err.message || err}`, 'error');
            }
        }
    }

    async function eliminarStockIngreso(id){
        if (!id) return;
        try {
            const confirmado = await confirmarAccionJSON({
                titulo: '¿Eliminar ingreso de stock?',
                mensaje: 'Esta acción eliminará el ingreso de stock de la base de datos. No se puede deshacer.',
                confirmarTexto: 'Eliminar',
                cancelarTexto: 'Cancelar',
            });
            if (!confirmado) return;
            const res = await fetch(`/api/stock/ingresos/${id}`, { method: 'DELETE' });
            const data = await res.json().catch(()=>({}));
            if (!res.ok || data.success === false){
                throw new Error(data.error || 'Error al eliminar ingreso');
            }
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion('✅ Ingreso de stock eliminado', 'success');
            }
            await cargarStockIngresos();
        } catch(err){
            if (typeof mostrarNotificacion === 'function'){
                mostrarNotificacion(`❌ ${err.message || err}`, 'error');
            }
        }
    }

    function entrarEdicionStockIngreso(id){
        if (!stockIngresoBody || !stockIngresoForm) return;
        stockEditId = id;
        const btn = stockIngresoBody.querySelector(`[data-action="st-edit"][data-id="${id}"]`);
        if (!btn) return;
        const tr = btn.closest('tr');
        if (!tr) return;
        const tds = tr.querySelectorAll('td');
        if (tds.length < 6) return;
        const fechaDisp = tds[0].textContent.trim();
        const idArt = tds[1].textContent.trim();
        const tipo = tds[2].textContent.trim();
        const costoIndTxt = tds[3].textContent.replace(/[^0-9.,-]/g, '');
        const cantTxt = tds[4].textContent.trim();
        const notasSpan = tds[6].querySelector('[data-note]');
        const notasRaw = notasSpan ? notasSpan.getAttribute('title') || '' : '';

        let fechaISO = today;
        const m = fechaDisp.match(/(\d{2})\/(\d{2})\/(\d{4})/);
        if (m){
            fechaISO = `${m[3]}-${m[2]}-${m[1]}`;
        }

        if (stFecha) stFecha.value = fechaISO;
        if (stIdArticulo) stIdArticulo.value = idArt;
        if (stTipo) stTipo.value = tipo;
        if (stCostoIndividual) stCostoIndividual.value = costoIndTxt;
        if (stCantidad) stCantidad.value = cantTxt;
        if (stNotas) stNotas.value = notasRaw;
        actualizarCostoTotalStock();
        if (stIdArticulo) stIdArticulo.focus();
    }

    if (stockIngresoForm){
        if (stFecha && !stFecha.value) stFecha.value = today;
        stockIngresoForm.addEventListener('submit', guardarStockIngreso);
        if (stockIngresoBody){
            stockIngresoBody.addEventListener('click', (ev)=>{
                const btn = ev.target.closest('button[data-action]');
                if (!btn) return;
                const id = Number(btn.getAttribute('data-id') || '0') || 0;
                const action = btn.getAttribute('data-action');
                if (action === 'st-edit'){
                    entrarEdicionStockIngreso(id);
                } else if (action === 'st-delete'){
                    eliminarStockIngreso(id);
                }
            });
        }
    }

    // STOCK ACTUAL (nivel principal)
    function getPuntoPedido(id){
        try {
            const raw = localStorage.getItem(`stock:reorder:${id}`);
            if (!raw) return 0;
            const n = parseInt(raw, 10);
            return isNaN(n) ? 0 : n;
        } catch(_){ return 0; }
    }
    function setPuntoPedido(id, val){
        try {
            const n = parseInt(val, 10);
            if (!isNaN(n) && n >= 0){
                localStorage.setItem(`stock:reorder:${id}`, String(n));
            }
        } catch(_){ /*noop*/ }
    }

    function calcularEstadoStock(cantidad, punto){
        const q = Number(cantidad || 0);
        const p = Number(punto || 0);
        if (q <= 0) return 'AGOTADO';
        if (q > 0 && q <= p) return 'NECESARIO';
        return 'OK';
    }

    function estadoToBadge(estado){
        if (estado === 'AGOTADO'){
            return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Agotado</span>';
        }
        if (estado === 'NECESARIO'){
            return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Necesario volver a comprar</span>';
        }
        return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">En stock</span>';
    }

    async function cargarStockActual(){
        if (!stockActualBody) return;
        try {
            const res = await fetch('/api/stock/actual');
            const data = await res.json();
            if (!res.ok || data.success === false){
                stockActualBody.innerHTML = '';
                return;
            }
            const rows = Array.isArray(data.rows) ? data.rows : [];
            stockActualBody.innerHTML = '';
            if (!rows.length){
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="7" class="px-4 py-3 text-sm text-gray-500 text-center">No hay datos de stock aún.</td>';
                stockActualBody.appendChild(tr);
                return;
            }

            rows.forEach((r) => {
                const id = r.id_articulo || '';
                const prod = (productosPorID && productosPorID[id]) || {};
                const nombre = prod.nombre || '';
                const cantidad = Number(r.cantidad_total || 0);
                const costoProm = Number(r.costo_promedio || 0);
                const punto = getPuntoPedido(id);
                const estado = calcularEstadoStock(cantidad, punto);

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">${id}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700" title="${nombre}">${nombre || '-'}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">${r.tipo || ''}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">${cantidad}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">$${formatMoney(costoProm)}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700">
                        <input type="number" min="0" step="1" value="${punto}" data-pp-id="${id}" class="w-20 px-2 py-1 border border-gray-300 rounded text-right text-sm" />
                    </td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-center">${estadoToBadge(estado)}</td>
                `;
                stockActualBody.appendChild(tr);
            });

            stockActualBody.addEventListener('change', (ev)=>{
                const input = ev.target.closest('input[data-pp-id]');
                if (!input) return;
                const id = input.getAttribute('data-pp-id');
                const val = input.value;
                setPuntoPedido(id, val);
                const tr = input.closest('tr');
                if (!tr) return;
                const cantTd = tr.querySelectorAll('td')[3];
                const estadoTd = tr.querySelectorAll('td')[6];
                if (!cantTd || !estadoTd) return;
                const cantidad = parseInt(cantTd.textContent.trim() || '0', 10) || 0;
                const estado = calcularEstadoStock(cantidad, parseInt(val || '0', 10) || 0);
                estadoTd.innerHTML = estadoToBadge(estado);
            }, { once: true });
        } catch(_){
            // noop
        }
    }

    try {
        window.renderStockIngreso = async function(){
            if (stFecha && !stFecha.value) {
                stFecha.value = today;
            }
            llenarDropdownStockIDs();
            await cargarStockIngresos();
        };
        window.renderStockActual = async function(){
            await cargarStockActual();
        };
    } catch(_){/*noop*/}

    // Variables globales
    let productosPorID = {}; 
    let editIndex = null;
    let ventasCache = [];
    let lastAddedIndex = -1; // Para trackear el último elemento agregado
    let rangosPrecios = {}; // Umbrales por grupo: { A: [0, 8000, 11600], AN: [0, 7600, 8000], ... }

    // ======== ELEMENTOS DOM =========
    const form = document.getElementById('ventaForm');
    const inputID = document.getElementById('id'); // oculto, se completa por lógica
    const selectTipoProducto = document.getElementById('tipoProducto');
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
    const idAsignadoInfo = document.getElementById('idAsignadoInfo');
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

    // Helper display de dinero es-AR
    const _fmtMoney = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    function formatMoney(n){ return _fmtMoney.format(Number(n)||0); }

    // === Formato en-input con miles (puntos) y coma decimal ===
    function formatThousandsEs(val) {
        if (val == null) return '';
        let s = String(val);
        // Normalizar: permitir solo dígitos y coma como decimal
        s = s.replace(/[^0-9,]/g, '');
        const parts = s.split(',');
        let ints = parts[0].replace(/\D/g, '');
        let dec = parts.length > 1 ? parts.slice(1).join('').replace(/\D/g, '') : '';
        // Formatear miles en parte entera
        if (ints.length > 3) {
            ints = ints.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        }
        return dec ? `${ints},${dec}` : ints;
    }

    function countDigits(str) {
        let c = 0; for (let i=0;i<str.length;i++){ if (/\d/.test(str[i])) c++; } return c;
    }
    function setCaretByDigitIndex(input, digitIndex) {
        const v = input.value;
        if (!v) { input.setSelectionRange(0,0); return; }
        let seen = 0;
        let pos = v.length;
        for (let i=0;i<v.length;i++){
            if (/\d/.test(v[i])) { seen++; }
            if (seen >= digitIndex) { pos = i+1; break; }
        }
        input.setSelectionRange(pos, pos);
    }
    function attachThousandsFormatter(input){
        if (!input) return;
        input.addEventListener('input', (e)=>{
            const el = e.target;
            const before = String(el.value);
            const caret = el.selectionStart || 0;
            const digitIdx = countDigits(before.slice(0, caret));
            const formatted = formatThousandsEs(before);
            if (formatted !== before){
                el.value = formatted;
                setCaretByDigitIndex(el, digitIdx);
            }
        });
    }

    // Parser para enviar/calcular: "12.345,67" -> 12345.67
    function parseMoneyEs(text){
        if (text == null) return NaN;
        const s = String(text).replace(/\./g, '').replace(',', '.').replace(/[^0-9.\-]/g, '');
        const n = parseFloat(s);
        return isNaN(n) ? NaN : n;
    }

    // Preview formateado (no altera el input)
    const fmtPreview = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    function toPreview(val){
        const n = parseFloat(val);
        if (isNaN(n)) return '';
        return `$ ${fmtPreview.format(n)}`;
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

    function resetForm() {
        if (!form) return;
        try {
            form.reset();
        } catch(_){}
        if (fechaField) {
            fechaField.value = today;
        }
        if (selectTipoProducto) {
            selectTipoProducto.value = '';
        }
        if (inputID) inputID.value = '';
        if (inputNombre) inputNombre.value = '';
        if (inputDescuento) inputDescuento.value = '';
        if (inputPrecioFinal) inputPrecioFinal.value = '';
        if (inputPrecio) inputPrecio.value = '';
        actualizarDisplayID('');
        setHelper('Elegí un tipo y un precio para que el sistema asigne el ID automáticamente.', false);
        isCambio = false;
        precioFinalTouched = false;
        aplicarModo();
    }

    // ======== EVENTOS =========
    form.addEventListener('submit', handleSubmit);
    addBtn.addEventListener('click', handleSubmit);
    resetBtn.addEventListener('click', resetForm);
    exportBtn.addEventListener('click', exportarExcel);

    // Recalcular Precio Final en tiempo real si no fue editado manualmente
    // Formateo en vivo de miles dentro del input (Precio, Precio Final)
    attachThousandsFormatter(inputPrecio);
    if (inputPrecio){
        inputPrecio.addEventListener('input', ()=>{
            precioFinalTouched = false;
            recalcularPrecioFinalSiAuto();
            // Cada vez que cambia el precio, intentar asignar automáticamente el ID
            asignarIDAUTOMATICO();
        });
    }
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
    attachThousandsFormatter(inputPrecioFinal);
    if (inputPrecioFinal){
        inputPrecioFinal.addEventListener('input', ()=>{
            // Solo formatear el propio input; no sincronizar precio base para evitar saltos
            precioFinalTouched = true;
        });
    }

    const egCostoInput = document.getElementById('eg_costo');
    if (egCostoInput){ attachThousandsFormatter(egCostoInput); }

    // ======== ARQUEO DE CAJA (clon MwAccesorios) =========
    const arqueoBtn = document.getElementById('arqueoBtn');
    const arqueoPanel = document.getElementById('arqueoPanel');
    const arqueoApertura = document.getElementById('arqueoApertura');
    const arqueoCierre = document.getElementById('arqueoCierre');
    const arqueoGuardar = document.getElementById('arqueoGuardar');
    const arqueoCerrarPanel = document.getElementById('arqueoCerrarPanel');

    function getArqueoKey(){
        const f = fechaField?.value || new Date().toISOString().split('T')[0];
        return `arqueo:${f}`;
    }
    function cargarArqueo(){
        try {
            const saved = localStorage.getItem(getArqueoKey());
            if (saved){
                const obj = JSON.parse(saved);
                if (arqueoApertura) arqueoApertura.value = obj?.apertura ?? '';
                if (arqueoCierre) arqueoCierre.value = obj?.cierre ?? '';
            } else {
                if (arqueoApertura) arqueoApertura.value = '';
                if (arqueoCierre) arqueoCierre.value = '';
            }
        } catch(_){}
    }
    function updateArqueoCierreState(){
        try {
            const hayPendVentas = Array.isArray(ventasCache) && ventasCache.length > 0;
            const hayPendientes = hayPendVentas;
            if (arqueoCierre){
                arqueoCierre.disabled = !!hayPendientes;
                arqueoCierre.title = hayPendientes ? 'No se puede cargar el Cierre con ventas pendientes sin exportar' : '';
                arqueoCierre.placeholder = hayPendientes ? 'Exporte primero' : '0.00';
                if (hayPendientes) arqueoCierre.value = '';
            }
        } catch(_){}
    }
    if (arqueoBtn){
        arqueoBtn.addEventListener('click', ()=>{
            if (!arqueoPanel) return;
            cargarArqueo();
            arqueoPanel.classList.toggle('hidden');
            updateArqueoCierreState();
        });
    }
    if (arqueoCerrarPanel){
        arqueoCerrarPanel.addEventListener('click', ()=> arqueoPanel?.classList.add('hidden'));
    }
    if (arqueoGuardar){
        arqueoGuardar.addEventListener('click', async ()=>{
            const apertura = parseFloat(arqueoApertura?.value || '');
            const cierre = parseFloat(arqueoCierre?.value || '');

            // Guardar solo apertura si no hay cierre informado aún
            if (!isFinite(cierre)){
                const payload = {
                    apertura: isFinite(apertura) ? +apertura.toFixed(2) : null,
                    cierre: null,
                    savedAt: new Date().toISOString()
                };
                try {
                    localStorage.setItem(getArqueoKey(), JSON.stringify(payload));
                    if (typeof mostrarNotificacion === 'function'){
                        mostrarNotificacion('✅ Apertura guardada', 'success');
                    }
                    arqueoPanel?.classList.add('hidden');
                } catch(e){
                    if (typeof mostrarNotificacion === 'function'){
                        mostrarNotificacion('❌ No se pudo guardar la apertura', 'error');
                    }
                }
                return;
            }

            // Calcular efectivo del día (solo ventas en efectivo) desde HISTORIAL
            const fechaSel = fechaField?.value || new Date().toISOString().split('T')[0];
            let efectivoDia = 0;
            try {
                const res = await fetch('/api/historial');
                const hist = await res.json();
                const ventasDia = Array.isArray(hist[fechaSel]) ? hist[fechaSel] : [];
                efectivoDia = ventasDia
                    .filter(v => (String(v.pago || '')).toLowerCase().includes('efect'))
                    .reduce((sum, v)=>{
                        const precio = Number(v.precio ?? 0);
                        const unidades = Number(v.unidades ?? 0);
                        const total = Number(v.total ?? (precio * unidades));
                        return sum + (isFinite(total) ? total : 0);
                    }, 0);
            } catch(_) { efectivoDia = 0; }

            const esperado = (isFinite(apertura) ? apertura : 0) + efectivoDia;
            const cierreVal = isFinite(cierre) ? cierre : NaN;
            const coincide = isFinite(cierreVal) && Math.abs(cierreVal - esperado) < 0.01;
            if (!coincide){
                const diff = isFinite(cierreVal) ? +(cierreVal - esperado).toFixed(2) : NaN;
                const cierreTxt = isFinite(cierreVal) ? cierreVal.toFixed(2) : 'N/A';
                const esperadoTxt = esperado.toFixed(2);
                const diffTxt = isNaN(diff) ? 'N/A' : Math.abs(diff).toFixed(2);
                const linea = `No coincide el cierre de caja | Cierre declarado $${cierreTxt} | Esperado $${esperadoTxt} | Diferencia $${diffTxt}`;
                if (typeof mostrarNotificacion === 'function'){
                    mostrarNotificacion(`❌ ${linea}`, 'error');
                } else {
                    alert(linea);
                }
                return;
            }

            const payload = {
                apertura: isFinite(apertura) ? +apertura.toFixed(2) : null,
                cierre: isFinite(cierre) ? +cierre.toFixed(2) : null,
                savedAt: new Date().toISOString()
            };
            try {
                localStorage.setItem(getArqueoKey(), JSON.stringify(payload));
                if (typeof mostrarNotificacion === 'function'){
                    mostrarNotificacion('✅ Arqueo guardado', 'success');
                }
                arqueoPanel?.classList.add('hidden');
            } catch(e){
                if (typeof mostrarNotificacion === 'function'){
                    mostrarNotificacion('❌ No se pudo guardar el arqueo', 'error');
                }
            }
        });
    }

    // Helpers para mapa de tipos y asignación automática de ID
    let mapaTipoAGrupo = {};     // "Aritos" -> "A"
    let mapaGrupoAIds = {};      // "A" -> ["A1","A2",...]

    function construirMapeosTipoYGrupos(){
        mapaTipoAGrupo = {};
        mapaGrupoAIds = {};
        if (!productosPorID || typeof productosPorID !== 'object') return;

        const parseId = (id) => {
            const m = String(id).toUpperCase().match(/^([A-Z]+)(\d+)$/);
            return m ? { letters: m[1], number: parseInt(m[2], 10), raw: id } : null;
        };

        const normalizarTipo = (nombreRaw) => {
            if (!nombreRaw) return '';
            let n = String(nombreRaw).trim();
            // Quitar textos como "Rango de precio 1", "Rango de precio 2", etc.
            n = n.replace(/rango\s*de\s*precio\s*\d+/gi, '').trim();
            // Quitar números sueltos al final
            n = n.replace(/\d+$/g, '').trim();
            return n;
        };

        Object.entries(productosPorID).forEach(([id, prod]) => {
            const parsed = parseId(id);
            if (!parsed) return;
            const grupo = parsed.letters;
            const nombreRaw = (prod && prod.nombre) ? String(prod.nombre).trim() : '';
            const tipoBase = normalizarTipo(nombreRaw);
            if (!tipoBase) return;

            mapaGrupoAIds[grupo] = mapaGrupoAIds[grupo] || [];
            mapaGrupoAIds[grupo].push(id);

            // Asociar este tipo base con el grupo (Aritos -> A, Anillos -> AN, etc.)
            if (!(tipoBase in mapaTipoAGrupo)){
                mapaTipoAGrupo[tipoBase] = grupo;
            }
        });

        // Ordenar IDs dentro de cada grupo de forma natural por número
        Object.keys(mapaGrupoAIds).forEach(grupo => {
            mapaGrupoAIds[grupo].sort((a,b)=>{
                const pa = parseInt(String(a).match(/\d+/)?.[0] || '0',10);
                const pb = parseInt(String(b).match(/\d+/)?.[0] || '0',10);
                return pa - pb;
            });
        });
    }

    function llenarSelectTipos(){
        const stTipoSelect = document.getElementById('st_tipo');
        if (!selectTipoProducto && !stTipoSelect) return;

        if (selectTipoProducto) {
            selectTipoProducto.innerHTML = '<option value="">Selecciona un tipo...</option>';
        }
        if (stTipoSelect && stTipoSelect.tagName === 'SELECT') {
            stTipoSelect.innerHTML = '<option value="">Selecciona un tipo...</option>';
        }

        const tipos = Object.keys(mapaTipoAGrupo);
        // Evitar duplicados accidentales y ordenar alfabéticamente
        const tiposOrdenados = [...new Set(tipos)].sort((a,b)=> a.localeCompare(b, 'es'));
        tiposOrdenados.forEach(tipo => {
            if (selectTipoProducto) {
                const opt = document.createElement('option');
                opt.value = tipo;
                opt.textContent = tipo;
                selectTipoProducto.appendChild(opt);
            }
            if (stTipoSelect && stTipoSelect.tagName === 'SELECT') {
                const opt2 = document.createElement('option');
                opt2.value = tipo;
                opt2.textContent = tipo;
                stTipoSelect.appendChild(opt2);
            }
        });
    }

    function actualizarDisplayID(idCalculado){
        if (!idAsignadoInfo) return;
        const txt = idCalculado ? `ID asignado: ${idCalculado}` : 'ID asignado: -';
        idAsignadoInfo.textContent = txt;
    }

    function asignarIDAUTOMATICO(){
        if (!selectTipoProducto || !inputPrecio) return;
        const tipoSel = selectTipoProducto.value || '';
        const grupo = mapaTipoAGrupo[tipoSel];
        if (!grupo){
            inputID.value = '';
            // No tocar el nombre; el usuario puede haber escrito algo manualmente
            setHelper('Elegí un tipo de producto válido.', false);
            actualizarDisplayID('');
            return;
        }
        const idsGrupo = mapaGrupoAIds[grupo] || [];
        const umbralesGrupo = rangosPrecios[grupo];
        const precioNum = parseMoneyEs(inputPrecio.value || '');
        if (!isFinite(precioNum) || precioNum <= 0 || !Array.isArray(umbralesGrupo) || !umbralesGrupo.length || !idsGrupo.length){
            inputID.value = '';
            // Mensaje informativo (no de error): mostrar en verde
            setHelper('Ingresá un precio válido para asignar el ID automáticamente.', true);
            actualizarDisplayID('');
            return;
        }

        // Elegir índice de rango considerando umbrales como mínimos inclusivos (>=)
        let idx = 0;
        for (let i = 0; i < umbralesGrupo.length; i++){
            if (precioNum >= umbralesGrupo[i]){
                idx = i;
            } else {
                break;
            }
        }
        if (idx >= idsGrupo.length) idx = idsGrupo.length - 1;
        const idAsignado = idsGrupo[idx];

        inputID.value = idAsignado || '';
        // Guardar como nombre básico el tipo general seleccionado, para que quede algo en la DB
        if (inputNombre) {
            inputNombre.value = tipoSel || '';
        }

        if (idAsignado){
            setHelper(`✅ Tipo: ${tipoSel} → ID asignado: ${idAsignado}`, true);
        } else {
            setHelper('No se pudo asignar un ID con los datos actuales.', false);
        }
        actualizarDisplayID(idAsignado || '');
    }

    if (selectTipoProducto){
        selectTipoProducto.addEventListener('change', ()=>{
            // Al cambiar tipo, intentamos recalcular ID si ya hay precio
            asignarIDAUTOMATICO();
        });
    }

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

            // Construir mapeos de tipos y grupos e inicializar select de tipos
            construirMapeosTipoYGrupos();
            llenarSelectTipos();
            // Llenar también el combo de IDs de Stock ingreso si existe
            try { llenarDropdownStockIDs(); } catch(_) {}
            
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
        // Ya no se usa para el formulario de ventas principal; se mantiene
        // únicamente por compatibilidad si en el futuro se requiere.
        // El nuevo flujo usa selectTipoProducto + asignarIDAUTOMATICO().
        inputPrecio.placeholder = "Ingresa el precio";
    }

    // ======== STOCK: helpers de catálogo para combo de IDs ========
    const stIdSelect = document.getElementById('st_id_articulo');
    function llenarDropdownStockIDs() {
        // Ya no se usa un combo de IDs en Stock ingreso; el ID se asigna automáticamente
        // en el input st_id_articulo según tipo y precio.
        return;
    }

    function asignarIDStockIngresoAutomatico() {
        if (!stIdSelect || !stTipo || !stPrecioIndividual) return;
        const tipoSelRaw = (stTipo.value || '').trim();
        if (!tipoSelRaw) {
            stIdSelect.value = '';
            return;
        }

        const tipoSel = tipoSelRaw;
        const grupo = mapaTipoAGrupo[tipoSel] || null;
        if (!grupo) {
            stIdSelect.value = '';
            return;
        }

        const idsGrupo = mapaGrupoAIds[grupo] || [];
        const umbralesGrupo = rangosPrecios[grupo];
        const precioNum = parseMoneyEs(stPrecioIndividual.value || '');
        if (!isFinite(precioNum) || precioNum <= 0 || !Array.isArray(umbralesGrupo) || !umbralesGrupo.length || !idsGrupo.length) {
            stIdSelect.value = '';
            return;
        }

        let idx = umbralesGrupo.length - 1;
        for (let i = 0; i < umbralesGrupo.length; i++){
            if (precioNum <= umbralesGrupo[i]){
                idx = i;
                break;
            }
        }
        if (idx >= idsGrupo.length) idx = idsGrupo.length - 1;
        const idAsignado = idsGrupo[idx];
        stIdSelect.value = idAsignado || '';
    }

    if (stTipo) {
        stTipo.addEventListener('change', asignarIDStockIngresoAutomatico);
    }
    if (stPrecioIndividual) {
        stPrecioIndividual.addEventListener('input', asignarIDStockIngresoAutomatico);
    }

    function calcularPlaceholderRango(idSeleccionado) {
        // Función mantenida por compatibilidad; ya no se muestra el rango en el placeholder.
        return '';
    }

    function setHelper(msg, ok) {
        const el = document.getElementById('idHelper');
        el.textContent = msg;
        el.className = `mt-1 text-xs ${ok ? 'text-green-600' : 'text-red-600'}`;
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
                    // Mostrar botón para abrir Google Sheets manualmente
                    if (downloadLink) {
                        downloadLink.href = '/download/sheets';
                        downloadLink.classList.remove('hidden');
                    }
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

        let precio = parseMoneyEs(precioValue);
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
            const pf = parseMoneyEs(inputPrecioFinal.value);
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
        const precioVal = parseMoneyEs(inputPrecio?.value || '');
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
        if (val === '') { inputPrecioFinal.value = ''; return; }
        // Pasar a coma decimal y miles con punto
        const esVal = String(val).replace('.', ',');
        inputPrecioFinal.value = formatThousandsEs(esVal);
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

    // Modal de notas (UI simple con paleta actual)
    const noteModal = document.getElementById('noteModal');
    const noteModalBody = document.getElementById('noteModalBody');
    const noteModalClose = document.getElementById('noteModalClose');
    function openNoteModal(text){
        if (!noteModal || !noteModalBody) return;
        noteModalBody.textContent = text || '';
        noteModal.classList.remove('hidden');
    }
    // Exponer global para que otros scripts (Historial Egresos / SPA) lo usen
    try { window.openNoteModal = openNoteModal; } catch(_) {}
    if (noteModalClose){ noteModalClose.addEventListener('click', ()=> noteModal.classList.add('hidden')); }
    if (noteModal){
        noteModal.addEventListener('click', (e)=>{ if (e.target === noteModal) noteModal.classList.add('hidden'); });
    }
    // Delegación global: cualquier elemento con data-note abre el modal
    document.addEventListener('click', (e)=>{
        const holder = e.target.closest('[data-note]');
        if (!holder) return;
        const note = holder.getAttribute('data-note') || '';
        try {
            const txt = decodeURIComponent(note);
            openNoteModal(txt);
        } catch(_) {
            openNoteModal(note);
        }
    }, { passive: true });

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
            currentDeleteIndex = null;
        });
        
        confirmCancelBtn.addEventListener('click', () => {
            confirmModal.classList.add('hidden');
            currentDeleteIndex = null;
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
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">$${formatMoney(Number(venta.precio))}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${venta.unidades}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">$${formatMoney(Number(venta.total))}</td>
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

        document.getElementById('totalGeneral').textContent = `$${formatMoney(totalGeneral)}`;

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
        document.getElementById('ingresosTotales').textContent = `$${formatMoney(ingresos)}`;
        document.getElementById('promedioVenta').textContent = `$${formatMoney(prom)}`;
    }

    function actualizarContador() {
        const totalVentas = ventasCache.length;
        document.getElementById('totalVentas').textContent = totalVentas;
    }

    // ======== DASHBOARD ========
    const dashState = {
        picker: null,
        start: null,
        end: null,
        charts: {}
    };

    function parseISODate(s){
        try { return new Date(String(s).slice(0,10)); } catch(_) { return null; }
    }

    function inRange(d){
        if (!d) return false;
        if (dashState.start && d < dashState.start) return false;
        if (dashState.end && d > dashState.end) return false;
        return true;
    }

    async function cargarHistorial(){
        const res = await fetch('/api/historial');
        if (!res.ok) return {};
        return await res.json();
    }

    function destroyCharts(){
        Object.values(dashState.charts).forEach(ch => { try { ch && ch.destroy(); } catch(_){} });
        dashState.charts = {};
    }

    function arColor(i){
        // Paleta suave con marrones claros y tonos neutros de la app
        const base = [
            '#dbd4bb', // primary-bg
            '#c7bcb5', // secondary-bg
            '#e6dcc8',
            '#d2c5b1',
            '#bfae98',
            '#a89278',
            '#8f7b5e',
            '#e8e2d3',
            '#d7cdc0',
            '#cabfae'
        ];
        return base[i % base.length];
    }

    // Paleta cualitativa contrastada pero armónica
    function paletteQual(n){
        const qual = [
            '#8B5E34', // brown
            '#C17F59', // light brown
            '#A7C957', // olive green
            '#3E8E7E', // teal
            '#5B8FB9', // desaturated blue
            '#E39A2F', // orange
            '#D96B6B', // soft red
            '#B779E2', // soft purple
            '#84A59D', // sage
            '#F28482', // coral
            '#43AA8B', // green
            '#F6BD60'  // sand
        ];
        const out = [];
        for (let i=0;i<n;i++){ out.push(qual[i % qual.length]); }
        return out;
    }

    // Helpers de colores por grupos (infinito y sin repetición perceptible)
    const baseHueMap = {
        'AN': 120, // green - Anillos
        'A': 210,  // blue  - Aritos
        'C': 30,   // orange/amber - Collar
        'P': 20,   // orange - Pulsera
        'G': 170,  // teal   - Gafas
        'R': 280,  // purple - Ropa
        'N': 40,   // sand   - Neceseres
        'V': 50,   // sand/yellow - Varios
        'OTROS': 0 // red fallback
    };
    function hslToHex(h, s, l){
        s/=100; l/=100; const k=n=> (n+ h/30)%12; const a=s*Math.min(l,1-l);
        const f=n=> l - a*Math.max(-1, Math.min(k(n)-3, Math.min(9-k(n),1)));
        const to = x => Math.round(255*x).toString(16).padStart(2,'0');
        return `#${to(f(0))}${to(f(8))}${to(f(4))}`;
    }
    function groupShades(hue, count, idx){
        // Variar luminosidad y saturación de forma alternada para generar muchas escalas
        const sat = 55 + (idx % 6) * 6;           // 55..85
        const lum = 55 + ((Math.floor(idx/6)) % 6) * 6; // 55..85
        return hslToHex(hue, Math.min(85, sat), Math.min(85, lum));
    }
    function groupedColors(labels, labelToPrefix){
        // contar elementos por prefijo para asignar shades
        const counts = {}; const indices = {};
        labels.forEach(l=>{
            const p = labelToPrefix[l] || 'OTROS';
            counts[p] = (counts[p]||0)+1;
        });
        const colors = [];
        labels.forEach(l=>{
            const p = labelToPrefix[l] || 'OTROS';
            const i = (indices[p]||0); indices[p]=i+1;
            const hue = baseHueMap[p] ?? baseHueMap['OTROS'];
            colors.push(groupShades(hue, counts[p], i));
        });
        return colors;
    }

    function adjustedDPR(){
        try {
            const z = parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
            return (window.devicePixelRatio || 1) / z;
        } catch(_) { return window.devicePixelRatio || 1; }
    }

    async function renderDashboardInner(){
        const elFact = document.getElementById('dashFacturacion');
        const elCant = document.getElementById('dashCantidad');
        const ctxLinea = document.getElementById('chartLinea');
        const ctxPago = document.getElementById('chartPago');
        const ctxTop = document.getElementById('chartTop');
        const ctxBar = document.getElementById('chartBar');
        if (!elFact || !elCant || !ctxLinea || !ctxPago || !ctxTop || !ctxBar) return;

        const hist = await cargarHistorial(); // { 'YYYY-MM-DD': [ventas...] }

        const timeline = []; // {fecha, total}
        const porPago = {};  // pago -> total
        const porProd = {};  // producto (nombre o id) -> total
        const prodPrefix = {}; // label -> prefix derivado del ID
        const porGrupo = {}; // grupo por prefijo de ID -> total
        let facturacion = 0;
        let cantidad = 0;

        Object.entries(hist).forEach(([fecha, arr]) => {
            const d = parseISODate(fecha);
            if (!inRange(d)) return;
            let totDia = 0;
            arr.forEach(v => {
                const total = Number(v.total != null ? v.total : (Number(v.precio||0) * Number(v.unidades||0)));
                const unidades = Number(v.unidades||0);
                facturacion += total;
                cantidad += Math.max(0, unidades); // unidades vendidas (evitar negativos de cambios)
                totDia += total;
                const pagoKey = String(v.pago||'Otro');
                porPago[pagoKey] = (porPago[pagoKey]||0) + total;
                const prodKey = String(v.nombre||v.id||'Producto');
                porProd[prodKey] = (porProd[prodKey]||0) + total;
                const id = String(v.id||'').toUpperCase();
                const m2 = id.match(/^([A-Z]+)/);
                const pref2 = m2 ? m2[1] : 'OTROS';
                prodPrefix[prodKey] = pref2;
                // Agrupar por prefijo de ID (letras antes de dígitos)
                const m = id.match(/^([A-Z]+)/);
                const pref = m ? m[1] : 'OTROS';
                // Mapeo a nombres amigables
                const map = {
                    'A': 'Aritos',
                    'AN': 'Anillos',
                    'C': 'Collar',
                    'P': 'Pulsera',
                    'G': 'Gafas',
                    'N': 'Neceseres',
                    'R': 'Ropa',
                    'V': 'Varios'
                };
                const labelGrupo = map[pref] || pref;
                porGrupo[labelGrupo] = (porGrupo[labelGrupo]||0) + total;
            });
            timeline.push({ fecha, total: totDia });
        });

        timeline.sort((a,b)=> a.fecha < b.fecha ? -1 : 1);
        elFact.textContent = `$ ${formatMoney(facturacion)}`;
        elCant.textContent = `${cantidad}`;

        destroyCharts();

        // Line chart ganancias por día
        // Registrar plugin crosshair una sola vez
        if (!window.__chartCrosshairRegistered) {
            try {
                Chart.register({
                    id: 'crosshair',
                    afterDatasetsDraw(chart, args, opts){
                        const tooltip = chart.tooltip;
                        if (!tooltip || typeof tooltip.getActiveElements !== 'function') return;
                        const active = tooltip.getActiveElements();
                        if (!active || !active.length) return;
                        const { chartArea, ctx } = chart;
                        const x = active[0].element?.x;
                        if (typeof x !== 'number') return;
                        ctx.save();
                        ctx.strokeStyle = (opts && opts.color) || 'rgba(90,83,67,0.35)';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(x, chartArea.top);
                        ctx.lineTo(x, chartArea.bottom);
                        ctx.stroke();
                        ctx.restore();
                    }
                });
                window.__chartCrosshairRegistered = true;
            } catch(_) { /* noop */ }
        }

        dashState.charts.linea = new Chart(ctxLinea, {
            type: 'line',
            data: {
                labels: timeline.map(x=>x.fecha),
                datasets: [{
                    label: 'Ingresos',
                    data: timeline.map(x=>+x.total.toFixed(2)),
                    borderColor: '#b2956b',
                    backgroundColor: 'rgba(210, 197, 177, 0.35)',
                    tension: 0.25,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHitRadius: 16,
                    pointHoverBackgroundColor: '#5a5343',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                devicePixelRatio: adjustedDPR(),
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        displayColors: false,
                        callbacks: {
                            title: (items)=> items?.[0]?.label ? new Date(items[0].label+ 'T00:00:00').toLocaleDateString('es-AR') : '',
                            label: (item)=> `Ingresos: $ ${formatMoney(item.parsed.y||0)}`
                        }
                    },
                    crosshair: { color: 'rgba(90,83,67,0.35)' }
                },
                scales: { y: { ticks: { callback: v => v.toLocaleString('es-AR') } } }
            }
        });

        // Doughnut por forma de pago
        const pagoLabels = Object.keys(porPago);
        const pagoData = pagoLabels.map(k=>+porPago[k].toFixed(2));
        const pagoColors = paletteQual(pagoLabels.length);
        dashState.charts.pago = new Chart(ctxPago, {
            type: 'doughnut',
            data: { labels: pagoLabels, datasets: [{ data: pagoData, backgroundColor: pagoColors, borderColor: '#ffffff', borderWidth: 1 }] },
            options: { devicePixelRatio: adjustedDPR(), plugins: { legend: { position: 'right' } } }
        });

        // Top productos (sin límite: mostrar todos)
        const prodEntries = Object.entries(porProd).sort((a,b)=>b[1]-a[1]);
        const prodLabels = prodEntries.map(x=>x[0]);
        const prodData = prodEntries.map(x=>+x[1].toFixed(2));
        // Colores: agrupar por prefijo con escalas dentro de cada grupo
        const prodColors = groupedColors(prodLabels, prodPrefix);
        dashState.charts.top = new Chart(ctxTop, {
            type: 'doughnut',
            data: { labels: prodLabels, datasets: [{ data: prodData, backgroundColor: prodColors, borderColor: '#ffffff', borderWidth: 1 }] },
            options: { devicePixelRatio: adjustedDPR(), plugins: { legend: { position: 'right' } } }
        });

        // Barras por tipo (grupo por prefijo de ID)
        const grupoEntries = Object.entries(porGrupo).sort((a,b)=>b[1]-a[1]);
        const grupoLabels = grupoEntries.map(x=>x[0]);
        const grupoData = grupoEntries.map(x=>+x[1].toFixed(2));
        const grupoColors = paletteQual(grupoLabels.length);
        dashState.charts.bar = new Chart(ctxBar, {
            type: 'bar',
            data: { labels: grupoLabels, datasets: [{ label: 'Ventas $', data: grupoData, backgroundColor: grupoColors, borderColor: grupoColors.map(c=>c), borderWidth: 1 }] },
            options: { devicePixelRatio: adjustedDPR(), plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: v => v.toLocaleString('es-AR') } } } }
        });
    }

    function initDashPicker(){
        const btn = document.getElementById('dashRangeBtn');
        const btnReset = document.getElementById('dashResetBtn');
        if (!btn || dashState.picker) return;
        try {
            dashState.picker = new Litepicker({
                element: btn,
                singleMode: false,
                numberOfMonths: 2,
                numberOfColumns: 2,
                autoApply: true,
                format: 'YYYY-MM-DD',
                tooltipText: { one: 'día', other: 'días' },
                dropdowns: { minYear: 2024, maxYear: new Date().getFullYear() + 1, months: true, years: true }
            });
            dashState.picker.on('selected', (date1, date2) => {
                dashState.start = date1 ? new Date(date1.format('YYYY-MM-DD')) : null;
                dashState.end = date2 ? new Date(date2.format('YYYY-MM-DD')) : null;
                btn.textContent = date1 && date2 ? `${date1.format('YYYY-MM-DD')} a ${date2.format('YYYY-MM-DD')}` : 'Selecciona un periodo';
                renderDashboardInner();
            });
            // Establecer selección inicial si ya tenemos un rango
            if (dashState.start && dashState.end) {
                try { dashState.picker.setDateRange(dashState.start, dashState.end); } catch(_) {}
                btn.textContent = `${dashState.start.toISOString().slice(0,10)} a ${dashState.end.toISOString().slice(0,10)}`;
            }
        } catch(_) { /* noop */ }
        if (btnReset){
            btnReset.addEventListener('click', ()=>{
                if (dashState.picker) dashState.picker.clearSelection();
                dashState.start = null; dashState.end = null;
                btn.textContent = 'Selecciona un periodo';
                renderDashboardInner();
            });
        }
    }

    // Exponer función para la SPA
    window.renderDashboard = function(){
        // Rango por defecto: último mes
        if (!dashState.start || !dashState.end) {
            const today = new Date();
            const end = new Date(today.getFullYear(), today.getMonth(), today.getDate());
            const start = new Date(end);
            start.setMonth(start.getMonth() - 1);
            dashState.start = start;
            dashState.end = end;
        }
        initDashPicker();
        const btn = document.getElementById('dashRangeBtn');
        if (btn) btn.textContent = `${dashState.start.toISOString().slice(0,10)} a ${dashState.end.toISOString().slice(0,10)}`;
        renderDashboardInner();
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
