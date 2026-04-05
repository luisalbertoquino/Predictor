#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluador Automático de Predicciones SuperAstro
Evalúa predicciones comparándolas con resultados reales de la BD
"""

from db import obtener_resultado
from superastro_tracker import SuperAstroTracker


def evaluar_pendientes():
    """Evalúa todas las predicciones pendientes que ya tienen resultado en la BD."""
    tracker  = SuperAstroTracker()
    evaluadas = 0
    pendientes = 0

    for pred in tracker.historial['predicciones']:
        if pred.get('evaluado', False):
            continue

        pendientes += 1
        fecha_sorteo = pred['fecha_sorteo']
        turno        = pred['turno']

        resultado = obtener_resultado(fecha_sorteo, turno)
        if resultado:
            tracker.actualizar_resultado_real(
                fecha_sorteo,
                0 if turno == 'SOL' else 1,
                resultado['numero'],
                resultado['signo'],
            )
            evaluadas += 1
            print(f"✅ Evaluada: {fecha_sorteo} {turno} → {resultado['numero']} {resultado['signo']}")

    print(f"\n{'='*60}")
    print(f"📊 Resumen de Evaluación")
    print(f"{'='*60}")
    print(f"Total predicciones pendientes : {pendientes}")
    print(f"Predicciones evaluadas        : {evaluadas}")
    print(f"Aún pendientes                : {pendientes - evaluadas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 EVALUADOR AUTOMÁTICO DE PREDICCIONES")
    print("="*60 + "\n")

    evaluar_pendientes()

    print("\n✅ Proceso de evaluación completado\n")
