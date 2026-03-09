# `load_data.py` — Carga de la base de datos de marcha

Script de acceso a la base de datos del proyecto. Proporciona funciones para navegar la estructura jerárquica del dataset y cargar datos en distintos niveles de granularidad.

---

## Estructura esperada del dataset

El `base_path` debe apuntar a la carpeta `data/` **dentro** del dataset (no a la raíz):

```
dataset/
└── data/                        ← base_path apunta aquí
    ├── healthy/
    │   └── HS/                  ← cohort
    │       ├── HS_1/            ← paciente
    │       │   ├── HS_1_1/     ← trial
    │       │   ├── HS_1_2/
    │       │   └── ...
    │       └── HS_2/ ...
    ├── neuro/
    │   ├── CIPN/
    │   ├── CVA/
    │   ├── PD/
    │   └── RIL/
    └── ortho/
        ├── ACL/
        ├── HOA/
        └── KOA/
```

### Archivos dentro de cada trial (`HS_1_1/`)

| Archivo | Descripción |
|---|---|
| `HS_1_1_raw_data_HE.txt` | Sensor cabeza (Head) — tab-delimitado |
| `HS_1_1_raw_data_LB.txt` | Sensor lumbar (Lower Back) |
| `HS_1_1_raw_data_LF.txt` | Sensor pie izquierdo (Left Foot) |
| `HS_1_1_raw_data_RF.txt` | Sensor pie derecho (Right Foot) |
| `HS_1_1_processed_data.txt` | Datos sincronizados de los 4 sensores (37 columnas) |
| `HS_1_1_meta.json` | Metadata del sujeto y del trial |

**Columnas de archivos raw:** `PacketCounter, Acc_X/Y/Z, Gyr_X/Y/Z, Mag_X/Y/Z`

**Columnas de processed:** prefijadas por sensor — `HE_Acc_X`, `LB_Gyr_Z`, etc. (+ variante `FreeAcc` con gravedad eliminada)

**Frecuencia de muestreo:** 100 Hz

---

## Funciones

### `load_bdd(base_path)`
Carga la estructura completa de la base de datos.

```python
bdd = load_bdd("path/to/dataset/data")
# Retorna:
# {
#   "healthy": {"HS": ["HS_1", "HS_2", ...]},
#   "ortho":   {"KOA": [...], "HOA": [...], "ACL": [...]},
#   "neuro":   {"PD": [...], "CVA": [...], "CIPN": [...], "RIL": [...]}
# }
```

---

### `load_cohort(base_path, cohort_name)`
Carga los pacientes de una cohorte específica.

```python
top_level, cohort = load_cohort(base_path, "HS")
# top_level → "healthy"
# cohort    → {"HS_1": ["HS_1_1", "HS_1_2", ...], "HS_2": [...], ...}
```

---

### `load_patient(base_path, patient_name)`
Carga los trials de un paciente. Infiere la cohorte desde el nombre.

```python
path, trials = load_patient(base_path, "HS_1")
# path   → ".../healthy/HS/HS_1"
# trials → ["HS_1_1", "HS_1_2", "HS_1_3", ...]
```

> El nombre de la cohorte se extrae del primer segmento del nombre del paciente: `"HS_1".split("_")[0]` → `"HS"`.

---

### `load_trial(base_path, trial_name)`
Carga todos los datos de un trial concreto.

```python
trial = load_trial(base_path, "HS_1_1")
# Retorna:
# {
#   "data_raw":       {"HE": DataFrame, "LB": DataFrame, "LF": DataFrame, "RF": DataFrame},
#   "data_processed": DataFrame,
#   "metadata":       dict
# }
```

> El nombre del paciente se infiere como los dos primeros segmentos: `"HS_1_1"` → `"HS_1"`.

---

### `load_data_raw(trial_path)` *(interna)*
Busca archivos que terminen en `_HE.txt`, `_LB.txt`, `_LF.txt`, `_RF.txt` y los carga como DataFrames. Lanza `ValueError` si falta algún sensor.

### `load_data_processed(trial_path)` *(interna)*
Busca el archivo con `"processed"` en el nombre y lo carga como DataFrame.

### `load_metadata(trial_path)` *(interna)*
Busca el archivo con `"meta"` en el nombre y lo deserializa como JSON.

---

## Uso típico

```python
from gait_project.io.load_data import load_bdd, load_trial

base_path = "data/raw/dataset/data"

# Ver toda la estructura
bdd = load_bdd(base_path)

# Cargar un trial
trial = load_trial(base_path, "HS_2_1")
df_raw_lb  = trial["data_raw"]["LB"]
df_proc    = trial["data_processed"]
meta       = trial["metadata"]

print(meta["age"], meta["pathology"])
```

---

## Metadata relevante (`*_meta.json`)

| Campo | Descripción |
|---|---|
| `subject`, `trial` | Identificadores |
| `age`, `gender`, `height`, `weight`, `BMI` | Datos demográficos |
| `group`, `pathology`, `pathologyKey` | Cohorte y diagnóstico |
| `freq` | Frecuencia de muestreo (Hz) |
| `uturnBoundaries` | Índices de inicio/fin del giro |
| `leftGaitEvents`, `rightGaitEvents` | Eventos de marcha `[toe-off, heel-strike]` por paso |
| `evaluationScoreName/Value` | Escala clínica (solo cohortes neuro/ortho) |
