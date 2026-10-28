# Estructura del Dataset

Dataset de señales de marcha clínica con sensores inerciales (IMU) en tres cohortes: sanos, neurológicos y ortopédicos.

---

## Estructura de directorios

```
dataset/
├── data/                          ← base_path para load_data.py
│   ├── healthy/
│   │   └── HS/                    ← Healthy Subject
│   │       ├── HS_1/
│   │       │   ├── HS_1_1/       ← trial
│   │       │   ├── HS_1_2/
│   │       │   └── ...
│   │       └── HS_2/ ... HS_73/
│   ├── neuro/
│   │   ├── CIPN/
│   │   ├── CVA/
│   │   ├── PD/
│   │   └── RIL/
│   └── ortho/
│       ├── ACL/
│       ├── HOA/
│       └── KOA/
└── quick_start/                   ← scripts originales del dataset
    ├── load_data.py
    └── plot_data.py
```

---

## Contenido de cada trial (`HS_1_1/`)

| Archivo | Descripción |
|---|---|
| `HS_1_1_raw_data_HE.txt` | Sensor cabeza — tab-delimitado (~2000 filas) |
| `HS_1_1_raw_data_LB.txt` | Sensor lumbar |
| `HS_1_1_raw_data_LF.txt` | Sensor pie izquierdo |
| `HS_1_1_raw_data_RF.txt` | Sensor pie derecho |
| `HS_1_1_processed_data.txt` | Datos sincronizados de los 4 sensores (37 columnas) |
| `HS_1_1_meta.json` | Metadata del sujeto y del trial |
| `HS_1_1_plot.png` | Visualización de eventos de marcha |

---

## Archivos raw (`*_raw_data_XX.txt`)

Columnas (tab-delimitado):

| Columna | Descripción |
|---|---|
| `PacketCounter` | Número de paquete secuencial |
| `Acc_X/Y/Z` | Aceleración en 3 ejes (m/s²) |
| `Gyr_X/Y/Z` | Velocidad angular en 3 ejes (deg/s) |
| `Mag_X/Y/Z` | Magnetómetro en 3 ejes |

---

## Archivo procesado (`*_processed_data.txt`)

37 columnas: `PacketCounter` + 9 columnas por sensor × 4 sensores.

Prefijos: `HE_`, `LB_`, `LF_`, `RF_`

Tipos por sensor: `Acc_X/Y/Z`, `FreeAcc_X/Y/Z` (aceleración sin gravedad), `Gyr_X/Y/Z`

---

## Metadata (`*_meta.json`)

```json
{
  "subject": "HS_1",
  "age": 18,
  "gender": "M",
  "height": 1.79,
  "weight": 60.0,
  "BMI": 18.7,
  "laterality": "right",
  "group": "healthy",
  "pathology": "healthy subject",
  "pathologyKey": "HS",
  "clinicalDeficitSide": null,
  "evaluationScoreName": null,
  "evaluationScoreValue": null,
  "session": 1,
  "daysSinceFirstSession": 0,
  "trial": 1,
  "freq": 100.0,
  "sensor": "MTw Awinda XSens",
  "protocol": "10.0m - uturn - 10.0m",
  "TUG": "Not evaluated",
  "visualGaitAssessment": 0.0,
  "uturnBoundaries": [1060, 1222],
  "leftGaitEvents": [[500, 543], [604, 648], "..."],
  "rightGaitEvents": [[431, 482], [554, 594], "..."]
}
```

> Para cohortes neuro/ortho: `evaluationScoreName` y `evaluationScoreValue` contienen la escala clínica usada (ej. `"TNSc (/28)"`).

---

## Cohortes y patologías

| Grupo | Clave | Patología |
|---|---|---|
| healthy | `HS` | Sujeto sano |
| neuro | `CIPN` | Neuropatía periférica inducida por quimioterapia |
| neuro | `CVA` | Accidente cerebrovascular (ictus) |
| neuro | `PD` | Enfermedad de Parkinson |
| neuro | `RIL` | Leucoencefalopatía inducida por radiación |
| ortho | `ACL` | Ligamento cruzado anterior |
| ortho | `HOA` | Osteoartritis de cadera |
| ortho | `KOA` | Osteoartritis de rodilla |

**Totales:** 73 sanos · 143 neuro · 44 ortho = **260 pacientes**

---

## Abreviaturas de sensores

| Clave | Ubicación |
|---|---|
| `HE` | Cabeza (Head) |
| `LB` | Lumbar (Lower Back) |
| `LF` | Pie izquierdo (Left Foot) |
| `RF` | Pie derecho (Right Foot) |

---

## Protocolo

- **Recorrido:** entre 6 y 10 m hacia adelante → giro → regreso
- **Frecuencia:** 100 Hz (10 ms entre muestras)
- **Eventos de marcha:** `[toe_off_idx, heel_strike_idx]` por paso, para pie izquierdo y derecho
- **Licencia:** CC BY 4.0

Fuente del protocolo y de las cohortes: [Voisard et al., Scientific Data (2025)](https://www.nature.com/articles/s41597-025-05959-w).

## Carga desde Python

La ruta de entrada apunta a `data/` dentro del dataset. Las funciones de [load_data.py](../src/gait_project/io/load_data.py) permiten explorar sus niveles y cargar un ensayo:

```python
from pathlib import Path
from gait_project.io.load_data import load_bdd, load_trial

base_path = Path("data/raw/dataset/data")
cohorts = load_bdd(base_path)
trial = load_trial(base_path, "HS_1_1", include_raw=False)
signals = trial["data_processed"]
metadata = trial["metadata"]
fs = metadata["freq"]
```

| Función | Resultado |
| --- | --- |
| `load_bdd(base_path)` | Grupos, cohortes y participantes disponibles |
| `load_cohort(base_path, cohort_name)` | Grupo y diccionario de participantes con sus ensayos |
| `load_patient(base_path, patient_name)` | Ruta del participante y nombres de sus ensayos |
| `load_trial(base_path, trial_name)` | Señales originales, señales procesadas y metadatos |

`include_raw=False` evita cargar los cuatro archivos de sensores originales cuando sólo se necesitan las señales procesadas. Los comandos para un ensayo, el procesamiento completo y el estudio EKF se encuentran en el [README](../README.md#optional-dataset-benchmark). Cada ejecución del dataset debe usar una carpeta de salida nueva.

## Convenciones del baseline

El pipeline espectral y de Hilbert conserva estas reglas de procesamiento:

- Recorta el relleno no finito de los extremos al intervalo bilateral común; rechaza huecos internos sin interpolarlos
- Procesa por separado los tramos anterior y posterior al giro, conservando los tiempos del registro original y excluyendo bordes de filtrado
- Calcula ventanas y tasas sobre el tiempo observable; sólo cuenta saltos entre muestras válidas adyacentes
- Valida las métricas antes de exportarlas, actualiza filas por clave y escribe cada tabla de forma atómica con un único proceso escritor
- Agrega direcciones de fase mediante medias circulares e identifica la mezcla de sesiones de un participante

Las señales procesadas de entrada ya incluyen el tratamiento del dataset original. La frecuencia dominante puede corresponder a un armónico: los nombres históricos de cadencia, zancada y antifase requieren esa cautela al interpretarse. `phase_slip_rate` mide saltos abruptos de la fase filtrada y no detecta necesariamente una deriva gradual de un ciclo.

Estas convenciones verifican procesamiento y consistencia numérica. La referencia de eventos es algorítmica y los resultados no establecen exactitud clínica. El [protocolo de comparación](phase_validation_protocol.md) y sus [resultados](phase_validation_results.md) describen la selección de fundamental, la separación por participante y las limitaciones de la evaluación.
