#!/bin/bash
# Script para extraer resultados y evaluar predicciones
# Se ejecuta después de cada sorteo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/extractor_$TIMESTAMP.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "Extracción y Evaluación - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Entorno virtual activado" | tee -a "$LOG_FILE"
fi

# Dar 5 minutos de margen después del sorteo para que publiquen resultados
echo "" | tee -a "$LOG_FILE"
echo "⏳ Esperando 5 minutos para que publiquen resultado..." | tee -a "$LOG_FILE"
sleep 300

# Extraer resultados de la página (solo hoy/ayer)
echo "" | tee -a "$LOG_FILE"
echo "[1/2] Extrayendo resultados recientes de SuperAstro..." | tee -a "$LOG_FILE"
python extraer_hoy.py >> "$LOG_FILE" 2>&1
echo "✓ Extracción completada" | tee -a "$LOG_FILE"

# Evaluar predicciones con los nuevos resultados
echo "" | tee -a "$LOG_FILE"
echo "[2/2] Evaluando predicciones..." | tee -a "$LOG_FILE"
python evaluar_predicciones.py >> "$LOG_FILE" 2>&1
echo "✓ Evaluación completada" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Proceso completado - $(date)" | tee -a "$LOG_FILE"
echo "Log guardado en: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit 0
