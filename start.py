#!/usr/bin/env python3
"""
Script de inicio rápido para Milo Store ERP
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    try:
        import flask
        import pandas
        import openpyxl
        import requests
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Falta instalar: {e}")
        print("💡 Ejecuta: py -m pip install -r requirements.txt")
        return False

def verificar_estructura():
    """Verifica que la estructura de archivos esté correcta"""
    print("📁 Verificando estructura de archivos...")
    
    archivos_requeridos = [
        "app.py",
        "config.py",
        "services/catalog_service.py",
        "services/sales_service.py",
        "services/export_service.py",
        "templates/index.html",
        "static/app.js",
        "static/notifications.js"
    ]
    
    faltantes = []
    for archivo in archivos_requeridos:
        if not Path(archivo).exists():
            faltantes.append(archivo)
    
    if faltantes:
        print(f"❌ Faltan archivos: {', '.join(faltantes)}")
        return False
    
    print("✅ Estructura de archivos correcta")
    return True

def iniciar_aplicacion():
    """Inicia la aplicación Flask"""
    print("🚀 Iniciando Milo Store ERP...")
    
    try:
        # Crear directorio de logs si no existe
        Path("logs").mkdir(exist_ok=True)
        
        # Crear directorio de datos si no existe
        Path("data").mkdir(exist_ok=True)
        
        print("✅ Directorios creados")
        print("\n🌐 La aplicación se está iniciando...")
        print("📱 Abre tu navegador en: http://localhost:5000")
        print("⏹️  Presiona Ctrl+C para detener")
        
        # Esperar un momento para que el usuario lea el mensaje
        time.sleep(2)
        
        # Abrir navegador automáticamente
        webbrowser.open("http://localhost:5000")
        
        # Iniciar la aplicación
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar: {e}")

def main():
    print("=" * 60)
    print("🏪 MILO STORE ERP - INICIO RÁPIDO")
    print("=" * 60)
    
    # Verificar dependencias
    if not verificar_dependencias():
        return
    
    # Verificar estructura
    if not verificar_estructura():
        return
    
    print("\n🎯 Todo listo para iniciar!")
    
    # Preguntar si quiere iniciar
    respuesta = input("\n¿Deseas iniciar la aplicación ahora? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        iniciar_aplicacion()
    else:
        print("\n💡 Para iniciar manualmente:")
        print("   py app.py")
        print("   Luego abre: http://localhost:5000")

if __name__ == "__main__":
    main() 