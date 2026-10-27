#!/usr/bin/env python3
"""Run spectral and bilateral phase analysis on one trial."""

import argparse
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase1 import run_phase1_pipeline
from gait_project.pipeline_phase3 import run_phase3_pipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial", nargs="?", default="HS_1_1")
    parser.add_argument(
        "--data-dir", type=Path, default=project_root / "data/raw/dataset/data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "outputs/baseline_v2/single_trial",
    )
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()
    try:
        run_phase1_pipeline(
            str(args.data_dir),
            args.trial,
            output_dir=str(args.output_dir),
            generate_figures=not args.no_figures,
        )
        metrics = run_phase3_pipeline(
            str(args.data_dir),
            args.trial,
            output_dir=str(args.output_dir),
            generate_figures=not args.no_figures,
        )
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"Completed {args.trial}: PLV={metrics['plv']:.3f}; results: {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
