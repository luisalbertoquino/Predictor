#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro Tracker - Sistema de Registro y Evaluación de Predicciones
Registra predicciones diarias y evalúa precisión a lo largo del tiempo
Autor: Luis Alberto Quino
Versión: 1.0
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os
from pathlib import Path


class SuperAstroTracker:
    """
    Sistema de seguimiento de predicciones vs resultados reales
    """
    
    def __init__(self, archivo_historial="predicciones_historial.json"):
        """
        Inicializa el tracker
        """
        self.archivo_historial = archivo_historial
        self.historial = self.cargar_historial()
    
    def cargar_historial(self):
        """
        Carga el historial de predicciones desde JSON
        """
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"predicciones": []}
        return {"predicciones": []}
    
    def guardar_historial(self):
        """
        Guarda el historial de predicciones en JSON
        """
        with open(self.archivo_historial, 'w', encoding='utf-8') as f:
            json.dump(self.historial, f, indent=2, ensure_ascii=False)
    
    def registrar_prediccion(self, fecha, turno, predicciones):
        """
        Registra una predicción para una fecha y turno específico
        
        Args:
            fecha: Fecha de la predicción (YYYY-MM-DD)
            turno: 0=SOL, 1=LUNA
            predicciones: Dict con las 4 predicciones de modelos
        """
        registro = {
            "fecha_prediccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_sorteo": fecha,
            "turno": "SOL" if turno == 0 else "LUNA",
            "rf_combinado": predicciones.get("rf_combinado", {}),
            "xgb_combinado": predicciones.get("xgb_combinado", {}),
            "rf_especifico": predicciones.get("rf_especifico", {}),
            "xgb_especifico": predicciones.get("xgb_especifico", {}),
            "resultado_real": None,
            "evaluado": False
        }
        
        self.historial["predicciones"].append(registro)
        self.guardar_historial()
        
        print(f"\n✅ Predicción registrada para {fecha} - {registro['turno']}")
    
    def actualizar_resultado_real(self, fecha, turno, numero_real, signo_real):
        """
        Actualiza el resultado real de un sorteo
        
        Args:
            fecha: Fecha del sorteo (YYYY-MM-DD)
            turno: 0=SOL, 1=LUNA
            numero_real: Número ganador (ej: "4470")
            signo_real: Signo ganador (ej: "Cancer")
        """
        turno_str = "SOL" if turno == 0 else "LUNA"
        
        for pred in self.historial["predicciones"]:
            if pred["fecha_sorteo"] == fecha and pred["turno"] == turno_str and not pred["evaluado"]:
                pred["resultado_real"] = {
                    "numero": numero_real,
                    "signo": signo_real
                }
                pred["evaluado"] = True
                
                # Calcular aciertos
                pred["aciertos"] = self.calcular_aciertos(pred)
                
                self.guardar_historial()
                print(f"\n✅ Resultado actualizado para {fecha} - {turno_str}: {numero_real} - {signo_real}")
                return True
        
        print(f"\n⚠️  No se encontró predicción para {fecha} - {turno_str}")
        return False
    
    def calcular_aciertos(self, prediccion):
        """
        Calcula cuántos dígitos acertó cada modelo
        """
        if not prediccion.get("resultado_real"):
            return None
        
        numero_real = prediccion["resultado_real"]["numero"]
        signo_real = prediccion["resultado_real"]["signo"]
        
        aciertos = {}
        
        for modelo in ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]:
            if modelo in prediccion and prediccion[modelo]:
                numero_pred = prediccion[modelo].get("numero", "")
                signo_pred = prediccion[modelo].get("signo", "")
                
                # Contar dígitos correctos en posición correcta
                digitos_correctos = sum(1 for i, (r, p) in enumerate(zip(numero_real, numero_pred)) if r == p)
                
                # Verificar signo
                signo_correcto = signo_real.lower() == signo_pred.lower()
                
                aciertos[modelo] = {
                    "digitos_correctos": digitos_correctos,
                    "signo_correcto": signo_correcto,
                    "numero_predicho": numero_pred,
                    "numero_real": numero_real
                }
        
        return aciertos
    
    def generar_reporte(self, ultimos_dias=5):
        """
        Genera un reporte de los últimos N días
        """
        print(f"\n{'='*80}")
        print(f"📊 REPORTE DE PREDICCIONES - ÚLTIMOS {ultimos_dias} DÍAS")
        print(f"{'='*80}\n")
        
        # Filtrar predicciones evaluadas de los últimos días
        fecha_limite = (datetime.now() - timedelta(days=ultimos_dias)).strftime("%Y-%m-%d")
        
        predicciones_evaluadas = [
            p for p in self.historial["predicciones"] 
            if p.get("evaluado") and p["fecha_sorteo"] >= fecha_limite
        ]
        
        if not predicciones_evaluadas:
            print("⚠️  No hay predicciones evaluadas en este período")
            return
        
        print(f"Total de predicciones evaluadas: {len(predicciones_evaluadas)}\n")
        
        # Estadísticas por modelo
        modelos = ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]
        nombres_modelos = {
            "rf_combinado": "RF Combinado",
            "xgb_combinado": "XGB Combinado",
            "rf_especifico": "RF Específico",
            "xgb_especifico": "XGB Específico"
        }
        
        estadisticas = {}
        
        for modelo in modelos:
            total_digitos = 0
            total_signos_correctos = 0
            aciertos_completos = 0
            total_predicciones = 0
            
            for pred in predicciones_evaluadas:
                if "aciertos" in pred and modelo in pred["aciertos"]:
                    acierto = pred["aciertos"][modelo]
                    total_digitos += acierto["digitos_correctos"]
                    if acierto["signo_correcto"]:
                        total_signos_correctos += 1
                    if acierto["digitos_correctos"] == 4 and acierto["signo_correcto"]:
                        aciertos_completos += 1
                    total_predicciones += 1
            
            if total_predicciones > 0:
                estadisticas[modelo] = {
                    "nombre": nombres_modelos[modelo],
                    "promedio_digitos": total_digitos / total_predicciones,
                    "porcentaje_signos": (total_signos_correctos / total_predicciones) * 100,
                    "aciertos_completos": aciertos_completos,
                    "total": total_predicciones
                }
        
        # Mostrar estadísticas
        print(f"{'─'*80}")
        print("📈 ESTADÍSTICAS POR MODELO")
        print(f"{'─'*80}\n")
        
        for modelo, stats in sorted(estadisticas.items(), 
                                     key=lambda x: x[1]["promedio_digitos"], 
                                     reverse=True):
            print(f"🔹 {stats['nombre']:20s}")
            print(f"   Promedio de dígitos correctos: {stats['promedio_digitos']:.2f}/4")
            print(f"   Acierto de signo: {stats['porcentaje_signos']:.1f}%")
            print(f"   Aciertos completos (4 dígitos + signo): {stats['aciertos_completos']}")
            print(f"   Total predicciones: {stats['total']}\n")
        
        # Detalle de cada predicción
        print(f"\n{'─'*80}")
        print("📋 DETALLE DE PREDICCIONES")
        print(f"{'─'*80}\n")
        
        for pred in sorted(predicciones_evaluadas, key=lambda x: x["fecha_sorteo"], reverse=True):
            print(f"📅 {pred['fecha_sorteo']} - {pred['turno']}")
            print(f"   Resultado real: {pred['resultado_real']['numero']} - {pred['resultado_real']['signo']}")
            
            if "aciertos" in pred:
                print(f"   Predicciones:")
                for modelo in modelos:
                    if modelo in pred["aciertos"]:
                        acierto = pred["aciertos"][modelo]
                        digitos = acierto["digitos_correctos"]
                        signo = "✓" if acierto["signo_correcto"] else "✗"
                        print(f"      {nombres_modelos[modelo]:20s}: {acierto['numero_predicho']} ({digitos}/4 dígitos) {signo}")
            print()
        
        # Guardar reporte en Excel
        self.exportar_reporte_excel(predicciones_evaluadas, ultimos_dias)
    
    def exportar_reporte_excel(self, predicciones, dias):
        """
        Exporta el reporte a Excel
        """
        if not predicciones:
            return
        
        # Preparar datos para DataFrame
        datos = []
        for pred in predicciones:
            fila_base = {
                "Fecha_Sorteo": pred["fecha_sorteo"],
                "Turno": pred["turno"],
                "Numero_Real": pred["resultado_real"]["numero"],
                "Signo_Real": pred["resultado_real"]["signo"]
            }
            
            if "aciertos" in pred:
                for modelo, nombre in {
                    "rf_combinado": "RF_Comb",
                    "xgb_combinado": "XGB_Comb",
                    "rf_especifico": "RF_Esp",
                    "xgb_especifico": "XGB_Esp"
                }.items():
                    if modelo in pred["aciertos"]:
                        acierto = pred["aciertos"][modelo]
                        fila_base[f"{nombre}_Numero"] = acierto["numero_predicho"]
                        fila_base[f"{nombre}_Digitos_OK"] = acierto["digitos_correctos"]
                        fila_base[f"{nombre}_Signo_OK"] = "Sí" if acierto["signo_correcto"] else "No"
            
            datos.append(fila_base)
        
        df = pd.DataFrame(datos)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_predicciones_{dias}dias_{timestamp}.xlsx"
        
        df.to_excel(nombre_archivo, index=False)
        
        print(f"{'─'*80}")
        print(f"✅ Reporte exportado: {nombre_archivo}")
        print(f"{'─'*80}\n")
    
    def obtener_mejor_modelo(self, ultimos_dias=5):
        """
        Determina cuál modelo ha sido el más preciso
        """
        fecha_limite = (datetime.now() - timedelta(days=ultimos_dias)).strftime("%Y-%m-%d")
        
        predicciones_evaluadas = [
            p for p in self.historial["predicciones"] 
            if p.get("evaluado") and p["fecha_sorteo"] >= fecha_limite
        ]
        
        if not predicciones_evaluadas:
            return None
        
        modelos = ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]
        scores = {m: 0 for m in modelos}
        
        for pred in predicciones_evaluadas:
            if "aciertos" in pred:
                for modelo in modelos:
                    if modelo in pred["aciertos"]:
                        acierto = pred["aciertos"][modelo]
                        # Puntaje: dígitos correctos + bonus por signo
                        score = acierto["digitos_correctos"]
                        if acierto["signo_correcto"]:
                            score += 1
                        scores[modelo] += score
        
        mejor_modelo = max(scores.items(), key=lambda x: x[1])
        
        nombres = {
            "rf_combinado": "Random Forest Combinado",
            "xgb_combinado": "XGBoost Combinado",
            "rf_especifico": "Random Forest Específico",
            "xgb_especifico": "XGBoost Específico"
        }
        
        print(f"\n🏆 MEJOR MODELO (últimos {ultimos_dias} días):")
        print(f"   {nombres[mejor_modelo[0]]}")
        print(f"   Puntaje total: {mejor_modelo[1]}\n")
        
        return mejor_modelo[0]


def menu_principal():
    """
    Menú principal del tracker
    """
    tracker = SuperAstroTracker()
    
    while True:
        print("\n" + "="*80)
        print("🎯 SUPERASTRO TRACKER - MENÚ PRINCIPAL")
        print("="*80 + "\n")
        
        print("1. Registrar nueva predicción")
        print("2. Actualizar resultado real de un sorteo")
        print("3. Ver reporte de últimos N días")
        print("4. Ver mejor modelo")
        print("5. Salir\n")
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == "1":
            print("\n--- Registrar Predicción ---")
            fecha = input("Fecha del sorteo (YYYY-MM-DD): ").strip()
            turno_input = input("Turno (0=SOL, 1=LUNA): ").strip()
            turno = int(turno_input)
            
            print("\nIngresa las predicciones de cada modelo:")
            predicciones = {}
            
            for modelo in ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]:
                print(f"\n{modelo.upper().replace('_', ' ')}:")
                numero = input("  Número (4 dígitos): ").strip()
                signo = input("  Signo: ").strip()
                predicciones[modelo] = {"numero": numero, "signo": signo}
            
            tracker.registrar_prediccion(fecha, turno, predicciones)
        
        elif opcion == "2":
            print("\n--- Actualizar Resultado Real ---")
            fecha = input("Fecha del sorteo (YYYY-MM-DD): ").strip()
            turno_input = input("Turno (0=SOL, 1=LUNA): ").strip()
            turno = int(turno_input)
            numero = input("Número ganador (4 dígitos): ").strip()
            signo = input("Signo ganador: ").strip()
            
            tracker.actualizar_resultado_real(fecha, turno, numero, signo)
        
        elif opcion == "3":
            print("\n--- Generar Reporte ---")
            dias = input("¿Cuántos días atrás? [5]: ").strip() or "5"
            tracker.generar_reporte(int(dias))
        
        elif opcion == "4":
            print("\n--- Mejor Modelo ---")
            dias = input("¿Cuántos días atrás? [5]: ").strip() or "5"
            tracker.obtener_mejor_modelo(int(dias))
        
        elif opcion == "5":
            print("\n👋 ¡Hasta pronto!\n")
            break
        
        else:
            print("\n❌ Opción no válida")


if __name__ == "__main__":
    menu_principal()