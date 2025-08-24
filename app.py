from flask import Flask, render_template, request, jsonify, send_file, abort, redirect
from pathlib import Path
from services.sales_service import listar_ventas, agregar_venta, actualizar_venta, eliminar_venta, obtener_estado_sheets
from services.export_service import exportar_a_google_sheets
from services.catalog_service import obtener_catalogo

app = Flask(__name__)

@app.route("/")
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

# Exportar a Google Sheets
@app.route("/api/exportar", methods=["POST"])
def api_exportar():
    ventas = listar_ventas()
    resultado = exportar_a_google_sheets(ventas)
    return jsonify(resultado), 200

# Redirigir a Google Sheets
@app.route("/download/excel", methods=["GET"])
def download_excel():
    # Redirigir a la hoja de Google Sheets
    sheet_id = GOOGLE_SHEETS_CONFIG["SHEET_ID"]
    return redirect(f"https://docs.google.com/spreadsheets/d/{sheet_id}")

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

if __name__ == "__main__":
    app.run(debug=True)
