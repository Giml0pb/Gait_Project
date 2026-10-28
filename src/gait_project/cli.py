"""Installed command-line interface for the reproducible technical demonstration."""

import argparse
from importlib.metadata import version
from pathlib import Path


def main(argv=None):
    from gait_project.research.phase_simulation import SCENARIOS

    parser = argparse.ArgumentParser(
        prog="gait-lab",
        description="Signal processing and harmonic EKF estimation lab.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('gait-project')}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser(
        "demo", help="Generate a synthetic benchmark and local HTML report"
    )
    demo.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    demo.add_argument("--seed", type=int, default=42)
    demo.add_argument(
        "--noise",
        type=float,
        default=0.1,
        help="Synthetic observation-noise standard deviation",
    )
    demo.add_argument(
        "--harmonic-ratio",
        type=float,
        default=3.0,
        help="Second/first harmonic amplitude ratio",
    )
    demo.add_argument("--output-dir", type=Path, default=Path("outputs/demo"))
    demo.add_argument(
        "--no-figures",
        action="store_true",
        help="Export numerical results without plots/report",
    )
    arguments = parser.parse_args(argv)
    import numpy as np

    if arguments.seed < 0:
        parser.error("--seed must be nonnegative")
    if not np.isfinite(arguments.noise) or arguments.noise < 0:
        parser.error("--noise must be finite and nonnegative")
    if (
        not np.isfinite(arguments.harmonic_ratio)
        or not 0 < arguments.harmonic_ratio <= 20
    ):
        parser.error("--harmonic-ratio must be in (0, 20]")
    from gait_project.demo.run import run_demo

    try:
        result = run_demo(
            arguments.output_dir,
            scenario=arguments.scenario,
            seed=arguments.seed,
            noise=arguments.noise,
            harmonic_ratio=arguments.harmonic_ratio,
            figures=not arguments.no_figures,
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    for case in result["cases"]:
        metrics = case["metrics"]["harmonic_ekf"]
        print(
            f"{case['scenario']}: EKF relative phase MAE={metrics['relative_phase_mae_deg']:.2f} deg"
        )
    print(
        "Uncertainty check: "
        f"{result['uncertainty_check']['repetitions_per_condition']} runs per waveform condition"
    )
    print(f"Results: {arguments.output_dir.resolve()}")
    if not arguments.no_figures:
        print(f"Open {arguments.output_dir.resolve() / 'report.html'} in your browser")
    return 0
