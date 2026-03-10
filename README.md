# Gait Analysis Pipeline

Bilateral gait coordination analysis pipeline using phase synchronization.

---

## Quick Start (3 steps)

### 1. Install Docker Desktop
Download and install from: https://www.docker.com/products/docker-desktop

### 2. Prepare data
Place your data following this structure:
```
Gait_Project/data/raw/dataset/data/
├── healthy/
├── neuro/
└── ortho/
```

### 3. Run
- **Windows**: Double-click `EJECUTAR.bat`
- **Linux/Mac**: `./ejecutar.sh` (coming soon)

The script offers 4 processing options:
- Option 1: 1 trial (10 seconds) - for testing
- Option 2: 8 trials/group (5 minutes)
- Option 3: 20 trials/group (15 minutes)
- Option 4: All trials (2 hours)

### Results
- **Figures**: `outputs/figures/`
- **Metrics**: `outputs/tables/`

---

## Key Metrics

- **PLV** (Phase Locking Value): 0-1, higher = better synchronization
- **Anti-phase error**: 0-180°, lower = better coordination
- **Phase slip rate**: slips/minute, lower = more stable
- **Cadence**: steps/minute per foot
- **Stride time**: stride duration in seconds

**Typical values** (987 trials):
- PLV: 0.96 ± 0.14
- Anti-phase error: 13° ± 25°
- Phase slip rate: 0.8 ± 3.1 slips/min

---

## Technical Documentation

### Scientific Pipeline (3 phases)

**Phase 1: Spectral Analysis**
- Identifies dominant frequency (f₀) via FFT
- Output: f₀ and spectral SNR

**Phase 2: Instantaneous Phase**
- Bandpass filtering around f₀
- Hilbert transform → analytic signal
- Output: φ_L(t), φ_R(t) with quality validation

**Phase 3: Bilateral Synchronization**
- Analyzes inter-foot coordination
- Static metrics: PLV, anti-phase error
- Temporal metrics: phase slips, windowed PLV
- Output: 19 synchronization metrics

### Advanced Usage (without Docker)

Requires Python 3.11+ and uv:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Process single trial
uv run python scripts/run_single_trial.py HS_1_1

# Batch processing
uv run python scripts/run_batch_processing.py --target 20

# Patient-level aggregation
uv run python scripts/aggregate_by_patient.py
```

### Output Files

```
outputs/tables/
├── master_metrics.csv              # 987 trials, 36 metrics
├── patient_aggregated_metrics.csv  # 232 patients (averaged)
├── frequency_summary.csv           # Phase 1 metrics
├── phase_summary.csv               # Phase 2 metrics
└── synchronization_summary.csv     # Phase 3 metrics
```

Use `patient_aggregated_metrics.csv` for statistical analysis (avoids pseudoreplication).

### Code Structure

```
src/gait_project/
├── io/                 # Data loading
├── spectral/           # Phase 1: spectral analysis
├── phase/              # Phase 2: instantaneous phase
├── synchronization/    # Phase 3: bilateral synchronization
├── validation/         # Pydantic schemas
├── viz/                # Visualizations
└── pipeline_*.py       # Complete pipelines
```

### Discriminative Metrics

Based on 232-patient analysis:
1. **anti_phase_error_deg** (p=0.008) - Best discriminator
2. **plv** (p=0.038) - Global synchronization
3. **plv_mean_windowed** (p=0.048) - Temporal stability

---

**Repository**: https://github.com/Giml0pb/Gait_Project
