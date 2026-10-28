"""Self-contained benchmark with separate synthetic calibration and test records."""

from importlib.metadata import version
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from gait_project.io.results import write_csv_atomic
from gait_project.research.phase_estimators import estimate_fundamental, legacy_dominant
from gait_project.research.phase_reference import circular_mae_deg
from gait_project.research.phase_simulation import SCENARIOS, simulate_case
from gait_project.research.phase_validation import METHODS, estimate_methods
from gait_project.state_space.harmonic_ekf import fit_template, normalized_signal
from gait_project.demo.uncertainty import run_uncertainty_check


DESCRIPTIONS = {
    "fixed_asymmetry": (
        "Stable coordination",
        "Track a fixed bilateral timing offset in noisy, harmonic-rich observations.",
    ),
    "frequency_modulation": (
        "Changing walking rhythm",
        "Follow a smoothly varying cycle frequency using a recursive state estimate.",
    ),
    "sensor_dropout": (
        "Missing sensor observations",
        "Predict through a 1.2 s observation gap; Hilbert abstains inside the gap.",
    ),
    "timing_drift": (
        "Changing bilateral timing",
        "Track a genuine change in the relative phase of the two simulated feet.",
    ),
    "morphology_drift": (
        "Observation-model mismatch",
        "Change waveform shape while keeping true bilateral timing fixed. This exposes estimator bias.",
    ),
}


def compute_case(scenario, seed=42, noise=0.1, harmonic_ratio=3.0):
    """Identify a template on a separate record and evaluate known test phase."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    time, signals, truth, _ = simulate_case(scenario, harmonic_ratio, noise, seed)
    _, calibration, calibration_phase, _ = simulate_case(
        "fixed_asymmetry", harmonic_ratio, noise, seed + 1_000_003
    )
    segments, fs = [slice(0, len(time))], 25.0
    sides, rows = {}, []
    for side in ("left", "right"):
        template = fit_template(
            normalized_signal(calibration[side]), calibration_phase[side]
        )
        dominant = legacy_dominant(signals[side], fs, segments)
        fundamental = estimate_fundamental(signals[side], fs, segments)
        phases, frequencies, mask, variance, diagnostics = estimate_methods(
            signals[side], fs, segments, dominant, fundamental.frequency_hz, template
        )
        sides[side] = {
            "phases": phases,
            "frequencies": frequencies,
            "mask": mask,
            "variance": variance,
            "diagnostics": diagnostics,
            "dominant_hz": dominant,
            "fundamental_hz": fundamental.frequency_hz,
            "fundamental_power_fraction": fundamental.fundamental_power_fraction,
            "template_coefficients": template.coefficients.tolist(),
        }
    common = sides["left"]["mask"] & sides["right"]["mask"]
    delta = truth["left"] - truth["right"]
    metrics = {}
    gap = ~np.isfinite(signals["right"])
    for method in METHODS:
        shift = np.pi if method == "dominant_hilbert" else 0.0
        difference = (
            sides["left"]["phases"][method] - sides["right"]["phases"][method] - shift
        )
        estimate = sides["right"]["phases"][method]
        metrics[method] = {
            "relative_phase_mae_deg": circular_mae_deg(difference, delta, common),
            "right_phase_mae_deg": circular_mae_deg(estimate, truth["right"], common),
            "scored_samples": int(common.sum()),
            "gap_prediction_coverage": float(np.isfinite(estimate[gap]).mean())
            if gap.any()
            else None,
            "gap_phase_mae_deg": circular_mae_deg(estimate, truth["right"], gap)
            if gap.any() and np.isfinite(estimate[gap]).any()
            else None,
        }
        rows.append({"scenario": scenario, "method": method, **metrics[method]})
    frame = pd.DataFrame(
        {
            "time_s": time,
            "right_observation": signals["right"],
            "left_observation": signals["left"],
            "right_reference_phase_rad": truth["right"],
            "left_reference_phase_rad": truth["left"],
            "right_ekf_phase_variance_rad2": sides["right"]["variance"],
            "common_score_mask": common,
        }
    )
    for side in ("left", "right"):
        for method in METHODS:
            frame[f"{side}_{method}_phase_rad"] = sides[side]["phases"][method]
            frame[f"{side}_{method}_frequency_hz"] = sides[side]["frequencies"][method]
    summary = {
        "scenario": scenario,
        "title": DESCRIPTIONS[scenario][0],
        "description": DESCRIPTIONS[scenario][1],
        "metrics": metrics,
        "frequency_selection": {
            s: {
                key: sides[s][key]
                for key in (
                    "dominant_hz",
                    "fundamental_hz",
                    "fundamental_power_fraction",
                )
            }
            for s in sides
        },
        "calibration_coefficients": {
            s: sides[s]["template_coefficients"] for s in sides
        },
        "ekf_diagnostics": {s: sides[s]["diagnostics"] for s in sides},
    }
    return summary, frame, rows


def run_demo(
    output_dir,
    scenario="all",
    seed=42,
    noise=0.1,
    harmonic_ratio=3.0,
    figures=True,
    uncertainty_repetitions=20,
):
    output_dir = Path(output_dir)
    manifest_path = output_dir / "manifest.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if (
            not manifest_path.exists()
            or json.loads(manifest_path.read_text()).get("generator") != "gait-lab-demo"
        ):
            raise ValueError(
                "Choose an empty output directory or a previous gait-lab demo directory"
            )
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = SCENARIOS if scenario == "all" else (scenario,)
    summaries, metrics = [], []
    for name in selected:
        summary, frame, rows = compute_case(name, seed, noise, harmonic_ratio)
        write_csv_atomic(frame, output_dir / f"{name}_timeseries.csv")
        summaries.append(summary)
        metrics.extend(rows)
        if figures:
            from gait_project.demo.plots import plot_case

            plot_case(summary, frame, output_dir / f"{name}.png")
    write_csv_atomic(pd.DataFrame(metrics), output_dir / "metrics.csv")
    uncertainty, uncertainty_runs = run_uncertainty_check(
        seed, noise, harmonic_ratio, uncertainty_repetitions
    )
    write_csv_atomic(uncertainty_runs, output_dir / "uncertainty_runs.csv")
    if figures:
        from gait_project.demo.plots import plot_uncertainty_check

        plot_uncertainty_check(uncertainty_runs, output_dir / "uncertainty.png")
    result = {
        "generator": "gait-lab-demo",
        "demo_version": 2,
        "parameters": {
            "seed": seed,
            "calibration_seed": seed + 1_000_003,
            "noise_std": noise,
            "second_harmonic_ratio": harmonic_ratio,
            "sampling_rate_hz": 25,
            "duration_s": 24,
            "uncertainty_repetitions": uncertainty_repetitions,
        },
        "cases": summaries,
        "uncertainty_check": uncertainty,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    package_root = Path(__file__).resolve().parents[1]
    manifest = {
        "generator": "gait-lab-demo",
        "package_version": version("gait-project"),
        "python": platform.python_version(),
        "dependencies": {
            name: version(name) for name in ("numpy", "scipy", "pandas", "matplotlib")
        },
        "parameters": result["parameters"],
        "scenarios": list(selected),
        "calibration": "Independent synthetic record; known calibration phase, fixed template on test record",
        "source_sha256": {
            str(path.relative_to(package_root)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(package_root.rglob("*.py"))
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    if figures:
        from gait_project.demo.report import write_report

        write_report(result, output_dir)
    return result
