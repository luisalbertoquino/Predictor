#!/bin/bash
# Script para ejecutar todos los predictores automáticamente
# Diseñado para ejecutarse a las 2 AM diariamente

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/predictors_$TIMESTAMP.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "Iniciando predictores - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Entorno virtual activado" | tee -a "$LOG_FILE"
fi

# Ejecutar cada predictor
echo "" | tee -a "$LOG_FILE"
echo "[1/5] Ejecutando Predictor Maestro..." | tee -a "$LOG_FILE"
python superastro_predictor_maestro.py >> "$LOG_FILE" 2>&1
echo "✓ Maestro completado" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[2/5] Ejecutando Predicción Avanzada..." | tee -a "$LOG_FILE"
python superastro_prediccion_avanzada.py >> "$LOG_FILE" 2>&1
echo "✓ Avanzada completada" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[3/5] Ejecutando Predictor Mejorado..." | tee -a "$LOG_FILE"
python superastro_predictor_mejorado.py >> "$LOG_FILE" 2>&1
echo "✓ Mejorado completado" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[4/5] Ejecutando ML Basic..." | tee -a "$LOG_FILE"
python superastro_ml_predictor.py >> "$LOG_FILE" 2>&1
echo "✓ ML Basic completado" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[5/5] Ejecutando LSTM..." | tee -a "$LOG_FILE"
python superastro_lstm_predictor.py >> "$LOG_FILE" 2>&1
echo "✓ LSTM completado" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[6/6] Evaluando predicciones con resultados reales..." | tee -a "$LOG_FILE"
python evaluar_predicciones.py >> "$LOG_FILE" 2>&1
echo "✓ Evaluación completada" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Todos los predictores y evaluaciones completados - $(date)" | tee -a "$LOG_FILE"
echo "Log guardado en: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Limpiar logs antiguos (mantener solo últimos 30 días)
find "$LOG_DIR" -name "predictors_*.log" -mtime +30 -delete 2>/dev/null

exit 0
