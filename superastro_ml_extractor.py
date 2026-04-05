#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SuperAstro ML Data Extractor
Extrae datos históricos y los prepara para Machine Learning
Autor: Luis Alberto Quino
Versión: 2.0
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import numpy as np
from pathlib import Path
import os

# (ARCHIVO_EXCEL eliminado - los datos se guardan en MySQL)

class SuperAstroMLExtractor:
    """
    Extractor de datos de SuperAstro optimizado para Machine Learning
    """
    
    # Mapeo de signos zodiacales a números (0-11 para compatibilidad con XGBoost)
    SIGNOS_MAP = {
        'Aries': 0,
        'Tauro': 1,
        'Geminis': 2,
        'Géminis': 2,
        'Cancer': 3,
        'Cáncer': 3,
        'Leo': 4,
        'Virgo': 5,
        'Libra': 6,
        'Escorpion': 7,
        'Escorpión': 7,
        'Sagitario': 8,
        'Capricornio': 9,
        'Acuario': 10,
        'Piscis': 11
    }
    
    def __init__(self):
        self.url = "https://superastro.com.co/historico.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Referer': 'https://superastro.com.co/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def extraer_numero_correcto(self, td_numero):
        """
        Extrae el número de 4 dígitos correctamente del HTML
        """
        try:
            # Buscar el <b> dentro del <div>
            div = td_numero.find('div')
            if div:
                b_tag = div.find('b')
                if b_tag:
                    numero = b_tag.text.strip()
                    # Asegurar que tenga 4 dígitos
                    return numero.zfill(4)
            
            # Fallback: buscar directamente
            numero = td_numero.text.strip().replace('<b>', '').replace('</b>', '')
            return numero.zfill(4)
        except:
            return "0000"
    
    def extraer_por_fecha(self, tipo_astro, fecha):
        """
        Extrae datos de una fecha específica usando el formulario de la página
        La página tiene dos pestañas (SOL y LUNA) con formularios separados
        
        Formularios:
        - SOL:  campo 'fecha_sol' en formato YYYY-MM-DD
        - LUNA: campo 'fecha_luna' en formato YYYY-MM-DD
        """
        # El input type="date" espera formato YYYY-MM-DD
        fecha_str_post = fecha.strftime("%Y-%m-%d")
        fecha_objetivo = fecha.strftime("%Y-%m-%d")  # Formato para validar
        
        # Usar el campo de formulario correcto según el tipo
        if tipo_astro == "SOL":
            payload = {
                'fecha_sol': fecha_str_post  # Campo del formulario SOL
            }
        else:  # LUNA
            payload = {
                'fecha_luna': fecha_str_post  # Campo del formulario LUNA
            }
        
        try:
            response = self.session.post(self.url, data=payload, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # La página tiene dos pestañas: #home (SOL) y #profile (LUNA)
            # Buscar en la pestaña correcta
            if tipo_astro == "SOL":
                tab_div = soup.find('div', id='home')
            else:
                tab_div = soup.find('div', id='profile')
            
            if not tab_div:
                # Fallback: buscar tabla directamente
                tabla = soup.find('table', class_='table')
            else:
                # Buscar tabla dentro de la pestaña correcta
                tabla = tab_div.find('table', class_='table')
            
            if not tabla:
                return None
            
            resultados = []
            tbody = tabla.find('tbody')
            if tbody:
                filas = tbody.find_all('tr')
            else:
                filas = tabla.find_all('tr')[1:]  # Omitir header
            
            # Cuando se envía una fecha específica, debería devolver SOLO 1 resultado
            # Si devuelve múltiples, tomamos solo el que coincide con la fecha
            for fila in filas:
                columnas = fila.find_all('td')
                
                if len(columnas) >= 4:
                    # Extraer fecha
                    fecha_fila_str = columnas[0].text.strip()
                    
                    # FILTRO CRÍTICO: Solo procesar si la fecha coincide exactamente
                    if fecha_fila_str != fecha_objetivo:
                        continue
                    
                    # Extraer número (con el método mejorado)
                    numero_str = self.extraer_numero_correcto(columnas[1])
                    
                    # Extraer signo
                    signo_str = columnas[2].text.strip()
                    
                    # Extraer sorteo
                    sorteo_str = columnas[3].text.strip()
                    
                    # Separar el número en 4 posiciones
                    if len(numero_str) == 4:
                        pos1 = int(numero_str[0])
                        pos2 = int(numero_str[1])
                        pos3 = int(numero_str[2])
                        pos4 = int(numero_str[3])
                    else:
                        continue  # Saltar si no tiene 4 dígitos
                    
                    # Mapear signo a número
                    signo_num = self.SIGNOS_MAP.get(signo_str, 0)
                    if signo_num is None:
                        signo_num = 0  # Default si no encuentra el signo
                    
                    # Turno: 0 = SOL (Día), 1 = LUNA (Noche)
                    turno = 0 if tipo_astro == "SOL" else 1
                    
                    resultado = {
                        'Fecha': fecha_fila_str,
                        'Tipo_Astro': tipo_astro,
                        'Turno': turno,
                        'Numero_Completo': numero_str,
                        'Posicion_1': pos1,
                        'Posicion_2': pos2,
                        'Posicion_3': pos3,
                        'Posicion_4': pos4,
                        'Signo_Nombre': signo_str,
                        'Signo_Codigo': signo_num,
                        'Sorteo': sorteo_str
                    }
                    resultados.append(resultado)
                    
                    # Detener después de encontrar el primer resultado válido
                    # (debería ser solo 1 cuando se consulta por fecha)
                    break
            
            return resultados if resultados else None
            
        except Exception as e:
            print(f"❌ Error en {fecha_str_post}: {str(e)}")
            return None
    
    def extraer_rango_fechas(self, tipo_astro, fecha_inicio, fecha_fin):
        """
        Extrae datos día por día en un rango de fechas
        """
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        todos_los_datos = []
        total_dias = (fin - inicio).days + 1
        dia_actual = 0
        
        print(f"\n{'='*70}")
        print(f"🎯 Extrayendo: Astro {tipo_astro} (Turno: {'Día' if tipo_astro == 'SOL' else 'Noche'})")
        print(f"📅 Rango: {fecha_inicio} a {fecha_fin} ({total_dias} días)")
        print(f"{'='*70}\n")
        
        fecha_actual = inicio
        
        while fecha_actual <= fin:
            dia_actual += 1
            progreso = (dia_actual / total_dias) * 100
            
            datos = self.extraer_por_fecha(tipo_astro, fecha_actual)
            
            if datos:
                todos_los_datos.extend(datos)
                print(f"[{progreso:5.1f}%] ✅ {fecha_actual.strftime('%Y-%m-%d')} → {len(datos)} resultados")
            else:
                print(f"[{progreso:5.1f}%] ⚪ {fecha_actual.strftime('%Y-%m-%d')} → Sin datos")
            
            fecha_actual += timedelta(days=1)
            time.sleep(0.4)  # Pausa entre peticiones
        
        print(f"\n✅ Total extraído para {tipo_astro}: {len(todos_los_datos)} registros\n")
        return todos_los_datos
    
    def preparar_para_ml(self, df):
        """
        Prepara el DataFrame con features adicionales para Machine Learning
        """
        # Convertir fecha a datetime
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d', errors='coerce')
        
        # Extraer características temporales
        df['Año'] = df['Fecha_DT'].dt.year
        df['Mes'] = df['Fecha_DT'].dt.month
        df['Dia_Mes'] = df['Fecha_DT'].dt.day
        df['Dia_Semana'] = df['Fecha_DT'].dt.dayofweek  # 0=Lunes, 6=Domingo
        df['Semana_Año'] = df['Fecha_DT'].dt.isocalendar().week
        
        # Ordenar por fecha y turno
        df = df.sort_values(['Fecha_DT', 'Turno']).reset_index(drop=True)
        
        # Features de secuencia (valores anteriores)
        for i in range(1, 6):  # Últimos 5 resultados
            df[f'Pos1_Lag{i}'] = df['Posicion_1'].shift(i)
            df[f'Pos2_Lag{i}'] = df['Posicion_2'].shift(i)
            df[f'Pos3_Lag{i}'] = df['Posicion_3'].shift(i)
            df[f'Pos4_Lag{i}'] = df['Posicion_4'].shift(i)
            df[f'Signo_Lag{i}'] = df['Signo_Codigo'].shift(i)
        
        # Estadísticas móviles (últimos 10 sorteos)
        df['Media_Pos1_10'] = df['Posicion_1'].rolling(window=10).mean()
        df['Media_Pos2_10'] = df['Posicion_2'].rolling(window=10).mean()
        df['Media_Pos3_10'] = df['Posicion_3'].rolling(window=10).mean()
        df['Media_Pos4_10'] = df['Posicion_4'].rolling(window=10).mean()
        
        # Suma total del número
        df['Suma_Total'] = df['Posicion_1'] + df['Posicion_2'] + df['Posicion_3'] + df['Posicion_4']
        
        # Frecuencia del signo
        df['Frecuencia_Signo'] = df.groupby('Signo_Codigo')['Signo_Codigo'].transform('count')
        
        return df
    
    def exportar_excel(self, datos_raw, datos_ml, nombre_base=None):
        """
        Exporta a Excel con múltiples hojas optimizadas - usa archivo compartido
        """
        # Método legacy - ya no se usa (datos en MySQL)
        nombre_archivo = 'superastro_ml_data.xlsx'
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            
            # Hoja 1: Datos RAW (sin procesar)
            df_raw = pd.DataFrame(datos_raw)
            df_raw = df_raw.sort_values('Fecha', ascending=False)
            df_raw.to_excel(writer, sheet_name='Datos_Raw', index=False)
            
            # Hoja 2: Datos para ML (con features)
            datos_ml.to_excel(writer, sheet_name='Datos_ML_Completo', index=False)
            
            # Hoja 3: Solo datos limpios para entrenar (sin NaN)
            df_ml_limpio = datos_ml.dropna()
            df_ml_limpio.to_excel(writer, sheet_name='Datos_ML_Entrenamiento', index=False)
            
            # Hoja 4: Datos SOL (Día)
            df_sol = datos_ml[datos_ml['Turno'] == 0].copy()
            df_sol.to_excel(writer, sheet_name='Solo_SOL_Dia', index=False)
            
            # Hoja 5: Datos LUNA (Noche)
            df_luna = datos_ml[datos_ml['Turno'] == 1].copy()
            df_luna.to_excel(writer, sheet_name='Solo_LUNA_Noche', index=False)
            
            # Hoja 6: Resumen estadístico
            resumen = pd.DataFrame({
                'Métrica': [
                    'Total de registros',
                    'Registros SOL (Día)',
                    'Registros LUNA (Noche)',
                    'Fecha inicial',
                    'Fecha final',
                    'Sorteo inicial',
                    'Sorteo final',
                    'Posición 1 más frecuente',
                    'Posición 2 más frecuente',
                    'Posición 3 más frecuente',
                    'Posición 4 más frecuente',
                    'Signo más frecuente'
                ],
                'Valor': [
                    len(datos_ml),
                    len(df_sol),
                    len(df_luna),
                    datos_ml['Fecha'].min(),
                    datos_ml['Fecha'].max(),
                    datos_ml['Sorteo'].min(),
                    datos_ml['Sorteo'].max(),
                    datos_ml['Posicion_1'].mode()[0] if not datos_ml['Posicion_1'].mode().empty else 'N/A',
                    datos_ml['Posicion_2'].mode()[0] if not datos_ml['Posicion_2'].mode().empty else 'N/A',
                    datos_ml['Posicion_3'].mode()[0] if not datos_ml['Posicion_3'].mode().empty else 'N/A',
                    datos_ml['Posicion_4'].mode()[0] if not datos_ml['Posicion_4'].mode().empty else 'N/A',
                    datos_ml['Signo_Nombre'].mode()[0] if not datos_ml['Signo_Nombre'].mode().empty else 'N/A'
                ]
            })
            resumen.to_excel(writer, sheet_name='Resumen_Estadistico', index=False)
        
        print(f"\n{'='*70}")
        print(f"✅ Archivo exportado: {nombre_archivo}")
        print(f"📊 Total de registros RAW: {len(datos_raw)}")
        print(f"📊 Total de registros ML: {len(datos_ml)}")
        print(f"📊 Registros listos para entrenar: {len(df_ml_limpio)}")
        print(f"📅 Rango: {datos_ml['Fecha'].min()} a {datos_ml['Fecha'].max()}")
        print(f"{'='*70}\n")
        
        return nombre_archivo


def extraer_actualizar(fecha_inicio="2020-01-01", silencioso=False, archivo_existente=None):
    """
    Función para extraer y actualizar datos
    Si existe un archivo previo, solo descarga lo que falta
    
    Args:
        fecha_inicio: Fecha inicial para descarga completa
        silencioso: Modo silencioso
        archivo_existente: Ruta del archivo existente para actualizar
    
    Returns:
        str: Ruta del archivo generado
    """
    if not silencioso:
        print("\n" + "="*70)
        print("🌟 SUPERASTRO ML DATA EXTRACTOR 🌟")
        print("Extracción y preparación de datos para Machine Learning")
        print("="*70 + "\n")
    
    # Crear instancia del extractor
    extractor = SuperAstroMLExtractor()
    
    # Configurar fechas
    FECHA_FIN = datetime.now().strftime("%Y-%m-%d")
    datos_previos = []
    
    # Si hay archivo existente, cargar datos previos
    if archivo_existente and os.path.exists(archivo_existente):
        try:
            if not silencioso:
                print(f"📂 Cargando datos existentes: {archivo_existente}")
            
            df_previo = pd.read_excel(archivo_existente, sheet_name='Datos_Raw')
            
            # Convertir a lista de diccionarios
            datos_previos = df_previo.to_dict('records')

            # Encontrar última fecha
            ultima_fecha_str = str(df_previo['Fecha'].max())
            # Asegurar formato correcto (puede venir como datetime)
            if ' ' in ultima_fecha_str:
                ultima_fecha_str = ultima_fecha_str.split(' ')[0]
            ultima_fecha = datetime.strptime(ultima_fecha_str, "%Y-%m-%d")
            
            # Calcular días faltantes
            fecha_inicio_nueva = (ultima_fecha + timedelta(days=1)).strftime("%Y-%m-%d")
            
            dias_faltantes = (datetime.now() - ultima_fecha).days
            
            if dias_faltantes <= 0:
                if not silencioso:
                    print(f"✅ Los datos ya están actualizados hasta hoy")
                    print(f"   Total de registros: {len(datos_previos)}")
                return archivo_existente
            
            if not silencioso:
                print(f"✅ Datos existentes: {len(datos_previos)} registros")
                print(f"📅 Última fecha en datos: {ultima_fecha_str}")
                print(f"🔄 Descargando {dias_faltantes} días faltantes ({fecha_inicio_nueva} a {FECHA_FIN})")
            
            fecha_inicio = fecha_inicio_nueva
            
        except Exception as e:
            if not silencioso:
                print(f"⚠️  Error al cargar datos previos: {e}")
                print(f"   Realizando descarga completa desde {fecha_inicio}")
            datos_previos = []
    else:
        if not silencioso:
            print(f"⚙️  Configuración:")
            print(f"   📅 Fecha inicio: {fecha_inicio}")
            print(f"   📅 Fecha fin: {FECHA_FIN}")
            print(f"   🎯 Extrayendo ambos turnos: SOL (Día) y LUNA (Noche)\n")
    
    # Extraer datos nuevos o faltantes
    if not silencioso and datos_previos:
        print(f"\n{'='*70}")
        print("📥 DESCARGANDO SOLO DÍAS FALTANTES")
        print(f"{'='*70}\n")

    datos_sol  = extractor.extraer_rango_fechas("SOL",  fecha_inicio, FECHA_FIN)
    datos_luna = extractor.extraer_rango_fechas("LUNA", fecha_inicio, FECHA_FIN)

    datos_nuevos = datos_sol + datos_luna

    if not datos_nuevos and not datos_previos:
        print("❌ No se extrajeron datos. Verifica la conexión y la página.")
        return None

    if not silencioso:
        print(f"\n{'='*70}")
        print(f"💾 Guardando en base de datos...")
        print(f"{'='*70}\n")

    # Guardar en MySQL (solo los nuevos; ON DUPLICATE KEY ignora duplicados)
    if datos_nuevos:
        from db import insertar_resultados_lote
        insertados = insertar_resultados_lote(datos_nuevos)
        if not silencioso:
            print(f"✅ {len(datos_nuevos)} registros enviados a la BD "
                  f"({insertados} filas afectadas)")

    if not silencioso:
        print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")

    return "mysql:superastro_db"


def main():
    """
    Función principal de ejecución
    """
    archivo = extraer_actualizar(fecha_inicio="2020-01-01", silencioso=False)
    
    if archivo:
        print("\n📋 Hojas del Excel:")
        print("   1️⃣  Datos_Raw: Datos originales sin procesar")
        print("   2️⃣  Datos_ML_Completo: Datos con features de ML")
        print("   3️⃣  Datos_ML_Entrenamiento: Datos limpios listos para entrenar")
        print("   4️⃣  Solo_SOL_Dia: Solo resultados del día")
        print("   5️⃣  Solo_LUNA_Noche: Solo resultados de la noche")
        print("   6️⃣  Resumen_Estadistico: Estadísticas generales")
        
        print("\n🤖 Próximos pasos:")
        print("   ✅ Los datos están listos para Random Forest, LSTM y XGBoost")
        print("   ✅ Usa la hoja 'Datos_ML_Entrenamiento' para entrenar modelos")
        print("   ✅ Las columnas Pos1_Lag1, Pos2_Lag1, etc. son para análisis secuencial")
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()