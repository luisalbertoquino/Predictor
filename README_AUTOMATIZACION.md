# 🤖 Sistema de Automatización SuperAstro

## 📋 Flujo Completo del Sistema

### 1. **Ejecución Automática Diaria (2:00 AM)**

El cron ejecuta `run_all_predictors.sh` que hace:

```
[1/6] Genera predicciones con Maestro
[2/6] Genera predicciones con Avanzada
[3/6] Genera predicciones con Mejorado
[4/6] Genera predicciones con ML Basic
[5/6] Genera predicciones con LSTM
[6/6] Evalúa predicciones pendientes comparando con resultados reales
```

### 2. **¿Qué hace cada paso?**

#### Predictores (1-5):
- Leen datos históricos del Excel `superastro_ml_data.xlsx`
- Generan predicciones para los próximos sorteos
- Guardan predicciones en `predicciones_historial.json`
- Estado inicial: `"evaluado": false`

#### Evaluador (6):
- Lee `predicciones_historial.json`
- Busca predicciones con `"evaluado": false`
- Compara contra resultados reales en `superastro_ml_data.xlsx`
- Si encuentra el resultado real, calcula aciertos
- Actualiza: `"evaluado": true` + `"aciertos": {...}`

### 3. **¿Cómo ingresar resultados reales?**

Tienes 2 opciones:

#### Opción A: Manualmente via Tracker Web
1. Ve a la pestaña "Tracker de Resultados" en el dashboard
2. Ingresa fecha, turno, número y signo del sorteo
3. El sistema automáticamente:
   - Agrega el resultado al Excel
   - Evalúa predicciones pendientes para esa fecha/turno
   - Actualiza estadísticas y rankings

#### Opción B: Actualizar Excel directamente
1. Edita `superastro_ml_data.xlsx`
2. Agrega nueva fila con: Fecha, Turno, Numero, Signo
3. El evaluador lo detectará en la próxima ejecución (2 AM)

### 4. **Logs y Monitoreo**

```bash
# Ver log del cron (todas las ejecuciones)
tail -100 /var/www/Predictor/logs/cron.log

# Ver log detallado de última ejecución
ls -lt /var/www/Predictor/logs/predictors_*.log | head -1

# Ver últimas evaluaciones
grep "Evaluada:" /var/www/Predictor/logs/predictors_*.log
```

### 5. **Verificar que todo funciona**

```bash
# Ver estado del cron
crontab -l

# Ver si supervisor mantiene Flask activo
supervisorctl status superastro

# Ejecutar manualmente (para testing)
cd /var/www/Predictor
./run_all_predictors.sh
```

### 6. **Flujo Visual**

```
┌─────────────────────────────────────┐
│   CADA DÍA A LAS 2:00 AM (CRON)    │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  1. GENERA PREDICCIONES (5 Scripts) │
│     - Maestro                       │
│     - Avanzada                      │
│     - Mejorado                      │
│     - ML Basic                      │
│     - LSTM                          │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  2. GUARDA EN JSON                  │
│     predicciones_historial.json     │
│     Estado: evaluado=false          │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  3. EVALÚA PREDICCIONES PENDIENTES  │
│     - Busca resultados reales       │
│     - Calcula aciertos              │
│     - Actualiza evaluado=true       │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  4. DASHBOARD SE ACTUALIZA AUTO     │
│     - Muestra predicciones nuevas   │
│     - Muestra evaluaciones          │
│     - Actualiza rankings            │
│     - Actualiza estadísticas        │
└─────────────────────────────────────┘
```

## ⚠️ IMPORTANTE

**El sistema NO hace scraping automático** de resultados. Debes ingresar los resultados manualmente:

1. **Después de cada sorteo**, ve al Tracker en el dashboard
2. Ingresa el resultado real
3. El sistema evaluará automáticamente

O actualiza el Excel manualmente y el cron lo detectará a las 2 AM del día siguiente.

## 🔧 Mantenimiento

- Los logs se limpian automáticamente (mantiene últimos 30 días)
- El JSON crece con el tiempo - todo el historial se mantiene
- El Excel debe actualizarse manualmente con resultados reales
