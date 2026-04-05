#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro Predicción Avanzada - Métodos Alternativos
Análisis de patrones, frecuencias y algoritmos de secuencias
Autor: Luis Alberto Quino
Versión: 1.0
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import itertools
import json

# Importar utilidades compartidas
from utils_compartido import (
    agregar_prediccion,
    ARCHIVO_EXCEL,
    ARCHIVO_JSON,
    calcular_proximo_sorteo_sol,
    calcular_proximo_sorteo_luna
)


class SuperAstroPrediccionAvanzada:
    """
    Métodos avanzados de predicción basados en análisis de patrones
    """

    def __init__(self, archivo_datos):
        """
        Inicializa con datos históricos
        """
        from db import cargar_datos_raw
        self.df = cargar_datos_raw()
        print(f"\n✅ Datos cargados: {len(self.df)} registros")
        print(f"📅 Rango: {self.df['Fecha'].min()} a {self.df['Fecha'].max()}\n")

    def analisis_frecuencia(self, turno=None, ultimos_n=100):
        """
        Método 1: Análisis de Frecuencia
        Predice basándose en los números más frecuentes
        """
        print(f"\n{'='*70}")
        print("📊 MÉTODO 1: ANÁLISIS DE FRECUENCIA")
        print(f"{'='*70}\n")

        # Filtrar por turno si se especifica
        if turno is not None:
            df_filtrado = self.df[self.df['Turno'] == turno].tail(ultimos_n)
            turno_str = "SOL" if turno == 0 else "LUNA"
        else:
            df_filtrado = self.df.tail(ultimos_n)
            turno_str = "AMBOS"

        print(f"Analizando últimos {len(df_filtrado)} sorteos ({turno_str})\n")

        # Contar frecuencia por posición
        frecuencias = {}
        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in df_filtrado.columns:
                frecuencias[pos] = Counter(df_filtrado[col])

        # Obtener dígitos más frecuentes por posición
        prediccion = []
        for pos in range(1, 5):
            if pos in frecuencias:
                mas_frecuente = frecuencias[pos].most_common(3)
                digito_pred = mas_frecuente[0][0]
                prediccion.append(digito_pred)

                print(f"Posición {pos}:")
                for digito, freq in mas_frecuente:
                    porcentaje = (freq / len(df_filtrado)) * 100
                    print(f"   Dígito {digito}: {freq} veces ({porcentaje:.1f}%)")

        numero_predicho = ''.join(map(str, prediccion))

        # Predecir signo
        signos_freq = Counter(df_filtrado['Signo_Nombre'])
        signo_pred = signos_freq.most_common(1)[0][0]

        print(f"\nSigno más frecuente: {signo_pred}")

        print(f"\n🎯 PREDICCIÓN POR FRECUENCIA: {numero_predicho} - {signo_pred}")

        return {"numero": numero_predicho, "signo": signo_pred, "metodo": "frecuencia"}

    def analisis_secuencial(self, turno=None):
        """
        Método 2: Análisis Secuencial
        Busca patrones en secuencias de números
        """
        print(f"\n{'='*70}")
        print("🔄 MÉTODO 2: ANÁLISIS SECUENCIAL (Markov Chain)")
        print(f"{'='*70}\n")

        # Filtrar por turno
        if turno is not None:
            df_filtrado = self.df[self.df['Turno'] == turno]
            turno_str = "SOL" if turno == 0 else "LUNA"
        else:
            df_filtrado = self.df
            turno_str = "AMBOS"

        print(f"Analizando patrones de secuencia ({turno_str})\n")

        # Crear cadenas de Markov para cada posición
        prediccion = []

        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in df_filtrado.columns:
                # Obtener secuencias
                secuencia = df_filtrado[col].tolist()

                # Crear transiciones (qué dígito sigue a cada dígito)
                transiciones = defaultdict(Counter)

                for i in range(len(secuencia) - 1):
                    actual = secuencia[i]
                    siguiente = secuencia[i + 1]
                    transiciones[actual][siguiente] += 1

                # Predecir basándose en el último valor
                ultimo_digito = secuencia[-1]

                if ultimo_digito in transiciones and transiciones[ultimo_digito]:
                    siguiente_pred = transiciones[ultimo_digito].most_common(1)[0][0]
                    prediccion.append(siguiente_pred)

                    print(f"Posición {pos}:")
                    print(f"   Último dígito: {ultimo_digito}")
                    print(f"   Predicción siguiente: {siguiente_pred}")

                    # Mostrar top 3 transiciones
                    top_trans = transiciones[ultimo_digito].most_common(3)
                    print(f"   Transiciones más comunes desde {ultimo_digito}:")
                    for dig, freq in top_trans:
                        print(f"      → {dig}: {freq} veces")
                else:
                    # Fallback: usar el más frecuente
                    prediccion.append(Counter(secuencia).most_common(1)[0][0])
                    print(f"Posición {pos}: Sin patrón claro, usando frecuencia")

        numero_predicho = ''.join(map(str, prediccion))

        # Predecir signo con el mismo método
        signos = df_filtrado['Signo_Nombre'].tolist()
        signo_pred = signos[-1]  # Simplificado

        print(f"\n🎯 PREDICCIÓN SECUENCIAL: {numero_predicho} - {signo_pred}")

        return {"numero": numero_predicho, "signo": signo_pred, "metodo": "secuencial"}

    def analisis_ciclos(self, turno=None):
        """
        Método 3: Análisis de Ciclos
        Detecta ciclos y patrones repetitivos
        """
        print(f"\n{'='*70}")
        print("🔁 MÉTODO 3: ANÁLISIS DE CICLOS Y PATRONES")
        print(f"{'='*70}\n")

        # Filtrar por turno
        if turno is not None:
            df_filtrado = self.df[self.df['Turno'] == turno]
            turno_str = "SOL" if turno == 0 else "LUNA"
        else:
            df_filtrado = self.df
            turno_str = "AMBOS"

        print(f"Buscando ciclos en datos ({turno_str})\n")

        # Analizar números completos
        numeros = df_filtrado['Numero_Completo'].tolist()

        # Buscar patrones que se repiten
        patrones = Counter(numeros)
        mas_repetidos = patrones.most_common(10)

        print("Números más repetidos en la historia:")
        for num, freq in mas_repetidos[:5]:
            print(f"   {num}: {freq} veces")

        # Buscar ciclos de aparición
        print("\nAnálisis de intervalos:")

        ultimo_numero = numeros[-1]

        # Encontrar cuándo apareció este número antes
        indices = [i for i, x in enumerate(numeros) if x == ultimo_numero]

        if len(indices) > 1:
            intervalos = [indices[i+1] - indices[i] for i in range(len(indices)-1)]
            promedio_intervalo = sum(intervalos) / len(intervalos)

            print(f"   Último número: {ultimo_numero}")
            print(f"   Apareció {len(indices)} veces")
            print(f"   Intervalo promedio: {promedio_intervalo:.1f} sorteos")

        # Predicción: siguiente número en el ciclo de frecuencia
        # Usar el número que hace más tiempo no sale
        conteo_ausencia = {}
        for num in set(numeros):
            ultima_aparicion = len(numeros) - 1 - numeros[::-1].index(num)
            dias_sin_salir = len(numeros) - 1 - ultima_aparicion
            conteo_ausencia[num] = dias_sin_salir

        # Top 5 números que hace más tiempo no salen
        mas_atrasados = sorted(conteo_ausencia.items(), key=lambda x: x[1], reverse=True)[:5]

        print(f"\nNúmeros que hace más tiempo no salen:")
        for num, dias in mas_atrasados:
            print(f"   {num}: {dias} sorteos atrás")

        numero_pred = mas_atrasados[0][0]

        # Signo del número predicho
        fila_num = df_filtrado[df_filtrado['Numero_Completo'] == numero_pred]
        if not fila_num.empty:
            signo_pred = fila_num.iloc[-1]['Signo_Nombre']
        else:
            signo_pred = df_filtrado['Signo_Nombre'].mode()[0]

        print(f"\n🎯 PREDICCIÓN POR CICLOS: {numero_pred} - {signo_pred}")
        print(f"   Razón: Hace {mas_atrasados[0][1]} sorteos que no sale")

        return {"numero": numero_pred, "signo": signo_pred, "metodo": "ciclos"}

    def analisis_hot_cold(self, turno=None, ultimos_n=50):
        """
        Método 4: Análisis Hot/Cold Numbers
        Números calientes (salen mucho) vs fríos (no salen)
        """
        print(f"\n{'='*70}")
        print("🔥❄️ MÉTODO 4: ANÁLISIS HOT/COLD NUMBERS")
        print(f"{'='*70}\n")

        # Filtrar por turno
        if turno is not None:
            df_filtrado = self.df[self.df['Turno'] == turno].tail(ultimos_n)
            turno_str = "SOL" if turno == 0 else "LUNA"
        else:
            df_filtrado = self.df.tail(ultimos_n)
            turno_str = "AMBOS"

        print(f"Analizando últimos {len(df_filtrado)} sorteos ({turno_str})\n")

        # Análisis por posición
        prediccion_hot = []
        prediccion_cold = []

        for pos in range(1, 5):
            col = f'Posicion_{pos}'
            if col in df_filtrado.columns:
                freq = Counter(df_filtrado[col])

                # Hot: más frecuente
                hot = freq.most_common(1)[0][0]

                # Cold: menos frecuente (que haya salido al menos 1 vez)
                cold = freq.most_common()[-1][0]

                prediccion_hot.append(hot)
                prediccion_cold.append(cold)

                print(f"Posición {pos}:")
                print(f"   🔥 HOT:  {hot} ({freq[hot]} veces)")
                print(f"   ❄️  COLD: {cold} ({freq[cold]} veces)")

        numero_hot = ''.join(map(str, prediccion_hot))
        numero_cold = ''.join(map(str, prediccion_cold))

        # Signo hot
        signos_freq = Counter(df_filtrado['Signo_Nombre'])
        signo_hot = signos_freq.most_common(1)[0][0]
        signo_cold = signos_freq.most_common()[-1][0]

        print(f"\n🎯 PREDICCIÓN HOT (números calientes): {numero_hot} - {signo_hot}")
        print(f"🎯 PREDICCIÓN COLD (números fríos): {numero_cold} - {signo_cold}")

        # Estrategia mixta: combinar hot y cold
        prediccion_mixta = []
        for i in range(4):
            if i % 2 == 0:
                prediccion_mixta.append(prediccion_hot[i])
            else:
                prediccion_mixta.append(prediccion_cold[i])

        numero_mixto = ''.join(map(str, prediccion_mixta))
        print(f"\n💡 ESTRATEGIA MIXTA: {numero_mixto} - {signo_hot}")

        return {
            "hot": {"numero": numero_hot, "signo": signo_hot},
            "cold": {"numero": numero_cold, "signo": signo_cold},
            "mixto": {"numero": numero_mixto, "signo": signo_hot},
            "metodo": "hot_cold"
        }

    def predecir_todo(self, turno=0):
        """
        Ejecuta todos los métodos y muestra resultados
        """
        turno_str = "SOL (DÍA)" if turno == 0 else "LUNA (NOCHE)"
        turno_nombre = "SOL" if turno == 0 else "LUNA"

        print("\n" + "="*70)
        print(f"🔮 PREDICCIONES AVANZADAS PARA: {turno_str}")
        print("="*70)

        # Ejecutar todos los métodos
        pred_freq = self.analisis_frecuencia(turno)
        pred_seq = self.analisis_secuencial(turno)
        pred_ciclo = self.analisis_ciclos(turno)
        pred_hc = self.analisis_hot_cold(turno)

        # Resumen final
        print(f"\n{'='*70}")
        print("📋 RESUMEN DE TODAS LAS PREDICCIONES")
        print(f"{'='*70}\n")

        print(f"1️⃣  Frecuencia:        {pred_freq['numero']} - {pred_freq['signo']}")
        print(f"2️⃣  Secuencial:        {pred_seq['numero']} - {pred_seq['signo']}")
        print(f"3️⃣  Ciclos:            {pred_ciclo['numero']} - {pred_ciclo['signo']}")
        print(f"4️⃣  Hot Numbers:       {pred_hc['hot']['numero']} - {pred_hc['hot']['signo']}")
        print(f"5️⃣  Cold Numbers:      {pred_hc['cold']['numero']} - {pred_hc['cold']['signo']}")
        print(f"6️⃣  Estrategia Mixta:  {pred_hc['mixto']['numero']} - {pred_hc['mixto']['signo']}")

        # Buscar consenso
        todos_numeros = [
            pred_freq['numero'],
            pred_seq['numero'],
            pred_ciclo['numero'],
            pred_hc['hot']['numero'],
            pred_hc['mixto']['numero']
        ]

        # Contar signos para consenso
        todos_signos = [
            pred_freq['signo'],
            pred_seq['signo'],
            pred_ciclo['signo'],
            pred_hc['hot']['signo'],
            pred_hc['mixto']['signo']
        ]

        consenso_num = Counter(todos_numeros)
        mas_votado = consenso_num.most_common(1)[0]

        consenso_signo = Counter(todos_signos)
        signo_votado = consenso_signo.most_common(1)[0][0]

        print(f"\n{'─'*70}")
        if mas_votado[1] >= 2:
            print(f"⭐ CONSENSO DETECTADO: {mas_votado[0]} - {signo_votado}")
            print(f"   {mas_votado[1]} métodos coinciden")
        else:
            print("⚠️  No hay consenso entre métodos")
            print("💡 Recomendación: Usar estrategia combinada")

        print(f"{'─'*70}\n")

        # Guardar en historial JSON
        fecha_pred = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calcular fecha correcta según el turno
        if turno_nombre == "SOL":
            fecha_sorteo = calcular_proximo_sorteo_sol()
        else:
            fecha_sorteo = calcular_proximo_sorteo_luna()

        entrada = {
            "fecha_prediccion": fecha_pred,
            "fecha_sorteo": fecha_sorteo,
            "turno": turno_nombre,
            "evaluado": False,
            "resultado_real": None,
            "metodos": {
                "Metodo1": {"numero": pred_freq['numero'], "signo": pred_freq['signo']},  # Frecuencia
                "Metodo2": {"numero": pred_seq['numero'], "signo": pred_seq['signo']},    # Secuencial
                "Metodo3": {"numero": pred_ciclo['numero'], "signo": pred_ciclo['signo']}, # Ciclos
                "Metodo4": {"numero": pred_hc['mixto']['numero'], "signo": pred_hc['mixto']['signo']} # Mixto
            },
            "consenso": {
                "numero": mas_votado[0],
                "signo": signo_votado,
                "nivel_consenso": f"{mas_votado[1]}/5 métodos",
                "confianza": "Alta" if mas_votado[1] >= 3 else "Media" if mas_votado[1] >= 2 else "Baja"
            } if mas_votado[1] >= 2 else None
        }

        agregar_prediccion(entrada)
        print(f"[OK] Predicciones guardadas en {ARCHIVO_JSON}")

        return {
            "frecuencia": pred_freq,
            "secuencial": pred_seq,
            "ciclos": pred_ciclo,
            "hot_cold": pred_hc
        }


def main():
    """
    Función principal
    """
    import os

    # Usar archivo compartido
    if not os.path.exists(ARCHIVO_EXCEL):
        print("❌ No se encontró archivo de datos")
        print("💡 Ejecuta primero superastro_ml_predictor.py para descargar datos")
        return

    archivo = ARCHIVO_EXCEL

    print("\n" + "="*70)
    print("🎯 SUPERASTRO - MÉTODOS AVANZADOS DE PREDICCIÓN")
    print("="*70)

    predictor = SuperAstroPrediccionAvanzada(archivo)

    # Predecir para SOL
    predictor.predecir_todo(turno=0)

    # Predecir para LUNA
    predictor.predecir_todo(turno=1)

    print("\n" + "="*70)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*70 + "\n")

    print("📌 NOTA SOBRE LOS MÉTODOS:")
    print("   • Frecuencia: Usa los dígitos que más salen")
    print("   • Secuencial: Analiza qué dígito suele seguir a otro")
    print("   • Ciclos: Busca números que hace tiempo no salen")
    print("   • Hot/Cold: Combina números calientes y fríos")
    print("\n⚠️  Recuerda: Las loterías son aleatorias, estos son solo análisis estadísticos\n")


if __name__ == "__main__":
    main()
