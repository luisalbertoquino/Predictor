# 🎰 SuperAstro Predictor - Sistema de Predicción ML

Sistema automatizado de predicción para SuperAstro usando Machine Learning y Deep Learning con dashboard web interactivo.

---

## 🚀 Inicio Rápido

### Dashboard Web (RECOMENDADO) 🌐

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar dashboard web
python superastro_web.py

# 3. Abrir navegador en: http://localhost:5000
```

**Dashboard Web incluye:**
- ✅ Ejecutar todos los predictores con un click
- ✅ Ver logs en tiempo real
- ✅ Gráficos de estadísticas
- ✅ Historial de predicciones
- ✅ Resultados evaluados automáticamente

---

### Opción 2: Línea de Comandos

```bash
# Instalar dependencias (solo la primera vez)
pip install pandas numpy scikit-learn xgboost openpyxl beautifulsoup4 requests statsmodels tensorflow

# Ejecutar predictor maestro
python superastro_predictor_maestro.py
```

---

## 📊 Métodos de Predicción Disponibles

El sistema incluye **4 métodos diferentes** que se ejecutan en paralelo:

| Método | Descripción | Fortaleza |
|--------|-------------|-----------|
| **Random Forest** | Bosques aleatorios | Patrones generales |
| **XGBoost** | Gradient Boosting | Tendencias recientes |
| **Estadístico Avanzado** | One-Hot + DW Test | Autocorrelación |
| **LSTM (Red Neuronal)** | Deep Learning | Secuencias temporales |

---

## 📁 Archivos Importantes

### Scripts Principales
- `superastro_predictor_maestro.py` - **Ejecuta todo** (usar este)
- `superastro_ml_predictor.py` - Random Forest + XGBoost
- `superastro_predictor_mejorado.py` - Método estadístico avanzado
- `superastro_lstm_predictor.py` - Red neuronal LSTM

### Datos
- `predicciones_historial.json` - Historial unificado de predicciones
- `superastro_ml_data_*.xlsx` - Base de datos actualizada (se usa el más reciente)

---

## 💡 Uso Diario Recomendado

### Opción 1: Ejecución Automática Completa (Recomendado)
```bash
python superastro_predictor_maestro.py
```
**Resultado:** Predicciones de los 4 métodos + comparación + consenso

### Opción 2: Ejecutar Métodos Individuales
```bash
# Solo Random Forest + XGBoost (rápido - 30 seg)
python superastro_ml_predictor.py

# Solo método estadístico avanzado (moderado - 2 min)
python superastro_predictor_mejorado.py

# Solo red neuronal LSTM (lento - 45 min)
python superastro_lstm_predictor.py
```

---

## 📈 Interpretación de Resultados

### Consenso Alto ✅
Cuando 3 o 4 métodos predicen números similares:
```
SOL:
  RF:     2450 - Acuario
  XGB:    2470 - Acuario
  LSTM:   2420 - Acuario
  Estad:  2490 - Acuario

→ Recomendación: 2450 - Acuario (alta confianza)
```

### Consenso Bajo ⚠️
Cuando los métodos predicen números muy diferentes:
```
SOL:
  RF:     1200 - Aries
  XGB:    5600 - Leo
  LSTM:   9100 - Piscis
  Estad:  3400 - Géminis

→ Usar con precaución (señal débil)
```

---

## 📊 Ver Estadísticas

### Resumen de Aciertos
El sistema automáticamente evalúa predicciones y muestra:
- Promedio de dígitos acertados
- Porcentaje de signos correctos
- Ranking de mejores métodos
- Tendencias (mejorando/empeorando)

### Comando de Estadísticas Detalladas
```bash
python superastro_estadisticas.py
```

---

## 🔄 Actualización de Datos

El sistema actualiza automáticamente los datos cada vez que ejecutas una predicción. Si quieres forzar actualización:

```bash
python superastro_ml_extractor.py
```

---

## ❓ Preguntas Frecuentes

### ¿Cuánto tiempo toma cada método?
- Random Forest + XGBoost: **30 segundos**
- Estadístico Avanzado: **2 minutos**
- LSTM: **45-60 minutos**
- Maestro (todos): **50-65 minutos**

### ¿Cuál método es mejor?
Después de 5-7 días de uso, revisa las estadísticas con:
```bash
python superastro_estadisticas.py
```

### ¿Qué significa "Durbin-Watson = 0.58"?
Indica **alta autocorrelación** (hay patrones detectables). Valores:
- < 1.5 = 🔥 Hay patrón fuerte
- 1.5-2.5 = ✅ Aleatorio normal
- > 2.5 = ⚠️ Patrón inverso

### ¿Los archivos Excel viejos se pueden borrar?
Sí, el sistema solo usa el más reciente. Borra manualmente los antiguos `superastro_ml_data_*.xlsx`.

---

## 🛠️ Solución de Problemas

### Error: "No module named 'tensorflow'"
```bash
pip install tensorflow
```

### Error: "No se encontró archivo de datos"
```bash
python superastro_ml_extractor.py
```

### Predicciones no se evalúan automáticamente
Ejecuta el predictor nuevamente después de que salgan los resultados oficiales.

---

## 📝 Notas Importantes

1. **Las predicciones son probabilísticas**, no garantizadas
2. Los resultados de loterías son **eventos aleatorios**
3. Requiere mínimo **5-7 días** de uso para evaluar confiabilidad
4. Ejecutar diariamente para mantener modelos actualizados
5. El historial se guarda automáticamente en `predicciones_historial.json`

---

## 📞 Soporte

Para reportar errores o pedir ayuda, revisa los logs del script o contacta al desarrollador.

**Versión:** 2.0 - Sistema Unificado
**Última actualización:** Enero 2026
