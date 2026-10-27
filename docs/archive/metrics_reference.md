# Metrics Reference Guide

> Documento histórico de la implementación anterior. Para el comportamiento y la validación actuales, consultar [baseline_validation.md](../baseline_validation.md) y el [README](../../README.md). Sus cifras y conclusiones deben recalcularse con la versión actual.

Comprehensive reference of all metrics computed by the Gait Analysis Pipeline, organized by processing phase.

---

## 📊 METRICS BY PHASE

### **PHASE 1: Spectral Analysis**

**Input**: Gyroscope signal (LF_Gyr_Y or RF_Gyr_Y)

**Core Metrics** (2):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Dominant frequency | `f0_hz` | float | 0.5-3.0 Hz | Gait frequency detected by spectral peak |
| Spectral SNR | `spectral_snr` | float | >0 | Signal-to-noise ratio in gait band (0.5-3 Hz) |

**Auxiliary Metrics** (in frequency_summary.csv, NOT in master):
- `peak_power`: Power of dominant peak
- `peak_width_hz`: Spectral peak width
- `energy_ratio`: Energy ratio in gait band vs total
- `signal_duration`: Signal duration in seconds

---

### **PHASE 2: Instantaneous Phase** (computed for both feet)

**Input**: Gyroscope signal + f₀ from Phase 1

**Core Metrics per Foot** (5 × 2 feet = 10):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Mean instantaneous frequency | `mean_inst_freq_left`<br>`mean_inst_freq_right` | float | 0.5-3.0 Hz | Average instantaneous frequency |
| Frequency CV | `cv_inst_freq_left`<br>`cv_inst_freq_right` | float | 0-0.5 | Coefficient of variation of instantaneous frequency |
| Valid fraction | `valid_fraction_left`<br>`valid_fraction_right` | float | 0-1 | Proportion of samples with valid phase |
| Cadence | `cadence_steps_per_min_left`<br>`cadence_steps_per_min_right` | float | 60-180 steps/min | Cadence in steps per minute |
| Stride time | `stride_time_left_s`<br>`stride_time_right_s` | float | 0.5-2.0 s | Stride time in seconds |

**Auxiliary Metrics** (in phase_summary.csv, NOT in master):
- `n_cycles_estimated`: Estimated number of gait cycles

---

### **PHASE 3: Bilateral Synchronization**

**Input**: Instantaneous phases from both feet (φ_L, φ_R)

#### **3.1 Frequency Metrics** (5):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Left foot frequency | `freq_left` | float | 0.5-3.0 Hz | Dominant frequency of left foot |
| Right foot frequency | `freq_right` | float | 0.5-3.0 Hz | Dominant frequency of right foot |
| Frequency difference | `freq_diff` | float | 0-1.0 Hz | \|freq_left - freq_right\| |
| Frequency ratio | `freq_ratio` | float | 0-1.0 | Relative difference (%) |
| Frequency match flag | `frequency_match_flag` | bool | True/False | Do frequencies match? (<10% diff) |

#### **3.2 Static Synchronization Metrics** (5):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| PLV (global) | `plv` | float | 0-1 | Phase Locking Value - global synchronization |
| Mean phase difference | `mean_phase_diff_deg` | float | -180 to 180° | Average φ_L - φ_R (in degrees) |
| Anti-phase error | `anti_phase_error_deg` | float | 0-180° | \|mean_phase_diff - 180°\| |
| Circular variance | `circular_variance` | float | 0-1 | Variability of phase difference |
| Circular std | `circular_std` | float | ≥0 rad | Circular standard deviation of phase difference |

#### **3.3 Temporal Synchronization Metrics** (5 - NEW):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Phase slip rate | `phase_slip_rate` | float | ≥0 slips/min | Abrupt changes >90° per minute |
| PLV mean (windowed) | `plv_mean_windowed` | float | 0-1 | Average PLV in 2s windows |
| PLV std (windowed) | `plv_std_windowed` | float | 0-1 | Standard deviation of PLV in windows |
| PLV temporal trend | `plv_trend` | float | -∞ to +∞ | PLV slope over time |
| Number of windows | `n_windows` | int | >0 | Windows analyzed (2s, 50% overlap) |

#### **3.4 Temporal Asymmetry Metrics** (2):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Absolute asymmetry | `stride_time_asymmetry_s` | float | ≥0 s | \|stride_time_L - stride_time_R\| |
| Relative asymmetry | `stride_time_asymmetry_pct` | float | 0-100% | Asymmetry as % of average |

#### **3.5 Validity Metrics** (2):

| Metric | CSV Column | Type | Range | Description |
|--------|------------|------|-------|-------------|
| Valid samples | `valid_samples_sync` | int | >0 | Samples with valid phase in both feet |
| Valid fraction sync | `valid_fraction_sync` | float | 0-1 | Proportion of valid samples |

---

## 📋 SUMMARY BY PHASE

| Phase | Core Metrics | Total (with auxiliary) |
|-------|--------------|------------------------|
| **Phase 1** | 2 | 6 (4 auxiliary) |
| **Phase 2** | 10 (5 × 2 feet) | 12 (2 auxiliary) |
| **Phase 3** | 19 | 21 (2 auxiliary) |
| **TOTAL** | **31 metrics** | **39 metrics** |

---

## 🗂️ MASTER_METRICS.CSV STRUCTURE (40 columns)

### Metadata (9):
1. `trial` - Trial identifier
2. `subject` - Subject identifier
3. `group` - Group: healthy, neuro, ortho
4. `pathology` - Pathology: HS, CIPN, CVA, PD, RIL, ACL, HOA, KOA
5. `age` - Age in years
6. `gender` - Gender: M/F
7. `BMI` - Body Mass Index
8. `evaluation_score_value` - Clinical evaluation score
9. `session` - Session number

### Phase 1 (2):
10. `f0_hz` - Dominant frequency
11. `spectral_snr` - Spectral SNR

### Phase 2 (10):
12. `mean_inst_freq_left` - Mean instantaneous frequency (left)
13. `mean_inst_freq_right` - Mean instantaneous frequency (right)
14. `cv_inst_freq_left` - Frequency CV (left)
15. `cv_inst_freq_right` - Frequency CV (right)
16. `valid_fraction_left` - Valid fraction (left)
17. `valid_fraction_right` - Valid fraction (right)
18. `cadence_steps_per_min_left` - Cadence (left)
19. `cadence_steps_per_min_right` - Cadence (right)
20. `stride_time_left_s` - Stride time (left)
21. `stride_time_right_s` - Stride time (right)

### Phase 3 (19):
22. `plv` - Phase Locking Value
23. `circular_variance` - Circular variance
24. `circular_std` - Circular standard deviation
25. `mean_phase_diff_deg` - Mean phase difference
26. `anti_phase_error_deg` - Anti-phase error
27. `freq_left` - Frequency (left)
28. `freq_right` - Frequency (right)
29. `freq_diff` - Frequency difference (absolute)
30. `freq_ratio` - Frequency ratio
31. `frequency_match_flag` - Frequency match flag
32. `stride_time_asymmetry_s` - Stride time asymmetry (absolute)
33. `stride_time_asymmetry_pct` - Stride time asymmetry (relative)
34. `phase_slip_rate` - Phase slip rate ⭐ NEW
35. `plv_mean_windowed` - PLV windowed mean ⭐ NEW
36. `plv_std_windowed` - PLV windowed std ⭐ NEW
37. `plv_trend` - PLV temporal trend ⭐ NEW
38. `n_windows` - Number of windows ⭐ NEW
39. `valid_samples_sync` - Valid samples for synchronization
40. `valid_fraction_sync` - Valid fraction for synchronization

---

## 🎯 KEY METRICS FOR REPORTING (Top 5)

Based on discriminatory power (p-values from patient-level analysis, N=232):

| Rank | Metric | Phase | p-value | Effect | Description |
|------|--------|-------|---------|--------|-------------|
| 🥇 1 | `anti_phase_error_deg` | 3 | **0.008** | Patho > Healthy | **Best discriminator** |
| 🥈 2 | `plv` | 3 | **0.038** | Healthy > Patho | Global synchronization |
| 🥉 3 | `plv_mean_windowed` | 3 | **0.048** | Healthy > Patho | Temporal synchronization |
| 4 | `phase_slip_rate` | 3 | 0.172 | Patho > Healthy | Instability (trend) |
| 5 | `plv_std_windowed` | 3 | 0.241 | Patho > Healthy | Temporal variability |

**Interpretation**:
- **Anti-phase error**: Most sensitive to pathology (p<0.01)
- **PLV metrics**: Significant at patient level (p<0.05), not at trial level
- **Temporal metrics**: Complementary, useful for individual characterization

---

## 📊 PATIENT-LEVEL METRICS (patient_aggregated_metrics.csv)

In addition to the 36 metrics above (averaged across trials), patient-level CSV includes:

### Aggregation Info (1):
- `n_trials` - Number of trials averaged per patient

### Intra-Subject Variability (9 - std across trials):
- `plv_std` - Intra-subject variability of PLV
- `anti_phase_error_deg_std` - Intra-subject variability of anti-phase error
- `phase_slip_rate_std` - Intra-subject variability of phase slip rate
- `plv_mean_windowed_std` - Intra-subject variability of windowed PLV
- `plv_std_windowed_std` - Intra-subject variability of PLV std
- `mean_inst_freq_left_std` - Intra-subject variability of inst. freq (left)
- `mean_inst_freq_right_std` - Intra-subject variability of inst. freq (right)
- `cv_inst_freq_left_std` - Intra-subject variability of CV (left)
- `cv_inst_freq_right_std` - Intra-subject variability of CV (right)

**Total**: 45 columns (8 metadata + 1 n_trials + 27 averaged metrics + 9 std)

---

## 🔬 TYPICAL VALUES (from 987 trials)

### Phase 1:
- `f0_hz`: 1.71 ± 0.18 Hz (range: 0.98-2.34)
- `spectral_snr`: 3.2 ± 1.8 (range: 1.5-12.5)

### Phase 2:
- `mean_inst_freq`: 1.75 ± 0.20 Hz
- `cv_inst_freq`: 0.045 ± 0.025
- `cadence`: 105 ± 12 steps/min
- `stride_time`: 1.15 ± 0.15 s

### Phase 3:
- `plv`: 0.964 ± 0.144 (range: 0.072-1.0)
- `anti_phase_error_deg`: 13.0° ± 25.4° (range: 0.5°-175.6°)
- `phase_slip_rate`: 0.84 ± 3.11 /min (range: 0-34.7)
- `plv_mean_windowed`: 0.964 ± 0.145
- `plv_std_windowed`: 0.023 ± 0.041

**Healthy vs Pathological** (patient-level, N=232):

| Metric | Healthy (n=57) | Pathological (n=175) | p-value |
|--------|----------------|---------------------|---------|
| `plv` | 0.973 ± 0.071 | 0.903 ± 0.247 | **0.038** * |
| `anti_phase_error_deg` | 5.3° ± 7.6° | 15.5° ± 28.5° | **0.008** ** |
| `phase_slip_rate` | 0.59 ± 1.28 | 1.26 ± 3.65 | 0.172 |

---

## 📖 REFERENCES

### Key Metrics:

**PLV (Phase Locking Value)**:
- Lachaux, J. P., et al. (1999). "Measuring phase synchrony in brain signals." *Human Brain Mapping*, 8(4), 194-208.
- Range: [0, 1] where 0 = no synchronization, 1 = perfect synchronization

**Anti-phase error**:
- Plotnik, M., et al. (2007). "A new measure for quantifying the bilateral coordination of human gait." *Experimental Brain Research*, 181(4), 561-570.
- Range: [0°, 180°] where 0° = perfect anti-phase coordination

**Phase slip rate**:
- Novel metric developed in this pipeline
- Detects abrupt phase changes >90° (loss of synchronization)
- Unit: slips per minute

**Windowed PLV**:
- Extension of global PLV to capture temporal dynamics
- Window size: 2 seconds, 50% overlap
- Provides: mean, std, temporal trend

---

## 🎓 USAGE NOTES

### For Statistical Analysis:
- Use **patient_aggregated_metrics.csv** (N=232 independent samples)
- Avoids pseudoreplication from multiple trials per patient
- Primary metrics: `anti_phase_error_deg`, `plv`, `plv_mean_windowed`

### For Individual Case Analysis:
- Use **master_metrics.csv** (N=987 trials)
- Provides trial-by-trial detail
- Temporal metrics useful for identifying abnormal patterns

### For Exploratory Analysis:
- Check **frequency_summary.csv**, **phase_summary.csv**, **synchronization_summary.csv**
- Contain auxiliary metrics not in master CSV
- Useful for debugging and quality checks

---

## 📝 NOTES

1. **Valid fraction**: Metrics are computed only on samples passing quality checks (amplitude, frequency, continuity tests). Typical valid fraction: 70% ± 10%.

2. **Temporal metrics**: New metrics (phase_slip_rate, plv_mean_windowed, plv_std_windowed, plv_trend, n_windows) added 2026-03-09 after critical analysis.

3. **Frequency matching**: Two feet are considered "matched" if `freq_diff < 10%` of average frequency.

4. **Anti-phase**: Normal gait is anti-phase (φ_L - φ_R ≈ 180°). Values close to 0° or 360° indicate in-phase (abnormal).

5. **Clinical interpretation**: Lower PLV, higher anti-phase error, and higher phase slip rate generally indicate impaired coordination.

---

**Last Updated**: 2026-03-09
**Version**: 1.0
