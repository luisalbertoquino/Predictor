#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluador Automático de Predicciones SuperAstro
Evalúa predicciones comparándolas con resultados reales
Autor: Luis Alberto Quino
Versión: 1.0
"""

import json
import os
from datetime import datetime, timedelta
from superastro_tracker import SuperAstroTracker

def cargar_resultados_excel():
    """
    Carga los resultados reales desde el Excel
    Retorna dict con key = "YYYY-MM-DD_TURNO" y value = {"numero": "XXXX", "signo": "Signo"}
    """
    import pandas as pd

    try:
        df = pd.read_excel('superastro_ml_data.xlsx')

        # Asegurarse que la columna Fecha sea datetime
        df['Fecha'] = pd.to_datetime(df['Fecha'])

        resultados = {}
        for _, row in df.iterrows():
            fecha_str = row['Fecha'].strftime('%Y-%m-%d')
            turno = 'SOL' if row['Turno'] == 0 else 'LUNA'
            key = f"{fecha_str}_{turno}"

            resultados[key] = {
                'numero': str(row['Numero_Completo']).zfill(4),
                'signo': row['Signo_Nombre']
            }

        return resultados
    except Exception as e:
        print(f"❌ Error cargando Excel: {e}")
        return {}

def evaluar_pendientes():
    """
    Evalúa todas las predicciones pendientes que ya tienen resultado real
    """
    tracker = SuperAstroTracker()
    resultados_reales = cargar_resultados_excel()

    if not resultados_reales:
        print("⚠️  No se encontraron resultados reales en el Excel")
        return

    evaluadas = 0
    pendientes = 0

    for pred in tracker.historial['predicciones']:
        # Solo procesar predicciones no evaluadas
        if pred.get('evaluado', False):
            continue

        pendientes += 1
        fecha_sorteo = pred['fecha_sorteo']
        turno = pred['turno']
        key = f"{fecha_sorteo}_{turno}"

        # Verificar si existe el resultado real
        if key in resultados_reales:
            resultado = resultados_reales[key]

            # Actualizar resultado real en la predicción
            tracker.actualizar_resultado_real(
                fecha_sorteo,
                0 if turno == 'SOL' else 1,
                resultado['numero'],
                resultado['signo']
            )

            evaluadas += 1
            print(f"✅ Evaluada: {fecha_sorteo} {turno} -> {resultado['numero']} {resultado['signo']}")

    print(f"\n{'='*60}")
    print(f"📊 Resumen de Evaluación")
    print(f"{'='*60}")
    print(f"Total predicciones pendientes: {pendientes}")
    print(f"Predicciones evaluadas: {evaluadas}")
    print(f"Aún pendientes: {pendientes - evaluadas}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 EVALUADOR AUTOMÁTICO DE PREDICCIONES")
    print("="*60 + "\n")

    evaluar_pendientes()

    print("\n✅ Proceso de evaluación completado\n")
