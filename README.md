# Gait Analysis Pipeline - Sistema de Análisis de Marcha

Sistema automatizado para análisis de coordinación bilateral en señales de marcha usando sincronización de fase.

## Requisitos del Sistema

- **Python 3.11 o superior**
- **Sistema operativo**: Linux, macOS, o Windows
- **Espacio en disco**: Mínimo 500 MB libres

## Instalación Rápida (3 pasos)

### Paso 1: Instalar uv (gestor de paquetes)

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Paso 2: Clonar el repositorio

```bash
git clone <repository-url>
cd Gait_Project
```

### Paso 3: Listo!

El sistema instalará automáticamente todas las dependencias en el primer uso.

## Uso del Sistema

### Opción 1: Procesamiento Individual (recomendado para exploración)

Procesar un único trial para inspección detallada:

```bash
uv run python scripts/run_single_trial.py HS_1_1
```

Esto genera:
- Figuras de diagnóstico en `outputs/figures/`
- Métricas en `outputs/tables/`

### Opción 2: Procesamiento en Lote

**Procesar 8 trials por grupo (rápido, ~5 minutos):**
```bash
uv run python scripts/run_batch_processing.py
```

**Procesar 20 trials por grupo (completo, ~15 minutos):**
```bash
uv run python scripts/run_batch_processing.py --target 20
```

**Procesar TODOS los trials disponibles (~2 horas):**
```bash
uv run python scripts/run_batch_processing.py --all
```

**Procesar solo ciertos grupos:**
```bash
uv run python scripts/run_batch_processing.py --groups healthy neuro
```

### Opción 3: Agregación por Paciente

Después del procesamiento en lote, agregar múltiples trials del mismo paciente:

```bash
uv run python scripts/aggregate_by_patient.py
```

Esto genera `patient_aggregated_metrics.csv` (232 pacientes agregados desde 987 trials), reduciendo ruido intra-sujeto y proporcionando muestras independientes para análisis estadístico.

### Opción 4: Análisis de Resultados

Analizar métricas y comparar grupos (healthy, neuro, ortho):

```bash
uv run python scripts/analyze_metrics.py
```

Esto imprime estadísticas descriptivas y comparaciones entre grupos.

## Scripts Avanzados (Procesamiento por Fases)

Para usuarios que desean ejecutar fases individuales del pipeline:

```bash
# Ejecutar solo Fase 1 (Análisis Espectral)
uv run python scripts/run_phase1.py <trial_id>

# Ejecutar solo Fase 2 (Fase Instantánea)
uv run python scripts/run_phase2.py <trial_id>

# Ejecutar solo Fase 3 (Sincronización Bilateral)
uv run python scripts/run_phase3.py <trial_id>
```

## Estructura de Salidas

```
outputs/
├── figures/          # Visualizaciones (PNG)
│   ├── *_phase1_*.png    # Análisis espectral
│   ├── *_phase2_*.png    # Fase instantánea
│   └── *_phase3_*.png    # Sincronización bilateral
├── tables/           # Métricas (CSV)
│   ├── master_metrics.csv              # ARCHIVO PRINCIPAL (987 trials)
│   ├── patient_aggregated_metrics.csv  # Agregado por paciente (232 pacientes)
│   ├── frequency_summary.csv           # Métricas Fase 1
│   ├── phase_summary.csv               # Métricas Fase 2
│   └── synchronization_summary.csv     # Métricas Fase 3
└── reports/          # Resúmenes de procesamiento
    └── batch_processing_summary.txt
```

## Métricas Computadas

El sistema calcula **36 métricas** organizadas en 3 fases del pipeline. Consultar `METRICS_REFERENCE.md` para detalles completos.

### Fase 1: Análisis Espectral (2 métricas)

- `f0_hz`: Frecuencia dominante de marcha (Hz)
- `spectral_snr`: Relación señal-ruido espectral

### Fase 2: Fase Instantánea (10 métricas, 5 por pie)

- `mean_inst_freq_left/right`: Frecuencia instantánea media (Hz)
- `cv_inst_freq_left/right`: Coeficiente de variación de frecuencia
- `valid_fraction_left/right`: Fracción de muestras válidas
- `cadence_steps_per_min_left/right`: Cadencia (pasos/minuto)
- `stride_time_left/right_s`: Tiempo de zancada (segundos)

### Fase 3: Sincronización Bilateral (19 métricas)

**Sincronización estática:**
- `plv`: Phase Locking Value [0-1] - sincronización global
- `anti_phase_error_deg`: Error respecto a anti-fase ideal (0-180°)
- `mean_phase_diff_deg`: Diferencia de fase media (grados)
- `circular_variance`: Varianza circular de diferencia de fase
- `circular_std`: Desviación estándar circular

**Sincronización temporal (nuevas métricas):**
- `phase_slip_rate`: Tasa de cambios abruptos de fase (slips/min)
- `plv_mean_windowed`: PLV promedio en ventanas de 2s
- `plv_std_windowed`: Desviación estándar de PLV en ventanas
- `plv_trend`: Tendencia temporal de PLV (pendiente)
- `n_windows`: Número de ventanas analizadas

**Frecuencia y asimetría:**
- `freq_left/right`: Frecuencia dominante por pie (Hz)
- `freq_diff`: Diferencia de frecuencia entre pies (Hz)
- `freq_ratio`: Ratio de frecuencias (relativo, %)
- `frequency_match_flag`: ¿Frecuencias coinciden? (bool)
- `stride_time_asymmetry_s`: Asimetría temporal absoluta (s)
- `stride_time_asymmetry_pct`: Asimetría temporal relativa (%)

**Validez:**
- `valid_samples_sync`: Muestras válidas para sincronización
- `valid_fraction_sync`: Fracción de muestras válidas [0-1]

## Métricas Clave para Análisis

Basado en poder discriminatorio (p-values del análisis de 232 pacientes):

1. **`anti_phase_error_deg`** (p=0.008) - Mejor discriminador entre healthy/pathological
2. **`plv`** (p=0.038) - Sincronización global significativa
3. **`plv_mean_windowed`** (p=0.048) - Sincronización temporal significativa

**Valores típicos** (N=987 trials):
- PLV: 0.964 ± 0.144 (healthy: 0.973, pathological: 0.903)
- Anti-phase error: 13.0° ± 25.4° (healthy: 5.3°, pathological: 15.5°)
- Phase slip rate: 0.84 ± 3.11 slips/min (healthy: 0.59, pathological: 1.26)

## Pipeline Científico

El sistema implementa un pipeline de 3 fases basado en el modelo de osciladores acoplados para marcha humana:

### Fase 1: Análisis Espectral
Identifica la frecuencia dominante de marcha (f₀) mediante análisis de Fourier del giroscopio (LF_Gyr_Y o RF_Gyr_Y).

**Entrada**: Señal gyroscope
**Salida**: Frecuencia dominante (f₀) y SNR espectral

### Fase 2: Extracción de Fase Instantánea
Calcula la fase instantánea φ(t) para ambos pies mediante:
1. Filtrado paso-banda alrededor de f₀ (±0.3 Hz)
2. Transformada de Hilbert para señal analítica
3. Extracción de fase con validación de calidad

**Entrada**: Señal gyroscope + f₀
**Salida**: Fase instantánea φ_L(t), φ_R(t) para ambos pies

### Fase 3: Sincronización Bilateral
Analiza la coordinación entre pies usando:
- **PLV (Phase Locking Value)**: Sincronización global
- **Anti-phase error**: Desviación de coordinación ideal (180°)
- **Métricas temporales**: Estabilidad y cambios dinámicos de sincronización

**Entrada**: Fases φ_L(t), φ_R(t)
**Salida**: 19 métricas de coordinación bilateral

## Agregación por Paciente

El pipeline ofrece dos niveles de análisis:

### Nivel Trial (master_metrics.csv)
- **N = 987 trials**
- Detalle trial-by-trial
- Útil para: análisis individuales, estudios longitudinales, visualizaciones de casos

### Nivel Paciente (patient_aggregated_metrics.csv)
- **N = 232 pacientes** (promedio de 4.3 trials/paciente)
- Métricas promediadas + variabilidad intra-sujeto (std)
- Útil para: análisis estadístico entre grupos, evita pseudoreplicación

**Recomendación**: Usar nivel paciente para análisis estadístico (comparaciones entre grupos, regresiones) y nivel trial para caracterización individual.
