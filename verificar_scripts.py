import json

# Cargar predicciones
with open('predicciones_historial.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

pendientes = [p for p in data.get('predicciones', []) if not p.get('evaluado', False)]

print("=" * 80)
print("VERIFICACION DE SCRIPTS PRESENTES EN PREDICCIONES")
print("=" * 80)

# Agrupar por fecha_sorteo + turno
grupos = {}
for pred in pendientes:
    key = f"{pred['fecha_sorteo']}_{pred['turno']}"
    if key not in grupos:
        grupos[key] = {
            'fecha_sorteo': pred['fecha_sorteo'],
            'turno': pred['turno'],
            'predicciones': []
        }
    grupos[key]['predicciones'].append(pred)

# Analizar cada grupo
for key, grupo in sorted(grupos.items()):
    print(f"\n{grupo['fecha_sorteo']} - {grupo['turno']}")
    print("-" * 80)
    print(f"Total predicciones: {len(grupo['predicciones'])}")

    # Combinar datos
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

        if pred.get('metodos') and isinstance(pred['metodos'], dict) and len(pred['metodos']) > 0:
            datosCombinados['metodos'].update(pred['metodos'])

    # Detectar scripts con la NUEVA lógica
    scriptsPresentes = set()

    # MAESTRO: Tiene consenso valido + RF/XGB en metodos{}
    if datosCombinados['consenso'] and datosCombinados['consenso'].get('numero') and datosCombinados['metodos'] and (datosCombinados['metodos'].get('RF') or datosCombinados['metodos'].get('XGB')):
        scriptsPresentes.add('Maestro')

    # ML BASIC: Tiene rf_combinado/xgb_combinado/rf_especifico/xgb_especifico en campos directos
    tieneCamposDirectos = datosCombinados['rf_combinado'] or datosCombinados['xgb_combinado'] or datosCombinados['rf_especifico'] or datosCombinados['xgb_especifico']
    if tieneCamposDirectos:
        scriptsPresentes.add('ML Basic')

    # MEJORADO: Tiene Estadistico en metodos{}
    if datosCombinados['metodos'] and datosCombinados['metodos'].get('Estadistico'):
        scriptsPresentes.add('Mejorado')

    # AVANZADA: Tiene Metodo1-4 en metodos{}
    if datosCombinados['metodos'] and (datosCombinados['metodos'].get('Metodo1') or datosCombinados['metodos'].get('Metodo2') or datosCombinados['metodos'].get('Metodo3') or datosCombinados['metodos'].get('Metodo4')):
        scriptsPresentes.add('Avanzada')

    # LSTM: Tiene LSTM en metodos{}
    if datosCombinados['metodos'] and datosCombinados['metodos'].get('LSTM'):
        scriptsPresentes.add('LSTM')

    print(f"\nScripts DETECTADOS: {scriptsPresentes}")
    print(f"\nAlgoritmos en metodos: {list(datosCombinados['metodos'].keys())}")
    print(f"Tiene consenso: {bool(datosCombinados['consenso'])}")
    print(f"Tiene campos directos: {tieneCamposDirectos}")

    # Mostrar que algoritmos tiene cada script detectado
    if 'Maestro' in scriptsPresentes:
        print(f"\n  MAESTRO - Algoritmos:")
        if datosCombinados['metodos'].get('RF'): print(f"    - Random Forest: {datosCombinados['metodos']['RF']['numero']}")
        if datosCombinados['metodos'].get('XGB'): print(f"    - XGBoost: {datosCombinados['metodos']['XGB']['numero']}")

    if 'ML Basic' in scriptsPresentes:
        print(f"\n  ML BASIC - Algoritmos:")
        if datosCombinados['rf_combinado']: print(f"    - RF Combinado: {datosCombinados['rf_combinado']['numero']}")
        if datosCombinados['xgb_combinado']: print(f"    - XGB Combinado: {datosCombinados['xgb_combinado']['numero']}")
        if datosCombinados['rf_especifico']: print(f"    - RF Especifico: {datosCombinados['rf_especifico']['numero']}")
        if datosCombinados['xgb_especifico']: print(f"    - XGB Especifico: {datosCombinados['xgb_especifico']['numero']}")

    if 'Mejorado' in scriptsPresentes:
        print(f"\n  MEJORADO - Algoritmos:")
        if datosCombinados['metodos'].get('Estadistico'): print(f"    - Estadistico Avanzado: {datosCombinados['metodos']['Estadistico']['numero']}")

    if 'Avanzada' in scriptsPresentes:
        print(f"\n  AVANZADA - Algoritmos:")
        if datosCombinados['metodos'].get('Metodo1'): print(f"    - Metodo 1: {datosCombinados['metodos']['Metodo1']['numero']}")
        if datosCombinados['metodos'].get('Metodo2'): print(f"    - Metodo 2: {datosCombinados['metodos']['Metodo2']['numero']}")
        if datosCombinados['metodos'].get('Metodo3'): print(f"    - Metodo 3: {datosCombinados['metodos']['Metodo3']['numero']}")
        if datosCombinados['metodos'].get('Metodo4'): print(f"    - Metodo 4: {datosCombinados['metodos']['Metodo4']['numero']}")

    if 'LSTM' in scriptsPresentes:
        print(f"\n  LSTM - Algoritmos:")
        if datosCombinados['metodos'].get('LSTM'): print(f"    - LSTM Red Neuronal: {datosCombinados['metodos']['LSTM']['numero']}")
