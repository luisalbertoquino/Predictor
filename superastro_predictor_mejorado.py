#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro Predictor Mejorado - Con Limpieza Estadística Avanzada
Incluye: One-Hot Encoding, Test Durbin-Watson, Estacionariedad
Autor: Luis Alberto Quino
Versión: 1.0 - Científicamente Mejorado
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
import os
import glob
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller
warnings.filterwarnings('ignore')

# Importar utilidades compartidas
from utils_compartido import (
    agregar_prediccion,
    ARCHIVO_JSON,
    calcular_proximo_sorteo_sol,
    calcular_proximo_sorteo_luna
)


class SuperAstroMejorado:
    """
    Predictor mejorado con técnicas estadísticas avanzadas
    """

    # Mapeo de signos
    SIGNOS_MAP = {
        'Aries': 0, 'Tauro': 1, 'Géminis': 2, 'Geminis': 2,
        'Cáncer': 3, 'Cancer': 3, 'Leo': 4, 'Virgo': 5,
        'Libra': 6, 'Escorpión': 7, 'Escorpion': 7,
        'Sagitario': 8, 'Capricornio': 9, 'Acuario': 10, 'Piscis': 11
    }

    SIGNOS_INVERSO = {v: k for k, v in SIGNOS_MAP.items() if k in [
        'Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo',
        'Libra', 'Escorpión', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis'
    ]}

    def __init__(self):
        self.df = None
        self.df_limpio = None
        self.modelos = {}
        self.scaler = StandardScaler()

    def cargar_datos(self):
        """Carga los datos desde la base de datos MySQL."""
        print("\n" + "="*70)
        print("📂 CARGANDO Y LIMPIANDO DATOS")
        print("="*70 + "\n")

        from db import cargar_datos_raw
        self.df = cargar_datos_raw()

        if self.df.empty:
            print("❌ No se encontraron datos en la base de datos")
            return False

        print(f"✅ Datos cargados: {len(self.df)} registros")
        print(f"📅 Rango: {self.df['Fecha'].min()} a {self.df['Fecha'].max()}\n")
        return True

    def analizar_autocorrelacion(self):
        """
        Test de Durbin-Watson para detectar autocorrelación
        Valores cercanos a 2 = no autocorrelación (aleatorio)
        Valores < 1 o > 3 = autocorrelación significativa
        """
        print(f"\n{'='*70}")
        print("📊 ANÁLISIS DE AUTOCORRELACIÓN (Test Durbin-Watson)")
        print(f"{'='*70}\n")

        resultados = {}

        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in self.df.columns:
                valores = self.df[col].values
                dw = durbin_watson(valores)

                # Interpretación
                if 1.5 <= dw <= 2.5:
                    interpretacion = "✅ Aleatorio (sin memoria)"
                    señal = "Baja"
                elif dw < 1.5:
                    interpretacion = "🔥 Autocorrelación positiva (¡hay patrón!)"
                    señal = "Alta"
                else:
                    interpretacion = "⚠️  Autocorrelación negativa"
                    señal = "Media"

                resultados[col] = {"dw": dw, "señal": señal}

                print(f"Posición {pos}:")
                print(f"   Durbin-Watson: {dw:.4f}")
                print(f"   Interpretación: {interpretacion}")
                print(f"   Señal útil para ML: {señal}\n")

        # Signo
        signos_num = self.df['Signo_Codigo'].values
        dw_signo = durbin_watson(signos_num)

        if 1.5 <= dw_signo <= 2.5:
            interpretacion = "✅ Aleatorio"
            señal = "Baja"
        elif dw_signo < 1.5:
            interpretacion = "🔥 Autocorrelación positiva"
            señal = "Alta"
        else:
            interpretacion = "⚠️  Autocorrelación negativa"
            señal = "Media"

        print(f"Signo Zodiacal:")
        print(f"   Durbin-Watson: {dw_signo:.4f}")
        print(f"   Interpretación: {interpretacion}")
        print(f"   Señal útil para ML: {señal}\n")

        resultados['Signo'] = {"dw": dw_signo, "señal": señal}

        print(f"{'─'*70}")
        print("💡 CONCLUSIÓN:")
        if any(r["señal"] == "Alta" for r in resultados.values()):
            print("   🎯 ¡Se detectaron patrones! Los modelos pueden aprovecharlos")
        else:
            print("   ⚠️  Los datos son mayormente aleatorios")
            print("   💡 Los modelos tendrán precisión limitada")
        print(f"{'─'*70}\n")

        return resultados

    def test_estacionariedad(self):
        """
        Test de Dickey-Fuller Aumentado
        Verifica si la serie es estacionaria (no tiene tendencia)
        """
        print(f"\n{'='*70}")
        print("📈 TEST DE ESTACIONARIEDAD (Augmented Dickey-Fuller)")
        print(f"{'='*70}\n")

        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in self.df.columns:
                valores = self.df[col].values
                resultado = adfuller(valores)

                p_value = resultado[1]

                if p_value < 0.05:
                    interpretacion = "✅ Estacionaria (bueno para ML)"
                else:
                    interpretacion = "⚠️  No estacionaria (necesita diferenciación)"

                print(f"Posición {pos}:")
                print(f"   P-value: {p_value:.4f}")
                print(f"   Interpretación: {interpretacion}\n")

        print(f"{'─'*70}\n")

    def aplicar_one_hot_encoding(self):
        """
        Convierte signos a One-Hot Encoding
        En lugar de 0-11, crea 12 columnas con 0/1
        """
        print(f"\n{'='*70}")
        print("🔢 APLICANDO ONE-HOT ENCODING A SIGNOS")
        print(f"{'='*70}\n")

        # Crear copia del DataFrame
        self.df_limpio = self.df.copy()

        # One-Hot Encoding para signos
        for i in range(12):
            nombre_signo = self.SIGNOS_INVERSO[i]
            self.df_limpio[f'Signo_{nombre_signo}'] = (self.df_limpio['Signo_Codigo'] == i).astype(int)

        print("✅ Signos convertidos a One-Hot Encoding")
        print(f"   Se crearon 12 columnas: Signo_Aries, Signo_Tauro, etc.")
        print(f"   Cada fila tiene un 1 en su signo y 0 en los demás\n")

        # Ejemplo
        ejemplo = self.df_limpio.iloc[0]
        signo_real = ejemplo['Signo_Nombre']
        print(f"Ejemplo (Fecha: {ejemplo['Fecha']}, Signo: {signo_real}):")
        for i in range(12):
            nombre_signo = self.SIGNOS_INVERSO[i]
            valor = ejemplo[f'Signo_{nombre_signo}']
            if valor == 1:
                print(f"   Signo_{nombre_signo}: {valor} ✓")
        print()

    def crear_diferencias(self):
        """
        Crea columnas de diferencias (estacionariedad)
        y_t - y_{t-1} para remover tendencias
        También crea lags para One-Hot de signos
        """
        print(f"\n{'='*70}")
        print("📉 CREANDO DIFERENCIAS Y LAGS")
        print(f"{'='*70}\n")

        # Diferencias para posiciones
        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in self.df_limpio.columns:
                # Diferencia de primer orden
                self.df_limpio[f'{col}_Diff'] = self.df_limpio[col].diff()

        # Diferencia en suma total
        if 'Suma_Total' in self.df_limpio.columns:
            self.df_limpio['Suma_Total_Diff'] = self.df_limpio['Suma_Total'].diff()

        # Crear lags para One-Hot de signos
        for i in range(12):
            nombre_signo = self.SIGNOS_INVERSO[i]
            col_signo = f'Signo_{nombre_signo}'
            if col_signo in self.df_limpio.columns:
                self.df_limpio[f'{col_signo}_Lag1'] = self.df_limpio[col_signo].shift(1)

        print("✅ Columnas de diferencias creadas:")
        print("   Posicion_1_Diff, Posicion_2_Diff, etc.")
        print("✅ Lags de One-Hot signos creados:")
        print("   Signo_Aries_Lag1, Signo_Tauro_Lag1, etc.")
        print("   Esto ayuda a detectar cambios, no valores absolutos\n")

    def preparar_features_mejoradas(self):
        """
        Prepara features con las mejoras aplicadas
        """
        print(f"\n{'='*70}")
        print("⚙️  PREPARANDO FEATURES MEJORADAS")
        print(f"{'='*70}\n")

        # Features básicas
        feature_cols = [
            'Turno', 'Mes', 'Dia_Mes', 'Dia_Semana'
        ]

        # Agregar lags
        for i in range(1, 6):
            feature_cols.extend([
                f'Pos1_Lag{i}', f'Pos2_Lag{i}',
                f'Pos3_Lag{i}', f'Pos4_Lag{i}'
            ])

        # Agregar medias móviles
        feature_cols.extend([
            'Media_Pos1_10', 'Media_Pos2_10',
            'Media_Pos3_10', 'Media_Pos4_10'
        ])

        # Agregar diferencias
        feature_cols.extend([
            'Posicion_1_Diff', 'Posicion_2_Diff',
            'Posicion_3_Diff', 'Posicion_4_Diff'
        ])

        # Agregar One-Hot lags de signos (ya creados en crear_diferencias)
        for i in range(12):
            nombre_signo = self.SIGNOS_INVERSO[i]
            feature_cols.append(f'Signo_{nombre_signo}_Lag1')

        # Limpiar NaNs
        self.df_limpio = self.df_limpio.dropna()

        # Filtrar solo columnas que existen
        feature_cols = [col for col in feature_cols if col in self.df_limpio.columns]

        print(f"✅ Features preparadas: {len(feature_cols)} columnas")
        print(f"   Registros disponibles: {len(self.df_limpio)}")
        print(f"\nCategorías de features:")
        print(f"   • Temporales: Turno, Mes, Día")
        print(f"   • Lags: Valores anteriores (5 pasos)")
        print(f"   • Medias móviles: Promedios últimos 10")
        print(f"   • Diferencias: Cambios entre valores")
        print(f"   • Signos One-Hot: 12 columnas binarias\n")

        return feature_cols

    def entrenar_modelos_mejorados(self, turno=None):
        """
        Entrena modelos con los datos limpios
        """
        print(f"\n{'='*70}")
        print("🤖 ENTRENANDO MODELOS CON DATOS LIMPIOS")
        print(f"{'='*70}\n")

        # Filtrar por turno si se especifica
        if turno is not None:
            df_train = self.df_limpio[self.df_limpio['Turno'] == turno].copy()
            turno_str = "SOL" if turno == 0 else "LUNA"
            print(f"🎯 Entrenando para: {turno_str}")
        else:
            df_train = self.df_limpio.copy()
            turno_str = "COMBINADO"
            print(f"🎯 Entrenando modelo combinado")

        print(f"📊 Registros de entrenamiento: {len(df_train)}\n")

        # Preparar features
        feature_cols = self.preparar_features_mejoradas()

        # Entrenar para cada posición
        for pos in range(1, 5):
            target = f'Posicion_{pos}'

            X = df_train[feature_cols]
            y = df_train[target]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # XGBoost
            modelo = xgb.XGBClassifier(
                n_estimators=150,
                max_depth=8,
                learning_rate=0.05,
                random_state=42,
                n_jobs=-1
            )

            modelo.fit(X_train, y_train)
            acc = accuracy_score(y_test, modelo.predict(X_test))

            self.modelos[f'{turno_str}_{target}'] = modelo

            print(f"   ✅ {target}: {acc*100:.2f}% accuracy")

        # Entrenar para signos (clasificación multiclase con One-Hot)
        # Usamos Signo_Codigo como target
        X = df_train[feature_cols]
        y = df_train['Signo_Codigo']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        modelo_signo = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.05,
            num_class=12,
            random_state=42,
            n_jobs=-1
        )

        modelo_signo.fit(X_train, y_train)
        acc = accuracy_score(y_test, modelo_signo.predict(X_test))

        self.modelos[f'{turno_str}_Signo'] = modelo_signo

        print(f"   ✅ Signo: {acc*100:.2f}% accuracy\n")

    def predecir(self, turno=0):
        """
        Genera predicción con modelos mejorados
        """
        turno_str = "SOL" if turno == 0 else "LUNA"

        print(f"\n{'='*70}")
        print(f"🔮 PREDICCIÓN PARA: {turno_str}")
        print(f"{'='*70}\n")

        # Preparar features del último registro
        ultimo = self.df_limpio.iloc[-1]
        feature_cols = self.preparar_features_mejoradas()

        # Crear features para predicción
        features_pred = []
        for col in feature_cols:
            if col in ultimo.index:
                features_pred.append(ultimo[col])
            else:
                features_pred.append(0)

        features_pred = np.array(features_pred).reshape(1, -1)

        # Predecir cada posición
        prediccion = []
        for pos in range(1, 5):
            target = f'Posicion_{pos}'
            modelo_key = f'{turno_str}_{target}'

            if modelo_key not in self.modelos:
                modelo_key = f'COMBINADO_{target}'

            if modelo_key in self.modelos:
                pred = self.modelos[modelo_key].predict(features_pred)[0]
                prediccion.append(int(pred))

        numero = ''.join(map(str, prediccion))

        # Predecir signo
        modelo_signo_key = f'{turno_str}_Signo'
        if modelo_signo_key not in self.modelos:
            modelo_signo_key = 'COMBINADO_Signo'

        if modelo_signo_key in self.modelos:
            signo_num = self.modelos[modelo_signo_key].predict(features_pred)[0]
            signo = self.SIGNOS_INVERSO.get(int(signo_num), 'Desconocido')
        else:
            signo = 'Desconocido'

        print(f"🎲 Número predicho: {numero}")
        print(f"♈ Signo predicho: {signo}\n")

        return {"numero": numero, "signo": signo}

    def ejecutar_completo(self):
        """
        Proceso completo mejorado
        """
        print("\n" + "="*70)
        print("🎯 SUPERASTRO PREDICTOR MEJORADO")
        print("   Con Limpieza Estadística Avanzada")
        print("="*70)

        # 1. Cargar datos
        if not self.cargar_datos():
            return

        # 2. Análisis de autocorrelación
        self.analizar_autocorrelacion()

        # 3. Test de estacionariedad
        self.test_estacionariedad()

        # 4. Aplicar One-Hot Encoding
        self.aplicar_one_hot_encoding()

        # 5. Crear diferencias
        self.crear_diferencias()

        # 6. Entrenar modelos mejorados
        self.entrenar_modelos_mejorados(turno=0)  # SOL
        self.entrenar_modelos_mejorados(turno=1)  # LUNA

        # 7. Generar predicciones
        pred_sol = self.predecir(turno=0)
        pred_luna = self.predecir(turno=1)

        # 8. Guardar predicciones en historial
        fecha_pred = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_sorteo_sol = calcular_proximo_sorteo_sol()
        fecha_sorteo_luna = calcular_proximo_sorteo_luna()

        # Guardar SOL
        entrada_sol = {
            "fecha_prediccion": fecha_pred,
            "fecha_sorteo": fecha_sorteo_sol,
            "turno": "SOL",
            "evaluado": False,
            "resultado_real": None,
            "metodos": {
                "Estadistico": pred_sol
            },
            "consenso": None
        }
        agregar_prediccion(entrada_sol)

        # Guardar LUNA
        entrada_luna = {
            "fecha_prediccion": fecha_pred,
            "fecha_sorteo": fecha_sorteo_luna,
            "turno": "LUNA",
            "evaluado": False,
            "resultado_real": None,
            "metodos": {
                "Estadistico": pred_luna
            },
            "consenso": None
        }
        agregar_prediccion(entrada_luna)

        print(f"\n[OK] Predicciones guardadas:")
        print(f"    - SOL:  {fecha_sorteo_sol}")
        print(f"    - LUNA: {fecha_sorteo_luna}")

        print(f"\n{'='*70}")
        print("✅ PROCESO COMPLETADO")
        print(f"{'='*70}\n")

        print("📌 MEJORAS APLICADAS:")
        print("   ✅ One-Hot Encoding para signos")
        print("   ✅ Test Durbin-Watson (autocorrelación)")
        print("   ✅ Test Dickey-Fuller (estacionariedad)")
        print("   ✅ Diferenciación para remover tendencias")
        print("   ✅ Features expandidas con lags de signos\n")


def main():
    predictor = SuperAstroMejorado()
    predictor.ejecutar_completo()


if __name__ == "__main__":
    main()
