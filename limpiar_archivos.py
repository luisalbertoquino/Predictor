# -*- coding: utf-8 -*-
"""
Script para limpiar archivos duplicados y organizar el JSON
"""

import sys
import io
import os
import glob

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from utils_compartido import limpiar_historial

print("Iniciando limpieza de archivos...")
print("="*60)

# 1. Limpiar y organizar JSON
print("\nLimpiando predicciones_historial.json...")
limpiar_historial()

# 2. Eliminar archivos Excel duplicados (los que tienen fecha en el nombre)
print("\nEliminando archivos Excel duplicados...")
archivos_excel = glob.glob("superastro_ml_data_*.xlsx")

if archivos_excel:
    print(f"   Encontrados {len(archivos_excel)} archivos duplicados:")
    for archivo in archivos_excel:
        try:
            os.remove(archivo)
            print(f"   [OK] Eliminado: {archivo}")
        except Exception as e:
            print(f"   [ERROR] Error al eliminar {archivo}: {e}")
else:
    print("   [OK] No hay archivos duplicados")

# 3. Verificar archivo Excel principal
if os.path.exists("superastro_ml_data.xlsx"):
    size_mb = os.path.getsize("superastro_ml_data.xlsx") / (1024 * 1024)
    print(f"\n[OK] Archivo Excel principal existe: superastro_ml_data.xlsx ({size_mb:.2f} MB)")
else:
    print("\n[AVISO] Archivo Excel principal no existe (se creara al ejecutar un script)")

print("\n" + "="*60)
print("[OK] Limpieza completada!")
print("\nArchivos que todos los scripts deben usar:")
print("  JSON:  predicciones_historial.json")
print("  EXCEL: superastro_ml_data.xlsx")
