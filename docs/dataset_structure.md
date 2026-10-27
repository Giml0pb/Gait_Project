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
