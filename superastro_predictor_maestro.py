# -*- coding: utf-8 -*-
"""
SuperAstro Predictor Maestro - Sistema Unificado
Ejecuta todos los métodos de predicción y genera resultado comparativo
Autor: Luis Alberto Quino
Versión: 2.0 - Sistema Maestro Unificado
"""

import sys
import io
import os

# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Importar utilidades compartidas
from utils_compartido import (
    agregar_prediccion,
    cargar_historial,
    ARCHIVO_JSON,
    calcular_proximo_sorteo_sol,
    calcular_proximo_sorteo_luna,
    calcular_proximos_sorteos
)

# Importar módulos de predicción
try:
    from superastro_ml_predictor import SuperAstroMLPredictor
    ML_DISPONIBLE = True
except ImportError:
    ML_DISPONIBLE = False

try:
    from superastro_predictor_mejorado import SuperAstroMejorado
    MEJORADO_DISPONIBLE = True
except ImportError:
    MEJORADO_DISPONIBLE = False

try:
    from superastro_lstm_predictor import SuperAstroLSTMPredictor
    LSTM_DISPONIBLE = True
except ImportError:
    LSTM_DISPONIBLE = False


class SuperAstroPredictorMaestro:
    """
    Predictor maestro que ejecuta todos los métodos disponibles
    y genera un consenso unificado
    """

    def __init__(self):
        self.predicciones_sol = {}
        self.predicciones_luna = {}
        self.archivo_historial = ARCHIVO_JSON

    def ejecutar_ml_basico(self):
        """Ejecuta Random Forest + XGBoost"""
        if not ML_DISPONIBLE:
            return None

        print(f"\n{'='*70}")
        print("🌲 MÉTODO 1: RANDOM FOREST + XGBOOST")
        print(f"{'='*70}\n")

        try:
            # Silenciar output
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            # Ejecutar predictor completo (esto hace todo el proceso)
            predictor = SuperAstroMLPredictor()
            predictor.ejecutar_completo()

            sys.stdout = old_stdout

            # Extraer últimas 2 predicciones del tracker (SOL y LUNA)
            if hasattr(predictor, 'tracker') and predictor.tracker.historial:
                todas_preds = predictor.tracker.historial.get('predicciones', [])

                # Buscar las últimas predicciones de HOY que tienen rf_combinado
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                for pred in reversed(todas_preds):
                    # Solo procesar predicciones que tienen el formato completo
                    if 'rf_combinado' not in pred or 'xgb_combinado' not in pred:
                        continue

                    # Solo predicciones de hoy
                    if not pred.get('fecha_prediccion', '').startswith(fecha_hoy):
                        continue

                    if pred.get('turno') == 'SOL' and 'RF' not in self.predicciones_sol:
                        self.predicciones_sol['RF'] = {
                            'numero': pred['rf_combinado']['numero'],
                            'signo': pred['rf_combinado']['signo']
                        }
                        self.predicciones_sol['XGB'] = {
                            'numero': pred['xgb_combinado']['numero'],
                            'signo': pred['xgb_combinado']['signo']
                        }
                    elif pred.get('turno') == 'LUNA' and 'RF' not in self.predicciones_luna:
                        self.predicciones_luna['RF'] = {
                            'numero': pred['rf_combinado']['numero'],
                            'signo': pred['rf_combinado']['signo']
                        }
                        self.predicciones_luna['XGB'] = {
                            'numero': pred['xgb_combinado']['numero'],
                            'signo': pred['xgb_combinado']['signo']
                        }

                    # Si ya tenemos ambas, salir
                    if 'RF' in self.predicciones_sol and 'RF' in self.predicciones_luna:
                        break

                # Verificar si obtuvimos predicciones
                if self.predicciones_sol.get('RF') and self.predicciones_luna.get('RF'):
                    print("✅ Random Forest + XGBoost completado\n")
                    return True
                elif self.predicciones_sol.get('RF') or self.predicciones_luna.get('RF'):
                    print("✅ Random Forest + XGBoost completado (parcial)\n")
                    return True
                else:
                    print("⚠️  RF/XGB ejecutado, revisa historial para ver predicciones\n")
                    return True
            else:
                print("❌ No se encontraron predicciones en tracker\n")
                return False
        except Exception as e:
            sys.stdout = old_stdout
            print(f"❌ Error en ML básico: {e}\n")
            return False

    def ejecutar_estadistico_mejorado(self):
        """Ejecuta método estadístico avanzado (One-Hot + DW)"""
        if not MEJORADO_DISPONIBLE:
            return None

        print(f"\n{'='*70}")
        print("📊 MÉTODO 2: ESTADÍSTICO AVANZADO (One-Hot + DW)")
        print(f"{'='*70}\n")

        try:
            predictor = SuperAstroMejorado()

            if predictor.cargar_datos():
                # Silenciar tests
                import io
                import sys
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                predictor.analizar_autocorrelacion()
                predictor.test_estacionariedad()
                predictor.aplicar_one_hot_encoding()
                predictor.crear_diferencias()

                sys.stdout = old_stdout

                predictor.entrenar_modelos_mejorados()

                # Obtener predicciones (turno 0=SOL, 1=LUNA)
                pred_sol = predictor.predecir(turno=0)
                pred_luna = predictor.predecir(turno=1)

                self.predicciones_sol['Estadistico'] = {
                    'numero': pred_sol['numero'],
                    'signo': pred_sol['signo']
                }

                self.predicciones_luna['Estadistico'] = {
                    'numero': pred_luna['numero'],
                    'signo': pred_luna['signo']
                }

                print("✅ Estadístico avanzado completado\n")
                return True
        except Exception as e:
            print(f"❌ Error en estadístico: {e}\n")
            return False

    def ejecutar_lstm(self):
        """Ejecuta red neuronal LSTM"""
        if not LSTM_DISPONIBLE:
            return None

        print(f"\n{'='*70}")
        print("🧠 MÉTODO 3: RED NEURONAL LSTM (Deep Learning)")
        print("   ⚠️  Este proceso puede tomar 45-60 minutos")
        print(f"{'='*70}\n")

        try:
            predictor = SuperAstroLSTMPredictor()

            if predictor.cargar_datos():
                predictor.entrenar_modelos()

                # Obtener predicciones (primera de cada turno)
                pred_sol = predictor.generar_predicciones('SOL', cantidad=1)
                pred_luna = predictor.generar_predicciones('LUNA', cantidad=1)

                self.predicciones_sol['LSTM'] = {
                    'numero': pred_sol[0]['numero'],
                    'signo': pred_sol[0]['signo']
                }

                self.predicciones_luna['LSTM'] = {
                    'numero': pred_luna[0]['numero'],
                    'signo': pred_luna[0]['signo']
                }

                print("✅ LSTM completado\n")
                return True
        except Exception as e:
            print(f"❌ Error en LSTM: {e}\n")
            return False

    def calcular_consenso(self, predicciones):
        """
        Calcula consenso entre métodos
        """
        if not predicciones:
            return None

        # Extraer números
        numeros = [p['numero'] for p in predicciones.values()]
        signos = [p['signo'] for p in predicciones.values()]

        # Contar signos más frecuente
        from collections import Counter
        signo_comun = Counter(signos).most_common(1)[0][0]

        # Calcular promedio de números (convertir a int)
        numeros_int = [int(n) for n in numeros]
        promedio = sum(numeros_int) // len(numeros_int)
        numero_consenso = str(promedio).zfill(4)

        # Calcular dispersión
        max_num = max(numeros_int)
        min_num = min(numeros_int)
        dispersion = max_num - min_num

        # Determinar nivel de consenso
        if dispersion < 1000:
            nivel = "ALTO ✅"
            confianza = "Alta confianza"
        elif dispersion < 3000:
            nivel = "MEDIO ⚠️"
            confianza = "Confianza moderada"
        else:
            nivel = "BAJO ❌"
            confianza = "Usar con precaución"

        return {
            'numero': numero_consenso,
            'signo': signo_comun,
            'nivel_consenso': nivel,
            'confianza': confianza,
            'dispersion': dispersion
        }

    def guardar_en_historial(self):
        """
        Guarda predicciones unificadas en historial JSON usando utilidades compartidas
        """
        fecha_pred = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calcular fechas correctas usando funciones compartidas
        fecha_sorteo_sol = calcular_proximo_sorteo_sol()
        fecha_sorteo_luna = calcular_proximo_sorteo_luna()

        # Crear entrada para SOL
        consenso_sol = self.calcular_consenso(self.predicciones_sol)
        entrada_sol = {
            "fecha_prediccion": fecha_pred,
            "fecha_sorteo": fecha_sorteo_sol,
            "turno": "SOL",
            "evaluado": False,
            "resultado_real": None,
            "metodos": self.predicciones_sol,
            "consenso": consenso_sol
        }

        # Crear entrada para LUNA
        consenso_luna = self.calcular_consenso(self.predicciones_luna)
        entrada_luna = {
            "fecha_prediccion": fecha_pred,
            "fecha_sorteo": fecha_sorteo_luna,
            "turno": "LUNA",
            "evaluado": False,
            "resultado_real": None,
            "metodos": self.predicciones_luna,
            "consenso": consenso_luna
        }

        # Usar función compartida que combina duplicados automáticamente
        agregar_prediccion(entrada_sol)
        agregar_prediccion(entrada_luna)

        print(f"[OK] Predicciones guardadas:")
        print(f"    - SOL:  {fecha_sorteo_sol}")
        print(f"    - LUNA: {fecha_sorteo_luna}\n")

    def obtener_resultados_anteriores(self):
        """Obtiene y analiza resultados de predicciones anteriores"""
        historial = cargar_historial()

        resultados = []
        for pred in historial.get('predicciones', []):
            if pred.get('evaluado') and pred.get('resultado_real'):
                resultados.append(pred)

        # Ordenar por fecha (más recientes primero)
        resultados.sort(key=lambda x: x.get('fecha_sorteo', ''), reverse=True)
        return resultados[:10]  # Últimos 10

    def calcular_tasa_acierto_metodo(self, metodo_nombre, resultados):
        """Calcula tasa de acierto para un método específico"""
        total = 0
        aciertos_digitos = 0
        aciertos_signos = 0

        for res in resultados:
            if 'aciertos' not in res or metodo_nombre not in res['aciertos']:
                continue

            total += 1
            acierto = res['aciertos'][metodo_nombre]
            aciertos_digitos += acierto.get('digitos_correctos', 0)
            if acierto.get('signo_correcto'):
                aciertos_signos += 1

        if total == 0:
            return None

        return {
            'total': total,
            'promedio_digitos': aciertos_digitos / total,
            'tasa_signos': (aciertos_signos / total) * 100
        }

    def mostrar_reporte_final(self):
        """
        Muestra reporte organizado en 3 secciones
        """
        print(f"\n{'='*70}")
        print(f"📊 REPORTE SUPERASTRO - PREDICTOR MAESTRO")
        print(f"{'='*70}\n")

        # ===== SECCIÓN 1: RESULTADOS ANTERIORES =====
        print(f"{'='*70}")
        print(f"📈 SECCIÓN 1: RESULTADOS ANTERIORES")
        print(f"{'='*70}\n")

        resultados = self.obtener_resultados_anteriores()
        if resultados:
            # Mostrar últimas 5 predicciones
            print("Últimas 5 predicciones evaluadas:\n")
            for i, res in enumerate(resultados[:5], 1):
                fecha = res['fecha_sorteo']
                turno = res['turno']
                real = res['resultado_real']

                print(f"{i}. {fecha} - {turno}")
                print(f"   Real: {real['numero']} - {real['signo']}")

                # Mostrar aciertos por método
                if 'aciertos' in res:
                    mejor_digitos = 0
                    mejor_metodo = ""

                    for metodo, acierto in res['aciertos'].items():
                        digitos = acierto.get('digitos_correctos', 0)
                        signo_ok = "✓" if acierto.get('signo_correcto') else "✗"

                        if digitos > mejor_digitos:
                            mejor_digitos = digitos
                            mejor_metodo = metodo

                        print(f"   {metodo:15s}: {digitos}/4 dígitos  Signo {signo_ok}")

                    if mejor_digitos > 0:
                        print(f"   ⭐ Mejor: {mejor_metodo}")
                print()

            # Tabla de tasas de acierto
            print(f"\n{'─'*70}")
            print("TASAS DE ACIERTO GENERAL (últimas 10 predicciones):\n")

            metodos = ['RF Combinado', 'XGB Combinado', 'RF Específico', 'XGB Específico', 'Estadistico', 'LSTM']
            nombres_cortos = {'RF Combinado': 'rf_combinado', 'XGB Combinado': 'xgb_combinado',
                             'RF Específico': 'rf_especifico', 'XGB Específico': 'xgb_especifico',
                             'Estadistico': 'Estadistico', 'LSTM': 'LSTM'}

            print(f"{'Método':<20} {'Predicciones':<15} {'Dígitos':<15} {'Signos':<10}")
            print("─" * 70)

            for metodo in metodos:
                metodo_key = nombres_cortos.get(metodo, metodo)
                tasa = self.calcular_tasa_acierto_metodo(metodo_key, resultados)

                if tasa:
                    print(f"{metodo:<20} {tasa['total']:<15} {tasa['promedio_digitos']:.2f}/4.00{'':<8} {tasa['tasa_signos']:.1f}%")
                else:
                    print(f"{metodo:<20} {'Sin datos':<15} {'-':<15} {'-':<10}")

        else:
            print("   No hay resultados anteriores para mostrar")
            print("   Ejecuta el script diariamente para acumular historial\n")

        # ===== SECCIÓN 2: PREDICCIONES ACTUALES =====
        print(f"\n{'='*70}")
        print(f"🎯 SECCIÓN 2: PREDICCIONES ACTUALES (Hoy)")
        print(f"{'='*70}\n")

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Fecha: {fecha_hoy}\n")

        # Buscar si hay predicciones para hoy en el historial
        predicciones_hoy = []
        historial = cargar_historial()
        for pred in historial.get('predicciones', []):
            if pred.get('fecha_sorteo') == fecha_hoy:
                predicciones_hoy.append(pred)

        if predicciones_hoy:
            for pred in predicciones_hoy:
                turno = pred['turno']
                evaluado = pred.get('evaluado', False)

                if turno == 'SOL':
                    print("☀️  SOL - ", end="")
                else:
                    print("🌙 LUNA - ", end="")

                if evaluado and pred.get('resultado_real'):
                    # Ya salió el resultado
                    real = pred['resultado_real']
                    print(f"✅ RESULTADO PUBLICADO")
                    print(f"   Real: {real['numero']} - {real['signo']}")

                    if 'aciertos' in pred:
                        print(f"   Aciertos:")
                        for metodo, acierto in pred['aciertos'].items():
                            digitos = acierto.get('digitos_correctos', 0)
                            signo = "✓" if acierto.get('signo_correcto') else "✗"
                            emoji = "🎉" if digitos >= 3 else "👍" if digitos >= 2 else "⚠️"
                            print(f"      {emoji} {metodo:15s}: {digitos}/4 dígitos  Signo {signo}")
                else:
                    # Aún no sale
                    print(f"⏳ ESPERANDO RESULTADO")

                    # Intentar obtener predicciones (formato maestro)
                    predicciones_mostrar = pred.get('metodos', {})

                    # Si no hay predicciones en formato maestro, buscar en formato antiguo
                    if not predicciones_mostrar:
                        if 'rf_combinado' in pred:
                            predicciones_mostrar = {
                                'RF': pred.get('rf_combinado', {}),
                                'XGB': pred.get('xgb_combinado', {}),
                                'RF Específico': pred.get('rf_especifico', {}),
                                'XGB Específico': pred.get('xgb_especifico', {})
                            }

                    if predicciones_mostrar:
                        print(f"   Predicciones realizadas:")
                        for metodo, p in predicciones_mostrar.items():
                            if p and 'numero' in p:
                                print(f"      {metodo:15s}: {p['numero']} - {p['signo']}")
                        if 'consenso' in pred and pred['consenso']:
                            cons = pred['consenso']
                            print(f"      {'CONSENSO':15s}: {cons['numero']} - {cons['signo']} ({cons['nivel_consenso']})")
                    else:
                        print(f"   (Sin predicciones registradas)")
                print()
        else:
            print("   No hay predicciones registradas para hoy\n")

        # ===== SECCIÓN 3: PREDICCIONES FUTURAS =====
        print(f"{'='*70}")
        print(f"🔮 SECCIÓN 3: PREDICCIONES FUTURAS (Mañana)")
        print(f"{'='*70}\n")

        fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 Fecha: {fecha_manana}\n")

        # SOL
        if self.predicciones_sol:
            print("☀️  SOL (Turno Día)")
            print("─" * 70)
            for metodo, pred in self.predicciones_sol.items():
                print(f"   {metodo:15s}: {pred['numero']} - {pred['signo']}")

            consenso_sol = self.calcular_consenso(self.predicciones_sol)
            if consenso_sol:
                print(f"\n   {'→ CONSENSO':15s}: {consenso_sol['numero']} - {consenso_sol['signo']}")
                print(f"   {'→ Confianza':15s}: {consenso_sol['nivel_consenso']}")
            print()

        # LUNA
        if self.predicciones_luna:
            print("🌙 LUNA (Turno Noche)")
            print("─" * 70)
            for metodo, pred in self.predicciones_luna.items():
                print(f"   {metodo:15s}: {pred['numero']} - {pred['signo']}")

            consenso_luna = self.calcular_consenso(self.predicciones_luna)
            if consenso_luna:
                print(f"\n   {'→ CONSENSO':15s}: {consenso_luna['numero']} - {consenso_luna['signo']}")
                print(f"   {'→ Confianza':15s}: {consenso_luna['nivel_consenso']}")
            print()

        if not self.predicciones_sol and not self.predicciones_luna:
            print("   No se generaron predicciones en esta ejecución\n")

        print(f"{'='*70}\n")

    def ejecutar_completo(self, incluir_lstm=False):
        """
        Ejecuta todos los métodos disponibles
        """
        print(f"\n{'='*70}")
        print("🎰 SUPERASTRO PREDICTOR MAESTRO")
        print("   Sistema Unificado de Predicción Multi-Método")
        print(f"{'='*70}\n")

        print("📋 Métodos a ejecutar:")
        if ML_DISPONIBLE:
            print("   ✅ Random Forest + XGBoost")
        if MEJORADO_DISPONIBLE:
            print("   ✅ Estadístico Avanzado (One-Hot + DW)")
        if incluir_lstm and LSTM_DISPONIBLE:
            print("   ✅ Red Neuronal LSTM (~60 min)")
        print()

        # Ejecutar métodos
        self.ejecutar_ml_basico()
        self.ejecutar_estadistico_mejorado()

        if incluir_lstm:
            self.ejecutar_lstm()

        # Guardar y mostrar
        self.guardar_en_historial()
        self.mostrar_reporte_final()

        print("📌 NOTAS:")
        print("   • Predicciones guardadas en predicciones_historial.json")
        print("   • Se evaluarán automáticamente cuando salgan resultados")
        print("   • Ejecuta 'python superastro_estadisticas.py' para ver rankings")
        print(f"\n{'='*70}\n")


def main():
    """Función principal"""
    import sys

    # Verificar si quiere incluir LSTM
    incluir_lstm = '--lstm' in sys.argv or '-l' in sys.argv

    maestro = SuperAstroPredictorMaestro()
    maestro.ejecutar_completo(incluir_lstm=incluir_lstm)

    if not incluir_lstm and LSTM_DISPONIBLE:
        print("💡 TIP: Para incluir predicciones LSTM, ejecuta:")
        print("   python superastro_predictor_maestro.py --lstm\n")


if __name__ == "__main__":
    main()
