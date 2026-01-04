import json
from datetime import datetime

# Load predictions
with open('predicciones_historial.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

pendientes = [p for p in data.get('predicciones', []) if not p.get('evaluado', False)]

print(f"Total pendientes: {len(pendientes)}\n")

# Check 2026-01-01 SOL
sol_01 = [p for p in pendientes if p['fecha_sorteo'] == '2026-01-01' and p['turno'] == 'SOL']
if sol_01:
    print("=" * 50)
    print("2026-01-01 SOL (ya jugó - no debería mostrarse):")
    print("=" * 50)
    for pred in sol_01:
        print(f"Fecha predicción: {pred.get('fecha_prediccion')}")
        print(f"Tiene metodos: {bool(pred.get('metodos'))}")
        print(f"Tiene rf_combinado: {bool(pred.get('rf_combinado'))}")
        print(f"Tiene consenso: {bool(pred.get('consenso'))}")
        if pred.get('metodos'):
            print(f"Metodos: {list(pred['metodos'].keys())}")

# Check 2026-01-03 LUNA
luna_03 = [p for p in pendientes if p['fecha_sorteo'] == '2026-01-03' and p['turno'] == 'LUNA']
if luna_03:
    print("\n" + "=" * 50)
    print("2026-01-03 LUNA (no ha jugado - DEBERÍA mostrarse):")
    print("=" * 50)
    for pred in luna_03:
        print(f"Fecha predicción: {pred.get('fecha_prediccion')}")
        print(f"Tiene metodos: {bool(pred.get('metodos'))}")
        print(f"Tiene rf_combinado: {bool(pred.get('rf_combinado'))}")
        print(f"Tiene consenso: {bool(pred.get('consenso'))}")
        if pred.get('metodos'):
            print(f"Metodos: {list(pred['metodos'].keys())}")

# Check 2026-01-04 SOL (first one only)
sol_04 = [p for p in pendientes if p['fecha_sorteo'] == '2026-01-04' and p['turno'] == 'SOL']
if sol_04:
    print("\n" + "=" * 50)
    print(f"2026-01-04 SOL (no ha jugado - DEBERÍA mostrarse) - {len(sol_04)} predicciones:")
    print("=" * 50)
    pred = sol_04[0]  # Just show first one
    print(f"Fecha predicción: {pred.get('fecha_prediccion')}")
    print(f"Tiene metodos: {bool(pred.get('metodos'))}")
    print(f"Tiene rf_combinado: {bool(pred.get('rf_combinado'))}")
    print(f"Tiene consenso: {bool(pred.get('consenso'))}")
    if pred.get('metodos'):
        print(f"Metodos: {list(pred['metodos'].keys())}")
    print(f"\nTOTAL para 2026-01-04 SOL: {len(sol_04)} predicciones duplicadas")

# Check 2026-01-04 LUNA (first one only)
luna_04 = [p for p in pendientes if p['fecha_sorteo'] == '2026-01-04' and p['turno'] == 'LUNA']
if luna_04:
    print("\n" + "=" * 50)
    print(f"2026-01-04 LUNA (no ha jugado - DEBERÍA mostrarse) - {len(luna_04)} predicciones:")
    print("=" * 50)
    pred = luna_04[0]  # Just show first one
    print(f"Fecha predicción: {pred.get('fecha_prediccion')}")
    print(f"Tiene metodos: {bool(pred.get('metodos'))}")
    print(f"Tiene rf_combinado: {bool(pred.get('rf_combinado'))}")
    print(f"Tiene consenso: {bool(pred.get('consenso'))}")
    if pred.get('metodos'):
        print(f"Metodos: {list(pred['metodos'].keys())}")
    print(f"\nTOTAL para 2026-01-04 LUNA: {len(luna_04)} predicciones duplicadas")

print("\n" + "=" * 50)
print("ANÁLISIS DE SCRIPTS PRESENTES:")
print("=" * 50)

# Analyze which scripts are present for each date
for fecha_turno in ['2026-01-01 - SOL', '2026-01-03 - LUNA', '2026-01-04 - SOL', '2026-01-04 - LUNA']:
    fecha, turno = fecha_turno.split(' - ')
    preds = [p for p in pendientes if p['fecha_sorteo'] == fecha and p['turno'] == turno]

    scripts = set()
    for pred in preds:
        # Check Maestro/ML Basic
        tiene_rf_xgb = (pred.get('rf_combinado') or pred.get('xgb_combinado') or
                       (pred.get('metodos') and (pred['metodos'].get('RF') or pred['metodos'].get('XGB'))))
        if tiene_rf_xgb:
            if pred.get('consenso') and pred['consenso'].get('numero'):
                scripts.add('Maestro')
            else:
                scripts.add('ML Basic')

        # Check Mejorado
        tiene_estadistico = pred.get('estadistico') or (pred.get('metodos') and pred['metodos'].get('Estadistico'))
        if tiene_estadistico:
            scripts.add('Mejorado')

        # Check Avanzada
        tiene_metodos = (pred.get('metodo1') or pred.get('metodo2') or pred.get('metodo3') or pred.get('metodo4') or
                        (pred.get('metodos') and (pred['metodos'].get('Metodo1') or pred['metodos'].get('Metodo2') or
                         pred['metodos'].get('Metodo3') or pred['metodos'].get('Metodo4'))))
        if tiene_metodos:
            scripts.add('Avanzada')

        # Check LSTM
        tiene_lstm = pred.get('lstm') or (pred.get('metodos') and pred['metodos'].get('lstm'))
        if tiene_lstm:
            scripts.add('LSTM')

    print(f"\n{fecha_turno}: {scripts if scripts else 'SIN SCRIPTS'}")
