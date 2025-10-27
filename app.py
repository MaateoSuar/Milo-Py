from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from pathlib import Path
from services.sales_service import listar_ventas, agregar_venta, actualizar_venta, eliminar_venta, obtener_estado_sheets, limpiar_ventas, cargar_ventas_desde_historial
from services.history_service import leer_historial, agregar_ventas_a_historial, eliminar_historial_por_fecha_idx
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

# User class for authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hardcoded user (in production, use a database)
USERS = {
    'Milostore@gmail.com': {
        'password': 'milostore2025',
        'id': 1
    }
}

@login_manager.user_loader
def load_user(user_id):
    for email, user_data in USERS.items():
        if user_data['id'] == int(user_id):
            return User(user_data['id'])
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS and USERS[email]['password'] == password:
            user = User(USERS[email]['id'])
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
    # Si la exportación fue exitosa, ahora SÍ persistimos en historial
    try:
        if resultado and resultado.get("success"):
            ventas_actuales = listar_ventas()
            if ventas_actuales:
                agregar_ventas_a_historial(ventas_actuales)
    except Exception:
        # No romper la respuesta original del endpoint
        pass
    return jsonify(resultado), 200

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
    ventas_cargadas = cargar_ventas_desde_historial()
    print(f"📊 Sistema iniciado con {ventas_cargadas} ventas cargadas desde historial persistente")
    app.run(debug=True)
