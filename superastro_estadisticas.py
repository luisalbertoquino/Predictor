#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro Estadísticas - Análisis Detallado de Rendimiento
Muestra estadísticas completas de todos los modelos
Autor: Luis Alberto Quino
Versión: 1.0
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
import os
from datetime import datetime
from collections import defaultdict


def cargar_historial():
    """Carga el historial de predicciones"""
    archivo = "predicciones_historial.json"
    if not os.path.exists(archivo):
        print("❌ No se encontró el archivo de historial")
        print("💡 Ejecuta primero: python superastro_ml_predictor.py")
        return None

    with open(archivo, 'r', encoding='utf-8') as f:
        return json.load(f)


def mostrar_estadisticas_diarias():
    """Muestra estadísticas día por día"""
    historial = cargar_historial()
    if not historial:
        return

    evaluadas = [p for p in historial["predicciones"] if p.get("evaluado")]

    if not evaluadas:
        print("\n⚠️  Aún no hay predicciones evaluadas")
        print("💡 Las predicciones se evalúan cuando hay resultados reales\n")
        return

    print("\n" + "="*70)
    print("📊 ESTADÍSTICAS DETALLADAS - RENDIMIENTO DIARIO")
    print("="*70 + "\n")

    # Ordenar por fecha
    evaluadas_ordenadas = sorted(evaluadas, key=lambda x: (x["fecha_sorteo"], x["turno"]))

    print(f"Total de predicciones evaluadas: {len(evaluadas_ordenadas)}\n")
    print(f"{'─'*70}")
    print("📅 RENDIMIENTO POR DÍA")
    print(f"{'─'*70}\n")

    # Agrupar por fecha
    por_fecha = defaultdict(list)
    for pred in evaluadas_ordenadas:
        por_fecha[pred["fecha_sorteo"]].append(pred)

    modelos = {
        "rf_combinado": "RF Comb",
        "xgb_combinado": "XGB Comb",
        "rf_especifico": "RF Esp",
        "xgb_especifico": "XGB Esp"
    }

    for fecha in sorted(por_fecha.keys()):
        print(f"📅 {fecha}")

        for pred in por_fecha[fecha]:
            turno = pred["turno"]
            resultado = pred["resultado_real"]

            print(f"\n   {turno}: {resultado['numero']} - {resultado['signo']}")

            if "aciertos" in pred:
                # Encontrar el mejor del día
                mejor_del_dia = max(
                    [(k, v) for k, v in pred["aciertos"].items()],
                    key=lambda x: x[1]["digitos_correctos"]
                )

                for modelo_key, modelo_nombre in modelos.items():
                    if modelo_key in pred["aciertos"]:
                        ac = pred["aciertos"][modelo_key]
                        prediccion = pred[modelo_key]

                        digitos = ac["digitos_correctos"]
                        signo = "✅" if ac["signo_correcto"] else "❌"

                        # Emoji según rendimiento
                        if digitos == 4 and ac["signo_correcto"]:
                            emoji = "🎉"
                        elif digitos >= 3:
                            emoji = "🔥"
                        elif digitos >= 2:
                            emoji = "👍"
                        else:
                            emoji = "⚠️"

                        # Marcar el mejor
                        estrella = " ⭐" if modelo_key == mejor_del_dia[0] else ""

                        print(f"      {emoji} {modelo_nombre:8s}: {prediccion['numero']} ({digitos}/4) {signo}{estrella}")

        print()

    # Estadísticas acumuladas
    print(f"{'─'*70}")
    print("📈 ESTADÍSTICAS ACUMULADAS")
    print(f"{'─'*70}\n")

    stats = {
        "rf_combinado": {"nombre": "RF Combinado", "aciertos": [], "signos": 0, "perfectos": 0},
        "xgb_combinado": {"nombre": "XGB Combinado", "aciertos": [], "signos": 0, "perfectos": 0},
        "rf_especifico": {"nombre": "RF Específico", "aciertos": [], "signos": 0, "perfectos": 0},
        "xgb_especifico": {"nombre": "XGB Específico", "aciertos": [], "signos": 0, "perfectos": 0}
    }

    for pred in evaluadas_ordenadas:
        if "aciertos" in pred:
            for modelo in stats.keys():
                if modelo in pred["aciertos"]:
                    ac = pred["aciertos"][modelo]
                    stats[modelo]["aciertos"].append(ac["digitos_correctos"])
                    if ac["signo_correcto"]:
                        stats[modelo]["signos"] += 1
                    if ac["digitos_correctos"] == 4 and ac["signo_correcto"]:
                        stats[modelo]["perfectos"] += 1

    # Tabla comparativa
    print("Modelo            │ Promedio │ Mejor │ Peor │ Signos │ Perfectos │ Total")
    print("─" * 70)

    for modelo_key, modelo_nombre in modelos.items():
        if stats[modelo_key]["aciertos"]:
            aciertos = stats[modelo_key]["aciertos"]
            promedio = sum(aciertos) / len(aciertos)
            mejor = max(aciertos)
            peor = min(aciertos)
            signos = stats[modelo_key]["signos"]
            pct_signos = (signos / len(aciertos)) * 100
            perfectos = stats[modelo_key]["perfectos"]
            total = len(aciertos)

            print(f"{stats[modelo_key]['nombre']:17s} │ {promedio:5.2f}/4  │ {mejor}/4   │ {peor}/4  │ {pct_signos:5.1f}% │ {perfectos:9d} │ {total:5d}")

    print()

    # Evolución temporal
    if len(evaluadas_ordenadas) >= 3:
        print(f"{'─'*70}")
        print("📊 EVOLUCIÓN TEMPORAL (últimos 3 vs primeros 3)")
        print(f"{'─'*70}\n")

        for modelo_key, modelo_info in stats.items():
            if len(modelo_info["aciertos"]) >= 6:
                primeros_3 = modelo_info["aciertos"][:3]
                ultimos_3 = modelo_info["aciertos"][-3:]

                prom_inicial = sum(primeros_3) / 3
                prom_reciente = sum(ultimos_3) / 3

                diferencia = prom_reciente - prom_inicial

                if diferencia > 0.3:
                    tendencia = "📈 Mejorando"
                elif diferencia < -0.3:
                    tendencia = "📉 Bajando"
                else:
                    tendencia = "➡️  Estable"

                print(f"{modelo_info['nombre']:17s}: {prom_inicial:.2f} → {prom_reciente:.2f}  {tendencia}")

        print()

    # Mejor modelo actual
    print(f"{'='*70}")
    print("🏆 RANKING FINAL")
    print(f"{'='*70}\n")

    ranking = sorted(
        [(k, v) for k, v in stats.items() if v["aciertos"]],
        key=lambda x: (sum(x[1]["aciertos"]) / len(x[1]["aciertos"]), x[1]["signos"] / len(x[1]["aciertos"])),
        reverse=True
    )

    for i, (modelo_key, modelo_info) in enumerate(ranking, 1):
        medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        promedio = sum(modelo_info["aciertos"]) / len(modelo_info["aciertos"])
        precision_pct = (promedio / 4) * 100

        print(f"{medalla} {modelo_info['nombre']}")
        print(f"   Precisión: {precision_pct:.1f}% ({promedio:.2f}/4 dígitos)")
        print(f"   Perfectos: {modelo_info['perfectos']}\n")

    # Recomendación
    mejor_modelo = ranking[0][1]["nombre"]
    mejor_promedio = sum(ranking[0][1]["aciertos"]) / len(ranking[0][1]["aciertos"])
    mejor_precision = (mejor_promedio / 4) * 100

    print(f"{'─'*70}")
    print("💡 RECOMENDACIÓN")
    print(f"{'─'*70}\n")

    if mejor_precision >= 65:
        print(f"   ⭐⭐⭐ CONFIANZA MUY ALTA")
        print(f"   Usa {mejor_modelo} para tus próximas apuestas")
    elif mejor_precision >= 50:
        print(f"   ⭐⭐ CONFIANZA ALTA")
        print(f"   {mejor_modelo} es tu mejor opción")
    elif mejor_precision >= 35:
        print(f"   ⭐ CONFIANZA MEDIA")
        print(f"   Considera {mejor_modelo}, combina con otros")
    else:
        print(f"   ⚠️  CONFIANZA BAJA")
        print(f"   Necesitas más datos. Ejecuta diariamente")

    print(f"\n   📊 Precisión actual: {mejor_precision:.1f}%")
    print(f"   📈 Evaluaciones: {len(ranking[0][1]['aciertos'])}")

    if len(ranking[0][1]["aciertos"]) < 10:
        print(f"\n   💡 Tip: Con más de 10 predicciones evaluadas,")
        print(f"       las estadísticas serán más confiables\n")
    else:
        print()


def exportar_a_csv():
    """Exporta estadísticas a CSV para análisis externo"""
    historial = cargar_historial()
    if not historial:
        return

    evaluadas = [p for p in historial["predicciones"] if p.get("evaluado")]

    if not evaluadas:
        print("\n⚠️  No hay datos para exportar\n")
        return

    import csv
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_csv = f"estadisticas_superastro_{timestamp}.csv"

    with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Encabezados
        writer.writerow([
            'Fecha', 'Turno', 'Numero_Real', 'Signo_Real',
            'RF_Comb_Numero', 'RF_Comb_Aciertos', 'RF_Comb_Signo',
            'XGB_Comb_Numero', 'XGB_Comb_Aciertos', 'XGB_Comb_Signo',
            'RF_Esp_Numero', 'RF_Esp_Aciertos', 'RF_Esp_Signo',
            'XGB_Esp_Numero', 'XGB_Esp_Aciertos', 'XGB_Esp_Signo'
        ])

        # Datos
        for pred in sorted(evaluadas, key=lambda x: x["fecha_sorteo"]):
            fila = [
                pred["fecha_sorteo"],
                pred["turno"],
                pred["resultado_real"]["numero"],
                pred["resultado_real"]["signo"]
            ]

            for modelo in ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]:
                if modelo in pred and "aciertos" in pred and modelo in pred["aciertos"]:
                    fila.append(pred[modelo]["numero"])
                    fila.append(pred["aciertos"][modelo]["digitos_correctos"])
                    fila.append("SI" if pred["aciertos"][modelo]["signo_correcto"] else "NO")
                else:
                    fila.extend(["", "", ""])

            writer.writerow(fila)

    print(f"\n✅ Exportado a: {archivo_csv}\n")


def main():
    """Función principal"""
    print("\n" + "="*70)
    print("📊 SUPERASTRO - ESTADÍSTICAS Y ANÁLISIS")
    print("="*70)

    if len(sys.argv) > 1 and sys.argv[1] in ["--export", "-e"]:
        exportar_a_csv()
    else:
        mostrar_estadisticas_diarias()

    print("="*70)
    print("💡 Comandos:")
    print("   python superastro_estadisticas.py          - Ver estadísticas")
    print("   python superastro_estadisticas.py --export - Exportar a CSV")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
