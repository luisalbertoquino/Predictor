#!/bin/bash
# ============================================================
# Script de actualización y recuperación completa
# Uso: ./actualizar.sh [--predictores] [--forzar]
#   --predictores : también ejecuta los predictores tras actualizar
#   --forzar      : hace git reset --hard antes del pull (descarta cambios locales)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/actualizacion_$(date +%Y-%m-%d_%H-%M-%S).log"

# ---- Colores ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

echo "=============================================" | tee -a "$LOG_FILE"
echo " SUPERASTRO - Actualización $(date)"          | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"

# ---- Argumentos ----
EJECUTAR_PREDICTORES=false
FORZAR=false
for arg in "$@"; do
    case $arg in
        --predictores) EJECUTAR_PREDICTORES=true ;;
        --forzar)      FORZAR=true ;;
    esac
done

# ============================================================
# PASO 1: Git pull
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "--- [1/4] Actualizando código desde GitHub ---" | tee -a "$LOG_FILE"

git config --global --add safe.directory "$SCRIPT_DIR" 2>/dev/null

if [ "$FORZAR" = true ]; then
    warn "Modo forzar: descartando cambios locales..."
    git reset --hard HEAD >> "$LOG_FILE" 2>&1
fi

git_output=$(git pull 2>&1)
git_status=$?
echo "$git_output" | tee -a "$LOG_FILE"

if [ $git_status -ne 0 ]; then
    err "git pull falló. Intentando con reset..."
    git reset --hard HEAD >> "$LOG_FILE" 2>&1
    git pull >> "$LOG_FILE" 2>&1 || { err "No se pudo actualizar. Revisa la conexión o conflictos."; exit 1; }
fi
ok "Código actualizado"

# Dar permisos a los scripts .sh
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null

# ============================================================
# PASO 2: Verificar entorno virtual e instalar dependencias nuevas
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "--- [2/4] Verificando dependencias ---" | tee -a "$LOG_FILE"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    ok "Entorno virtual activado"

    # Solo instalar si requirements.txt cambió en el pull
    if echo "$git_output" | grep -q "requirements.txt"; then
        warn "requirements.txt cambió, instalando dependencias..."
        pip install -r requirements.txt >> "$LOG_FILE" 2>&1
        ok "Dependencias actualizadas"
    else
        ok "Sin cambios en dependencias"
    fi
else
    warn "No hay entorno virtual en venv/. Flask podría fallar."
fi

# ============================================================
# PASO 3: Reiniciar Flask via Supervisor
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "--- [3/4] Reiniciando servidor Flask ---" | tee -a "$LOG_FILE"

if command -v supervisorctl &> /dev/null; then
    supervisorctl restart superastro >> "$LOG_FILE" 2>&1
    sleep 3

    # Verificar que levantó correctamente
    status=$(supervisorctl status superastro 2>&1)
    echo "$status" | tee -a "$LOG_FILE"

    if echo "$status" | grep -q "RUNNING"; then
        ok "Flask corriendo correctamente"
    else
        err "Flask NO está corriendo. Revisando logs..."
        echo "--- Últimas líneas de flask_error.log ---" | tee -a "$LOG_FILE"
        tail -20 "$LOG_DIR/flask_error.log" 2>/dev/null | tee -a "$LOG_FILE"
        echo "--- Últimas líneas de flask_output.log ---" | tee -a "$LOG_FILE"
        tail -20 "$LOG_DIR/flask_output.log" 2>/dev/null | tee -a "$LOG_FILE"
    fi
else
    warn "supervisorctl no disponible. Intenta reiniciar Flask manualmente."
fi

# ============================================================
# PASO 4 (opcional): Ejecutar predictores
# ============================================================
if [ "$EJECUTAR_PREDICTORES" = true ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "--- [4/4] Ejecutando predictores ---" | tee -a "$LOG_FILE"
    bash "$SCRIPT_DIR/run_all_predictors.sh" | tee -a "$LOG_FILE"
    ok "Predictores completados"
else
    echo "" | tee -a "$LOG_FILE"
    ok "[4/4] Predictores omitidos (usa --predictores para ejecutarlos)"
fi

# ============================================================
# Resumen final
# ============================================================
echo "" | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"
echo " Actualización completada: $(date)"           | tee -a "$LOG_FILE"
echo " Log guardado en: $LOG_FILE"                  | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"

# Verificar estado del JSON
echo "" | tee -a "$LOG_FILE"
echo "--- Estado del sistema ---" | tee -a "$LOG_FILE"
python3 -c "
import json, os
f = 'predicciones_historial.json'
if os.path.exists(f):
    with open(f) as fp:
        d = json.load(fp)
    preds = d.get('predicciones', [])
    evaluadas = [p for p in preds if p.get('evaluado')]
    pendientes = [p for p in preds if not p.get('evaluado')]
    print(f'  Predicciones totales : {len(preds)}')
    print(f'  Evaluadas            : {len(evaluadas)}')
    print(f'  Pendientes           : {len(pendientes)}')
    if preds:
        print(f'  Más reciente         : {preds[0].get(\"fecha_sorteo\")} - {preds[0].get(\"turno\")}')
else:
    print('  ADVERTENCIA: predicciones_historial.json no existe!')
" 2>&1 | tee -a "$LOG_FILE"

exit 0
