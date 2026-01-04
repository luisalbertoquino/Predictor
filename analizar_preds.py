import json

data = json.load(open('c:/Users/alber/Desktop/theme/predicciones_historial.json', encoding='utf-8'))
preds_04_sol = [p for p in data['predicciones'] if p['fecha_sorteo'] == '2026-01-04' and not p.get('evaluado', False) and p['turno'] == 'SOL']

print(f'Total predicciones 2026-01-04 SOL: {len(preds_04_sol)}\n')

# Analizar estructuras
con_rf_directo = 0
con_metodos_rf = 0
con_consenso_numero = 0
con_estadistico = 0

for p in preds_04_sol:
    if p.get('rf_combinado'):
        con_rf_directo += 1

    metodos = p.get('metodos', {})
    if metodos and metodos.get('RF'):
        con_metodos_rf += 1
    if metodos and metodos.get('Estadistico'):
        con_estadistico += 1

    consenso = p.get('consenso')
    if consenso and isinstance(consenso, dict) and consenso.get('numero'):
        con_consenso_numero += 1

print('Análisis de estructuras:')
print(f'  Con rf_combinado (campo directo): {con_rf_directo}')
print(f'  Con metodos.RF: {con_metodos_rf}')
print(f'  Con metodos.Estadistico: {con_estadistico}')
print(f'  Con consenso.numero: {con_consenso_numero}')

# Mostrar ejemplo de cada tipo
print('\n' + '='*60)
print('EJEMPLO con rf_combinado (ML Basic):')
print('='*60)
ej1 = [p for p in preds_04_sol if p.get('rf_combinado')][0]
print(f"Fecha predicción: {ej1['fecha_prediccion']}")
print(f"rf_combinado: {ej1.get('rf_combinado')}")
print(f"metodos: {ej1.get('metodos')}")
print(f"consenso: {ej1.get('consenso')}")

if con_metodos_rf > 0:
    print('\n' + '='*60)
    print('EJEMPLO con metodos.RF (Maestro/Mejorado):')
    print('='*60)
    ej2 = [p for p in preds_04_sol if p.get('metodos', {}).get('RF')][0]
    print(f"Fecha predicción: {ej2['fecha_prediccion']}")
    print(f"rf_combinado: {ej2.get('rf_combinado')}")
    print(f"metodos: {ej2.get('metodos')}")
    print(f"consenso: {ej2.get('consenso')}")
