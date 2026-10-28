# Technical walkthrough

_A short route through the signal-processing and state-estimation implementation._

## Start with a working system

```bash
uv sync --locked
uv run gait-lab demo --scenario sensor_dropout
```

Open `outputs/demo/report.html`. The plot, CSV and manifest come from the same run. To see a controlled failure, repeat with `--scenario morphology_drift`: waveform shape changes while the true bilateral timing stays fixed.

The checked-in [synthetic results](../examples/synthetic/summary.json) use seed 42, observation noise 0.1 and a second-harmonic amplitude ratio of 3. They can be regenerated with:

```bash
uv run gait-lab demo
uv run python scripts/export_showcase.py
```

![The local synthetic report](assets/report_preview.png)

## Follow the data

```mermaid
flowchart LR
    accTitle: Synthetic estimation data flow
    accDescr: A separate calibration record supplies the Fourier template, while test observations pass through spectral selection and independent Hilbert and EKF estimators before evaluation.
    calibration["Separate calibration record"] --> identification["Fit Fourier observation template"]
    observations["Noisy test observations"] --> spectrum["Estimate spectrum and fundamental"]
    spectrum --> hilbert["Filter and extract Hilbert phase"]
    spectrum --> ekf["Predict and correct EKF state"]
    identification --> ekf
    identification --> hilbert
    ekf --> comparison["Compare on shared support"]
    hilbert --> comparison
    reference["Known synthetic reference"] --> comparison
```

Read [demo/run.py](../src/gait_project/demo/run.py) for orchestration. It generates independent calibration and evaluation records, identifies the template, selects frequencies, invokes the estimators and exports their shared evaluation mask. Ground-truth evaluation phase is not passed to the test-record estimator.

For the optional dataset benchmark, training templates use different people from the evaluated participant. All sessions of one participant remain in the same fold. That benchmark uses detected gait events as a reference, rather than independent biomechanical ground truth.

## Signal processing

[phase_estimators.py](../src/gait_project/research/phase_estimators.py) contains the signal-only fundamental selector and Hilbert comparator. Important choices are explicit:

- A dominant peak can represent the second harmonic. A three-harmonic power sum provides an alternative fundamental estimate and exports its power-support diagnostic.
- Finite segments are processed independently. Neither spectral windows nor filters cross an observation gap or a turn.
- SOS Butterworth filtering precedes the Hilbert transform. The comparison excludes initialization and filter edges from all methods equally.
- Hilbert leaves missing observations undefined. An undefined estimate is reported as missing coverage, not zero error.

The dataset loader and [trial preparation](../src/gait_project/preprocess/trial_signal.py) additionally align the finite bilateral interval, preserve original sample times and reject internal missing data in the established dataset pipeline. Synthetic gaps are introduced separately for estimator stress tests.

## System identification

[fit_template](../src/gait_project/state_space/harmonic_ekf.py) fits sine and cosine Fourier coefficients by least squares against a calibration phase. The demo uses a separate synthetic calibration record with known phase. The real-data study learns templates from other participants.

The Fourier coefficients describe observation shape; they are not the EKF state. The EKF updates phase, frequency, positive amplitude and offset while keeping that learned shape fixed. The mismatch scenario tests exactly where that assumption fails.

## Extended Kalman Filter

The state is `[phase_rad, angular_frequency_rad_s, amplitude, bias]`. Frequency drives phase through the state transition; the observation is a nonlinear periodic function of phase. An EKF is needed because the observation model is nonlinear even though the transition matrix is linear.

The implementation in [harmonic_ekf.py](../src/gait_project/state_space/harmonic_ekf.py) uses NumPy directly:

1. Propagate state and covariance through the transition and process noise.
2. Evaluate the Fourier observation and its analytic derivative.
3. Compute innovation, innovation variance and Kalman gain.
4. Correct state and apply the Joseph covariance update.
5. For missing observations, retain the prediction and skip correction.

Each foot is estimated independently. Relative phase is calculated afterwards; expected synchronization is never imposed on the estimator. Frequency and amplitude bounds and ambiguous initializations are exposed as diagnostics.

The first two nominal cycles are reserved for a bootstrap fit. That fitted state is advanced to the last bootstrap timestamp, and recursive prediction/correction begins on the next sample. Outputs before `result.initialization_stop` are undefined. The covariance at this boundary is an operational assumption, not an inferred bootstrap posterior; these samples never enter a second round of measurement corrections.

```python
import numpy as np
from gait_project.state_space.harmonic_ekf import HarmonicTemplate, estimate_phase_ekf

fs = 25.0
phase = 2 * np.pi * 0.9 * np.arange(600) / fs
template = HarmonicTemplate([0, 1, -0.2, 3, 0.9, 0.15, 0])
observations = template.evaluate(phase)
observations[250:280] = np.nan

result = estimate_phase_ekf(observations, fs, 0.9, template)
# result.phase remains defined during the missing-observation interval.
# result.variance_phase grows while correction is unavailable.
```

The [mathematical note](phase_state_space.md) defines the transition, observation Jacobian, noise scaling and circular error. Its explanatory text is in Spanish. The EKF is an offline benchmark with recursive updates: full-record frequency initialization, normalization and filtering have not been converted into a streaming front end. Local covariance bands are approximate and have not been calibrated as confidence guarantees.

## Check the uncertainty

[demo/uncertainty.py](../src/gait_project/demo/uncertainty.py) compares fixed and changing waveforms over 20 seeded runs per condition. Each run uses a separate calibration record; both conditions share the run seed. The EKF settings are held fixed, and the generated [CSV](../examples/synthetic/uncertainty_runs.csv) retains every run, including ambiguous initializations and contacts with operational bounds.

For each run, the check measures circular phase MAE, coverage of the local ±1.96σ band, mean normalized innovation squared (NIS) and lag-1 correlation of standardized innovations. Innovations and their variances are recorded before correction. Bootstrap and missing observations have no innovations; correlation uses adjacent observed samples only.

![Per-run uncertainty diagnostics](assets/uncertainty_check.png)

The ideal-model references are 95% coverage, mean scalar NIS of 1 and uncorrelated innovations. These simulations are not exact draws from the EKF's stochastic process model. The report uses medians and 10th–90th percentiles across runs, without treating dependent timestamps as independent experiments or applying a chi-square pass/fail test.

With the default seed and parameters, the median fixed-waveform coverage is 100%, with NIS about 0.025: the bands are conservative. For changing waveforms, phase coverage falls to about 13% while mean NIS remains below 1 and residuals are correlated. The filter can absorb a shape error into its phase estimate. A low NIS alone therefore cannot establish calibrated state uncertainty; the known phase reference exposes the failure.

## Verification and evidence

[Tests](../tests/) cover finite-difference checks of the Fourier derivative, disjoint bootstrap/correction samples, covariance propagation through missing data, circular coverage and NIS arithmetic, reference recovery, harmonic ambiguity, event matching, output integrity and installed CLI execution from outside the repository directory.

The [research benchmark](phase_validation_results.md) also retains the negative result: this population-template EKF did not outperform Hilbert fundamental on median bilateral phase error. This helps distinguish an implementation that is numerically correct from an observation model that fits every recording.

## Extend one component at a time

A different observation model belongs in `state_space/`; a new comparator belongs in `research/`. Preserve the known-phase simulation and participant separation when changing either one. Recompute the reference metrics and report missing coverage and model-bound contacts alongside error. The synthetic demo is the fast entry point; the optional dataset study checks behavior beyond the synthetic generator.
