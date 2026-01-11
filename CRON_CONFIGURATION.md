# ⏰ Configuración de Cron Jobs para SuperAstro

## Descripción del Sistema

El sistema ejecuta automáticamente:
1. **Predicciones** cada día a las 2:00 AM
2. **Extracción y evaluación** después de cada sorteo

## Horarios de Sorteos

### SOL
- Lunes a Sábado: 4:00 PM (16:00)
- No juega domingos ni festivos

### LUNA
- Lunes a Viernes: 10:40 PM (22:40)
- Sábado y Domingo: 10:42 PM (22:42)

## Configuración de Cron

Editar crontab:
```bash
crontab -e
```

Agregar las siguientes líneas:

```bash
# ===== PREDICCIONES DIARIAS =====
# Genera predicciones cada día a las 2:00 AM
0 2 * * * cd /var/www/Predictor && /var/www/Predictor/run_all_predictors.sh >> /var/www/Predictor/logs/cron.log 2>&1

# ===== EXTRACCIÓN Y EVALUACIÓN DESPUÉS DE SORTEOS =====

# SOL - Lunes a Sábado a las 4:10 PM (10 min después del sorteo)
10 16 * * 1-6 cd /var/www/Predictor && /var/www/Predictor/extraer_y_evaluar.sh >> /var/www/Predictor/logs/cron_extractor.log 2>&1

# LUNA - Lunes a Viernes a las 10:50 PM (10 min después del sorteo)
50 22 * * 1-5 cd /var/www/Predictor && /var/www/Predictor/extraer_y_evaluar.sh >> /var/www/Predictor/logs/cron_extractor.log 2>&1

# LUNA - Sábado y Domingo a las 10:52 PM (10 min después del sorteo)
52 22 * * 0,6 cd /var/www/Predictor && /var/www/Predictor/extraer_y_evaluar.sh >> /var/www/Predictor/logs/cron_extractor.log 2>&1
```

## Verificar Configuración

```bash
# Ver crontab activo
crontab -l

# Ver logs de predicciones
tail -f /var/www/Predictor/logs/cron.log

# Ver logs de extracción
tail -f /var/www/Predictor/logs/cron_extractor.log

# Ver logs detallados de extracción
ls -lt /var/www/Predictor/logs/extractor_*.log | head -5
```

## Flujo Completo del Sistema

```
2:00 AM (Diario)
    ↓
Genera Predicciones (5 algoritmos)
    ↓
Evalúa predicciones pendientes (si hay resultados)
    ↓
Dashboard actualizado


4:10 PM (Lun-Sáb) - Después de SOL
    ↓
Extrae resultado de SuperAstro.com.co
    ↓
Actualiza Excel con nuevo resultado
    ↓
Evalúa predicción de SOL
    ↓
Dashboard muestra aciertos


10:50 PM (Lun-Vie) - Después de LUNA
10:52 PM (Sáb-Dom) - Después de LUNA
    ↓
Extrae resultado de SuperAstro.com.co
    ↓
Actualiza Excel con nuevo resultado
    ↓
Evalúa predicción de LUNA
    ↓
Dashboard muestra aciertos
```

## Notas Importantes

1. **Margen de 10 minutos**: Se espera 10 minutos después del sorteo para dar tiempo a que publiquen el resultado
2. **Espera adicional de 5 minutos**: El script `extraer_y_evaluar.sh` espera 5 minutos adicionales antes de scrapear
3. **Total: 15 minutos** desde el sorteo hasta la extracción
4. **Logs automáticos**: Todos los procesos se registran en `/var/www/Predictor/logs/`
5. **Limpieza automática**: Los logs antiguos se limpian automáticamente (30+ días)

## Troubleshooting

Si los resultados no se extraen:

```bash
# Ejecutar manualmente para ver errores
cd /var/www/Predictor
source venv/bin/activate
python superastro_ml_extractor.py

# Ver última extracción
ls -lt logs/extractor_*.log | head -1 | awk '{print $NF}' | xargs cat
```

Si las evaluaciones no funcionan:

```bash
# Ejecutar evaluador manualmente
python evaluar_predicciones.py

# Ver estado del JSON
tail -50 predicciones_historial.json
```
