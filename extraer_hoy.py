#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de resultados del día actual
Ejecuta después de cada sorteo para obtener el resultado más reciente
"""

from datetime import datetime, timedelta
from superastro_ml_extractor import extraer_actualizar
from utils_compartido import ARCHIVO_EXCEL

def extraer_hoy():
    """
    Extrae solo los resultados de hoy
    """
    # Obtener fecha de hoy y ayer (por si el sorteo fue a medianoche)
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)

    fecha_inicio = ayer.strftime("%Y-%m-%d")
    fecha_fin = hoy.strftime("%Y-%m-%d")

    print(f"\n{'='*70}")
    print(f"📅 Extrayendo resultados recientes")
    print(f"🔍 Buscando desde: {fecha_inicio} hasta {fecha_fin}")
    print(f"{'='*70}\n")

    # Extraer y actualizar - pasar archivo existente para acumular historial
    import os
    archivo_existente = ARCHIVO_EXCEL if os.path.exists(ARCHIVO_EXCEL) else None
    archivo = extraer_actualizar(fecha_inicio=fecha_inicio, silencioso=False, archivo_existente=archivo_existente)

    if archivo:
        print(f"\n✅ Resultados actualizados en: {archivo}")
        return True
    else:
        print("\n❌ No se pudo actualizar el archivo")
        return False

if __name__ == "__main__":
    extraer_hoy()
