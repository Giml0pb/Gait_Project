"""Seeded stress tests with known phase and explicit observation-model mismatch."""

import numpy as np
import pandas as pd

from gait_project.research.phase_estimators import estimate_fundamental, legacy_dominant
from gait_project.research.phase_reference import circular_mae_deg
from gait_project.research.phase_validation import METHODS, estimate_methods
from gait_project.state_space.harmonic_ekf import HarmonicTemplate


SCENARIOS = (
    "fixed_asymmetry",
    "morphology_drift",
    "timing_drift",
    "frequency_modulation",
    "sensor_dropout",
)


def simulate_case(scenario, harmonic_ratio, noise_std, seed, duration=24, fs=25):
    rng = np.random.default_rng(seed)
    time = np.arange(int(duration * fs)) / fs
    initial = rng.uniform(-np.pi, np.pi)
    base = 2 * np.pi * 0.9 * time + initial
    if scenario == "frequency_modulation":
        base += (
            2
            * np.pi
            * (0.1 / (2 * np.pi * 0.05))
            * (1 - np.cos(2 * np.pi * 0.05 * time))
        )
    delta = np.full(len(time), np.pi + 0.15)
    if scenario in ("morphology_drift", "sensor_dropout", "frequency_modulation"):
        delta[:] = np.pi
    if scenario == "timing_drift":
        delta = np.pi + 0.4 * np.sin(2 * np.pi * 0.06 * time)
    truth = {"left": base, "right": base - delta}
    coefficients = np.array(
        [0.0, 1.0, -0.2, harmonic_ratio, 0.3 * harmonic_ratio, 0.15, 0.0]
    )
    template = HarmonicTemplate(coefficients)
    signals = {}
    for side in ("left", "right"):
        phase = truth[side]
        values = template.evaluate(phase)
        if scenario == "morphology_drift" and side == "right":
            beta = 0.8 * np.sin(2 * np.pi * 0.06 * time)
            values += harmonic_ratio * (np.cos(2 * phase + beta) - np.cos(2 * phase))
            values += (
                0.3 * harmonic_ratio * (np.sin(2 * phase + beta) - np.sin(2 * phase))
            )
        values += rng.normal(0, noise_std, len(time))
        if scenario == "sensor_dropout" and side == "right":
            values[(time >= 10) & (time < 11.2)] = np.nan
        signals[side] = values
    return time, signals, truth, template


def run_simulations(repetitions=5, seed=20261026):
    if repetitions < 1:
        raise ValueError("At least one simulation repetition is required")
    rows, example = [], None
    for scenario_index, scenario in enumerate(SCENARIOS):
        for ratio_index, ratio in enumerate((0.5, 1.0, 3.0, 6.0)):
            for noise_index, noise in enumerate((0.05, 0.2)):
                for repetition in range(repetitions):
                    case_seed = (
                        seed
                        + 10000 * scenario_index
                        + 1000 * ratio_index
                        + 100 * noise_index
                        + repetition
                    )
                    time, signals, truth, template = simulate_case(
                        scenario, ratio, noise, case_seed
                    )
                    segments, fs = [slice(0, len(time))], 25
                    phases, masks, rates, diagnostics = {}, {}, {}, {}
                    for side in ("left", "right"):
                        dominant = legacy_dominant(signals[side], fs, segments)
                        fundamental = estimate_fundamental(signals[side], fs, segments)
                        p, f, m, _, diag = estimate_methods(
                            signals[side],
                            fs,
                            segments,
                            dominant,
                            fundamental.frequency_hz,
                            template,
                        )
                        phases[side], rates[side], masks[side], diagnostics[side] = (
                            p,
                            f,
                            m,
                            diag,
                        )
                    common = masks["left"] & masks["right"]
                    true_difference = truth["left"] - truth["right"]
                    for method in METHODS:
                        shift = np.pi if method == "dominant_hilbert" else 0
                        difference = (
                            phases["left"][method] - phases["right"][method] - shift
                        )
                        # Paired error uses equal observed support for every method.
                        relative_error = circular_mae_deg(
                            difference, true_difference, common
                        )
                        # Missing-interval prediction is separately evaluated, never
                        # silently compared with a Hilbert method that abstains.
                        gap = (
                            (~np.isfinite(signals["right"]))
                            & (time > 3)
                            & (time < time[-1] - 1)
                        )
                        gap_coverage = (
                            float(np.isfinite(phases["right"][method][gap]).mean())
                            if gap.any()
                            else np.nan
                        )
                        gap_error = (
                            circular_mae_deg(
                                phases["right"][method], truth["right"], gap
                            )
                            if gap.any()
                            else np.nan
                        )
                        rows.append(
                            {
                                "scenario": scenario,
                                "harmonic_ratio": ratio,
                                "noise_std": noise,
                                "repetition": repetition,
                                "seed": case_seed,
                                "method": method,
                                "relative_phase_mae_deg": relative_error,
                                "left_phase_mae_deg": circular_mae_deg(
                                    phases["left"][method], truth["left"], common
                                ),
                                "right_phase_mae_deg": circular_mae_deg(
                                    phases["right"][method], truth["right"], common
                                ),
                                "scored_samples": int(common.sum()),
                                "gap_prediction_coverage": gap_coverage,
                                "gap_phase_mae_deg": gap_error,
                                "initialization_ambiguous": diagnostics["right"][
                                    "initialization_ambiguous"
                                ]
                                if method == "harmonic_ekf"
                                else False,
                            }
                        )
                    if (
                        scenario == "morphology_drift"
                        and ratio == 3
                        and noise == 0.05
                        and repetition == 0
                    ):
                        example = (time, true_difference, phases)
    # Exact even-harmonic symmetry: no estimator can infer the branch from
    # this observation alone without additional information.
    phases = np.linspace(-np.pi, np.pi, 257)
    even_template = HarmonicTemplate(np.array([0, 0, 0, 1, 0.3, 0, 0]))
    ambiguity = {
        "max_observation_difference_under_pi_shift": float(
            np.max(
                np.abs(
                    even_template.evaluate(phases)
                    - even_template.evaluate(phases + np.pi)
                )
            )
        ),
        "odd_harmonic_power_fraction": even_template.odd_power_fraction,
    }
    return pd.DataFrame(rows), example, ambiguity
