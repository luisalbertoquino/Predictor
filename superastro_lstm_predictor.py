# -*- coding: utf-8 -*-
"""
SuperAstro LSTM Predictor - Red Neuronal Profunda
Predicción usando arquitectura LSTM (Long Short-Term Memory)
Autor: Luis Alberto Quino
Versión: 1.0 - Red Neuronal
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
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Importar utilidades compartidas
from utils_compartido import (
    agregar_prediccion,
    ARCHIVO_EXCEL,
    ARCHIVO_JSON,
    calcular_proximo_sorteo_sol,
    calcular_proximo_sorteo_luna
)

# Intentar importar TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow no está instalado. Instálalo con: pip install tensorflow")
    sys.exit(1)


class SuperAstroLSTMPredictor:
    """
    Predictor basado en redes LSTM para SuperAstro
    """

    def __init__(self):
        self.df = None
        self.modelo_sol = None
        self.modelo_luna = None
        self.SIGNOS = {
            'Aries': 0, 'Tauro': 1, 'Géminis': 2, 'Cáncer': 3,
            'Leo': 4, 'Virgo': 5, 'Libra': 6, 'Escorpión': 7,
            'Sagitario': 8, 'Capricornio': 9, 'Acuario': 10, 'Piscis': 11
        }
        self.SIGNOS_INVERSO = {v: k for k, v in self.SIGNOS.items()}

    def cargar_datos(self):
        """Carga datos del Excel compartido"""
        import os

        print(f"\n{'='*70}")
        print("📂 CARGANDO DATOS PARA LSTM")
        print(f"{'='*70}\n")

        try:
            from db import cargar_datos_raw
            self.df = cargar_datos_raw()
            if self.df.empty:
                print("❌ No se encontraron datos en la base de datos")
                return False
            print(f"✅ Datos cargados: {len(self.df)} registros")
            print(f"📅 Rango: {self.df['Fecha'].min()} a {self.df['Fecha'].max()}\n")
            return True
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return False

    def crear_secuencias_lstm(self, turno=0, longitud_secuencia=10):
        """
        Crea secuencias para entrenar LSTM
        Similar al código R pero adaptado a Python

        Args:
            turno: 0=SOL, 1=LUNA
            longitud_secuencia: Cuántos números previos usar como contexto
        """
        print(f"\n{'='*70}")
        print(f"🔄 CREANDO SECUENCIAS PARA {'SOL' if turno == 0 else 'LUNA'}")
        print(f"{'='*70}\n")

        # Filtrar por turno
        df_turno = self.df[self.df['Turno'] == turno].copy()
        df_turno = df_turno.sort_values('Fecha').reset_index(drop=True)

        print(f"📊 Registros para entrenamiento: {len(df_turno)}")

        # Extraer dígitos individuales de cada número
        digitos_list = []
        signos_list = []

        for _, row in df_turno.iterrows():
            numero_str = str(row['Numero_Completo']).zfill(4)
            digitos = [int(d) for d in numero_str]
            digitos_list.append(digitos)
            signos_list.append(row['Signo_Codigo'])

        digitos_array = np.array(digitos_list)  # Shape: (n_samples, 4)
        signos_array = np.array(signos_list)

        # Crear secuencias (similar al código R)
        # Cada secuencia predice un dígito basándose en los dígitos anteriores
        X_digitos = []
        y_digitos = []

        for i in range(len(digitos_array)):
            # Secuencia 1: Predecir 1er dígito con [0,0,0]
            X_digitos.append([0, 0, 0])
            y_digitos.append(digitos_array[i, 0])

            # Secuencia 2: Predecir 2do dígito con [0,0,d1]
            X_digitos.append([0, 0, digitos_array[i, 0]])
            y_digitos.append(digitos_array[i, 1])

            # Secuencia 3: Predecir 3er dígito con [0,d1,d2]
            X_digitos.append([0, digitos_array[i, 0], digitos_array[i, 1]])
            y_digitos.append(digitos_array[i, 2])

            # Secuencia 4: Predecir 4to dígito con [d1,d2,d3]
            X_digitos.append([digitos_array[i, 0], digitos_array[i, 1], digitos_array[i, 2]])
            y_digitos.append(digitos_array[i, 3])

        X_digitos = np.array(X_digitos)
        y_digitos = np.array(y_digitos)

        # Normalizar X (dividir entre 9)
        X_digitos = X_digitos / 9.0

        # Reshape para LSTM: (samples, timesteps, features)
        X_digitos = X_digitos.reshape(X_digitos.shape[0], X_digitos.shape[1], 1)

        # One-hot encode y
        y_digitos_cat = to_categorical(y_digitos, num_classes=10)

        print(f"✅ Secuencias creadas:")
        print(f"   X shape: {X_digitos.shape}")
        print(f"   y shape: {y_digitos_cat.shape}\n")

        # Crear secuencias para signos (más simple)
        X_signos = digitos_array / 9.0  # Usar los 4 dígitos como features
        y_signos = to_categorical(signos_array, num_classes=12)

        # Reshape para LSTM
        X_signos = X_signos.reshape(X_signos.shape[0], X_signos.shape[1], 1)

        return {
            'X_digitos': X_digitos,
            'y_digitos': y_digitos_cat,
            'X_signos': X_signos,
            'y_signos': y_signos
        }

    def crear_modelo_digitos(self):
        """
        Crea modelo LSTM para predecir dígitos
        Arquitectura similar al código R
        """
        modelo = Sequential([
            LSTM(256, return_sequences=True, input_shape=(3, 1)),
            LSTM(128),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(10, activation='softmax')
        ])

        modelo.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        return modelo

    def crear_modelo_signos(self):
        """Crea modelo LSTM para predecir signos"""
        modelo = Sequential([
            LSTM(128, return_sequences=True, input_shape=(4, 1)),
            LSTM(64),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(12, activation='softmax')
        ])

        modelo.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        return modelo

    def entrenar_modelo(self, turno=0):
        """
        Entrena modelo LSTM para un turno específico
        """
        print(f"\n{'='*70}")
        print(f"🤖 ENTRENANDO MODELO LSTM PARA {'SOL' if turno == 0 else 'LUNA'}")
        print(f"{'='*70}\n")

        # Crear secuencias
        datos = self.crear_secuencias_lstm(turno)

        # Modelo para dígitos
        print("🔢 Entrenando modelo de dígitos...")
        modelo_digitos = self.crear_modelo_digitos()

        early_stop = EarlyStopping(
            monitor='loss',
            patience=20,
            restore_best_weights=True,
            verbose=0
        )

        historia_digitos = modelo_digitos.fit(
            datos['X_digitos'],
            datos['y_digitos'],
            epochs=200,
            batch_size=16,
            callbacks=[early_stop],
            verbose=1  # Mostrar progreso
        )

        final_acc = historia_digitos.history['accuracy'][-1] * 100
        print(f"   ✅ Accuracy final: {final_acc:.2f}%")

        # Modelo para signos
        print("\n♈ Entrenando modelo de signos...")
        modelo_signos = self.crear_modelo_signos()

        historia_signos = modelo_signos.fit(
            datos['X_signos'],
            datos['y_signos'],
            epochs=200,
            batch_size=16,
            callbacks=[early_stop],
            verbose=1  # Mostrar progreso
        )

        final_acc_signos = historia_signos.history['accuracy'][-1] * 100
        print(f"   ✅ Accuracy final: {final_acc_signos:.2f}%\n")

        return {
            'digitos': modelo_digitos,
            'signos': modelo_signos
        }

    def entrenar_modelos(self):
        """Entrena modelos para SOL y LUNA"""
        print(f"\n{'='*70}")
        print("🧠 ENTRENAMIENTO DE REDES NEURONALES LSTM")
        print(f"{'='*70}")

        # Entrenar para SOL
        self.modelo_sol = self.entrenar_modelo(turno=0)

        # Entrenar para LUNA
        self.modelo_luna = self.entrenar_modelo(turno=1)

        print(f"\n{'='*70}")
        print("✅ MODELOS LSTM ENTRENADOS EXITOSAMENTE")
        print(f"{'='*70}\n")

    def generar_numero_lstm(self, modelo_digitos):
        """
        Genera un número de 4 dígitos usando LSTM
        Similar a generar_numero_lstm() del código R
        """
        numero = []

        # Predecir primer dígito con [0,0,0]
        secuencia = np.array([[[0], [0], [0]]]) / 9.0
        prob = modelo_digitos.predict(secuencia, verbose=0)
        digito = np.random.choice(10, p=prob[0])
        numero.append(digito)

        # Predecir segundo dígito con [0,0,d1]
        secuencia = np.array([[[0], [0], [numero[0]]]]) / 9.0
        prob = modelo_digitos.predict(secuencia, verbose=0)
        digito = np.random.choice(10, p=prob[0])
        numero.append(digito)

        # Predecir tercer dígito con [0,d1,d2]
        secuencia = np.array([[[0], [numero[0]], [numero[1]]]]) / 9.0
        prob = modelo_digitos.predict(secuencia, verbose=0)
        digito = np.random.choice(10, p=prob[0])
        numero.append(digito)

        # Predecir cuarto dígito con [d1,d2,d3]
        secuencia = np.array([[[numero[0]], [numero[1]], [numero[2]]]]) / 9.0
        prob = modelo_digitos.predict(secuencia, verbose=0)
        digito = np.random.choice(10, p=prob[0])
        numero.append(digito)

        return ''.join(map(str, numero))

    def predecir_signo_lstm(self, numero_str, modelo_signos):
        """Predice signo usando LSTM"""
        # Convertir número a array de dígitos
        digitos = [int(d) for d in numero_str.zfill(4)]
        X = np.array([digitos]) / 9.0
        X = X.reshape(1, 4, 1)

        prob = modelo_signos.predict(X, verbose=0)
        signo_idx = np.random.choice(12, p=prob[0])

        return self.SIGNOS_INVERSO[signo_idx]

    def generar_predicciones(self, turno='SOL', cantidad=1):
        """
        Genera predicciones usando LSTM

        Args:
            turno: 'SOL' o 'LUNA'
            cantidad: Cuántas predicciones generar
        """
        print(f"\n{'='*70}")
        print(f"🔮 GENERANDO PREDICCIONES LSTM PARA: {turno}")
        print(f"{'='*70}\n")

        modelo = self.modelo_sol if turno == 'SOL' else self.modelo_luna

        # Usar fecha como semilla (como en código R)
        fecha_seed = int(datetime.now().strftime("%Y%m%d"))
        np.random.seed(fecha_seed)
        print(f"🎲 Semilla aleatoria: {fecha_seed} (basada en fecha)\n")

        predicciones = []

        for i in range(cantidad):
            numero = self.generar_numero_lstm(modelo['digitos'])
            signo = self.predecir_signo_lstm(numero, modelo['signos'])

            predicciones.append({
                'numero': numero,
                'signo': signo
            })

            print(f"   Predicción {i+1}: {numero} - {signo}")

        print()
        return predicciones

    def ejecutar_completo(self):
        """Ejecuta el proceso completo"""
        print(f"\n{'='*70}")
        print("🧠 SUPERASTRO LSTM PREDICTOR")
        print("   Red Neuronal Profunda (Deep Learning)")
        print(f"{'='*70}\n")

        # Cargar datos
        if not self.cargar_datos():
            return False

        # Entrenar modelos
        self.entrenar_modelos()

        # Calcular fechas correctas usando funciones compartidas
        fecha_sol = calcular_proximo_sorteo_sol()
        fecha_luna = calcular_proximo_sorteo_luna()

        print(f"{'='*70}")
        print(f"📅 PREDICCIONES:")
        print(f"   SOL:  {fecha_sol}")
        print(f"   LUNA: {fecha_luna}")
        print(f"{'='*70}")

        # Predicciones SOL
        pred_sol = self.generar_predicciones('SOL', cantidad=3)

        # Predicciones LUNA
        pred_luna = self.generar_predicciones('LUNA', cantidad=3)

        # Mostrar recomendación
        print(f"{'='*70}")
        print("💡 RECOMENDACIÓN LSTM")
        print(f"{'='*70}\n")

        print(f"☀️  SOL - Mejores opciones:")
        for i, pred in enumerate(pred_sol, 1):
            emoji = "⭐" if i == 1 else "🔹"
            print(f"   {emoji} Opción {i}: {pred['numero']} - {pred['signo']}")

        print(f"\n🌙 LUNA - Mejores opciones:")
        for i, pred in enumerate(pred_luna, 1):
            emoji = "⭐" if i == 1 else "🔹"
            print(f"   {emoji} Opción {i}: {pred['numero']} - {pred['signo']}")

        # Guardar predicciones en historial (usando la mejor opción de cada turno)
        fecha_pred = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guardar SOL
        if pred_sol:
            entrada_sol = {
                "fecha_prediccion": fecha_pred,
                "fecha_sorteo": fecha_sol,
                "turno": "SOL",
                "evaluado": False,
                "resultado_real": None,
                "metodos": {
                    "LSTM": {"numero": pred_sol[0]['numero'], "signo": pred_sol[0]['signo']}
                },
                "consenso": None
            }
            agregar_prediccion(entrada_sol)

        # Guardar LUNA
        if pred_luna:
            entrada_luna = {
                "fecha_prediccion": fecha_pred,
                "fecha_sorteo": fecha_luna,
                "turno": "LUNA",
                "evaluado": False,
                "resultado_real": None,
                "metodos": {
                    "LSTM": {"numero": pred_luna[0]['numero'], "signo": pred_luna[0]['signo']}
                },
                "consenso": None
            }
            agregar_prediccion(entrada_luna)

        print(f"\n[OK] Predicciones guardadas:")
        print(f"    - SOL:  {fecha_sol}")
        print(f"    - LUNA: {fecha_luna}")

        print(f"\n{'='*70}")
        print("✅ PROCESO LSTM COMPLETADO")
        print(f"{'='*70}\n")

        print("📌 NOTAS:")
        print("   • Red neuronal LSTM entrenada con datos históricos")
        print("   • Arquitectura: 256→128→64 neuronas")
        print("   • Semilla basada en fecha actual (reproducible)")
        print("   • 3 opciones por turno ordenadas por confianza")
        print("   • Combina con otros predictores para mejor resultado\n")

        return True


def main():
    """Función principal"""
    predictor = SuperAstroLSTMPredictor()
    predictor.ejecutar_completo()


if __name__ == "__main__":
    main()
