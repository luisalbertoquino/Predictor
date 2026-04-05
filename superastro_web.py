# -*- coding: utf-8 -*-
"""
SuperAstro Web Dashboard
Interfaz web para ejecutar y visualizar todos los predictores
Autor: Luis Alberto Quino
Versión: 1.0 - Dashboard Web
"""

import sys
import io
# Configurar codificación UTF-8 en Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

from flask import Flask, render_template, jsonify, request, Response
import subprocess
import json
import os
from datetime import datetime
import threading

app = Flask(__name__)

# Estado global de ejecuciones
estado_ejecuciones = {
    'ml_predictor': {'ejecutando': False, 'ultimo': None, 'log': ''},
    'predictor_mejorado': {'ejecutando': False, 'ultimo': None, 'log': ''},
    'lstm_predictor': {'ejecutando': False, 'ultimo': None, 'log': ''},
    'predictor_maestro': {'ejecutando': False, 'ultimo': None, 'log': ''},
    'prediccion_avanzada': {'ejecutando': False, 'ultimo': None, 'log': ''},
    'extractor': {'ejecutando': False, 'ultimo': None, 'log': ''},
}

def ejecutar_script_async(script_name, comando):
    """Ejecuta un script en background"""
    estado_ejecuciones[script_name]['ejecutando'] = True
    estado_ejecuciones[script_name]['log'] = f'Iniciando {script_name}...\n'

    try:
        process = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        output = ''
        for line in process.stdout:
            output += line
            estado_ejecuciones[script_name]['log'] = output

        process.wait()
        estado_ejecuciones[script_name]['ultimo'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_ejecuciones[script_name]['log'] = output + f"\n✅ Completado a las {estado_ejecuciones[script_name]['ultimo']}"
    except Exception as e:
        estado_ejecuciones[script_name]['log'] = f"❌ Error: {str(e)}"
    finally:
        estado_ejecuciones[script_name]['ejecutando'] = False

@app.route('/')
def index():
    """Página principal"""
    return render_template('dashboard.html')

@app.route('/api/ejecutar/<script>', methods=['POST'])
def ejecutar_script(script):
    """Ejecuta un script específico"""
    comandos = {
        'ml_predictor': ['python', 'superastro_ml_predictor.py'],
        'predictor_mejorado': ['python', 'superastro_predictor_mejorado.py'],
        'lstm_predictor': ['python', 'superastro_lstm_predictor.py'],
        'predictor_maestro': ['python', 'superastro_predictor_maestro.py'],
        'prediccion_avanzada': ['python', 'superastro_prediccion_avanzada.py'],
        'extractor': ['python', 'superastro_ml_extractor.py'],
    }

    if script not in comandos:
        return jsonify({'error': 'Script no encontrado'}), 404

    # Usar directamente el nombre del script para estado
    script_estado = script

    if estado_ejecuciones.get(script_estado, {}).get('ejecutando'):
        return jsonify({'error': 'Script ya está ejecutándose'}), 400

    # Ejecutar en background
    thread = threading.Thread(
        target=ejecutar_script_async,
        args=(script_estado, comandos[script])
    )
    thread.start()

    return jsonify({'mensaje': f'Script {script} iniciado'})

def obtener_ultima_ejecucion_cron():
    """
    Lee el cron.log para obtener la última ejecución exitosa
    Retorna fecha/hora de última ejecución o None
    """
    try:
        cron_log = 'logs/cron.log'
        if not os.path.exists(cron_log):
            return None

        with open(cron_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Buscar última línea que indica completado
        for line in reversed(lines):
            if 'Todos los predictores' in line and 'completados' in line:
                # Extraer fecha del formato: "... completados - Sun Jan 11 02:40:50 -05 2026"
                import re
                match = re.search(r'completados - \w+ (\w+)\s+(\d+)\s+(\d+):(\d+):(\d+).+(\d{4})', line)
                if match:
                    mes_en = match.group(1)
                    dia = match.group(2)
                    hora = match.group(3)
                    minuto = match.group(4)
                    año = match.group(6)

                    # Traducir mes
                    meses = {
                        'Jan': 'Ene', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Abr',
                        'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
                        'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dic'
                    }
                    mes = meses.get(mes_en, mes_en)

                    return f"{dia} {mes} {año} - {hora}:{minuto}"

        return None
    except Exception as e:
        print(f"Error leyendo cron.log: {e}")
        return None

@app.route('/api/estado/<script>')
def obtener_estado(script):
    """Obtiene el estado de ejecución de un script"""
    if script not in estado_ejecuciones:
        return jsonify({'error': 'Script no encontrado'}), 404

    estado = estado_ejecuciones[script].copy()

    # Si no está ejecutando y no tiene timestamp propio, usar el del cron
    if not estado['ejecutando'] and not estado['ultimo']:
        ultima_cron = obtener_ultima_ejecucion_cron()
        if ultima_cron:
            estado['ultimo'] = f"Cron: {ultima_cron}"

    return jsonify(estado)

@app.route('/api/historial')
def obtener_historial():
    """Obtiene el historial de predicciones"""
    try:
        with open('predicciones_historial.json', 'r', encoding='utf-8') as f:
            historial = json.load(f)

        # Organizar datos para el dashboard
        predicciones = historial.get('predicciones', [])

        # Últimas 10 evaluadas (el JSON ya viene ordenado descendente, tomar las primeras)
        evaluadas = [p for p in predicciones if p.get('evaluado')][:10]

        # Pendientes de hoy y mañana
        hoy = datetime.now().strftime("%Y-%m-%d")
        pendientes = [p for p in predicciones if not p.get('evaluado')]

        # Calcular estadísticas
        stats = calcular_estadisticas(evaluadas)

        return jsonify({
            'evaluadas': evaluadas,
            'pendientes': pendientes,
            'estadisticas': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calcular_estadisticas(predicciones_evaluadas):
    """Calcula estadísticas de aciertos para todos los métodos"""
    # Todos los métodos posibles de todos los scripts
    metodos = [
        'rf_combinado', 'xgb_combinado', 'rf_especifico', 'xgb_especifico',  # ML Basic
        'RF', 'XGB',  # Maestro
        'Metodo1', 'Metodo2', 'Metodo3', 'Metodo4',  # Avanzada
        'Estadistico',  # Mejorado
        'LSTM'  # LSTM
    ]
    stats = {}

    for metodo in metodos:
        total = 0
        aciertos_digitos = 0
        aciertos_signos = 0

        for pred in predicciones_evaluadas:
            if 'aciertos' in pred and metodo in pred['aciertos']:
                total += 1
                acierto = pred['aciertos'][metodo]
                aciertos_digitos += acierto.get('digitos_correctos', 0)
                if acierto.get('signo_correcto'):
                    aciertos_signos += 1

        if total > 0:
            stats[metodo] = {
                'total': total,
                'promedio_digitos': round(aciertos_digitos / total, 2),
                'tasa_signos': round((aciertos_signos / total) * 100, 1)
            }
        else:
            stats[metodo] = {
                'total': 0,
                'promedio_digitos': 0,
                'tasa_signos': 0
            }

    return stats

@app.route('/api/exportar-csv')
def exportar_csv():
    """Descarga todos los resultados históricos como CSV."""
    try:
        from db import exportar_csv as _csv
        contenido = _csv()
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        return Response(
            contenido,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=superastro_resultados_{fecha_hoy}.csv'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ultimos-resultados')
def ultimos_resultados():
    """Retorna los últimos 10 resultados de SOL y LUNA desde la BD."""
    try:
        from db import get_connection
        conn = get_connection()
        resultados = {'SOL': [], 'LUNA': []}
        try:
            with conn.cursor() as cur:
                for turno_nombre, turno_num in [('SOL', 0), ('LUNA', 1)]:
                    cur.execute("""
                        SELECT fecha, numero_completo, signo_nombre, sorteo
                        FROM sorteo_resultados
                        WHERE turno = %s
                        ORDER BY fecha DESC
                        LIMIT 10
                    """, (turno_num,))
                    rows = cur.fetchall()
                    resultados[turno_nombre] = [
                        {
                            'fecha': str(r['fecha']),
                            'numero': str(r['numero_completo']).zfill(4),
                            'signo': r['signo_nombre'],
                            'sorteo': r['sorteo']
                        }
                        for r in rows
                    ]
        finally:
            conn.close()
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detener/<script>', methods=['POST'])
def detener_script(script):
    """Marca un script como detenido (nota: subprocess no se puede detener fácilmente)"""
    if script in estado_ejecuciones:
        estado_ejecuciones[script]['log'] += "\n⚠️ Solicitud de detención recibida"
    return jsonify({'mensaje': 'Señal de detención enviada'})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 SUPERASTRO WEB DASHBOARD")
    print("="*70)
    print("\n✅ Servidor iniciado en: http://localhost:5000")
    print("📊 Abre tu navegador y accede a la URL anterior")
    print("\nPresiona Ctrl+C para detener el servidor\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
