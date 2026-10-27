# Batch Processing - Guía de Uso

> Documento histórico de la implementación anterior. Para el comportamiento y la validación actuales, consultar [baseline_validation.md](../baseline_validation.md) y el [README](../../README.md). Sus cifras y conclusiones deben recalcularse con la versión actual.

## Uso Básico

### 1. Procesar 8 trials por grupo (DEFAULT)
```bash
uv run python scripts/run_batch_processing.py
```
- Procesa 8 trials exitosos de cada grupo médico
- Salta automáticamente trials con NaN/Inf
- Genera: `outputs/tables/master_metrics.csv`

---

### 2. Procesar TODOS los trials disponibles
```bash
uv run python scripts/run_batch_processing.py --all
```
- Procesa todos los trials disponibles (~360 healthy, ~784 neuro, ~212 ortho)
- Salta automáticamente trials con NaN/Inf
- **Tiempo estimado**: 2-4 horas (sin imágenes)

---

### 3. Procesar número específico por grupo
```bash
# 20 trials por grupo
uv run python scripts/run_batch_processing.py --target 20

# 50 trials por grupo
uv run python scripts/run_batch_processing.py --target 50
```

---

### 4. Procesar solo ciertos grupos médicos

#### Solo sanos:
```bash
uv run python scripts/run_batch_processing.py --groups healthy
```

#### Solo neurológicos:
```bash
uv run python scripts/run_batch_processing.py --groups neuro
```

#### Solo ortopédicos:
```bash
uv run python scripts/run_batch_processing.py --groups ortho
```

#### Sanos + Neurológicos:
```bash
uv run python scripts/run_batch_processing.py --groups healthy neuro
```

---

### 5. Combinaciones avanzadas

#### TODOS los trials neurológicos:
```bash
uv run python scripts/run_batch_processing.py --all --groups neuro
```

#### 100 trials de sanos y ortopédicos:
```bash
uv run python scripts/run_batch_processing.py --target 100 --groups healthy ortho
```

---

## Archivos Generados

### 1. CSV Principal
- **Ubicación**: `outputs/tables/master_metrics.csv`
- **Contenido**: 25 columnas con métricas de Fase 1, 2 y 3
- **Uso**: Análisis estadístico, machine learning, visualización

### 2. Log de Errores
- **Ubicación**: `outputs/tables/processing_errors.csv`
- **Contenido**: Trials que fallaron (NaN/Inf) con mensaje de error

### 3. Reporte de Resumen
- **Ubicación**: `outputs/reports/batch_processing_summary.txt`
- **Contenido**: Estadísticas de procesamiento por grupo

---

## Características

✅ **Sin generación de imágenes** - Procesamiento rápido
✅ **Guardado incremental** - Checkpoint cada 20 trials
✅ **Manejo robusto de errores** - Salta NaN/Inf automáticamente
✅ **Deduplicación** - Elimina entradas duplicadas al finalizar
✅ **Progreso en tiempo real** - Muestra PLV de cada trial

---

## Tiempos Estimados

| Configuración | Trials | Tiempo estimado |
|---------------|--------|-----------------|
| Default (8 por grupo) | ~24 | 3-5 min |
| Target 20 | ~60 | 8-12 min |
| Target 50 | ~150 | 20-30 min |
| --all (todos) | ~800-1000 | 2-4 horas |

*Nota: Los tiempos asumen ~54% de trials exitosos (resto tiene NaN/Inf)*

---

## Ver Ayuda

```bash
uv run python scripts/run_batch_processing.py --help
```
