from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from services.sales_service import listar_ventas, agregar_venta, actualizar_venta, eliminar_venta, obtener_estado_sheets, limpiar_ventas, cargar_ventas_desde_historial
from services.expenses_service import enviar_egresos, estado_egresos, listar_egresos
from services.history_service import (
    leer_historial,
    agregar_ventas_a_historial,
    eliminar_historial_por_fecha_idx,
    actualizar_historial_por_fecha_idx,
)
from services.catalog_service import obtener_catalogo, obtener_rangos
from config import GOOGLE_SHEETS_CONFIG, GOOGLE_APPS_SCRIPT
try:
    from services.db import init_db
except Exception:
    init_db = None

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize DB eagerly (Flask 3 ya no expone before_first_request)
try:
    if init_db:
        ok = init_db()
        if ok:
            print("🗄️ Base de datos inicializada (Postgres)")
except Exception as e:
    print(f"⚠️ No se pudo inicializar la base de datos: {e}")

# User class for authentication (muy simple, con roles)
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    @property
    def is_admin(self):
        return self.role == "admin"


def admin_required(f):
    """Decorator sencillo para restringir vistas a usuarios admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


# Hardcoded users (en producción conviene DB)
# Usuario mili (admin): acceso total
#   usuario: "mili nicosia"
#   contraseña: "milostore1618"
# Usuario vendedoras (seller): solo ventas e historial de ventas
#   usuario: "milo store"
#   contraseña: "milostore2022"
USERS = {
    "mili nicosia": {
        "password": "milostore1618",
        "id": 1,
        "role": "admin",
    },
    "milo store": {
        "password": "milostore2022",
        "id": 2,
        "role": "seller",
    },
}

@login_manager.user_loader
def load_user(user_id):
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    for username, user_data in USERS.items():
        if user_data.get("id") == uid:
            return User(user_data["id"], username=username, role=user_data.get("role", "seller"))
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == "POST":
        identifier = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        # Buscar usuario por nombre (case-insensitive)
        matched_username = None
        for uname in USERS.keys():
            if uname.lower() == identifier:
                matched_username = uname
                break

        if matched_username and USERS[matched_username]["password"] == password:
            data = USERS[matched_username]
            user = User(data["id"], username=matched_username, role=data.get("role", "seller"))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'error')
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

# Nueva vista: Historial de Ventas
@app.route("/historial")
@login_required
def historial():
    # Redirigir a la vista SPA en el index con la pestaña historial activa
    return redirect(url_for('index', view='historial'))

# Nueva vista: Egresos (solo admin)
@app.route("/egresos")
@login_required
@admin_required
def egresos_view():
    # Redirigir a la vista SPA en el index con la pestaña egresos activa
    return redirect(url_for('index', view='egresos'))

# Nueva vista: Historial de Egresos (SPA, solo admin)
@app.route("/egresos/historial")
@login_required
@admin_required
def egresos_historial_view():
    return redirect(url_for('index', view='historial_egresos'))

# API de ventas (memoria)
@app.route("/api/ventas", methods=["GET"])
def api_listar_ventas():
    return jsonify(listar_ventas())

# API de historial agrupado por fecha (persistente)
@app.route("/api/historial", methods=["GET"])
def api_historial():
    return jsonify(leer_historial())

@app.route("/api/ventas", methods=["POST"])
def api_agregar_venta():
    data = request.get_json(force=True, silent=True) or {}
    try:
        agregar_venta(data)
        return jsonify({"message": "Venta agregada"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/ventas/<int:index>", methods=["PUT"])
def api_actualizar_venta(index: int):
    data = request.get_json(force=True, silent=True) or {}
    try:
        actualizar_venta(index, data)
        return jsonify({"message": "Venta actualizada"}), 200
    except IndexError:
        return jsonify({"error": "Índice fuera de rango"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/ventas/<int:index>", methods=["DELETE"])
def api_eliminar_venta(index: int):
    try:
        eliminar_venta(index)
        return jsonify({"message": "Venta eliminada"}), 200
    except IndexError:
        return jsonify({"error": "Índice fuera de rango"}), 404

# Eliminar por fecha e índice relativo dentro del día (persistente)
@app.route("/api/historial/<fecha>/<int:idx>", methods=["DELETE"])
def api_eliminar_historial_por_fecha(fecha: str, idx: int):
    if idx < 0:
        return jsonify({"success": False, "error": "Índice inválido"}), 400
    ok = eliminar_historial_por_fecha_idx(fecha, idx)
    if not ok:
        return jsonify({"success": False, "error": "No se encontró elemento para esa fecha/índice"}), 404
    return jsonify({"success": True}), 200


# Actualizar por fecha e índice relativo dentro del día (persistente)
@app.route("/api/historial/<fecha>/<int:idx>", methods=["PUT"])
def api_actualizar_historial_por_fecha(fecha: str, idx: int):
    if idx < 0:
        return jsonify({"success": False, "error": "Índice inválido"}), 400
    data = request.get_json(force=True, silent=True) or {}
    ok = actualizar_historial_por_fecha_idx(fecha, idx, data)
    if not ok:
        return jsonify({"success": False, "error": "No se encontró elemento para esa fecha/índice"}), 404
    return jsonify({"success": True}), 200

@app.route("/api/ventas", methods=["DELETE"])
def api_eliminar_todas_las_ventas():
    """Vacía todas las ventas en memoria (confirmado desde el front)"""
    try:
        limpiar_ventas()
        return jsonify({"message": "Todas las ventas fueron eliminadas"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Exportar a Google Sheets
@app.route("/api/exportar", methods=["POST"])
def api_exportar():
    """Exporta TODAS las ventas acumuladas en memoria a Google Sheets"""
    from services.sales_service import exportar_todas_las_ventas_a_sheets
    resultado = exportar_todas_las_ventas_a_sheets()
    # Si la exportación fue exitosa, persistimos SOLO lo realmente exportado (con costo_unitario calculado)
    try:
        if resultado and resultado.get("success"):
            # Preferir la lista enriquecida que devuelve sales_service (incluye costo_unitario)
            ventas_ok = resultado.get("ventas_exportadas_items") or []

            # Fallback de compatibilidad: si por algún motivo no vino la lista enriquecida,
            # reconstruirla desde las ventas en memoria usando los índices exitosos.
            if not ventas_ok:
                ventas_actuales = listar_ventas()
                indices = resultado.get("indices_exitosos") or list(range(len(ventas_actuales)))
                ventas_ok = [ventas_actuales[i] for i in indices if 0 <= i < len(ventas_actuales)]

            if ventas_ok:
                agregar_ventas_a_historial(ventas_ok)

            # Limpiar ventas en memoria para empezar de nuevo
            limpiar_ventas()
    except Exception:
        # No romper la respuesta original del endpoint
        pass
    return jsonify(resultado), 200


def _generate_remito_pdf(venta: dict) -> BytesIO:
    """Genera un PDF de remito simple en memoria a partir de una venta del historial.

    Campos usados:
      - fecha: YYYY-MM-DD
      - id: código de producto
      - nombre: nombre del producto
      - precio: precio unitario (ya final)
      - unidades: cantidad
      - total: subtotal (precio * unidades)
      - pago: condición de venta
    """
    fecha_raw = str(venta.get("fecha") or "")[:10]
    try:
        y, m, d = fecha_raw.split("-")
        fecha_display = f"{d}/{m}/{y}"
    except Exception:
        fecha_display = fecha_raw

    codigo = str(venta.get("id") or "")
    nombre = str(venta.get("nombre") or "")
    precio = float(venta.get("precio") or 0)
    unidades = int(venta.get("unidades") or 0)
    subtotal = float(venta.get("total") or (precio * unidades))
    forma_pago = str(venta.get("pago") or "")
    concepto = "Venta de productos"

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    y = height - margin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "Remito - Milo Store")
    y -= 12 * mm

    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Fecha del comprobante: {fecha_display}")
    y -= 6 * mm
    c.drawString(margin, y, f"Concepto: {concepto}")
    y -= 6 * mm
    if forma_pago:
        c.drawString(margin, y, f"Condición de venta: {forma_pago}")
        y -= 10 * mm
    else:
        y -= 4 * mm

    # Encabezado de la tabla
    c.setFont("Helvetica-Bold", 10)
    x_codigo = margin
    x_prod = x_codigo + 30 * mm
    x_cant = width - margin - 60 * mm
    x_precio = width - margin - 40 * mm
    x_bonif = width - margin - 25 * mm
    x_subt = width - margin

    c.drawString(x_codigo, y, "Código")
    c.drawString(x_prod, y, "Producto")
    c.drawRightString(x_cant, y, "Cant")
    c.drawRightString(x_precio, y, "P. Unit")
    c.drawRightString(x_bonif, y, "Bonif")
    c.drawRightString(x_subt, y, "Subtotal")
    y -= 5 * mm
    c.line(margin, y, width - margin, y)
    y -= 6 * mm

    # Fila única
    c.setFont("Helvetica", 10)
    c.drawString(x_codigo, y, codigo)
    c.drawString(x_prod, y, nombre[:60])
    c.drawRightString(x_cant, y, str(unidades))
    c.drawRightString(x_precio, y, f"${precio:.2f}")
    # Bonificación: por ahora 0 / vacío porque no se guarda descuento explícito
    c.drawRightString(x_bonif, y, "-")
    c.drawRightString(x_subt, y, f"${subtotal:.2f}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(x_subt, y, f"TOTAL: ${subtotal:.2f}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


@app.route("/remito/<fecha>/<int:idx>")
@login_required
def descargar_remito(fecha: str, idx: int):
    """Descarga un remito PDF generado a partir de una venta del historial.

    fecha: string YYYY-MM-DD (clave del historial)
    idx: índice de la venta dentro de esa fecha
    """
    try:
        hist = leer_historial() or {}
    except Exception:
        hist = {}

    ventas_dia = hist.get(fecha)
    if not isinstance(ventas_dia, list) or idx < 0 or idx >= len(ventas_dia):
        abort(404)

    venta = ventas_dia[idx]
    pdf_buf = _generate_remito_pdf(venta)
    filename = f"Remito-{fecha}-{idx+1}.pdf"
    return send_file(pdf_buf, mimetype="application/pdf", as_attachment=True, download_name=filename)

# Diagnóstico: exporta una fila de prueba vía Apps Script / Sheets
@app.route("/api/diagnostico", methods=["GET"])
@login_required
def api_diagnostico():
    """Endpoint de diagnóstico del sistema"""
    try:
        ventas_memoria = len(listar_ventas())
        historial = leer_historial()
        ventas_historial = sum(len(ventas) for ventas in historial.values())
        fechas_historial = len(historial.keys())
        
        # Calcular tamaño aproximado del archivo
        import os
        hist_path = Path(__file__).resolve().parent / 'data' / 'historial.json'
        tamaño_archivo = os.path.getsize(hist_path) if hist_path.exists() else 0
        
        return jsonify({
            "ventas_en_memoria": ventas_memoria,
            "ventas_en_historial": ventas_historial,
            "fechas_en_historial": fechas_historial,
            "tamaño_archivo_kb": round(tamaño_archivo / 1024, 2),
            "estado": "✅ Sistema funcionando correctamente",
            "recomendacion": "Mantener sistema actual" if ventas_historial < 50000 else "Considerar migración a base de datos"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Diagnóstico: exporta una fila de prueba vía Apps Script / Sheets
@app.route("/api/exportar_prueba", methods=["POST"])
def api_exportar_prueba():
    try:
        from services.sales_service import _get_sheets_writer
        writer = _get_sheets_writer()
        if writer is None:
            return jsonify({"success": False, "error": "NO_WRITER"}), 500
        from datetime import datetime
        venta_demo = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "id": "TEST001",
            "nombre": "Prueba Exportación",
            "precio": 1234.56,
            "unidades": 2,
            "pago": "Efectivo",
            "notas": "Fila de prueba"
        }
        res = writer.agregar_multiples_ventas_a_sheets([venta_demo])
        return jsonify({"success": True, "resultado": res}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Stock: Ingresos y Stock Actual (DB) =====
@app.route("/api/stock/ingresos", methods=["GET"])
def api_stock_ingresos_list():
    """Lista ingresos de stock desde la DB.

    Devuelve una lista de objetos con los campos básicos para poblar la
    tabla de "Stock Ingreso" (historial editable) en el front.
    """
    try:
        limit = int(request.args.get("limit", "500"))
        try:
            from services.db import get_session
            from services.models import StockIngreso
        except (ImportError, ModuleNotFoundError):
            return jsonify({"success": True, "rows": []}), 200

        session = get_session()
        try:
            query = session.query(StockIngreso).order_by(StockIngreso.fecha.desc(), StockIngreso.id.desc())
            ingresos = query.limit(limit).all()
        finally:
            session.close()

        rows = []
        for ing in ingresos:
            fecha_str = ing.fecha.isoformat() if getattr(ing, "fecha", None) else ""
            rows.append({
                "id": int(getattr(ing, "id", 0) or 0),
                "fecha": fecha_str,
                "id_articulo": getattr(ing, "id_articulo", "") or "",
                "tipo": getattr(ing, "tipo", "") or "",
                "precio_individual": float(getattr(ing, "precio_individual", 0) or 0),
                "costo_individual": float(getattr(ing, "costo_individual", 0) or 0),
                "cantidad": int(getattr(ing, "cantidad", 0) or 0),
                "costo_total": float(getattr(ing, "costo_total", 0) or 0),
                "notas": getattr(ing, "notas", "") or "",
            })
        return jsonify({"success": True, "rows": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stock/ingresos", methods=["POST"])
def api_stock_ingresos_create():
    """Crea uno o varios ingresos de stock.

    Acepta:
      - un solo objeto ingreso
      - una lista de objetos
      - { "ingresos": [...] }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}

        if isinstance(data, list):
            ingresos = data
        else:
            ingresos = data.get("ingresos") if isinstance(data.get("ingresos"), list) else [data]

        from datetime import datetime
        from services.db import get_session
        from services.models import StockIngreso

        session = get_session()
        try:
            created = 0
            for item in ingresos:
                if not isinstance(item, dict):
                    continue

                fecha_raw = (item.get("fecha") or "").strip()
                if fecha_raw:
                    try:
                        fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
                    except ValueError:
                        # Si viene en otro formato, intentar parseo genérico
                        try:
                            fecha = datetime.fromisoformat(fecha_raw).date()
                        except Exception:
                            fecha = None
                else:
                    fecha = None

                if not fecha:
                    # Si no hay fecha válida, saltar este ingreso
                    continue

                id_articulo = (item.get("id_articulo") or "").strip()
                tipo = (item.get("tipo") or "").strip()

                # Campos numéricos
                def _to_number(val, default=0):
                    if val is None:
                        return default
                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        return default

                precio_individual = _to_number(item.get("precio_individual"), 0)
                costo_individual = _to_number(item.get("costo_individual"), 0)
                cantidad = int(_to_number(item.get("cantidad"), 0))

                costo_total = item.get("costo_total")
                costo_total = _to_number(costo_total, None)
                if costo_total is None:
                    costo_total = costo_individual * cantidad

                notas = (item.get("notas") or "").strip() or None

                if not id_articulo or cantidad <= 0 or costo_individual < 0:
                    # Validación mínima; si algo clave falta, se ignora ese item
                    continue

                ingreso = StockIngreso(
                    fecha=fecha,
                    id_articulo=id_articulo,
                    tipo=tipo,
                    precio_individual=precio_individual,
                    costo_individual=costo_individual,
                    cantidad=cantidad,
                    costo_total=costo_total,
                    notas=notas,
                )
                session.add(ingreso)
                created += 1

            if created == 0:
                session.rollback()
                return jsonify({"success": False, "error": "NO_ROWS"}), 400

            session.commit()
            return jsonify({"success": True, "rows_inserted": created}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stock/ingresos/<int:ingreso_id>", methods=["PUT"])
def api_stock_ingresos_update(ingreso_id: int):
    """Actualiza un ingreso de stock existente por ID."""
    try:
        data = request.get_json(force=True, silent=True) or {}

        from datetime import datetime
        from services.db import get_session
        from services.models import StockIngreso

        session = get_session()
        try:
            ingreso = session.query(StockIngreso).get(ingreso_id)
            if not ingreso:
                return jsonify({"success": False, "error": "NOT_FOUND"}), 404

            # Actualizar campos si vienen en el payload
            if "fecha" in data:
                fecha_raw = (data.get("fecha") or "").strip()
                if fecha_raw:
                    try:
                        ingreso.fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
                    except ValueError:
                        try:
                            ingreso.fecha = datetime.fromisoformat(fecha_raw).date()
                        except Exception:
                            pass

            if "id_articulo" in data:
                ingreso.id_articulo = (data.get("id_articulo") or "").strip()

            if "tipo" in data:
                ingreso.tipo = (data.get("tipo") or "").strip()

            def _to_number(val, default=None):
                if val is None:
                    return default
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default

            changed_qty_or_cost = False
            if "precio_individual" in data:
                val = _to_number(data.get("precio_individual"), None)
                if val is not None:
                    ingreso.precio_individual = val

            if "costo_individual" in data:
                val = _to_number(data.get("costo_individual"), None)
                if val is not None:
                    ingreso.costo_individual = val
                    changed_qty_or_cost = True

            if "cantidad" in data:
                val = _to_number(data.get("cantidad"), None)
                if val is not None:
                    ingreso.cantidad = int(val)
                    changed_qty_or_cost = True

            if "costo_total" in data:
                val = _to_number(data.get("costo_total"), None)
                if val is not None:
                    ingreso.costo_total = val
                    changed_qty_or_cost = False

            # Si se modificaron cantidad o costo_individual y no vino costo_total explícito, recalcular
            if changed_qty_or_cost:
                try:
                    ingreso.costo_total = (ingreso.costo_individual or 0) * (ingreso.cantidad or 0)
                except Exception:
                    pass

            if "notas" in data:
                notas = (data.get("notas") or "").strip()
                ingreso.notas = notas or None

            session.commit()
            return jsonify({"success": True}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stock/ingresos/<int:ingreso_id>", methods=["DELETE"])
def api_stock_ingresos_delete(ingreso_id: int):
    """Elimina un ingreso de stock por ID."""
    try:
        from services.db import get_session
        from services.models import StockIngreso

        session = get_session()
        try:
            ingreso = session.query(StockIngreso).get(ingreso_id)
            if not ingreso:
                return jsonify({"success": False, "error": "NOT_FOUND"}), 404

            session.delete(ingreso)
            session.commit()
            return jsonify({"success": True}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            session.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stock/actual", methods=["GET"])
def api_stock_actual():
    """Devuelve el stock actual consolidado por ID de artículo.

    Calcula stock neto como:
      ingresos (StockIngreso) - ventas (Venta)

    Y costo promedio como costo_neto / cantidad_total si cantidad_total > 0.
    """
    try:
        try:
            from sqlalchemy import select, func
            from services.db import get_session
            from services.models import StockIngreso, Venta
            from services.catalog_service import obtener_catalogo
        except (ImportError, ModuleNotFoundError):
            return jsonify({"success": True, "rows": []}), 200

        # Catálogo completo: todos los IDs que queremos mostrar aunque no tengan stock
        try:
            catalogo = obtener_catalogo() or {}
        except Exception:
            catalogo = {}

        session = get_session()
        try:
            # Ingresos de stock por artículo
            stmt_ing = (
                select(
                    StockIngreso.id_articulo.label("id"),
                    func.max(StockIngreso.tipo).label("tipo"),
                    func.sum(StockIngreso.cantidad).label("cant_ingresos"),
                    func.sum(StockIngreso.costo_total).label("costo_ingresos"),
                )
                .group_by(StockIngreso.id_articulo)
            )
            ingresos = {row.id: row for row in session.execute(stmt_ing)}

            # Ventas por artículo (solo "nuevas": aquellas con costo_unitario no nulo)
            stmt_ven = (
                select(
                    Venta.producto_id.label("id"),
                    func.sum(Venta.unidades).label("cant_ventas"),
                    func.sum(func.coalesce(Venta.costo_unitario, 0) * Venta.unidades).label("costo_vendido"),
                )
                .where(Venta.costo_unitario.isnot(None))
                .group_by(Venta.producto_id)
            )
            ventas = {row.id: row for row in session.execute(stmt_ven)}
        finally:
            session.close()

        # Unir IDs del catálogo + ingresos + ventas
        ids_catalogo = set((catalogo or {}).keys())
        ids = ids_catalogo | set(ingresos.keys()) | set(ventas.keys())

        rows = []
        for id_articulo in sorted(ids):
            ing = ingresos.get(id_articulo)
            ven = ventas.get(id_articulo)

            tipo_max = getattr(ing, "tipo", "") if ing is not None else ""
            cant_ing = int(getattr(ing, "cant_ingresos", 0) or 0)
            costo_ing = float(getattr(ing, "costo_ingresos", 0) or 0)

            cant_ven = int(getattr(ven, "cant_ventas", 0) or 0)
            costo_ven = float(getattr(ven, "costo_vendido", 0) or 0)

            cantidad_total = cant_ing - cant_ven
            if cantidad_total < 0:
                cantidad_total = 0

            costo_neto = costo_ing - costo_ven
            if cantidad_total > 0 and costo_neto > 0:
                costo_promedio = float(costo_neto / cantidad_total)
            else:
                costo_promedio = 0.0

            rows.append({
                "id_articulo": id_articulo or "",
                "tipo": tipo_max or "",
                "cantidad_total": int(cantidad_total),
                "costo_total": float(max(costo_neto, 0)),
                "costo_promedio": float(costo_promedio),
            })

        return jsonify({"success": True, "rows": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== Egresos: hard delete en DB =====
@app.route("/api/egresos/<int:egreso_id>", methods=["DELETE"])
def api_egresos_delete(egreso_id: int):
    try:
        try:
            from services.db import get_session
            from services.egresos_repository import eliminar_egreso_db
        except (ImportError, ModuleNotFoundError):
            return jsonify({"success": False, "error": "DB no configurada"}), 500

        session = get_session()
        try:
            ok = eliminar_egreso_db(session, egreso_id)
            if not ok:
                session.rollback()
                return jsonify({"success": False, "error": "EGRESO_NO_ENCONTRADO"}), 404
            session.commit()
            return jsonify({"success": True}), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Historial de Egresos desde DB (formato simple de filas)
@app.route("/api/egresos/historial_db", methods=["GET"])
def api_egresos_historial_db():
    try:
        limit = int(request.args.get('limit', '200'))
        try:
            from services.db import get_session
            from services.egresos_repository import listar_egresos_db
        except (ImportError, ModuleNotFoundError):
            # Sin SQLAlchemy/DB configurada: devolver vacío para que el front muestre estado vacío
            return jsonify({"success": True, "rows": []}), 200

        session = get_session()
        try:
            egresos = listar_egresos_db(session, limit=limit)
        finally:
            session.close()
        # Responder en formato compatible con el front: rows = [ [fecha, motivo, costo, tipo, pago, observaciones, id], ... ]
        rows = []
        for e in egresos:
            fecha_str = e.fecha.isoformat() if getattr(e, 'fecha', None) else ''
            rows.append([
                fecha_str,
                getattr(e, 'motivo', '') or '',
                float(getattr(e, 'costo', 0) or 0),
                getattr(e, 'tipo', '') or '',
                getattr(e, 'pago', '') or '',
                getattr(e, 'observaciones', '') or '',
                int(getattr(e, 'id', 0) or 0),
            ])
        return jsonify({"success": True, "rows": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Redirigir a Google Sheets
@app.route("/download/sheets", methods=["GET"])
def download_sheets():
    # Redirigir a la hoja específica de Google Sheets
    return redirect("https://docs.google.com/spreadsheets/d/1QG8a6yHmad5sFpVcKhC3l0oEAcjJftmHV2KAF56bkkM/edit?gid=561161202#gid=561161202")

@app.route("/api/catalogo", methods=["GET"])
def api_catalogo():
    try:
        return jsonify(obtener_catalogo())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/rangos", methods=["GET"])
def api_rangos():
    try:
        return jsonify({"rangos": obtener_rangos()})
    except Exception as e:
        return jsonify({"rangos": {}}), 200

@app.route("/api/sheets/status", methods=["GET"])
def api_sheets_status():
    try:
        return jsonify(obtener_estado_sheets())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Egresos (Apps Script) =====
@app.route("/api/egresos", methods=["POST"])
def api_egresos_post():
    try:
        data = request.get_json(force=True, silent=True) or {}
        if isinstance(data, list):
            egresos = data
        else:
            # Aceptar un solo egreso o { egresos: [...] }
            egresos = data.get("egresos") if isinstance(data.get("egresos"), list) else [data]
        # Intentar guardar en DB primero (para no perder registros si GAS falla)
        db_saved = False
        db_rows = 0
        db_error = None
        try:
            from services.db import get_session
            from services.egresos_repository import guardar_egresos
            session = get_session()
            try:
                db_rows = guardar_egresos(session, egresos)
                session.commit()
                db_saved = db_rows > 0
            finally:
                session.close()
        except Exception as _db_err:
            db_error = str(_db_err)

        # Intentar exportar a GAS
        gas_res = enviar_egresos(egresos)
        gas_ok = bool(gas_res.get("success"))

        # Consolidar respuesta: éxito si al menos una de las dos operaciones funcionó
        success = gas_ok or db_saved
        resp = {
            "success": success,
            "gas_saved": gas_ok,
            "db_saved": db_saved,
            "db_rows": db_rows,
        }
        if not gas_ok:
            resp["gas_error"] = gas_res.get("error") or gas_res.get("message") or "GAS export failed"
        if db_error:
            resp["db_error"] = db_error

        return jsonify(resp), (200 if success else 500)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/egresos/status", methods=["GET"])
def api_egresos_status():
    try:
        return jsonify(estado_egresos()), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# API: Historial de Egresos (lee desde Apps Script)
@app.route("/api/egresos/historial", methods=["GET"])
def api_egresos_historial():
    try:
        limit = int(request.args.get('limit', '200'))
        res = listar_egresos(limit=limit)
        code = 200 if res.get("success") else 400
        return jsonify(res), code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Endpoint de verificación rápida
@app.route("/test_sheets", methods=["GET"])
def test_sheets():
    try:
        from services.sales_service import _get_sheets_writer
        writer = _get_sheets_writer()
        if writer is None:
            return jsonify({"status": "error", "error": "No hay cliente de Google Sheets"}), 500
        # Listar títulos de hojas disponibles
        if hasattr(writer, 'spreadsheet'):
            sheets = [ws.title for ws in writer.spreadsheet.worksheets()]
            return jsonify({"status": "ok", "mode": "sheets_api", "sheets": sheets})
        else:
            return jsonify({"status": "ok", "mode": "apps_script"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Endpoint de verificación de Apps Script
@app.route("/test_gas", methods=["GET"])
def test_gas():
    try:
        from services.apps_script_writer import AppsScriptWriter
        gas_url = (GOOGLE_APPS_SCRIPT.get("GAS_URL") or "").strip()
        if not gas_url:
            return jsonify({"status": "error", "error": "GAS_URL no configurado"}), 400
        writer = AppsScriptWriter()
        estado = writer.obtener_estado_gas()
        return jsonify(estado), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Estado de DB (diagnóstico rápido)
@app.route("/api/db_status", methods=["GET"])
def api_db_status():
    try:
        from services.history_service import DATABASE_URL as DB_URL_IN_HS, USE_DB as USE_DB_IN_HS
        status = {
            "database_url_set": bool(DB_URL_IN_HS),
            "using_db": bool(USE_DB_IN_HS),
        }
        if not USE_DB_IN_HS:
            status["message"] = "DATABASE_URL no configurada; usando JSON"
            return jsonify(status), 200
        # Intentar contar filas en ventas
        from sqlalchemy import select, func
        from services.db import get_session
        from services.models import Venta
        session = get_session()
        try:
            total = session.execute(select(func.count(Venta.id))).scalar() or 0
            status["ventas_count"] = int(total)
        finally:
            session.close()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"using_db": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Cargar ventas desde historial persistente al iniciar el servidor
    print("🔄 Iniciando servidor...")
    # Inicializar DB si está configurada
    try:
        if init_db:
            ok = init_db()
            if ok:
                print("🗄️ Base de datos inicializada (Postgres)")
    except Exception as e:
        print(f"⚠️ No se pudo inicializar la base de datos: {e}")
    # No cargar historial en memoria para evitar duplicados/saturación en la tabla de sesión
    print("📊 Sistema iniciado (sin cargar historial en memoria)")
    app.run(debug=True)
