#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro ML Predictor - Versión Autónoma con Tracking
Ejecuta extracción automática, entrena modelos, genera predicciones y registra resultados
Autor: Luis Alberto Quino
Versión: 2.1 - Con Sistema de Tracking
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
import os
import glob
import json
warnings.filterwarnings('ignore')

# Importar utilidades compartidas
from utils_compartido import (
    agregar_prediccion,
    cargar_historial,
    ARCHIVO_JSON,
    ARCHIVO_EXCEL,
    calcular_proximo_sorteo_sol,
    calcular_proximo_sorteo_luna
)

# Intentar importar el extractor
try:
    from superastro_ml_extractor import extraer_actualizar, SuperAstroMLExtractor
    EXTRACTOR_DISPONIBLE = True
except ImportError:
    EXTRACTOR_DISPONIBLE = False

# Intentar importar TensorFlow/Keras para LSTM
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False


class SuperAstroTracker:
    """
    Sistema de seguimiento de predicciones vs resultados reales
    """

    def __init__(self, archivo_historial=None):
        self.archivo_historial = archivo_historial or ARCHIVO_JSON
        self.historial = self.cargar_historial()

    def cargar_historial(self):
        """Carga el historial desde JSON usando utilidades compartidas"""
        return cargar_historial()

    def guardar_historial(self):
        """Guarda el historial en JSON - ya no se usa directamente, se usa agregar_prediccion"""
        # Esta función se mantiene por compatibilidad pero ya no guarda directamente
        pass
    
    def registrar_prediccion(self, fecha_sorteo, turno, predicciones):
        """
        Registra una predicción usando utilidades compartidas

        Args:
            fecha_sorteo: Fecha para la que se predice (YYYY-MM-DD)
            turno: 0=SOL, 1=LUNA
            predicciones: Dict con rf_comb, xgb_comb, rf_esp, xgb_esp
        """
        turno_str = "SOL" if turno == 0 else "LUNA"

        # Crear registro con formato estándar
        registro = {
            "fecha_prediccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fecha_sorteo": fecha_sorteo,
            "turno": turno_str,
            "evaluado": False,
            "resultado_real": None,
            "metodos": {}  # Será llenado por agregar_prediccion si existe
        }
        registro.update(predicciones)

        # Usar función compartida que maneja duplicados automáticamente
        agregar_prediccion(registro)
        # Recargar historial para mantener sincronizado
        self.historial = cargar_historial()
        print(f"   [OK] Prediccion guardada para {fecha_sorteo} - {turno_str}")
    
    def actualizar_resultados_desde_datos(self, archivo_datos=None):
        """Actualiza resultados reales consultando la BD MySQL."""
        try:
            from db import cargar_datos_raw
            df = cargar_datos_raw()
            actualizados = 0
            
            for pred in self.historial["predicciones"]:
                if pred["evaluado"]:
                    continue

                # Buscar resultado real en los datos
                turno_val = 0 if pred["turno"] == "SOL" else 1
                # Convertir fecha a string para comparación
                df_temp = df.copy()
                df_temp['Fecha'] = df_temp['Fecha'].astype(str)
                resultado = df_temp[(df_temp['Fecha'] == pred['fecha_sorteo']) & (df_temp['Turno'] == turno_val)]
                
                if not resultado.empty:
                    fila = resultado.iloc[0]
                    pred["resultado_real"] = {
                        "numero": str(fila['Numero_Completo']),
                        "signo": str(fila['Signo_Nombre'])
                    }
                    pred["aciertos"] = self.calcular_aciertos(pred)
                    pred["evaluado"] = True
                    actualizados += 1
            
            if actualizados > 0:
                self.guardar_historial()
                print(f"\n   ✅ {actualizados} predicciones evaluadas con resultados reales")
        
        except Exception as e:
            print(f"\n   ⚠️  Error al actualizar resultados: {e}")
    
    def calcular_aciertos(self, prediccion):
        """Calcula aciertos de cada modelo"""
        if not prediccion.get("resultado_real"):
            return None

        numero_real = str(prediccion["resultado_real"]["numero"])
        signo_real = str(prediccion["resultado_real"]["signo"])

        aciertos = {}

        for modelo in ["rf_combinado", "xgb_combinado", "rf_especifico", "xgb_especifico"]:
            if modelo in prediccion and prediccion[modelo]:
                numero_pred = str(prediccion[modelo].get("numero", ""))
                signo_pred = str(prediccion[modelo].get("signo", ""))

                # Contar dígitos correctos
                digitos_correctos = sum(1 for i, (r, p) in enumerate(zip(numero_real, numero_pred)) if r == p)
                signo_correcto = signo_real.lower() == signo_pred.lower()

                aciertos[modelo] = {
                    "digitos_correctos": int(digitos_correctos),
                    "signo_correcto": bool(signo_correcto)
                }

        return aciertos
    
    def generar_reporte(self, ultimos_dias=5):
        """Genera reporte de últimos N días"""
        print(f"\n{'='*70}")
        print(f"📊 REPORTE DE SEGUIMIENTO - ÚLTIMOS {ultimos_dias} DÍAS")
        print(f"{'='*70}\n")
        
        fecha_limite = (datetime.now() - timedelta(days=ultimos_dias)).strftime("%Y-%m-%d")
        
        evaluadas = [p for p in self.historial["predicciones"] 
                    if p.get("evaluado") and p["fecha_sorteo"] >= fecha_limite]
        
        pendientes = [p for p in self.historial["predicciones"]
                     if not p.get("evaluado") and p["fecha_sorteo"] >= fecha_limite]
        
        print(f"📈 Predicciones evaluadas: {len(evaluadas)}")
        print(f"⏳ Predicciones pendientes: {len(pendientes)}\n")
        
        if not evaluadas:
            print("⚠️  No hay predicciones evaluadas todavía\n")
            if pendientes:
                print("Predicciones pendientes de evaluación:")
                for p in pendientes:
                    print(f"   • {p['fecha_sorteo']} - {p['turno']}")
            return
        
        # Estadísticas por modelo
        modelos = {
            "rf_combinado": "RF Combinado",
            "xgb_combinado": "XGB Combinado",
            "rf_especifico": "RF Específico",
            "xgb_especifico": "XGB Específico"
        }
        
        stats = {}
        for key, nombre in modelos.items():
            total_dig = 0
            total_sig = 0
            count = 0
            
            for pred in evaluadas:
                if "aciertos" in pred and key in pred["aciertos"]:
                    acierto = pred["aciertos"][key]
                    total_dig += acierto["digitos_correctos"]
                    total_sig += (1 if acierto["signo_correcto"] else 0)
                    count += 1
            
            if count > 0:
                stats[key] = {
                    "nombre": nombre,
                    "prom_digitos": total_dig / count,
                    "prom_signos": (total_sig / count) * 100,
                    "total": count
                }
        
        # Mostrar estadísticas
        print(f"{'─'*70}")
        print("🏆 RANKING DE MODELOS")
        print(f"{'─'*70}\n")
        
        ranking = sorted(stats.items(), key=lambda x: x[1]["prom_digitos"], reverse=True)
        
        for i, (key, stat) in enumerate(ranking, 1):
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            print(f"{medalla} {stat['nombre']:20s}")
            print(f"   Promedio dígitos: {stat['prom_digitos']:.2f}/4")
            print(f"   Acierto signo:    {stat['prom_signos']:.1f}%")
            print(f"   Predicciones:     {stat['total']}\n")
        
        # Detalle de últimas predicciones
        print(f"{'─'*70}")
        print("📋 DETALLE DE ÚLTIMAS PREDICCIONES")
        print(f"{'─'*70}\n")
        
        for pred in sorted(evaluadas, key=lambda x: x["fecha_sorteo"], reverse=True)[:10]:
            print(f"📅 {pred['fecha_sorteo']} - {pred['turno']}")
            print(f"   Real: {pred['resultado_real']['numero']} - {pred['resultado_real']['signo']}")
            
            if "aciertos" in pred:
                mejor_modelo = max(pred["aciertos"].items(), 
                                  key=lambda x: x[1]["digitos_correctos"])
                
                for key, nombre in modelos.items():
                    if key in pred["aciertos"]:
                        ac = pred["aciertos"][key]
                        pred_num = pred[key]["numero"]
                        digitos = ac["digitos_correctos"]
                        signo = "✓" if ac["signo_correcto"] else "✗"
                        
                        destacado = " ⭐" if key == mejor_modelo[0] and digitos == mejor_modelo[1]["digitos_correctos"] else ""
                        print(f"      {nombre:15s}: {pred_num} ({digitos}/4) {signo}{destacado}")
            print()


class SuperAstroMLPredictor:
    """
    Predictor autónomo de números usando Machine Learning
    """
    
    # Mapeo inverso de signos (0-11)
    SIGNOS_INVERSO = {
        0: 'Aries', 1: 'Tauro', 2: 'Géminis', 3: 'Cáncer',
        4: 'Leo', 5: 'Virgo', 6: 'Libra', 7: 'Escorpión',
        8: 'Sagitario', 9: 'Capricornio', 10: 'Acuario', 11: 'Piscis'
    }
    
    def __init__(self):
        """
        Inicializa el predictor
        """
        self.df = None
        # Modelos combinados (SOL + LUNA)
        self.rf_models = {}
        self.xgb_models = {}
        # Modelos separados por turno
        self.rf_models_sol = {}
        self.xgb_models_sol = {}
        self.rf_models_luna = {}
        self.xgb_models_luna = {}
        self.lstm_models = {}
        self.archivo_datos = None
        # Sistema de tracking
        self.tracker = SuperAstroTracker()
    
    def verificar_actualizar_datos(self, forzar_actualizacion=False):
        """
        Verifica que la BD MySQL tiene datos.
        Si está vacía o se fuerza actualización, descarga desde 2025-01-01.
        """
        print(f"\n{'='*70}")
        print("🔍 VERIFICACIÓN DE DATOS")
        print(f"{'='*70}\n")

        from db import total_registros, ultima_fecha as uf
        n = total_registros()

        if n > 0 and not forzar_actualizacion:
            print(f"✅ BD lista: {n} registros hasta {uf()}")
            return True

        fecha_inicio = "2020-01-01" if forzar_actualizacion else "2025-01-01"
        print(f"🔄 Descargando datos desde {fecha_inicio}...")

        if EXTRACTOR_DISPONIBLE:
            try:
                resultado = extraer_actualizar(fecha_inicio=fecha_inicio, silencioso=False)
                if resultado:
                    print(f"\n✅ Datos guardados en la BD")
                    return True
                else:
                    print("\n❌ Error al descargar datos")
                    return False
            except Exception as e:
                print(f"\n❌ Error en la descarga: {e}")
                return False
        else:
            print("❌ Módulo extractor no disponible")
            return False
    
    def cargar_datos(self):
        """Carga datos con features ML desde la BD MySQL."""
        print(f"\n{'='*70}")
        print("📂 CARGANDO DATOS")
        print(f"{'='*70}\n")

        try:
            from db import cargar_datos_ml
            self.df = cargar_datos_ml()
            if self.df.empty:
                print("❌ No hay datos en la base de datos")
                return False
            
            print(f"✅ Datos cargados: {len(self.df)} registros")
            print(f"📅 Rango: {self.df['Fecha'].min()} a {self.df['Fecha'].max()}")
            
            # Información del último sorteo
            ultimo = self.df.iloc[-1]
            print(f"\n🎯 Último resultado registrado:")
            print(f"   Fecha: {ultimo['Fecha']}")
            print(f"   Turno: {'SOL (Día)' if ultimo['Turno'] == 0 else 'LUNA (Noche)'}")
            print(f"   Número: {ultimo['Numero_Completo']}")
            print(f"   Signo: {ultimo['Signo_Nombre']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return False
    
    def preparar_datos_rf_xgb(self, target_col, filtrar_turno=None):
        """
        Prepara datos para Random Forest y XGBoost
        
        Args:
            target_col: Columna objetivo a predecir
            filtrar_turno: None=todos, 0=solo SOL, 1=solo LUNA
        """
        feature_cols = [
            'Turno', 'Mes', 'Dia_Mes', 'Dia_Semana',
            'Pos1_Lag1', 'Pos2_Lag1', 'Pos3_Lag1', 'Pos4_Lag1', 'Signo_Lag1',
            'Pos1_Lag2', 'Pos2_Lag2', 'Pos3_Lag2', 'Pos4_Lag2', 'Signo_Lag2',
            'Media_Pos1_10', 'Media_Pos2_10', 'Media_Pos3_10', 'Media_Pos4_10',
            'Suma_Total', 'Frecuencia_Signo'
        ]
        
        # Filtrar por turno si se especifica
        if filtrar_turno is not None:
            df_filtrado = self.df[self.df['Turno'] == filtrar_turno].copy()
        else:
            df_filtrado = self.df.copy()
        
        df_clean = df_filtrado.dropna(subset=feature_cols + [target_col])
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def entrenar_modelos_por_turno(self, turno, nombre_turno):
        """
        Entrena modelos específicos para un turno (SOL o LUNA)
        
        Args:
            turno: 0 para SOL, 1 para LUNA
            nombre_turno: Nombre descriptivo del turno
        
        Returns:
            dict: Modelos Random Forest y XGBoost entrenados
        """
        print(f"\n{'─'*70}")
        print(f"🎯 Entrenando modelos ESPECÍFICOS para: {nombre_turno}")
        print(f"{'─'*70}\n")
        
        targets = ['Posicion_1', 'Posicion_2', 'Posicion_3', 'Posicion_4', 'Signo_Codigo']
        rf_models = {}
        xgb_models = {}
        
        # Contar registros disponibles
        df_turno = self.df[self.df['Turno'] == turno]
        print(f"📊 Registros disponibles para {nombre_turno}: {len(df_turno)}\n")
        
        print("🌲 Random Forest...")
        for target in targets:
            X_train, X_test, y_train, y_test = self.preparar_datos_rf_xgb(target, filtrar_turno=turno)
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            accuracy = accuracy_score(y_test, rf.predict(X_test))
            rf_models[target] = rf
            print(f"   {target}: {accuracy*100:.1f}% accuracy")
        
        print("\n🚀 XGBoost...")
        for target in targets:
            X_train, X_test, y_train, y_test = self.preparar_datos_rf_xgb(target, filtrar_turno=turno)
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1)
            xgb_model.fit(X_train, y_train)
            accuracy = accuracy_score(y_test, xgb_model.predict(X_test))
            xgb_models[target] = xgb_model
            print(f"   {target}: {accuracy*100:.1f}% accuracy")
        
        return rf_models, xgb_models
    
    def entrenar_modelos(self):
        """
        Entrena todos los modelos: combinados y separados por turno
        """
        print(f"\n{'='*70}")
        print("🤖 ENTRENAMIENTO DE MODELOS DE MACHINE LEARNING")
        print(f"{'='*70}\n")
        
        targets = ['Posicion_1', 'Posicion_2', 'Posicion_3', 'Posicion_4', 'Signo_Codigo']
        
        # ===== MODELOS COMBINADOS (SOL + LUNA juntos) =====
        print("📊 ESTRATEGIA 1: Modelos COMBINADOS (SOL + LUNA)")
        print("─"*70 + "\n")
        
        print("🌲 Random Forest...")
        for target in targets:
            X_train, X_test, y_train, y_test = self.preparar_datos_rf_xgb(target, filtrar_turno=None)
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            accuracy = accuracy_score(y_test, rf.predict(X_test))
            self.rf_models[target] = rf
            print(f"   {target}: {accuracy*100:.1f}% accuracy")
        
        print("\n🚀 XGBoost...")
        for target in targets:
            X_train, X_test, y_train, y_test = self.preparar_datos_rf_xgb(target, filtrar_turno=None)
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1)
            xgb_model.fit(X_train, y_train)
            accuracy = accuracy_score(y_test, xgb_model.predict(X_test))
            self.xgb_models[target] = xgb_model
            print(f"   {target}: {accuracy*100:.1f}% accuracy")
        
        # ===== MODELOS SOLO SOL =====
        print(f"\n{'='*70}")
        print("📊 ESTRATEGIA 2: Modelos INDIVIDUALES")
        print(f"{'='*70}")
        
        self.rf_models_sol, self.xgb_models_sol = self.entrenar_modelos_por_turno(0, "SOL (DÍA)")
        self.rf_models_luna, self.xgb_models_luna = self.entrenar_modelos_por_turno(1, "LUNA (NOCHE)")
        
        print("\n✅ Entrenamiento completado")
        print(f"\n{'='*70}")
        print("📌 RESUMEN DE MODELOS ENTRENADOS:")
        print(f"{'='*70}")
        print("  ✅ Modelos Combinados (SOL+LUNA): RF + XGBoost")
        print("  ✅ Modelos Solo SOL: RF + XGBoost")
        print("  ✅ Modelos Solo LUNA: RF + XGBoost")
        print(f"  📊 Total: 6 estrategias de predicción\n")
    
    def generar_predicciones_completas(self):
        """
        Genera predicciones para ambos turnos usando TODAS las estrategias
        y muestra comparación. GUARDA AUTOMÁTICAMENTE EN EL TRACKER.
        """
        print(f"\n{'='*70}")
        print("🔮 GENERACIÓN DE PREDICCIONES CON MÚLTIPLES ESTRATEGIAS")
        print(f"{'='*70}\n")
        
        ultimo_registro = self.df.iloc[-1]
        fecha_hoy = datetime.now()

        print(f"📅 Fecha actual: {fecha_hoy.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Predicciones para ambos turnos
        for turno in [0, 1]:
            turno_nombre = "SOL (DÍA)" if turno == 0 else "LUNA (NOCHE)"

            # Calcular fecha correcta según el turno usando funciones compartidas
            if turno == 0:
                fecha_prediccion = calcular_proximo_sorteo_sol()
            else:
                fecha_prediccion = calcular_proximo_sorteo_luna()

            print(f"🎯 Prediciendo para {turno_nombre}: {fecha_prediccion}")
            
            print(f"\n{'═'*70}")
            print(f"🎯 PREDICCIONES PARA: {turno_nombre}")
            print(f"{'═'*70}\n")
            
            # Preparar features
            features = [[
                turno,
                fecha_hoy.month,
                fecha_hoy.day,
                fecha_hoy.weekday(),
                ultimo_registro['Posicion_1'],
                ultimo_registro['Posicion_2'],
                ultimo_registro['Posicion_3'],
                ultimo_registro['Posicion_4'],
                ultimo_registro['Signo_Codigo'],
                ultimo_registro.get('Pos1_Lag1', 0),
                ultimo_registro.get('Pos2_Lag1', 0),
                ultimo_registro.get('Pos3_Lag1', 0),
                ultimo_registro.get('Pos4_Lag1', 0),
                ultimo_registro.get('Signo_Lag1', 0),
                ultimo_registro.get('Media_Pos1_10', 5),
                ultimo_registro.get('Media_Pos2_10', 5),
                ultimo_registro.get('Media_Pos3_10', 5),
                ultimo_registro.get('Media_Pos4_10', 5),
                ultimo_registro.get('Suma_Total', 20),
                ultimo_registro.get('Frecuencia_Signo', 100)
            ]]
            
            # Seleccionar modelos específicos según el turno
            if turno == 0:  # SOL
                rf_especifico = self.rf_models_sol
                xgb_especifico = self.xgb_models_sol
                estrategia_nombre = "ESPECÍFICO SOL"
            else:  # LUNA
                rf_especifico = self.rf_models_luna
                xgb_especifico = self.xgb_models_luna
                estrategia_nombre = "ESPECÍFICO LUNA"
            
            # ===== ESTRATEGIA 1: MODELOS COMBINADOS =====
            print("┌─────────────────────────────────────────────────────────────────────┐")
            print("│ ESTRATEGIA 1: Modelos COMBINADOS (entrenados con SOL + LUNA)       │")
            print("└─────────────────────────────────────────────────────────────────────┘\n")
            
            print("🌲 Random Forest (Combinado):")
            rf_comb_pred = []
            for i in range(1, 5):
                target = f'Posicion_{i}'
                pred = int(self.rf_models[target].predict(features)[0])
                rf_comb_pred.append(pred)
            rf_comb_numero = ''.join(map(str, rf_comb_pred))
            rf_comb_signo_num = int(self.rf_models['Signo_Codigo'].predict(features)[0])
            rf_comb_signo = self.SIGNOS_INVERSO.get(rf_comb_signo_num, 'Desconocido')
            print(f"   🎲 Número: {rf_comb_numero}")
            print(f"   ♈ Signo:  {rf_comb_signo}")
            
            print("\n🚀 XGBoost (Combinado):")
            xgb_comb_pred = []
            for i in range(1, 5):
                target = f'Posicion_{i}'
                pred = int(self.xgb_models[target].predict(features)[0])
                xgb_comb_pred.append(pred)
            xgb_comb_numero = ''.join(map(str, xgb_comb_pred))
            xgb_comb_signo_num = int(self.xgb_models['Signo_Codigo'].predict(features)[0])
            xgb_comb_signo = self.SIGNOS_INVERSO.get(xgb_comb_signo_num, 'Desconocido')
            print(f"   🎲 Número: {xgb_comb_numero}")
            print(f"   ♈ Signo:  {xgb_comb_signo}")
            
            # ===== ESTRATEGIA 2: MODELOS ESPECÍFICOS =====
            print(f"\n┌─────────────────────────────────────────────────────────────────────┐")
            print(f"│ ESTRATEGIA 2: Modelos {estrategia_nombre:45s} │")
            print(f"└─────────────────────────────────────────────────────────────────────┘\n")
            
            print(f"🌲 Random Forest ({estrategia_nombre}):")
            rf_esp_pred = []
            for i in range(1, 5):
                target = f'Posicion_{i}'
                pred = int(rf_especifico[target].predict(features)[0])
                rf_esp_pred.append(pred)
            rf_esp_numero = ''.join(map(str, rf_esp_pred))
            rf_esp_signo_num = int(rf_especifico['Signo_Codigo'].predict(features)[0])
            rf_esp_signo = self.SIGNOS_INVERSO.get(rf_esp_signo_num, 'Desconocido')
            print(f"   🎲 Número: {rf_esp_numero}")
            print(f"   ♈ Signo:  {rf_esp_signo}")
            
            print(f"\n🚀 XGBoost ({estrategia_nombre}):")
            xgb_esp_pred = []
            for i in range(1, 5):
                target = f'Posicion_{i}'
                pred = int(xgb_especifico[target].predict(features)[0])
                xgb_esp_pred.append(pred)
            xgb_esp_numero = ''.join(map(str, xgb_esp_pred))
            xgb_esp_signo_num = int(xgb_especifico['Signo_Codigo'].predict(features)[0])
            xgb_esp_signo = self.SIGNOS_INVERSO.get(xgb_esp_signo_num, 'Desconocido')
            print(f"   🎲 Número: {xgb_esp_numero}")
            print(f"   ♈ Signo:  {xgb_esp_signo}")
            
            # ===== ANÁLISIS DE CONSENSO =====
            print(f"\n{'─'*70}")
            print("📊 ANÁLISIS DE CONSENSO")
            print(f"{'─'*70}\n")
            
            todos_numeros = [rf_comb_numero, xgb_comb_numero, rf_esp_numero, xgb_esp_numero]
            todos_signos = [rf_comb_signo, xgb_comb_signo, rf_esp_signo, xgb_esp_signo]
            
            # Contar coincidencias de números
            from collections import Counter
            contador_numeros = Counter(todos_numeros)
            contador_signos = Counter(todos_signos)
            
            numero_mas_votado = contador_numeros.most_common(1)[0]
            signo_mas_votado = contador_signos.most_common(1)[0]
            
            print(f"Números predichos:")
            print(f"  • RF Combinado:  {rf_comb_numero}")
            print(f"  • XGB Combinado: {xgb_comb_numero}")
            print(f"  • RF Específico: {rf_esp_numero}")
            print(f"  • XGB Específico: {xgb_esp_numero}")
            
            if numero_mas_votado[1] >= 2:
                print(f"\n⭐ CONSENSO DETECTADO:")
                print(f"   {numero_mas_votado[1]}/4 modelos predicen: {numero_mas_votado[0]}")
            
            if numero_mas_votado[1] == 4:
                print(f"\n   🎯 ¡CONSENSO TOTAL! Los 4 modelos coinciden en: {numero_mas_votado[0]}")
            
            # ===== ANÁLISIS DE PROBABILIDADES =====
            print(f"\n{'─'*70}")
            print("📈 ANÁLISIS DE PROBABILIDADES (Modelo Específico)")
            print(f"{'─'*70}\n")
            self.mostrar_probabilidades(features, rf_especifico)
            
            # ===== RECOMENDACIÓN FINAL =====
            print(f"\n{'─'*70}")
            print(f"💡 RECOMENDACIÓN FINAL PARA {turno_nombre}")
            print(f"{'─'*70}\n")
            
            if numero_mas_votado[1] >= 3:
                print(f"   🥇 ALTA CONFIANZA: {numero_mas_votado[0]} - {signo_mas_votado[0]}")
                print(f"      ({numero_mas_votado[1]}/4 modelos coinciden)")
            elif numero_mas_votado[1] == 2:
                print(f"   🥈 CONFIANZA MEDIA:")
                print(f"      Opción A: {rf_esp_numero} - {rf_esp_signo} (Modelo Específico RF)")
                print(f"      Opción B: {xgb_esp_numero} - {xgb_esp_signo} (Modelo Específico XGB)")
            else:
                print(f"   ⚠️  PREDICCIONES DIVERGENTES - Usar con precaución:")
                print(f"      RF Específico: {rf_esp_numero} - {rf_esp_signo}")
                print(f"      XGB Específico: {xgb_esp_numero} - {xgb_esp_signo}")
            
            # ===== GUARDAR EN TRACKER =====
            predicciones_guardar = {
                "rf_combinado": {"numero": rf_comb_numero, "signo": rf_comb_signo},
                "xgb_combinado": {"numero": xgb_comb_numero, "signo": xgb_comb_signo},
                "rf_especifico": {"numero": rf_esp_numero, "signo": rf_esp_signo},
                "xgb_especifico": {"numero": xgb_esp_numero, "signo": xgb_esp_signo}
            }
            
            self.tracker.registrar_prediccion(fecha_prediccion, turno, predicciones_guardar)
    
    def mostrar_probabilidades(self, features, modelos_rf=None):
        """
        Muestra las probabilidades de cada dígito para cada posición
        
        Args:
            features: Features de entrada
            modelos_rf: Modelos RF a usar (si None, usa self.rf_models)
        """
        if modelos_rf is None:
            modelos_rf = self.rf_models
        
        for i in range(1, 5):
            target = f'Posicion_{i}'
            
            # Obtener probabilidades de Random Forest
            rf_probs = modelos_rf[target].predict_proba(features)[0]
            
            # Top 3 dígitos más probables
            top_indices = np.argsort(rf_probs)[-3:][::-1]
            
            print(f"   Posición {i} - Top 3 dígitos:")
            for idx in top_indices:
                prob = rf_probs[idx] * 100
                barra = "█" * int(prob / 5)  # Barra visual
                print(f"      Dígito {idx}: {prob:5.1f}% {barra}")

    def mostrar_resumen_aciertos(self):
        """
        Muestra un resumen simple de aciertos recientes
        """
        print(f"\n{'='*70}")
        print("📊 RESUMEN DE ACIERTOS - ÚLTIMAS PREDICCIONES")
        print(f"{'='*70}\n")

        # Obtener predicciones evaluadas
        evaluadas = [p for p in self.tracker.historial["predicciones"] if p.get("evaluado")]

        if not evaluadas:
            print("⚠️  Aún no hay predicciones evaluadas")
            print("💡 Las predicciones se evaluarán cuando haya resultados reales\n")
            return

        # Mostrar últimas 5 predicciones evaluadas
        ultimas = sorted(evaluadas, key=lambda x: x["fecha_sorteo"], reverse=True)[:5]

        print(f"Mostrando últimas {len(ultimas)} predicciones evaluadas:\n")

        for pred in ultimas:
            print(f"📅 {pred['fecha_sorteo']} - {pred['turno']}")
            print(f"   🎯 Resultado Real: {pred['resultado_real']['numero']} - {pred['resultado_real']['signo']}\n")

            if "aciertos" in pred:
                modelos_info = {
                    "rf_combinado": "RF Combinado",
                    "xgb_combinado": "XGB Combinado",
                    "rf_especifico": "RF Específico",
                    "xgb_especifico": "XGB Específico"
                }

                for modelo_key, modelo_nombre in modelos_info.items():
                    if modelo_key in pred["aciertos"] and modelo_key in pred:
                        acierto = pred["aciertos"][modelo_key]
                        prediccion = pred[modelo_key]
                        digitos = acierto["digitos_correctos"]
                        signo = "✅" if acierto["signo_correcto"] else "❌"

                        # Determinar emoji según aciertos
                        if digitos == 4 and acierto["signo_correcto"]:
                            emoji = "🎉"  # Perfecto
                        elif digitos >= 3:
                            emoji = "🔥"  # Muy bien
                        elif digitos >= 2:
                            emoji = "👍"  # Bien
                        else:
                            emoji = "⚠️"  # Bajo

                        print(f"   {emoji} {modelo_nombre:18s}: {prediccion['numero']} - {prediccion['signo']}")
                        print(f"      Aciertos: {digitos}/4 dígitos {signo} signo")

            print()

        # Estadísticas generales
        print(f"{'─'*70}")
        print("📈 ESTADÍSTICAS GENERALES (todas las predicciones evaluadas)\n")

        modelos_stats = {
            "rf_combinado": {"nombre": "RF Combinado", "total_dig": 0, "total_sig": 0, "perfectos": 0, "count": 0},
            "xgb_combinado": {"nombre": "XGB Combinado", "total_dig": 0, "total_sig": 0, "perfectos": 0, "count": 0},
            "rf_especifico": {"nombre": "RF Específico", "total_dig": 0, "total_sig": 0, "perfectos": 0, "count": 0},
            "xgb_especifico": {"nombre": "XGB Específico", "total_dig": 0, "total_sig": 0, "perfectos": 0, "count": 0}
        }

        for pred in evaluadas:
            if "aciertos" in pred:
                for modelo in modelos_stats.keys():
                    if modelo in pred["aciertos"]:
                        ac = pred["aciertos"][modelo]
                        modelos_stats[modelo]["total_dig"] += ac["digitos_correctos"]
                        if ac["signo_correcto"]:
                            modelos_stats[modelo]["total_sig"] += 1
                        if ac["digitos_correctos"] == 4 and ac["signo_correcto"]:
                            modelos_stats[modelo]["perfectos"] += 1
                        modelos_stats[modelo]["count"] += 1

        # Ordenar por promedio de dígitos
        ranking = sorted(modelos_stats.items(),
                        key=lambda x: x[1]["total_dig"] / max(x[1]["count"], 1),
                        reverse=True)

        for i, (key, stats) in enumerate(ranking, 1):
            if stats["count"] > 0:
                prom_dig = stats["total_dig"] / stats["count"]
                prom_sig = (stats["total_sig"] / stats["count"]) * 100

                medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

                print(f"{medalla} {stats['nombre']}")
                print(f"   Promedio dígitos: {prom_dig:.2f}/4")
                print(f"   Acierto signo: {prom_sig:.1f}%")
                print(f"   Predicciones perfectas: {stats['perfectos']}")
                print(f"   Total evaluado: {stats['count']}\n")

        print(f"{'─'*70}\n")

        # Mostrar tendencias y mejor modelo actual
        self.mostrar_mejor_modelo_actual(evaluadas, modelos_stats)

    def mostrar_mejor_modelo_actual(self, evaluadas, modelos_stats):
        """
        Muestra el modelo ganador actual y recomendación
        """
        if not evaluadas or not any(s["count"] > 0 for s in modelos_stats.values()):
            return

        print(f"{'='*70}")
        print("🏆 MODELO MÁS CONFIABLE ACTUALMENTE")
        print(f"{'='*70}\n")

        # Encontrar el mejor
        mejor = max(
            [(k, v) for k, v in modelos_stats.items() if v["count"] > 0],
            key=lambda x: (x[1]["total_dig"] / x[1]["count"], x[1]["total_sig"] / x[1]["count"])
        )

        mejor_nombre = mejor[1]["nombre"]
        mejor_prom = mejor[1]["total_dig"] / mejor[1]["count"]
        mejor_sig = (mejor[1]["total_sig"] / mejor[1]["count"]) * 100
        mejor_perfectos = mejor[1]["perfectos"]

        # Calcular precisión en porcentaje (cada dígito = 25%)
        precision_pct = (mejor_prom / 4) * 100

        print(f"┌{'─'*68}┐")
        print(f"│ {mejor_nombre:^66s} │")
        print(f"├{'─'*68}┤")
        print(f"│ Precisión en números:  {precision_pct:5.1f}% ({mejor_prom:.2f}/4 dígitos)     {'':>15s}│")
        print(f"│ Precisión en signos:   {mejor_sig:5.1f}%{'':>38s}│")
        print(f"│ Aciertos perfectos:    {mejor_perfectos:2d}{'':>43s}│")
        print(f"│ Total evaluado:        {mejor[1]['count']:2d}{'':>43s}│")
        print(f"└{'─'*68}┘\n")

        # Tendencia (comparar últimas 3 vs primeras 3)
        if len(evaluadas) >= 6:
            evaluadas_ordenadas = sorted(evaluadas, key=lambda x: x["fecha_sorteo"])

            primeras_3 = evaluadas_ordenadas[:3]
            ultimas_3 = evaluadas_ordenadas[-3:]

            prom_inicial = sum(
                p["aciertos"][mejor[0]]["digitos_correctos"]
                for p in primeras_3
                if "aciertos" in p and mejor[0] in p["aciertos"]
            ) / 3

            prom_reciente = sum(
                p["aciertos"][mejor[0]]["digitos_correctos"]
                for p in ultimas_3
                if "aciertos" in p and mejor[0] in p["aciertos"]
            ) / 3

            tendencia = "📈 Mejorando" if prom_reciente > prom_inicial else "📉 Bajando" if prom_reciente < prom_inicial else "➡️ Estable"

            print(f"📊 TENDENCIA: {tendencia}")
            print(f"   Primeros 3 sorteos: {prom_inicial:.2f}/4 dígitos")
            print(f"   Últimos 3 sorteos:  {prom_reciente:.2f}/4 dígitos\n")

        # Recomendación para la próxima apuesta
        print(f"{'─'*70}")
        print("💡 RECOMENDACIÓN PARA LA PRÓXIMA PREDICCIÓN")
        print(f"{'─'*70}\n")

        if precision_pct >= 65:
            confianza = "MUY ALTA ⭐⭐⭐"
            consejo = f"Confía principalmente en {mejor_nombre}"
        elif precision_pct >= 50:
            confianza = "ALTA ⭐⭐"
            consejo = f"Usa {mejor_nombre} como primera opción"
        elif precision_pct >= 35:
            confianza = "MEDIA ⭐"
            consejo = f"Considera {mejor_nombre}, pero combina con otros modelos"
        else:
            confianza = "BAJA ⚠️"
            consejo = "Los modelos aún están aprendiendo. Espera más datos"

        print(f"   Nivel de confianza: {confianza}")
        print(f"   Consejo: {consejo}\n")

        if mejor[1]["count"] < 5:
            print(f"   ⚠️  Aún hay pocos datos ({mejor[1]['count']} predicciones)")
            print(f"   💡 Ejecuta el script diariamente para mejorar la precisión\n")

        print(f"{'─'*70}\n")

    def ejecutar_completo(self, forzar_actualizacion=False, mostrar_reporte=True, dias_reporte=5):
        """
        Ejecuta el proceso completo: verificar datos, entrenar, predecir y hacer seguimiento
        
        Args:
            forzar_actualizacion: Forzar descarga de datos
            mostrar_reporte: Mostrar reporte de seguimiento
            dias_reporte: Días para el reporte
        """
        print("\n" + "="*70)
        print("🎰 SUPERASTRO ML PREDICTOR - VERSIÓN AUTÓNOMA 🎰")
        print("="*70)
        
        # Paso 1: Verificar y actualizar datos
        if not self.verificar_actualizar_datos(forzar_actualizacion):
            print("\n❌ No se pudo obtener datos actualizados")
            return False
        
        # Paso 2: Cargar datos
        if not self.cargar_datos():
            print("\n❌ No se pudo cargar los datos")
            return False
        
        # Paso 3: Actualizar resultados reales en el tracker
        print(f"\n{'='*70}")
        print("📝 ACTUALIZANDO RESULTADOS REALES")
        print(f"{'='*70}")
        self.tracker.actualizar_resultados_desde_datos(self.archivo_datos)
        
        # Paso 4: Mostrar reporte si hay predicciones evaluadas
        if mostrar_reporte:
            self.tracker.generar_reporte(dias_reporte)
        
        # Paso 5: Entrenar modelos
        self.entrenar_modelos()
        
        # Paso 6: Generar predicciones (se guardan automáticamente)
        self.generar_predicciones_completas()

        # Paso 7: Mostrar resumen de aciertos históricos
        self.mostrar_resumen_aciertos()

        print(f"\n{'='*70}")
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print(f"{'='*70}\n")

        print("📌 NOTAS IMPORTANTES:")
        print("   • Las predicciones son probabilísticas, no garantizadas")
        print("   • Basadas en análisis de patrones históricos")
        print("   • Los resultados de loterías son eventos aleatorios")
        print("   • Las predicciones se guardan automáticamente en predicciones_historial.json")
        print("   • Use esta información con responsabilidad\n")

        return True


def main():
    """
    Función principal
    """
    import sys
    
    # Verificar argumentos
    forzar_actualizacion = '--actualizar' in sys.argv or '-a' in sys.argv
    solo_reporte = '--reporte' in sys.argv or '-r' in sys.argv
    
    # Crear predictor
    predictor = SuperAstroMLPredictor()
    
    # Si solo quiere ver el reporte
    if solo_reporte:
        print("\n" + "="*70)
        print("📊 MODO REPORTE")
        print("="*70)
        
        # Buscar cuántos días
        dias = 5
        for i, arg in enumerate(sys.argv):
            if arg in ['--dias', '-d'] and i + 1 < len(sys.argv):
                try:
                    dias = int(sys.argv[i + 1])
                except:
                    dias = 5
        
        predictor.tracker.generar_reporte(dias)
    else:
        # Ejecutar proceso completo
        predictor.ejecutar_completo(forzar_actualizacion)


if __name__ == "__main__":
    main()