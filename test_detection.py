import json
from datetime import datetime

# Load predictions
with open('predicciones_historial.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

pendientes = [p for p in data.get('predicciones', []) if not p.get('evaluado', False)]

print("=" * 60)
print("SIMULANDO DETECCIÓN DE SCRIPTS (como JavaScript)")
print("=" * 60)

# Simulate JavaScript grouping
prediccionesAgrupadas = {}
for pred in pendientes:
    key = f"{pred['fecha_sorteo']}_{pred['turno']}"
    if key not in prediccionesAgrupadas:
        prediccionesAgrupadas[key] = {
            'fecha_sorteo': pred['fecha_sorteo'],
            'turno': pred['turno'],
            'predicciones': []
        }
    prediccionesAgrupadas[key]['predicciones'].append(pred)

# Filter future dates (simulate JavaScript filter)
ahora = datetime.now()
ahoraStr = ahora.strftime('%Y-%m-%d')
horaActual = ahora.hour

print(f"\nFecha actual: {ahoraStr}")
print(f"Hora actual: {horaActual}:00")

gruposFuturos = []
for key, grupo in prediccionesAgrupadas.items():
    fechaSorteoStr = grupo['fecha_sorteo']

    # Si la fecha es futura, incluir
    if fechaSorteoStr > ahoraStr:
        gruposFuturos.append(grupo)
        continue

    # Si es hoy, verificar el turno
    if fechaSorteoStr == ahoraStr:
        if grupo['turno'] == 'SOL' and horaActual < 13:
            gruposFuturos.append(grupo)
        elif grupo['turno'] == 'LUNA' and horaActual < 21:
            gruposFuturos.append(grupo)

print(f"\nGrupos futuros encontrados: {len(gruposFuturos)}")

# Sort ascending
gruposFuturos.sort(key=lambda g: (g['fecha_sorteo'], 0 if g['turno'] == 'SOL' else 1))

# Take first 2
gruposOrdenados = gruposFuturos[:2]

print(f"Grupos a mostrar (primeros 2): {len(gruposOrdenados)}\n")

# Show what would be displayed
for grupo in gruposOrdenados:
    print("=" * 60)
    print(f"FECHA: {grupo['fecha_sorteo']} - {grupo['turno']}")
    print(f"Total predicciones: {len(grupo['predicciones'])}")
    print("=" * 60)

    # Combine data (simulate JavaScript)
    datosCombinados = {
        'rf_combinado': None,
        'xgb_combinado': None,
        'rf_especifico': None,
        'xgb_especifico': None,
        'estadistico': None,
        'lstm': None,
        'metodo1': None,
        'metodo2': None,
        'metodo3': None,
        'metodo4': None,
        'consenso': None,
        'metodos': {}
    }

    for pred in grupo['predicciones']:
        if pred.get('rf_combinado'): datosCombinados['rf_combinado'] = pred['rf_combinado']
        if pred.get('xgb_combinado'): datosCombinados['xgb_combinado'] = pred['xgb_combinado']
        if pred.get('rf_especifico'): datosCombinados['rf_especifico'] = pred['rf_especifico']
        if pred.get('xgb_especifico'): datosCombinados['xgb_especifico'] = pred['xgb_especifico']
        if pred.get('estadistico'): datosCombinados['estadistico'] = pred['estadistico']
        if pred.get('lstm'): datosCombinados['lstm'] = pred['lstm']
        if pred.get('metodo1'): datosCombinados['metodo1'] = pred['metodo1']
        if pred.get('metodo2'): datosCombinados['metodo2'] = pred['metodo2']
        if pred.get('metodo3'): datosCombinados['metodo3'] = pred['metodo3']
        if pred.get('metodo4'): datosCombinados['metodo4'] = pred['metodo4']
        if pred.get('consenso') and pred['consenso'].get('numero'):
            datosCombinados['consenso'] = pred['consenso']

        # Copy metodos{}
        if pred.get('metodos') and isinstance(pred['metodos'], dict) and len(pred['metodos']) > 0:
            datosCombinados['metodos'].update(pred['metodos'])

    # Detect scripts
    scriptsPresentes = set()

    # Check Maestro/ML Basic
    tieneRF = (datosCombinados['rf_combinado'] or datosCombinados['xgb_combinado'] or
               (datosCombinados['metodos'] and (datosCombinados['metodos'].get('RF') or datosCombinados['metodos'].get('XGB'))))
    if tieneRF:
        if datosCombinados['consenso'] and datosCombinados['consenso'].get('numero'):
            scriptsPresentes.add('Maestro')
        else:
            scriptsPresentes.add('ML Basic')

    # Check Mejorado
    tieneEstadistico = datosCombinados['estadistico'] or (datosCombinados['metodos'] and datosCombinados['metodos'].get('Estadistico'))
    if tieneEstadistico:
        scriptsPresentes.add('Mejorado')

    # Check LSTM
    if datosCombinados['lstm'] or (datosCombinados['metodos'] and datosCombinados['metodos'].get('LSTM')):
        scriptsPresentes.add('LSTM')

    # Check Avanzada
    tieneMetodos = (datosCombinados['metodo1'] or datosCombinados['metodo2'] or
                   datosCombinados['metodo3'] or datosCombinados['metodo4'] or
                   (datosCombinados['metodos'] and (datosCombinados['metodos'].get('Metodo1') or
                    datosCombinados['metodos'].get('Metodo2') or datosCombinados['metodos'].get('Metodo3') or
                    datosCombinados['metodos'].get('Metodo4'))))
    if tieneMetodos:
        scriptsPresentes.add('Avanzada')

    print(f"\n✅ Scripts detectados: {scriptsPresentes}")

    # Show details
    print(f"\nDatos combinados:")
    print(f"  - rf_combinado: {bool(datosCombinados['rf_combinado'])}")
    print(f"  - xgb_combinado: {bool(datosCombinados['xgb_combinado'])}")
    print(f"  - estadistico: {bool(datosCombinados['estadistico'])}")
    print(f"  - consenso: {bool(datosCombinados['consenso'])}")
    print(f"  - metodos keys: {list(datosCombinados['metodos'].keys())}")

    # Show what would be displayed for each script
    todosLosScripts = ['Maestro', 'Avanzada', 'Mejorado', 'ML Basic', 'LSTM']

    print(f"\nQué se mostraría:")
    for script in todosLosScripts:
        if script in scriptsPresentes:
            print(f"  ✅ {script}: RESULTADOS")

            # Show which algorithms
            if script in ['Maestro', 'ML Basic']:
                algos = []
                if datosCombinados['rf_combinado']: algos.append('RF Combinado')
                if datosCombinados['xgb_combinado']: algos.append('XGB Combinado')
                if datosCombinados['rf_especifico']: algos.append('RF Específico')
                if datosCombinados['xgb_especifico']: algos.append('XGB Específico')
                if datosCombinados['metodos'].get('RF'): algos.append('RF')
                if datosCombinados['metodos'].get('XGB'): algos.append('XGB')
                print(f"       Algoritmos: {', '.join(algos)}")

            elif script == 'Mejorado':
                algos = []
                if datosCombinados['estadistico']: algos.append('Estadístico (directo)')
                if datosCombinados['metodos'].get('Estadistico'): algos.append('Estadístico (metodos)')
                print(f"       Algoritmos: {', '.join(algos)}")

            elif script == 'Avanzada':
                algos = []
                if datosCombinados['metodo1']: algos.append('Método 1 (directo)')
                if datosCombinados['metodos'].get('Metodo1'): algos.append('Método 1 (metodos)')
                # Similar para otros métodos
                print(f"       Algoritmos: {', '.join(algos)}")
        else:
            print(f"  ⚠️  {script}: NO EJECUTADO")

    print()

print("\n" + "=" * 60)
print("RESUMEN:")
print("=" * 60)
print(f"✅ Se filtró 2026-01-01 SOL: {'Sí' if not any(g['fecha_sorteo'] == '2026-01-01' for g in gruposOrdenados) else 'NO'}")
print(f"✅ Se muestra 2026-01-03 LUNA: {'Sí' if any(g['fecha_sorteo'] == '2026-01-03' and g['turno'] == 'LUNA' for g in gruposOrdenados) else 'NO'}")
print(f"✅ Se muestra 2026-01-04: {'Sí' if any(g['fecha_sorteo'] == '2026-01-04' for g in gruposOrdenados) else 'NO'}")
