# Fases Futuras del Proyecto de Análisis de Marcha

> Historical document. See the [current documentation](../README.md) for maintained commands and specifications.

**Estado Actual**: Fases 1, 2, 3 implementadas y validadas

**Siguientes pasos**: Análisis poblacional y comparaciones multi-cohorte

---

## Fase 4: Batch Processing Pipeline

### Objetivo

Procesar automáticamente todos los 260 pacientes del dataset (73 sanos + 143 neurológicos + 44 ortopédicos) ejecutando las 3 fases del pipeline para generar un CSV master consolidado con todas las métricas.

### Implementación Propuesta

**Script principal**: `scripts/run_full_analysis.py`

**Funcionalidades**:

1. **Iteración sobre todo el dataset**:
   - Escanear directorios `healthy/`, `neuro/`, `ortho/`
   - Detectar automáticamente todos los trials disponibles
   - Manejar estructura jerárquica (grupo → patología → sujeto → trial)

2. **Ejecución robusta de pipelines**:
   - Ejecutar Fase 1 (espectral) para ambos pies
   - Ejecutar Fase 2 (fase instantánea) para ambos pies
   - Ejecutar Fase 3 (sincronización)
   - Manejo de errores por trial (skip y log)
   - Progress bar para seguimiento

3. **Consolidación de resultados**:
   - Cargar CSVs individuales (frequency_summary.csv, phase_summary.csv, synchronization_summary.csv)
   - Merge con metadata del trial
   - Generar CSV master único

4. **Logging**:
   - Trials procesados exitosamente
   - Trials con errores (señal corrupta, metadata faltante, etc.)
   - Estadísticas de procesamiento

### Outputs Esperados

**Archivo principal**: `results/master_metrics.csv`

**Columnas** (~35-40):

**Metadata** (del JSON):
- `subject`, `group`, `pathologyKey`, `age`, `gender`, `height`, `weight`, `BMI`
- `laterality`, `clinicalDeficitSide`
- `evaluationScoreName`, `evaluationScoreValue`
- `session`, `daysSinceFirstSession`, `trial`

**Fase 1 - Métricas espectrales** (por pie):
- `f0_left`, `f0_right`
- `spectral_snr_left`, `spectral_snr_right`
- `peak_width_left`, `peak_width_right`
- `energy_ratio_left`, `energy_ratio_right`

**Fase 2 - Métricas de fase** (por pie):
- `mean_inst_freq_left`, `mean_inst_freq_right`
- `median_inst_freq_left`, `median_inst_freq_right`
- `cv_inst_freq_left`, `cv_inst_freq_right`
- `mad_inst_freq_left`, `mad_inst_freq_right`
- `valid_fraction_left`, `valid_fraction_right`
- `mask_strategy_left`, `mask_strategy_right`

**Fase 3 - Métricas de sincronización**:
- `plv`, `mean_phase_diff`, `anti_phase_error`
- `circular_variance`, `circular_std`
- `freq_diff`, `freq_ratio`, `frequency_match_flag`
- `valid_fraction_sync`

### Pseudocódigo

```python
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def run_full_analysis(base_path, output_dir):
    """
    Process all trials in the dataset.
    """
    results = []
    errors = []

    # Scan all groups and pathologies
    for group in ['healthy', 'neuro', 'ortho']:
        group_path = Path(base_path) / group

        for pathology_dir in group_path.iterdir():
            for subject_dir in pathology_dir.iterdir():
                for trial_dir in subject_dir.iterdir():
                    trial_name = trial_dir.name

                    try:
                        # Run Phase 1, 2, 3
                        metrics_p1_left = run_phase1(trial_name, "LF_Gyr_Y")
                        metrics_p1_right = run_phase1(trial_name, "RF_Gyr_Y")
                        metrics_p2_left = run_phase2(trial_name, "LF_Gyr_Y")
                        metrics_p2_right = run_phase2(trial_name, "RF_Gyr_Y")
                        metrics_p3 = run_phase3(trial_name)

                        # Load metadata
                        metadata = load_metadata(trial_dir)

                        # Consolidate
                        row = {**metadata, **metrics_p1_left, **metrics_p1_right,
                               **metrics_p2_left, **metrics_p2_right, **metrics_p3}

                        results.append(row)

                    except Exception as e:
                        errors.append({"trial": trial_name, "error": str(e)})

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_dir / "master_metrics.csv", index=False)

    # Save error log
    df_errors = pd.DataFrame(errors)
    df_errors.to_csv(output_dir / "processing_errors.csv", index=False)

    return df, df_errors
```

### Consideraciones

1. **Paralelización**: Usar `multiprocessing` o `joblib` para procesar trials en paralelo
2. **Memoria**: Procesar de forma incremental si hay problemas de RAM
3. **Cache**: Evitar re-procesar trials ya analizados (verificar existencia en CSVs)
4. **Validación**: Verificar integridad de datos antes de análisis estadístico

---

## Fase 5: Statistical Analysis & Visualization

### Objetivo

Realizar análisis estadístico comparativo entre grupos (sanos vs patológicos) y generar visualizaciones publication-ready para identificar biomarcadores de marcha.

### Implementación Propuesta

**Script principal**: `scripts/statistical_analysis.py`

**Análisis a realizar**:

### 1. Comparación entre grupos principales

**Grupos a comparar**:
- Healthy (n=73) vs Neuro (n=143) vs Ortho (n=44)

**Tests estadísticos**:
- **Kruskal-Wallis** (no paramétrico, 3+ grupos)
- **Post-hoc**: Dunn's test con corrección Bonferroni
- **Tamaño de efecto**: Cohen's d o rank-biserial correlation

**Métricas clave**:
- `plv`: ¿Sincronización deteriorada en patologías?
- `anti_phase_error`: ¿Coordinación anormal?
- `freq_ratio`: ¿Asimetría entre pies?
- `cv_inst_freq_left/right`: ¿Ritmo irregular?
- `spectral_snr_left/right`: ¿Calidad de señal?

### 2. Comparación entre patologías específicas

**Dentro de neuro**:
- CIPN vs CVA vs PD vs RIL

**Dentro de ortho**:
- ACL vs HOA vs KOA

**Hipótesis**:
- Parkinson (PD): PLV bajo, cv_inst_freq alto
- CVA (ictus): alta asimetría (freq_ratio), anti_phase_error alto
- Ortopédicos: asimetría correlacionada con lado afectado

### 3. Análisis de asimetría

**Métricas derivadas**:
```python
asymmetry_freq = abs(f0_left - f0_right)
asymmetry_cv = abs(cv_inst_freq_left - cv_inst_freq_right)
asymmetry_amplitude = abs(amplitude_mean_left - amplitude_mean_right)
```

**Comparación**:
- Healthy vs CVA (esperado: CVA >> asimetría)
- Healthy vs ACL (esperado: ACL > asimetría)
- Correlación con `clinicalDeficitSide`

### 4. Correlación con escalas clínicas

**Para pacientes con evaluación clínica**:
- Correlación Spearman entre métricas objetivas y scores clínicos
- Ejemplo: TNSc (neuropatía) vs cv_inst_freq
- Ejemplo: UPDRS (Parkinson) vs plv

**Outputs**:
- Matriz de correlaciones
- Scatter plots con líneas de regresión
- p-values y R² ajustado

### 5. Análisis por demografía

**Covariables**:
- Edad: ¿cv_inst_freq aumenta con edad?
- Sexo: ¿Diferencias hombre vs mujer?
- BMI: ¿Afecta a frecuencia de marcha?

**Método**: ANCOVA o regresión lineal múltiple

### Visualizaciones a Generar

**Archivo**: `results/figures/`

**Figuras principales**:

1. **Boxplots de métricas clave por grupo** (6 figuras):
   - PLV por grupo (healthy vs neuro vs ortho)
   - Anti-phase error por grupo
   - CV inst. freq (left) por grupo
   - Freq ratio (asimetría) por grupo
   - Spectral SNR (left) por grupo
   - Dominant frequency por grupo

2. **Violin plots por patología** (4 figuras):
   - PLV por patología (8 categorías)
   - Anti-phase error por patología
   - Freq ratio por patología
   - CV inst. freq por patología

3. **Scatter plots de asimetría** (3 figuras):
   - freq_left vs freq_right (colored by group)
   - cv_left vs cv_right (colored by group)
   - amplitude_left vs amplitude_right (colored by clinical deficit side)

4. **Correlación con escalas clínicas** (2 figuras):
   - PLV vs clinical scores
   - CV inst. freq vs clinical scores

5. **Heatmap de correlaciones** (1 figura):
   - Matriz de correlación entre todas las métricas

**Formato**:
- PDF vectorial (para publicaciones)
- DPI 300 (alta resolución)
- Estilo seaborn "whitegrid"
- Tamaños consistentes (figsize=(10, 6))

### Pseudocódigo

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def statistical_analysis(master_csv_path, output_dir):
    """
    Comprehensive statistical analysis.
    """
    # Load data
    df = pd.read_csv(master_csv_path)

    # 1. Descriptive statistics
    summary_stats = df.groupby('group')[['plv', 'anti_phase_error',
                                          'freq_ratio', 'cv_inst_freq_left']].describe()
    summary_stats.to_csv(output_dir / "descriptive_stats.csv")

    # 2. Kruskal-Wallis test
    groups = [df[df['group'] == g]['plv'].dropna() for g in ['healthy', 'neuro', 'ortho']]
    h_stat, p_value = stats.kruskal(*groups)

    print(f"Kruskal-Wallis H-test for PLV: H={h_stat:.3f}, p={p_value:.4f}")

    # 3. Post-hoc Dunn's test
    # (using scikit-posthocs library)
    from scikit_posthocs import posthoc_dunn
    posthoc_results = posthoc_dunn(df, val_col='plv', group_col='group', p_adjust='bonferroni')

    # 4. Generate boxplots
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x='group', y='plv', ax=ax)
    ax.set_title("Phase Locking Value by Group", fontsize=14, fontweight='bold')
    ax.set_ylabel("PLV", fontsize=12)
    ax.set_xlabel("Group", fontsize=12)
    plt.savefig(output_dir / "figures" / "plv_by_group.pdf", dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Correlation with clinical scores
    neuro_df = df[df['group'] == 'neuro'].dropna(subset=['evaluationScoreValue', 'plv'])
    correlation, p_val = stats.spearmanr(neuro_df['evaluationScoreValue'], neuro_df['plv'])

    print(f"Spearman correlation PLV vs Clinical Score: r={correlation:.3f}, p={p_val:.4f}")

    # ... (more analyses)

    return summary_stats, posthoc_results
```

### Outputs Esperados

1. **`results/descriptive_stats.csv`**: Estadísticas descriptivas por grupo
2. **`results/statistical_tests.csv`**: Resultados de tests (p-values, effect sizes)
3. **`results/posthoc_results.csv`**: Comparaciones post-hoc
4. **`results/correlations.csv`**: Matriz de correlaciones
5. **`results/figures/*.pdf`**: 15-20 figuras publication-ready
6. **`results/statistical_report.md`**: Informe narrativo con interpretación

### Dependencias Adicionales

```toml
# Añadir a pyproject.toml
dependencies = [
    # ... existing
    "seaborn>=0.12.0",
    "scikit-posthocs>=0.7.0",  # Para tests post-hoc
    "statsmodels>=0.14.0",     # Para ANCOVA y regresión
]
```

---

## Cronograma Sugerido

**Semana 1-2**: Implementar Fase 4 (Batch Processing)
- Desarrollar script de procesamiento batch
- Ejecutar en todos los 260 pacientes
- Validar CSV master

**Semana 3**: Implementar Fase 5 (Statistical Analysis)
- Análisis exploratorio del CSV master
- Tests estadísticos comparativos
- Generar figuras preliminares

**Semana 4**: Refinamiento y Documentación
- Revisar resultados con criterio científico
- Generar informe final
- Preparar figuras para publicación

---

## Valor Científico Esperado

### Hipótesis a validar:

1. **PLV será significativamente menor en neurológicos vs sanos** (p < 0.001)
2. **Anti-phase error será mayor en CVA** (coordinación alterada post-ictus)
3. **Freq ratio (asimetría) será mayor en ortopédicos con lesión unilateral**
4. **CV inst. freq correlacionará con severidad clínica** (r > 0.5)

### Publicaciones potenciales:

- **Paper 1**: "Phase synchronization analysis reveals impaired gait coordination in neurological disorders"
- **Paper 2**: "Automated gait metrics from IMU sensors as objective biomarkers for clinical assessment"
- **Dataset contribution**: Validación de métricas en dataset público (CitableURL cuando se publique)

---

## Próximos Pasos Inmediatos

1. ✅ **Validar Fase 3** con varios trials (en curso)
2. Implementar Fase 4 (batch processing)
3. Ejecutar análisis completo del dataset
4. Generar resultados para Fase 5
