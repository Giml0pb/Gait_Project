#!/usr/bin/env python3
"""Descriptive participant-level summaries for a selected baseline run."""

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from gait_project.analysis.aggregation import mean_metric
from gait_project.analysis.circular_statistics import circular_std


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root
        / "outputs/baseline_v2/tables/patient_aggregated_metrics.csv",
    )
    args = parser.parse_args()
    try:
        frame = pd.read_csv(args.input)
    except OSError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Descriptive summaries: {args.input} ({len(frame)} rows)")
    for group, values in frame.groupby("group"):
        print(f"\n{group}: n={len(values)}")
        for metric in (
            "plv",
            "anti_phase_error_deg",
            "mean_phase_diff_deg",
            "f0_hz",
            "cv_inst_freq_left",
            "cv_inst_freq_right",
        ):
            finite = values[metric].dropna().to_numpy()
            mean = mean_metric(metric, finite)
            std = (
                np.rad2deg(circular_std(np.deg2rad(finite)))
                if metric == "mean_phase_diff_deg" and len(finite)
                else np.std(finite, ddof=1)
                if len(finite) > 1
                else np.nan
            )
            print(f"  {metric}: mean={mean:.4f}, std={std:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
