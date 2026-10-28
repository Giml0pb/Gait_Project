#!/usr/bin/env python3
"""Run the exploratory phase-validity study without modifying baseline outputs."""

import argparse
from datetime import datetime
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from gait_project.io.results import write_csv_atomic
from gait_project.preprocess.trial_signal import prepare_trial_signal
from gait_project.research.phase_simulation import run_simulations
from gait_project.research.phase_validation import (
    make_participant_folds,
    prepare_study_trial,
    score_trial,
    training_templates,
)
from run_batch_processing import scan_dataset


def participant_summary(pairs):
    scored = pairs.loc[pairs.evaluation_status == "scored"]
    metrics = [
        "relative_phase_mae_deg",
        "plv",
        "reference_plv",
        "anti_phase_error_deg",
        "score_duration_s",
    ]
    summary = scored.groupby(
        ["subject", "group", "pathology", "method"], as_index=False
    )[metrics].mean()
    counts = scored.groupby(["subject", "method"]).size().rename("n_scored_trials")
    return summary.merge(counts, on=["subject", "method"])


def participant_event_summary(feet):
    scored = feet.loc[feet.evaluation_status == "scored"].copy()
    scored["matched_absolute_error_sum_s"] = (
        scored.matched_event_mae_s.fillna(0) * scored.event_true_positives
    )
    columns = [
        "event_true_positives",
        "event_false_positives",
        "event_false_negatives",
        "matched_absolute_error_sum_s",
    ]
    result = scored.groupby(
        ["subject", "group", "pathology", "method"], as_index=False
    )[columns].sum()
    denominator = (
        2 * result.event_true_positives
        + result.event_false_positives
        + result.event_false_negatives
    )
    result["event_f1"] = (
        2 * result.event_true_positives / denominator.replace(0, np.nan)
    )
    result["matched_event_mae_s"] = (
        result.matched_absolute_error_sum_s
        / result.event_true_positives.replace(0, np.nan)
    )
    return result


def generate_figures(audit, participants, simulations, example, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination.mkdir(parents=True, exist_ok=True)
    colors = {"healthy": "#0072B2", "neuro": "#D55E00", "ortho": "#009E73"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for group, frame in audit.groupby("group"):
        for ax, col in zip(axes, ("dominant_hz", "fundamental_hz")):
            ax.scatter(
                frame.event_stride_hz,
                frame[col],
                s=8,
                alpha=0.25,
                color=colors[group],
                label=group,
            )
    for ax, title in zip(
        axes, ("Pipeline dominant peak", "Signal-selected fundamental")
    ):
        x = np.linspace(0, 2, 100)
        ax.plot(x, x, "k--", linewidth=1, label="1:1 ratio")
        ax.plot(x, 2 * x, color="0.5", linestyle=":", linewidth=1, label="2:1 ratio")
        ax.set(
            xlim=(0, 2),
            ylim=(0, 3.5),
            xlabel="Event-derived stride frequency (Hz)",
            ylabel="Selected frequency (Hz)",
            title=title,
        )
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].legend(fontsize=8)
    fig.savefig(destination / "frequency_reference.png", dpi=180)
    plt.close(fig)
    methods = ("dominant_hilbert", "fundamental_hilbert", "harmonic_ekf")
    labels = ("Dominant-band Hilbert", "Fundamental-band Hilbert", "Harmonic EKF")
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    values = [
        participants.loc[participants.method == m, "relative_phase_mae_deg"].dropna()
        for m in methods
    ]
    ax.boxplot(values, tick_labels=labels, showfliers=False)
    ax.set(
        ylabel="Absolute relative-phase error (degrees)",
        title="Event reference; trial means within participants",
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(destination / "participant_phase_error.png", dpi=180)
    plt.close(fig)
    if not simulations.empty:
        groups = list(simulations.scenario.unique())
        fig, ax = plt.subplots(figsize=(11, 4.5), layout="constrained")
        x = np.arange(len(groups))
        for index, (method, label) in enumerate(zip(methods, labels)):
            means = [
                simulations.loc[
                    (simulations.method == method) & (simulations.scenario == group),
                    "relative_phase_mae_deg",
                ].median()
                for group in groups
            ]
            ax.bar(x + (index - 1) * 0.25, means, width=0.25, label=label)
        ax.set_xticks(x, groups, rotation=15, ha="right")
        ax.set(
            ylabel="Median relative-phase error (degrees)",
            title="Known-phase simulation: varying harmonics and noise",
        )
        ax.legend(fontsize=8)
        fig.savefig(destination / "simulation_phase_error.png", dpi=180)
        plt.close(fig)
    if example is not None:
        time, reference, phases = example
        fig, ax = plt.subplots(figsize=(11, 4.5), layout="constrained")
        ax.plot(
            time,
            np.rad2deg(reference - np.pi),
            "k",
            linewidth=2,
            label="True deviation from antiphase",
        )
        for method, label in zip(methods, labels):
            shift = np.pi if method == "dominant_hilbert" else 0
            difference = phases["left"][method] - phases["right"][method] - shift
            error = np.rad2deg(np.angle(np.exp(1j * (difference - np.pi))))
            ax.plot(time, error, linewidth=1, alpha=0.8, label=label)
        ax.axvspan(
            0, 3, color="0.9", label="Initialization; excluded from interpretation"
        )
        ax.set(
            xlabel="Time (s)",
            ylabel="Deviation from antiphase (degrees)",
            title="Changing waveform with constant coordination",
        )
        ax.legend(fontsize=8)
        fig.savefig(destination / "morphology_counterexample.png", dpi=180)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", type=Path, default=project_root / "data/raw/dataset/data"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=project_root / "outputs/phase_validation"
    )
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--max-subjects-per-cohort", type=int)
    parser.add_argument("--simulation-repetitions", type=int, default=5)
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args()
    if (
        args.folds < 2
        or args.simulation_repetitions < 1
        or (
            args.max_subjects_per_cohort is not None
            and args.max_subjects_per_cohort < 1
        )
    ):
        parser.error(
            "Fold/repetition/participant settings must be positive (at least two folds)"
        )
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Select a fresh --output-dir; study runs cannot be mixed")
    output.mkdir(parents=True, exist_ok=True)
    sources = [
        *project_root.glob("src/**/*.py"),
        project_root / "scripts/validate_phase_model.py",
        project_root / "scripts/run_batch_processing.py",
        project_root / "uv.lock",
    ]
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True
    )
    manifest = {
        "study_version": "0.2.0",
        "package_version": version("gait-project"),
        "status": "running",
        "started_at": datetime.now().astimezone().isoformat(),
        "git_commit": git.stdout.strip(),
        "data_dir": str(args.data_dir.resolve()),
        "python": platform.python_version(),
        "dependencies": {
            name: version(name) for name in ("numpy", "scipy", "pandas", "matplotlib")
        },
        "parameters": {
            "folds": args.folds,
            "seed": args.seed,
            "analysis_fs_hz": 25,
            "harmonics": 3,
            "fundamental_range_hz": [0.25, 2.0],
            "fundamental_weak_power_fraction": 0.05,
            "first_harmonic_score_bonus": 0.001,
            "ekf_observation_std": 0.15,
            "ekf_frequency_diffusion_hz": 0.025,
            "warmup_cycles": 2,
            "bootstrap_samples_reused": False,
            "event_matching_tolerance_s": 0.15,
            "simulation_repetitions": args.simulation_repetitions,
            "max_subjects_per_cohort": args.max_subjects_per_cohort,
        },
        "source_sha256": {
            str(p.relative_to(project_root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(sources)
        },
    }
    path = output / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    try:
        infos = scan_dataset(args.data_dir)
        if args.max_subjects_per_cohort is not None:
            subjects = {}
            for info in infos:
                subjects.setdefault(info.pathology, set()).add(info.subject_id)
            selected = set(
                s
                for names in subjects.values()
                for s in sorted(names)[: args.max_subjects_per_cohort]
            )
            infos = [info for info in infos if info.subject_id in selected]
        trials, errors = [], []
        for index, info in enumerate(infos):
            try:
                processed = info.trial_path / f"{info.trial_name}_processed_data.txt"
                meta_path = info.trial_path / f"{info.trial_name}_meta.json"
                metadata = json.loads(meta_path.read_text())
                data = pd.read_csv(
                    processed, sep="\t", usecols=["LF_Gyr_Y", "RF_Gyr_Y"]
                )
                prepared = {
                    side: prepare_trial_signal(
                        data, signal_name, metadata["freq"], metadata["uturnBoundaries"]
                    )
                    for side, signal_name in (
                        ("left", "LF_Gyr_Y"),
                        ("right", "RF_Gyr_Y"),
                    )
                }
                fingerprint = hashlib.sha256(
                    processed.read_bytes() + meta_path.read_bytes()
                ).hexdigest()
                trials.append(
                    prepare_study_trial(info, metadata, prepared, fingerprint)
                )
            except (ValueError, OSError, KeyError) as error:
                errors.append(
                    {
                        "trial": info.trial_name,
                        "stage": "preparation",
                        "error": str(error),
                    }
                )
            if (index + 1) % 100 == 0:
                print(f"Prepared {index + 1}/{len(infos)} trials", flush=True)
        if not trials:
            raise ValueError("No trials with usable signal/reference data")
        folds = make_participant_folds(
            {trial.subject: trial.pathology for trial in trials}, args.folds, args.seed
        )
        template_folds = {
            fold: training_templates(trials, folds, fold) for fold in range(args.folds)
        }
        manifest["folds"] = {
            str(fold): {
                "training_subjects": sorted(s for s, f in folds.items() if f != fold),
                "validation_subjects": sorted(s for s, f in folds.items() if f == fold),
                "templates": {
                    side: template.coefficients.tolist()
                    for side, template in templates.items()
                },
            }
            for fold, templates in template_folds.items()
        }
        audit_rows, foot_rows, pair_rows = [], [], []
        for index, trial in enumerate(trials):
            try:
                audit, feet, pairs = score_trial(
                    trial, template_folds[folds[trial.subject]], folds[trial.subject]
                )
                audit_rows.extend(audit)
                foot_rows.extend(feet)
                pair_rows.extend(pairs)
            except (ValueError, np.linalg.LinAlgError) as error:
                errors.append(
                    {"trial": trial.trial, "stage": "estimation", "error": str(error)}
                )
            if (index + 1) % 50 == 0:
                print(f"Compared {index + 1}/{len(trials)} trials", flush=True)
        audit, feet, pairs = (
            pd.DataFrame(audit_rows),
            pd.DataFrame(foot_rows),
            pd.DataFrame(pair_rows),
        )
        if pairs.empty:
            raise ValueError("No estimator comparisons could be scored")
        participants = participant_summary(pairs)
        participant_events = participant_event_summary(feet)
        print("Running known-phase simulations", flush=True)
        simulations, example, symmetry = run_simulations(
            args.simulation_repetitions, args.seed
        )
        for name, table in (
            ("frequency_audit", audit),
            ("foot_phase_comparison", feet),
            ("bilateral_comparison", pairs),
            ("participant_comparison", participants),
            ("participant_event_comparison", participant_events),
            ("simulations", simulations),
            (
                "processing_errors",
                pd.DataFrame(errors, columns=["trial", "stage", "error"]),
            ),
        ):
            write_csv_atomic(table, output / "tables" / f"{name}.csv")
        if not args.skip_figures:
            generate_figures(
                audit, participants, simulations, example, output / "figures"
            )
        summary = {
            "study_version": manifest["study_version"],
            "package_version": manifest["package_version"],
            "trials_prepared": len(trials),
            "trials_compared": int(pairs.trial.nunique()),
            "participants": len(folds),
            "participants_with_bilateral_scores": int(participants.subject.nunique()),
            "errors": len(errors),
            "symmetry_check": symmetry,
            "median_dominant_to_event_ratio": float(
                audit.dominant_to_event_ratio.median()
            ),
            "median_fundamental_to_event_ratio": float(
                audit.fundamental_to_event_ratio.median()
            ),
            "weak_fundamental_feet": int(audit.weak_fundamental.sum()),
            "participant_median_relative_phase_error_deg": participants.groupby(
                "method"
            )
            .relative_phase_mae_deg.median()
            .to_dict(),
            "participant_median_event_f1": participant_events.groupby("method")
            .event_f1.median()
            .to_dict(),
            "participant_median_matched_event_mae_s": participant_events.groupby(
                "method"
            )
            .matched_event_mae_s.median()
            .to_dict(),
            "scored_trials_by_method": pairs.loc[pairs.evaluation_status == "scored"]
            .groupby("method")
            .size()
            .to_dict(),
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        manifest.update(
            status="completed",
            finished_at=datetime.now().astimezone().isoformat(),
            summary=summary,
        )
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        return 0
    except Exception:
        manifest.update(status="failed", error=traceback.format_exc())
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        raise


if __name__ == "__main__":
    sys.exit(main())
