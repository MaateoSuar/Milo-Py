from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from pathlib import Path
from services.sales_service import listar_ventas, agregar_venta, actualizar_venta, eliminar_venta, obtener_estado_sheets, limpiar_ventas
from services.export_service import exportar_a_google_sheets
from services.catalog_service import obtener_catalogo
from config import GOOGLE_SHEETS_CONFIG

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

# API de ventas (memoria)
@app.route("/api/ventas", methods=["GET"])
def api_listar_ventas():
    return jsonify(listar_ventas())

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
    return jsonify(resultado), 200

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
        sheets = [ws.title for ws in writer.spreadsheet.worksheets()]
        return jsonify({"status": "ok", "sheets": sheets})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
