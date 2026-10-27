# Gait Project - Scientific Architecture

> Documento histórico de la implementación anterior. Para el comportamiento y la validación actuales, consultar [baseline_validation.md](../baseline_validation.md) y el [README](../../README.md). Sus cifras y conclusiones deben recalcularse con la versión actual.

**Phase 0 Completed**: Complete scientific infrastructure ready for phased development.

---

## Overview

This document describes the scientific architecture of the gait analysis project, which studies human gait as a system of coupled oscillators using IMU sensor data.

## Core Scientific Question

**Can gait be described as two coordinated oscillators (the feet), and how is this coordination altered by pathology?**

Study dimensions:
1. Gait rhythm (dominant frequency)
2. Temporal stability of rhythm (frequency variability)
3. Inter-foot coordination (phase synchronization)

---

## Module Architecture

### 1. `io/` — Data Loading

**Purpose**: Load and structure clinical gait dataset

**Files**:
- `load_data.py` — Dataset navigation and loading functions
- `data_structures.py` — Dataclasses for structured data representation

**Key Data Structures**:
- `GaitMetadata` — Trial metadata (subject info, gait events, clinical scores)
- `RawSignalData` — Raw IMU signals from 4 sensors (HE, LB, LF, RF)
- `TrialData` — Complete trial data wrapper
- `PreprocessedSignal` — Cleaned signals ready for analysis
- `SpectralFeatures` — Spectral characterization results
- `PhaseAnalysis` — Instantaneous phase attributes
- `SynchronizationMetrics` — Inter-foot coordination metrics
- `SubjectMetrics` — Aggregated subject-level metrics
- `GroupStatistics` — Group comparison results
- `AnalysisPipeline` — End-to-end analysis container

**Usage**:
```python
from gait_project.io.load_data import load_trial
from gait_project.io.data_structures import TrialData

trial_dict = load_trial(base_path, "HS_1_1")
trial = TrialData.from_load_trial("HS_1_1", trial_dict)
```

---

### 2. `preprocess/` — Signal Preprocessing

**Purpose**: Clean and prepare signals for spectral analysis

**Files**:
- `signal_cleaning.py` — Detrending, mean removal, filtering
- `turn_removal.py` — U-turn segment exclusion

**Key Functions**:
- `detrend_signal()` — Remove linear/constant trend
- `remove_mean()` — Center signal at zero
- `bandpass_filter()` — Bandpass filtering
- `preprocess_signal()` — Complete preprocessing pipeline
- `exclude_uturn()` — Remove turning segment using metadata
- `extract_straight_walking()` — Separate before/after turn segments

**Typical Operations**:
1. Detrend signal
2. Remove mean
3. Optional bandpass filter (e.g., 0.5-5 Hz)
4. Exclude U-turn using `uturnBoundaries` from metadata

---

### 3. `spectral/` — Spectral Analysis

**Purpose**: Frequency-domain characterization of gait rhythm

**Files**:
- `psd_analysis.py` — Welch's PSD and spectrograms
- `dominant_frequency.py` — Dominant frequency detection and metrics

**Key Functions**:
- `compute_psd()` — Welch's method for PSD estimation
- `compute_spectrogram()` — Time-frequency representation
- `find_dominant_frequency()` — Detect peak in physiological range (0.5-3 Hz)
- `compute_spectral_peak_width()` — Measure spectral concentration
- `compute_energy_ratio()` — Energy in dominant band / total energy

**Outputs**:
- Dominant gait frequency f₀
- Spectral peak width (rhythm regularity)
- Energy concentration ratio

---

### 4. `phase/` — Phase Analysis

**Purpose**: Extract instantaneous phase via Hilbert transform

**Files**:
- `narrowband_filter.py` — Bandpass around f₀ for quasi-monocomponent signal
- `hilbert_transform.py` — Analytic signal and instantaneous attributes
- `phase_metrics.py` — Phase stability and variability metrics

**Key Functions**:
- `apply_narrowband_filter()` — Filter around f₀ ± 0.5 Hz
- `compute_analytic_signal()` — z(t) = x(t) + i·H[x(t)]
- `compute_instantaneous_phase()` — Extract φ(t)
- `compute_instantaneous_amplitude()` — Extract A(t)
- `compute_instantaneous_frequency()` — Extract f(t) = (1/2π)·dφ/dt
- `unwrap_phase()` — Remove 2π discontinuities
- `compute_frequency_variability()` — Measure rhythm stability

**Workflow**:
1. Narrowband filter signal around f₀
2. Compute analytic signal via Hilbert transform
3. Extract instantaneous phase φ(t)
4. Unwrap phase for continuous representation
5. Compute instantaneous frequency and stability metrics

---

### 5. `synchronization/` — Inter-Foot Coordination

**Purpose**: Quantify phase synchronization between left and right feet

**Files**:
- `phase_difference.py` — Relative phase computation
- `plv.py` — Phase Locking Value
- `circular_statistics.py` — Circular statistics for angular data

**Key Functions**:
- `compute_phase_difference()` — Δφ(t) = φ_LF(t) - φ_RF(t)
- `compute_relative_phase_metrics()` — Mean phase, circular variance
- `compute_plv()` — Global Phase Locking Value
- `compute_plv_windowed()` — Time-resolved PLV in sliding windows
- `circular_mean()` — Mean direction of angles
- `circular_variance()` — Dispersion measure (0 = perfect, 1 = uniform)
- `circular_std()` — Circular standard deviation

**Key Metrics**:
- **Phase difference Δφ(t)**: Instantaneous coordination
- **Mean relative phase**: Preferred phase relationship
- **Circular variance**: Consistency of coordination
- **PLV**: Global synchronization (0-1 scale)
- **Windowed PLV**: Temporal evolution of synchronization

---

### 6. `analysis/` — Group-Level Analysis

**Purpose**: Aggregate metrics and compare clinical groups

**Files**:
- `subject_analysis.py` — Subject-level metric aggregation
- `group_analysis.py` — Group comparison statistics

**Key Functions**:
- `aggregate_subject_metrics()` — Mean/std across subject's trials
- `export_metrics_to_csv()` — Export results to CSV
- `compute_group_statistics()` — Descriptive stats per group
- `compare_groups()` — Kruskal-Wallis / ANOVA tests
- `pairwise_group_comparison()` — Post-hoc pairwise tests
- `compute_effect_size()` — Cohen's d between groups

**Workflow**:
1. Aggregate metrics across trials for each subject
2. Compute group-level statistics (healthy, neuro, ortho)
3. Statistical comparison between groups
4. Export results to CSV for reporting

---

### 7. `viz/` — Visualization

**Purpose**: Scientific plotting for all analysis stages

**Files**:
- `signal_plots.py` — Time-domain signal visualizations
- `spectral_plots.py` — PSD and spectrograms
- `phase_plots.py` — Phase analysis visualizations
- `group_plots.py` — Group comparison plots

**Key Plot Types**:

**Signal Plots**:
- `plot_raw_signal()` — Single time series
- `plot_filtered_comparison()` — Raw vs filtered
- `plot_dual_signals()` — Left vs right foot comparison

**Spectral Plots**:
- `plot_psd()` — Power spectral density with f₀ marker
- `plot_dual_psd()` — Compare LF and RF spectra
- `plot_spectrogram()` — Time-frequency heatmap

**Phase Plots**:
- `plot_instantaneous_phase()` — φ_LF(t) and φ_RF(t)
- `plot_phase_difference()` — Δφ(t) over time
- `plot_plv_temporal()` — Windowed PLV evolution
- `plot_phase_portrait()` — Phase space plot (φ_LF vs φ_RF)

**Group Plots**:
- `plot_group_boxplot()` — Metric comparison across groups
- `plot_group_distributions()` — Overlapping histograms
- `plot_metric_comparison()` — Multi-panel comparison

---

## Data Flow Pipeline

```
RAW DATA (load_trial)
    ↓
TrialData (data_structures)
    ↓
PREPROCESS (signal_cleaning, turn_removal)
    ↓
PreprocessedSignal
    ↓
SPECTRAL ANALYSIS (psd_analysis, dominant_frequency)
    ↓
SpectralFeatures (f₀, peak width, energy ratio)
    ↓
NARROWBAND FILTER (phase/narrowband_filter)
    ↓
HILBERT TRANSFORM (phase/hilbert_transform)
    ↓
PhaseAnalysis (φ(t), A(t), f(t))
    ↓
SYNCHRONIZATION (phase_difference, plv, circular_statistics)
    ↓
SynchronizationMetrics (Δφ, PLV, circular variance)
    ↓
SUBJECT AGGREGATION (subject_analysis)
    ↓
SubjectMetrics
    ↓
GROUP ANALYSIS (group_analysis)
    ↓
GroupStatistics + Statistical Tests
```

---

## Development Phases

### ✅ PHASE 0: Infrastructure (COMPLETED)
- ✅ Complete module structure
- ✅ Data structures with typed dataclasses
- ✅ All function signatures and docstrings
- ✅ Visualization utilities

### 📋 PHASE 1: Minimal Functional Pipeline
**Goal**: Load → Preprocess → Spectral analysis → Dominant frequency

**Implementation**:
1. Load trial using `load_trial` + `TrialData`
2. Preprocess LF_Gyr_Y and RF_Gyr_Y signals
3. Compute PSD and find dominant frequency f₀
4. Visualize: raw signal, PSD, spectrogram

**Deliverable**: Notebook demonstrating pipeline on one trial

---

### 📋 PHASE 2: Instantaneous Phase Analysis
**Goal**: Extract phase from narrowband signals

**Implementation**:
1. Narrowband filter around f₀
2. Compute analytic signal via Hilbert transform
3. Extract φ(t), A(t), f(t)
4. Compute frequency variability metrics

**Deliverable**: Phase visualizations and stability metrics

---

### 📋 PHASE 3: Inter-Foot Synchronization
**Goal**: Quantify coordination between feet

**Implementation**:
1. Compute phase difference Δφ(t)
2. Calculate circular statistics (mean, variance)
3. Compute global PLV
4. Compute windowed PLV for temporal analysis

**Deliverable**: Synchronization metrics and temporal plots

---

### 📋 PHASE 4: Group-Level Analysis
**Goal**: Compare healthy vs pathological groups

**Implementation**:
1. Process all trials in dataset
2. Aggregate by subject
3. Compute group statistics
4. Statistical comparison (Kruskal-Wallis, pairwise tests)
5. Generate boxplots and distributions

**Deliverable**: Statistical analysis report + group comparison figures

---

### 📋 PHASE 5 (Optional): Advanced Methods
**Goal**: Handle complex signals

**Implementation**:
- Empirical Mode Decomposition (EMD) for multi-component signals
- Stride-based analysis using gait events
- Advanced synchronization measures

---

## Dataset Information

**Source**: Clinical gait database with IMU sensors

**Sensors**: 4 IMUs (Head, Lower Back, Left Foot, Right Foot)

**Signals**: Acc_X/Y/Z, Gyr_X/Y/Z, FreeAcc_X/Y/Z per sensor

**Primary Signals**: `LF_Gyr_Y` and `RF_Gyr_Y` (sagittal plane angular velocity)

**Sampling Frequency**: 100 Hz

**Groups**:
- Healthy: 73 subjects (HS)
- Neuro: 143 subjects (PD, CVA, CIPN, RIL)
- Ortho: 44 subjects (KOA, HOA, ACL)

**Total**: 260 patients

**Metadata**: Age, gender, clinical scores, gait events, U-turn boundaries

---

## Key Scientific Concepts

### Coupled Oscillators Framework
- Each foot = oscillator with phase φ(t) and frequency f(t)
- Coordination = phase relationship Δφ(t) = φ_LF - φ_RF
- Healthy gait: stable phase locking (high PLV, low circular variance)
- Pathological gait: desynchronization (low PLV, high variance)

### Hilbert Transform Approach
- Requires quasi-monocomponent signal → narrowband filtering
- Analytic signal: z(t) = x(t) + i·H[x(t)]
- Instantaneous phase: φ(t) = arg[z(t)]
- Instantaneous frequency: f(t) = (1/2π)·dφ/dt

### Phase Locking Value (PLV)
- PLV = |⟨e^(i·Δφ(t))⟩|
- Range: [0, 1]
- 0 = no locking (random phase)
- 1 = perfect locking (constant Δφ)

---

## Next Steps

1. **Implement PHASE 1**: Create minimal pipeline notebook
2. **Test on sample data**: Validate spectral analysis
3. **Iterate through PHASES 2-4**: Add phase and synchronization analysis
4. **Batch processing**: Apply to full dataset
5. **Statistical analysis**: Group comparisons and hypothesis testing

---

## Dependencies

All scientific dependencies already declared in `pyproject.toml`:
- `numpy` — Array operations
- `scipy` — Signal processing, statistics
- `pandas` — Data handling
- `matplotlib` — Visualization

Development tools:
- `pytest` — Testing
- `ruff` — Linting/formatting
- `pre-commit` — Git hooks

---

## Author Notes

This architecture follows the specifications in `Descripcion_Proyecto.md`:
- ✅ Respects existing infrastructure (uv, ruff, src-layout)
- ✅ Modular scientific design
- ✅ Phased development approach
- ✅ Type hints and docstrings throughout
- ✅ Complete data structures for pipeline
- ✅ Ready for PHASE 1 implementation

**Status**: Infrastructure complete, ready for scientific implementation.
