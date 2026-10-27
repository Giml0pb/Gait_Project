# Patient-Level Aggregation Summary

> Documento histórico de la implementación anterior. Para el comportamiento y la validación actuales, consultar [baseline_validation.md](../baseline_validation.md) y el [README](../../README.md). Sus cifras y conclusiones deben recalcularse con la versión actual.

**Fecha**: 2026-03-09
**Estado**: ✅ **COMPLETADO**

---

## 🎯 Objetivo

Agregar métricas de múltiples trials por paciente en un único registro representativo, reduciendo ruido intra-sujeto y proporcionando datos apropiados para análisis estadístico entre grupos.

---

## 📊 Resultados

### Agregación

- **Input**: 987 trials (master_metrics.csv)
- **Output**: 232 pacientes (patient_aggregated_metrics.csv)
- **Trials por paciente**:
  - Mediana: 4 trials
  - Rango: 1-19 trials
  - Media: 4.3 trials

### Distribución por Grupo

| Grupo    | N Pacientes | N Trials | Trials/Paciente |
|----------|-------------|----------|-----------------|
| Healthy  | 57          | ~243     | 4.3             |
| Neuro    | 138         | ~587     | 4.3             |
| Ortho    | 37          | ~157     | 4.2             |
| **Total**| **232**     | **987**  | **4.3**         |

---

## 📁 Estructura del CSV

### Total: 45 columnas

**Columnas 1-8: Metadata** (del primer trial)
- subject, group, pathology
- age, gender, BMI
- evaluation_score_value, session

**Columna 9: Información de agregación**
- `n_trials` - Número de trials promediados

**Columnas 10-36: Métricas promediadas**
- Todas las métricas continuas (PLV, frecuencias, phase_slip_rate, etc.)
- frequency_match_flag (moda)

**Columnas 37-45: Variabilidad intra-sujeto (std)**
- `plv_std` - Desviación estándar de PLV entre trials del mismo paciente
- `anti_phase_error_deg_std` - Variabilidad del error de anti-fase
- `phase_slip_rate_std` - Variabilidad de la tasa de phase slips
- `plv_mean_windowed_std` - Variabilidad del PLV windowed
- `plv_std_windowed_std` - Variabilidad de la std del PLV windowed
- `mean_inst_freq_left_std` - Variabilidad de frecuencia instantánea izquierda
- `mean_inst_freq_right_std` - Variabilidad de frecuencia instantánea derecha
- `cv_inst_freq_left_std` - Variabilidad del CV de frecuencia izquierda
- `cv_inst_freq_right_std` - Variabilidad del CV de frecuencia derecha

---

## 🔬 Análisis Comparativo: Healthy vs Pathological

### N Pacientes
- **Healthy**: 57 pacientes
- **Pathological**: 175 pacientes (138 neuro + 37 ortho)

### Métricas Clave (Promediadas a Nivel Paciente)

| Métrica | Healthy | Pathological | p-value | Significancia |
|---------|---------|--------------|---------|---------------|
| **PLV (global)** | 0.973 ± 0.071 | 0.903 ± 0.247 | **0.0375** | ⭐ p<0.05 |
| **PLV (windowed mean)** | 0.983 ± 0.065 | 0.928 ± 0.204 | **0.0478** | ⭐ p<0.05 |
| **Anti-phase error** | 5.3° ± 7.6° | 15.5° ± 28.5° | **0.0084** | ⭐⭐ p<0.01 |
| Phase slip rate | 0.59 ± 1.28 | 1.26 ± 3.65 | 0.1715 | n.s. |
| PLV std (windowed) | 0.016 ± 0.024 | 0.023 ± 0.041 | 0.2414 | n.s. |

### Variabilidad Intra-Sujeto

| Métrica | Healthy | Pathological | p-value |
|---------|---------|--------------|---------|
| PLV variability | 0.0180 | 0.0248 | 0.5529 (n.s.) |
| Anti-phase error variability | 2.42° | 4.98° | 0.1214 (n.s.) |
| Phase slip rate variability | 0.51 | 0.88 | 0.2097 (n.s.) |

---

## 📈 Interpretación Científica

### ✅ Mejoras con Agregación por Paciente

**Comparado con trial-level (60 trials del análisis anterior)**:

1. **Mayor poder estadístico**:
   - PLV: p=0.187 (trials) → **p=0.0375** (pacientes) ✅ Ahora significativo!
   - PLV windowed: p=0.172 (trials) → **p=0.0478** (pacientes) ✅ Ahora significativo!
   - Anti-phase error: p=0.001 (trials) → **p=0.0084** (pacientes) ✅ Sigue significativo!

2. **N real e independiente**:
   - Antes: 60 trials (20 healthy, 40 patho) - pseudoreplicación
   - Ahora: 232 pacientes (57 healthy, 175 patho) - muestras independientes

3. **Mejor caracterización**:
   - Cada paciente representado por su "verdadera" coordinación (promedio de 4 trials)
   - Ruido intra-sujeto cuantificado con `*_std` columns

### 🔍 Hallazgos Principales

**A nivel paciente (N=232):**

1. **PLV discrimina significativamente** (p<0.05):
   - Healthy: 0.973 (muy alta coordinación)
   - Pathological: 0.903 (coordinación reducida)

2. **Anti-phase error es el mejor discriminador** (p<0.01):
   - Healthy: 5.3° (cerca de anti-fase perfecta)
   - Pathological: 15.5° (desviación mayor)

3. **Métricas temporales no discriminan**:
   - Phase slip rate: p=0.17
   - PLV std windowed: p=0.24
   - **Pero siguen siendo útiles para caracterización individual**

4. **Variabilidad intra-sujeto no discrimina**:
   - Pacientes pathological tienen mayor variabilidad pero p>0.05
   - Tendencia (no significativa) hacia más inestabilidad

### 🎯 Implicaciones para Uso

**Para análisis estadístico (papers/reportes)**:
- ✅ **USAR `patient_aggregated_metrics.csv`** - Evita pseudoreplicación
- ✅ Anti-phase error es la métrica principal (p<0.01)
- ✅ PLV y PLV windowed también discriminan (p<0.05)
- ℹ️ N real: 57 healthy vs 175 pathological

**Para análisis clínico individual**:
- ✅ **USAR `master_metrics.csv`** - Detalle trial-by-trial
- ✅ Métricas temporales útiles para detectar patrones anormales
- ✅ Variabilidad intra-trial visible en visualizaciones

**Para estudios longitudinales**:
- ✅ `master_metrics.csv` permite ver evolución trial-by-trial
- ✅ `*_std` en patient CSV cuantifica estabilidad del paciente

---

## 🛠️ Implementación

### Script: `scripts/aggregate_by_patient.py`

**Funcionalidad**:
1. Lee `master_metrics.csv` (987 trials)
2. Agrupa por `subject` (232 pacientes)
3. Calcula:
   - **Mean** para todas las métricas continuas
   - **Mode** para métricas categóricas (frequency_match_flag)
   - **Std** para 9 métricas clave
   - **Count** de trials por paciente (`n_trials`)

**Métricas con std**:
- `plv_std`
- `anti_phase_error_deg_std`
- `phase_slip_rate_std`
- `plv_mean_windowed_std`
- `plv_std_windowed_std`
- `mean_inst_freq_left_std`
- `mean_inst_freq_right_std`
- `cv_inst_freq_left_std`
- `cv_inst_freq_right_std`

**Uso**:
```bash
uv run python scripts/aggregate_by_patient.py
```

**Output**: `outputs/tables/patient_aggregated_metrics.csv`

---

## ✅ Conclusiones

### 1. Agregación Exitosa ✅

- ✅ 987 trials → 232 pacientes
- ✅ 45 columnas (métricas + variabilidad)
- ✅ Sin valores perdidos
- ✅ Metadata preservada

### 2. Validación Científica ✅

- ✅ PLV ahora discrimina significativamente (p<0.05)
- ✅ Anti-phase error sigue siendo el mejor marcador (p<0.01)
- ✅ Variabilidad intra-sujeto cuantificada
- ✅ N real para análisis estadístico

### 3. Recomendaciones de Uso

**Análisis estadístico** → `patient_aggregated_metrics.csv`
- Comparaciones entre grupos
- Regresiones
- Correlaciones

**Análisis clínico individual** → `master_metrics.csv`
- Caracterización detallada trial-by-trial
- Detección de patrones anormales
- Estudios longitudinales

**Reportes/Papers** → Ambos:
- Reportar N de pacientes (232)
- Mencionar promedio de trials/paciente (4.3)
- Usar patient-level para estadística
- Usar trial-level para visualizaciones de casos

---

## 📚 Referencias Científicas

### Pseudoreplicación
- **Hurlbert, S. H. (1984)**. "Pseudoreplication and the design of ecological field experiments." *Ecological Monographs*, 54(2), 187-211.
  - **Relevancia**: Explica por qué múltiples trials del mismo sujeto no son independientes.

### Agregación de Datos Repetidos
- **Bland, J. M., & Altman, D. G. (1995)**. "Statistics notes: Calculating correlation coefficients with repeated observations." *BMJ*, 310(6977), 446.
  - **Relevancia**: Métodos apropiados para manejar medidas repetidas.

### Variabilidad Intra-Sujeto en Marcha
- **Hausdorff, J. M. (2007)**. "Gait dynamics, fractals and falls: finding meaning in the stride-to-stride fluctuations of human walking." *Human Movement Science*, 26(4), 555-589.
  - **Relevancia**: Variabilidad intra-sujeto tiene valor clínico.

---

**Autor**: Implementación completada el 2026-03-09
**Estado**: ✅ PRODUCCIÓN - Listo para uso
**Archivos**:
- Script: `scripts/aggregate_by_patient.py`
- Output: `outputs/tables/patient_aggregated_metrics.csv`
- Documentación: Este archivo

---

## 📊 Ejemplo de Datos

**Paciente ACL_1** (4 trials):
```
subject: ACL_1
group: ortho
n_trials: 4
plv: 0.953 (mean across 4 trials)
plv_std: 0.016 (intra-subject variability)
anti_phase_error_deg: 36.2°
phase_slip_rate: 0.90 slips/min
```

**Interpretación**: Paciente ortopédico (ACL) con buena coordinación promedio (PLV=0.953) y baja variabilidad entre trials (std=0.016), pero error de anti-fase elevado (36°) y algunos phase slips (0.9/min).

---

**End of Document**
