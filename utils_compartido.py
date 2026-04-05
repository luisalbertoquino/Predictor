# -*- coding: utf-8 -*-
"""
Utilidades Compartidas para SuperAstro
Maneja archivos JSON y Excel de forma centralizada
Autor: Luis Alberto Quino
Versión: 1.0
"""

import json
import os
from datetime import datetime, timedelta

# Archivo de historial de predicciones (JSON)
ARCHIVO_JSON = 'predicciones_historial.json'

# Re-exportar funciones de BD para que los scripts existentes solo importen utils_compartido
from db import cargar_datos_raw, cargar_datos_ml, init_db

def cargar_historial():
    """Carga el historial de predicciones del JSON único"""
    if os.path.exists(ARCHIVO_JSON):
        try:
            with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'predicciones': []}
    return {'predicciones': []}

def guardar_historial(historial):
    """Guarda el historial en el JSON único"""
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

def agregar_prediccion(prediccion):
    """
    Agrega o actualiza una predicción en el historial
    Si ya existe una predicción para la misma fecha/turno, la combina
    """
    historial = cargar_historial()

    # Buscar si ya existe predicción para esta fecha/turno
    fecha_sorteo = prediccion.get('fecha_sorteo')
    turno = prediccion.get('turno')

    prediccion_existente = None
    indice_existente = None

    for i, pred in enumerate(historial['predicciones']):
        if pred.get('fecha_sorteo') == fecha_sorteo and pred.get('turno') == turno:
            prediccion_existente = pred
            indice_existente = i
            break

    if prediccion_existente:
        # Combinar predicciones
        # Copiar campos directos si no existen
        for campo in ['rf_combinado', 'xgb_combinado', 'rf_especifico', 'xgb_especifico']:
            if campo in prediccion and campo not in prediccion_existente:
                prediccion_existente[campo] = prediccion[campo]

        # Combinar metodos
        if 'metodos' not in prediccion_existente:
            prediccion_existente['metodos'] = {}
        if 'metodos' in prediccion and prediccion['metodos']:
            prediccion_existente['metodos'].update(prediccion['metodos'])

        # Actualizar consenso si es nuevo
        if 'consenso' in prediccion and prediccion['consenso']:
            if 'consenso' not in prediccion_existente or not prediccion_existente['consenso']:
                prediccion_existente['consenso'] = prediccion['consenso']

        # Actualizar fecha de última modificación
        prediccion_existente['fecha_prediccion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Reemplazar en el historial
        historial['predicciones'][indice_existente] = prediccion_existente
    else:
        # Agregar nueva predicción
        historial['predicciones'].append(prediccion)

    # Ordenar por fecha_sorteo y turno (SOL primero, luego LUNA)
    historial['predicciones'].sort(
        key=lambda x: (x.get('fecha_sorteo', ''), 0 if x.get('turno') == 'SOL' else 1),
        reverse=True
    )

    guardar_historial(historial)
    return historial

def limpiar_historial():
    """
    Limpia el historial eliminando duplicados y ordenando
    Combina predicciones duplicadas en una sola entrada
    """
    historial = cargar_historial()
    predicciones_unicas = {}

    for pred in historial['predicciones']:
        key = f"{pred.get('fecha_sorteo')}_{pred.get('turno')}"

        if key not in predicciones_unicas:
            # Asegurar que tenga estructura correcta
            if 'metodos' not in pred:
                pred['metodos'] = {}
            if 'consenso' not in pred:
                pred['consenso'] = None
            predicciones_unicas[key] = pred
        else:
            # Combinar con la existente
            existente = predicciones_unicas[key]

            # Copiar campos directos
            for campo in ['rf_combinado', 'xgb_combinado', 'rf_especifico', 'xgb_especifico']:
                if campo in pred and campo not in existente:
                    existente[campo] = pred[campo]

            # Combinar metodos
            if 'metodos' in pred and pred['metodos']:
                if 'metodos' not in existente:
                    existente['metodos'] = {}
                existente['metodos'].update(pred['metodos'])

            # Actualizar consenso
            if 'consenso' in pred and pred['consenso'] and not existente.get('consenso'):
                existente['consenso'] = pred['consenso']

            # Mantener el evaluado y resultado real si existen
            if pred.get('evaluado') and not existente.get('evaluado'):
                existente['evaluado'] = pred['evaluado']
                existente['resultado_real'] = pred.get('resultado_real')
                existente['aciertos'] = pred.get('aciertos')

    # Convertir de vuelta a lista y ordenar
    historial['predicciones'] = sorted(
        predicciones_unicas.values(),
        key=lambda x: (x.get('fecha_sorteo', ''), 0 if x.get('turno') == 'SOL' else 1),
        reverse=True
    )

    guardar_historial(historial)
    print(f"[OK] Historial limpiado: {len(historial['predicciones'])} predicciones unicas")
    return historial

# ========== FESTIVOS DE COLOMBIA 2026 ==========
FESTIVOS_COLOMBIA_2026 = [
    "2026-01-01",  # Año Nuevo
    "2026-01-12",  # Día de los Reyes Magos
    "2026-03-23",  # Día de San José
    "2026-04-09",  # Jueves Santo
    "2026-04-10",  # Viernes Santo
    "2026-05-01",  # Día del Trabajo
    "2026-05-25",  # Ascensión del Señor
    "2026-06-15",  # Corpus Christi
    "2026-06-22",  # Sagrado Corazón de Jesús
    "2026-06-29",  # San Pedro y San Pablo
    "2026-07-20",  # Día de la Independencia
    "2026-08-07",  # Batalla de Boyacá
    "2026-08-17",  # Asunción de la Virgen
    "2026-10-12",  # Día de la Raza
    "2026-11-02",  # Día de Todos los Santos
    "2026-11-16",  # Independencia de Cartagena
    "2026-12-08",  # Inmaculada Concepción
    "2026-12-25",  # Navidad
]

def es_festivo(fecha):
    """
    Verifica si una fecha es festivo en Colombia

    Args:
        fecha: datetime o string en formato YYYY-MM-DD

    Returns:
        bool: True si es festivo, False en caso contrario
    """
    if isinstance(fecha, datetime):
        fecha_str = fecha.strftime("%Y-%m-%d")
    else:
        fecha_str = fecha

    return fecha_str in FESTIVOS_COLOMBIA_2026

def calcular_proximo_sorteo_sol():
    """
    Calcula la fecha del próximo sorteo SOL
    SOL juega de lunes a sábado a las 4:00 PM (16:00)
    No juega domingos ni festivos

    Returns:
        str: Fecha del próximo sorteo SOL en formato YYYY-MM-DD
    """
    ahora = datetime.now()
    fecha_candidata = ahora

    # Si ya pasaron las 4:00 PM de hoy, empezar desde mañana
    if ahora.hour >= 16:
        fecha_candidata = ahora + timedelta(days=1)

    # Buscar el próximo día hábil (lunes a sábado, no festivo)
    while True:
        dia_semana = fecha_candidata.weekday()  # 0=Lunes, 6=Domingo

        # Si es domingo (6), saltar al lunes
        if dia_semana == 6:
            fecha_candidata = fecha_candidata + timedelta(days=1)
            continue

        # Si es festivo, saltar al siguiente día
        if es_festivo(fecha_candidata):
            fecha_candidata = fecha_candidata + timedelta(days=1)
            continue

        # Si llegamos aquí, es un día válido
        break

    return fecha_candidata.strftime("%Y-%m-%d")

def calcular_proximo_sorteo_luna():
    """
    Calcula la fecha del próximo sorteo LUNA
    LUNA juega todos los días:
    - Lunes a Viernes: 10:40 PM (22:40)
    - Sábado: 10:42 PM (22:42)
    - Domingo: 10:42 PM (22:42)

    Returns:
        str: Fecha del próximo sorteo LUNA en formato YYYY-MM-DD
    """
    ahora = datetime.now()
    fecha_candidata = ahora
    dia_semana = ahora.weekday()
    hora_actual = ahora.hour
    minuto_actual = ahora.minute

    # Determinar hora de corte según el día
    if dia_semana == 6 or dia_semana == 5:  # Sábado o Domingo
        hora_corte = 22
        minuto_corte = 42
    else:  # Lunes a viernes
        hora_corte = 22
        minuto_corte = 40

    # Si ya pasó la hora del sorteo de hoy, ir a mañana
    if hora_actual > hora_corte or (hora_actual == hora_corte and minuto_actual >= minuto_corte):
        fecha_candidata = ahora + timedelta(days=1)

    return fecha_candidata.strftime("%Y-%m-%d")

def calcular_proximos_sorteos():
    """
    Calcula las fechas de los próximos 4 sorteos (2 SOL + 2 LUNA)

    Returns:
        list: Lista de tuplas (fecha, turno) ordenadas cronológicamente
    """
    sorteos = []
    ahora = datetime.now()

    # Calcular próximo SOL
    fecha_sol = calcular_proximo_sorteo_sol()
    sorteos.append((fecha_sol, 'SOL'))

    # Calcular segundo SOL (buscar después del primero)
    fecha_temp = datetime.strptime(fecha_sol, "%Y-%m-%d") + timedelta(days=1)
    contador = 0
    while contador < 10:  # Límite de seguridad
        dia_semana = fecha_temp.weekday()
        if dia_semana != 6 and not es_festivo(fecha_temp):  # No domingo ni festivo
            sorteos.append((fecha_temp.strftime("%Y-%m-%d"), 'SOL'))
            break
        fecha_temp = fecha_temp + timedelta(days=1)
        contador += 1

    # Calcular próximo LUNA
    fecha_luna = calcular_proximo_sorteo_luna()
    sorteos.append((fecha_luna, 'LUNA'))

    # Calcular segundo LUNA
    fecha_temp = datetime.strptime(fecha_luna, "%Y-%m-%d") + timedelta(days=1)
    sorteos.append((fecha_temp.strftime("%Y-%m-%d"), 'LUNA'))

    # Ordenar cronológicamente
    sorteos.sort(key=lambda x: (x[0], 0 if x[1] == 'SOL' else 1))

    return sorteos[:4]  # Retornar solo los primeros 4
