#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de resultados del día actual
Ejecuta después de cada sorteo para obtener el resultado más reciente
"""

from datetime import datetime, timedelta
from superastro_ml_extractor import extraer_actualizar


def extraer_hoy():
    """Extrae los resultados de hoy y ayer y los guarda en la BD."""
    hoy  = datetime.now()
    ayer = hoy - timedelta(days=1)

    fecha_inicio = ayer.strftime("%Y-%m-%d")

    print(f"\n{'='*70}")
    print(f"📅 Extrayendo resultados recientes")
    print(f"🔍 Buscando desde: {fecha_inicio} hasta {hoy.strftime('%Y-%m-%d')}")
    print(f"{'='*70}\n")

    resultado = extraer_actualizar(fecha_inicio=fecha_inicio, silencioso=False)

    if resultado:
        print(f"\n✅ Resultados guardados en la base de datos")
        return True
    else:
        print("\n❌ No se pudo actualizar la base de datos")
        return False


if __name__ == "__main__":
    extraer_hoy()
