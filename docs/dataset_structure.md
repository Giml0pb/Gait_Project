# Dataset guide

Optional clinical gait signals recorded with inertial measurement units (IMUs), covering healthy, neurological and orthopedic cohorts. The synthetic demo runs independently of these data.

## Directory layout

Place the dataset under `data/raw/dataset/`. The loader's `base_path` points to the nested `data/` directory:

```text
dataset/
├── data/
│   ├── healthy/
│   │   └── HS/
│   │       ├── HS_1/
│   │       │   ├── HS_1_1/       # Trial
│   │       │   └── HS_1_2/
│   │       └── HS_2/
│   ├── neuro/
│   │   ├── CIPN/
│   │   ├── CVA/
│   │   ├── PD/
│   │   └── RIL/
│   └── ortho/
│       ├── ACL/
│       ├── HOA/
│       └── KOA/
└── quick_start/                   # Original dataset utilities
```

## Trial files

| File | Contents |
| --- | --- |
| `HS_1_1_raw_data_HE.txt` | Head sensor; tab-delimited |
| `HS_1_1_raw_data_LB.txt` | Lower-back sensor |
| `HS_1_1_raw_data_LF.txt` | Left-foot sensor |
| `HS_1_1_raw_data_RF.txt` | Right-foot sensor |
| `HS_1_1_processed_data.txt` | Synchronized signals from four sensors; 37 columns |
| `HS_1_1_meta.json` | Participant and trial metadata |
| `HS_1_1_plot.png` | Dataset gait-event visualization |

Raw files contain `PacketCounter`, `Acc_X/Y/Z`, `Gyr_X/Y/Z` and `Mag_X/Y/Z`. Acceleration is expressed in m/s² and angular velocity in degrees/s. The processed table contains `PacketCounter` and nine columns per sensor: `Acc_X/Y/Z`, `FreeAcc_X/Y/Z` and `Gyr_X/Y/Z`, prefixed by `HE_`, `LB_`, `LF_` or `RF_`. `FreeAcc` denotes gravity-compensated acceleration.

## Metadata

| Fields | Meaning |
| --- | --- |
| `subject`, `trial`, `session`, `daysSinceFirstSession` | Participant, recording and session identifiers |
| `age`, `gender`, `height`, `weight`, `BMI`, `laterality` | Participant descriptors |
| `group`, `pathology`, `pathologyKey`, `clinicalDeficitSide` | Cohort and clinical descriptors |
| `evaluationScoreName`, `evaluationScoreValue` | Clinical scale and value, when available |
| `freq`, `sensor`, `protocol` | Sampling rate, sensor and acquisition protocol |
| `uturnBoundaries` | Start and end indices of the turn |
| `leftGaitEvents`, `rightGaitEvents` | Pairs of `[toe_off_idx, heel_strike_idx]` for each foot |

Use `metadata["freq"]` for the sampling rate and convert event indices with that value. The dataset's processed signals already include filtering and interpolation of some original gaps. Event annotations were generated algorithmically and are not independent biomechanical ground truth.[^dataset]

## Cohorts and sensors

| Group | Key | Cohort |
| --- | --- | --- |
| healthy | `HS` | Healthy participants |
| neuro | `CIPN` | Chemotherapy-induced peripheral neuropathy |
| neuro | `CVA` | Cerebrovascular accident |
| neuro | `PD` | Parkinson's disease |
| neuro | `RIL` | Radiation-induced leukoencephalopathy |
| ortho | `ACL` | Anterior cruciate ligament |
| ortho | `HOA` | Hip osteoarthritis |
| ortho | `KOA` | Knee osteoarthritis |

The dataset contains 260 participants: 73 healthy, 143 neurological and 44 orthopedic. Sensor identifiers are `HE` (head), `LB` (lower back), `LF` (left foot) and `RF` (right foot). Participants walk 6–10 m, turn and return; the sampling rate is 100 Hz. Dataset license: CC BY 4.0.[^dataset]

## Load a trial in Python

The functions in [load_data.py](../src/gait_project/io/load_data.py) expose the dataset hierarchy:

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

| Function | Result |
| --- | --- |
| `load_bdd(base_path)` | Available groups, cohorts and participants |
| `load_cohort(base_path, cohort_name)` | Group and participant-to-trial mapping |
| `load_patient(base_path, patient_name)` | Participant path and trial names |
| `load_trial(base_path, trial_name)` | Raw signals, processed signals and metadata |

`include_raw=False` skips the four original sensor files when only processed signals are needed. The [README](../README.md#optional-dataset-benchmark) provides single-trial, batch and EKF-study commands. Use a fresh output directory for each dataset run. Source data and participant-level outputs are excluded from Git.

## Baseline processing conventions

The spectral/Hilbert baseline follows these rules:

- Trim nonfinite edge padding to the common bilateral interval; reject internal gaps without interpolation
- Process pre-turn and post-turn segments independently, preserve original timestamps and exclude filter edges
- Compute windows and rates on observable time; count phase jumps only between adjacent valid samples
- Validate metrics before export, update rows by key and write each table atomically with a single writer
- Use circular means for phase directions and identify aggregation across participant sessions

Dominant frequency can represent a harmonic. Historical cadence, stride and antiphase metric names require that caveat. `phase_slip_rate` counts abrupt filtered-phase jumps and need not detect gradual drift by a full cycle.

These conventions establish processing behavior and numerical consistency. The [comparison protocol](phase_validation_protocol.md) and [results](phase_validation_results.md) explain fundamental selection, participant separation and limits on interpretation; they do not establish clinical accuracy.

[^dataset]: Voisard et al. (2025). A Dataset of Clinical Gait Signals with Wearable Sensors from Healthy, Neurological, and Orthopedic Cohorts. https://www.nature.com/articles/s41597-025-05959-w
