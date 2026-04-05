# -*- coding: utf-8 -*-
"""
Módulo de base de datos - SuperAstro
Maneja la conexión MySQL y todas las operaciones de datos
Reemplaza el uso de archivos Excel
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime

# ──────────────────────────────────────────────────────────
# Configuración de conexión
# ──────────────────────────────────────────────────────────

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'database': 'superastro_db',
    'charset': 'utf8mb4',
}

DB_PASSWORD_FILE = '/root/.db_password'


def _leer_password():
    """Lee la contraseña de MySQL desde el archivo de configuración del servidor."""
    # En producción (VPS): leer del archivo
    if os.path.exists(DB_PASSWORD_FILE):
        with open(DB_PASSWORD_FILE, 'r') as f:
            for line in f:
                match = re.search(r'root_mysql_pass=["\']?([^"\'\\n]+)["\']?', line.strip())
                if match:
                    return match.group(1)
    # En desarrollo local: usar variable de entorno
    return os.environ.get('MYSQL_ROOT_PASSWORD', '')


def get_connection():
    """Retorna una conexión activa a MySQL."""
    import pymysql
    password = _leer_password()
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=password,
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


# ──────────────────────────────────────────────────────────
# Inicialización del esquema
# ──────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE DATABASE IF NOT EXISTS superastro_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE superastro_db;

CREATE TABLE IF NOT EXISTS sorteo_resultados (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    fecha           DATE        NOT NULL,
    turno           TINYINT     NOT NULL COMMENT '0=SOL, 1=LUNA',
    tipo_astro      VARCHAR(10) NOT NULL,
    numero_completo CHAR(4)     NOT NULL,
    posicion_1      TINYINT     NOT NULL,
    posicion_2      TINYINT     NOT NULL,
    posicion_3      TINYINT     NOT NULL,
    posicion_4      TINYINT     NOT NULL,
    signo_nombre    VARCHAR(20) NOT NULL,
    signo_codigo    TINYINT     NOT NULL,
    sorteo          INT,
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fecha_turno (fecha, turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def init_db():
    """Crea la base de datos y la tabla si no existen."""
    import pymysql
    password = _leer_password()
    # Conectar sin seleccionar BD para poder crearla
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=password,
        charset=DB_CONFIG['charset'],
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            for statement in SCHEMA_SQL.split(';'):
                stmt = statement.strip()
                if stmt:
                    cur.execute(stmt)
        print('[DB] Base de datos inicializada correctamente')
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────
# Operaciones de escritura
# ──────────────────────────────────────────────────────────

def insertar_resultado(fecha, turno, tipo_astro, numero_completo,
                       posicion_1, posicion_2, posicion_3, posicion_4,
                       signo_nombre, signo_codigo, sorteo=None):
    """
    Inserta o actualiza un resultado de sorteo.
    Si ya existe el registro (fecha + turno), lo actualiza.
    """
    sql = """
        INSERT INTO sorteo_resultados
            (fecha, turno, tipo_astro, numero_completo,
             posicion_1, posicion_2, posicion_3, posicion_4,
             signo_nombre, signo_codigo, sorteo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            numero_completo = VALUES(numero_completo),
            posicion_1      = VALUES(posicion_1),
            posicion_2      = VALUES(posicion_2),
            posicion_3      = VALUES(posicion_3),
            posicion_4      = VALUES(posicion_4),
            signo_nombre    = VALUES(signo_nombre),
            signo_codigo    = VALUES(signo_codigo),
            sorteo          = VALUES(sorteo)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                fecha, turno, tipo_astro, numero_completo,
                posicion_1, posicion_2, posicion_3, posicion_4,
                signo_nombre, signo_codigo, sorteo
            ))
        conn.commit()
    finally:
        conn.close()


def insertar_resultados_lote(lista_resultados):
    """
    Inserta o actualiza una lista de resultados en un solo batch.
    lista_resultados: lista de dicts con las mismas claves que insertar_resultado()
    """
    if not lista_resultados:
        return 0

    sql = """
        INSERT INTO sorteo_resultados
            (fecha, turno, tipo_astro, numero_completo,
             posicion_1, posicion_2, posicion_3, posicion_4,
             signo_nombre, signo_codigo, sorteo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            numero_completo = VALUES(numero_completo),
            posicion_1      = VALUES(posicion_1),
            posicion_2      = VALUES(posicion_2),
            posicion_3      = VALUES(posicion_3),
            posicion_4      = VALUES(posicion_4),
            signo_nombre    = VALUES(signo_nombre),
            signo_codigo    = VALUES(signo_codigo),
            sorteo          = VALUES(sorteo)
    """
    valores = [
        (
            r['Fecha'], r['Turno'], r['Tipo_Astro'], r['Numero_Completo'],
            r['Posicion_1'], r['Posicion_2'], r['Posicion_3'], r['Posicion_4'],
            r['Signo_Nombre'], r['Signo_Codigo'], r.get('Sorteo')
        )
        for r in lista_resultados
    ]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, valores)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────
# Operaciones de lectura
# ──────────────────────────────────────────────────────────

def cargar_datos_raw():
    """
    Carga todos los resultados como DataFrame.
    Equivalente a leer la hoja 'Datos_Raw' del Excel anterior.
    Retorna DataFrame con columnas:
        Fecha, Turno, Tipo_Astro, Numero_Completo,
        Posicion_1..4, Signo_Nombre, Signo_Codigo, Sorteo
    """
    sql = """
        SELECT
            fecha           AS Fecha,
            turno           AS Turno,
            tipo_astro      AS Tipo_Astro,
            numero_completo AS Numero_Completo,
            posicion_1      AS Posicion_1,
            posicion_2      AS Posicion_2,
            posicion_3      AS Posicion_3,
            posicion_4      AS Posicion_4,
            signo_nombre    AS Signo_Nombre,
            signo_codigo    AS Signo_Codigo,
            sorteo          AS Sorteo
        FROM sorteo_resultados
        ORDER BY fecha ASC, turno ASC
    """
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    finally:
        conn.close()


def cargar_datos_ml():
    """
    Carga datos con features de ML calculados.
    Equivalente a la hoja 'Datos_ML_Entrenamiento' del Excel anterior.
    Incluye: lag features (5 períodos), rolling averages (10),
             features temporales, Suma_Total, Frecuencia_Signo.
    """
    df = cargar_datos_raw()
    if df.empty:
        return df
    return _calcular_features_ml(df)


def obtener_resultado(fecha_str, turno):
    """
    Obtiene un resultado específico para una fecha y turno.
    turno: 'SOL' o 'LUNA'
    Retorna dict {'numero': '1234', 'signo': 'Aries'} o None.
    """
    turno_num = 0 if turno == 'SOL' else 1
    sql = """
        SELECT numero_completo, signo_nombre
        FROM sorteo_resultados
        WHERE fecha = %s AND turno = %s
        LIMIT 1
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (fecha_str, turno_num))
            row = cur.fetchone()
        if row:
            return {
                'numero': str(row['numero_completo']).zfill(4),
                'signo':  row['signo_nombre']
            }
        return None
    finally:
        conn.close()


def ultima_fecha():
    """Retorna la fecha más reciente registrada en la BD o None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(fecha) AS uf FROM sorteo_resultados")
            row = cur.fetchone()
        if row and row['uf']:
            return str(row['uf'])
        return None
    finally:
        conn.close()


def total_registros():
    """Retorna el total de registros en la BD."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM sorteo_resultados")
            return cur.fetchone()['n']
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────
# Exportación CSV
# ──────────────────────────────────────────────────────────

def exportar_csv():
    """
    Exporta todos los resultados como string CSV.
    Usado por el endpoint de descarga del dashboard.
    """
    df = cargar_datos_raw()
    if df.empty:
        return ''
    # Formatear fecha para CSV
    df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d')
    df['Turno'] = df['Turno'].map({0: 'SOL', 1: 'LUNA'})
    return df.to_csv(index=False)


# ──────────────────────────────────────────────────────────
# Cálculo de features ML (uso interno)
# ──────────────────────────────────────────────────────────

def _calcular_features_ml(df):
    """
    Agrega features temporales y de secuencia al DataFrame raw.
    Misma lógica que SuperAstroMLExtractor.preparar_para_ml().
    """
    df = df.copy()

    # Features temporales
    df['Año']        = df['Fecha'].dt.year
    df['Mes']        = df['Fecha'].dt.month
    df['Dia_Mes']    = df['Fecha'].dt.day
    df['Dia_Semana'] = df['Fecha'].dt.dayofweek
    df['Semana_Año'] = df['Fecha'].dt.isocalendar().week.astype(int)

    # Ordenar para que los lags sean correctos
    df = df.sort_values(['Fecha', 'Turno']).reset_index(drop=True)

    # Lag features (últimos 5)
    for i in range(1, 6):
        df[f'Pos1_Lag{i}']  = df['Posicion_1'].shift(i)
        df[f'Pos2_Lag{i}']  = df['Posicion_2'].shift(i)
        df[f'Pos3_Lag{i}']  = df['Posicion_3'].shift(i)
        df[f'Pos4_Lag{i}']  = df['Posicion_4'].shift(i)
        df[f'Signo_Lag{i}'] = df['Signo_Codigo'].shift(i)

    # Medias móviles (ventana 10)
    df['Media_Pos1_10'] = df['Posicion_1'].rolling(10).mean()
    df['Media_Pos2_10'] = df['Posicion_2'].rolling(10).mean()
    df['Media_Pos3_10'] = df['Posicion_3'].rolling(10).mean()
    df['Media_Pos4_10'] = df['Posicion_4'].rolling(10).mean()

    # Suma dígitos y frecuencia de signo
    df['Suma_Total']       = df['Posicion_1'] + df['Posicion_2'] + df['Posicion_3'] + df['Posicion_4']
    df['Frecuencia_Signo'] = df.groupby('Signo_Codigo')['Signo_Codigo'].transform('count')

    # Eliminar filas con NaN (los primeros registros sin historial suficiente)
    return df.dropna().reset_index(drop=True)
