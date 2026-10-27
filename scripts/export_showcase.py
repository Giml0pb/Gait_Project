#!/usr/bin/env python3
"""Export reproducible synthetic examples and aggregate figures for the README."""

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-dir", type=Path, default=ROOT / "outputs/demo")
    parser.add_argument("--study-dir", type=Path)
    args = parser.parse_args()
    assets = ROOT / "docs/assets"
    example = ROOT / "examples/synthetic"
    assets.mkdir(parents=True, exist_ok=True)
    example.mkdir(parents=True, exist_ok=True)
    for name in ("summary.json", "metrics.csv", "manifest.json"):
        shutil.copyfile(args.demo_dir / name, example / name)
    shutil.copyfile(args.demo_dir / "sensor_dropout.png", assets / "ekf_demo.png")
    if args.study_dir:
        study = ROOT / "examples/phase_validation"
        study.mkdir(parents=True, exist_ok=True)
        summary = json.loads((args.study_dir / "summary.json").read_text())
        (study / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        for name in (
            "frequency_reference",
            "participant_phase_error",
            "simulation_phase_error",
            "morphology_counterexample",
        ):
            shutil.copyfile(
                args.study_dir / "figures" / f"{name}.png",
                assets / f"validation_{name}.png",
            )
    print(f"Exported synthetic examples to {example} and figures to {assets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
