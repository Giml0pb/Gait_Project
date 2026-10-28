"""Seeded checks of operational EKF uncertainty, without retuning its noise."""

import numpy as np
import pandas as pd

from gait_project.research.phase_estimators import estimate_fundamental
from gait_project.research.phase_simulation import simulate_case
from gait_project.state_space.harmonic_ekf import (
    estimate_phase_ekf,
    fit_template,
    normalized_signal,
)


CONDITIONS = {
    "fixed_asymmetry": "Fixed waveform",
    "morphology_drift": "Changing waveform",
}


def uncertainty_metrics(result, reference):
    """Score phase coverage and pre-correction innovations after initialization.

    The phase error is circular. NIS uses only observed updates; undefined
    innovations in bootstrap/missing intervals never count as zero residuals.
    """
    error = np.angle(np.exp(1j * (result.phase - reference)))
    scored = result.score_mask & np.isfinite(error) & np.isfinite(result.variance_phase)
    if not scored.any():
        raise ValueError("No scored samples for the uncertainty check")
    if (result.variance_phase[scored] < 0).any():
        raise ValueError("Negative phase variance")
    observed = (
        scored
        & np.isfinite(result.innovation)
        & np.isfinite(result.innovation_variance)
        & (result.innovation_variance > 0)
    )
    standardized = np.full(len(error), np.nan)
    standardized[observed] = result.innovation[observed] / np.sqrt(
        result.innovation_variance[observed]
    )
    adjacent = observed[:-1] & observed[1:]
    previous, following = standardized[:-1][adjacent], standardized[1:][adjacent]
    correlation = None
    if len(previous) > 2 and min(np.std(previous), np.std(following)) > 1e-12:
        correlation = float(np.corrcoef(previous, following)[0, 1])
    return {
        "phase_mae_deg": float(np.rad2deg(np.abs(error[scored])).mean()),
        "coverage_95": float(
            (
                np.abs(error[scored]) <= 1.96 * np.sqrt(result.variance_phase[scored])
            ).mean()
        ),
        "mean_nis": float(np.mean(standardized[observed] ** 2))
        if observed.any()
        else None,
        "innovation_lag1": correlation,
        "scored_samples": int(scored.sum()),
        "innovation_samples": int(observed.sum()),
    }


def run_uncertainty_check(seed=42, noise=0.1, harmonic_ratio=3.0, repetitions=20):
    """Compare two waveform conditions over independent, paired random seeds.

    Neither condition is an exact draw from the EKF's stochastic process model.
    Nominal coverage/NIS values are diagnostic references, not pass/fail tests.
    """
    if repetitions < 1:
        raise ValueError("At least one uncertainty repetition is required")
    rows = []
    for repetition in range(repetitions):
        run_seed = seed + 2_000_003 + repetition
        _, calibration, calibration_phase, _ = simulate_case(
            "fixed_asymmetry", harmonic_ratio, noise, run_seed + 1_000_003
        )
        template = fit_template(
            normalized_signal(calibration["right"]), calibration_phase["right"]
        )
        for scenario in CONDITIONS:
            _, signals, truth, _ = simulate_case(
                scenario, harmonic_ratio, noise, run_seed
            )
            values = signals["right"]
            initial = estimate_fundamental(values, 25, [slice(0, len(values))])
            result = estimate_phase_ekf(values, 25, initial.frequency_hz, template)
            rows.append(
                {
                    "scenario": scenario,
                    "seed": run_seed,
                    **uncertainty_metrics(result, truth["right"]),
                    "initialization_ambiguous": result.initialization_ambiguity,
                    "frequency_bound_hits": result.frequency_bound_hits,
                    "amplitude_bound_hits": result.amplitude_bound_hits,
                }
            )
    frame = pd.DataFrame(rows)
    conditions = []
    for scenario, label in CONDITIONS.items():
        selected = frame[frame.scenario == scenario]
        metrics = {}
        for name in ("phase_mae_deg", "coverage_95", "mean_nis", "innovation_lag1"):
            finite = selected[name].dropna().to_numpy()
            metrics[name] = {
                key: float(np.quantile(finite, quantile)) if len(finite) else None
                for key, quantile in (("median", 0.5), ("p10", 0.1), ("p90", 0.9))
            }
        conditions.append(
            {
                "scenario": scenario,
                "label": label,
                "metrics": metrics,
                "ambiguous_runs": int(selected.initialization_ambiguous.sum()),
                "runs_with_bound_hits": int(
                    (
                        (selected.frequency_bound_hits + selected.amplitude_bound_hits)
                        > 0
                    ).sum()
                ),
            }
        )
    return {
        "repetitions_per_condition": repetitions,
        "run_seed_start": seed + 2_000_003,
        "noise_parameters_retuned": False,
        "conditions": conditions,
    }, frame
