#!/usr/bin/env python3
"""
Phase 1 Execution Script

This script runs the Phase 1 pipeline on a single trial to demonstrate
spectral analysis of gait signals.

Usage:
    python scripts/run_phase1.py

You can modify the parameters below to analyze different trials.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase1 import run_phase1_pipeline


def main():
    """Run Phase 1 pipeline on a sample trial."""

    # ===== CONFIGURATION =====
    # Modify these parameters as needed

    # Path to dataset (adjust to your local path)
    BASE_PATH = project_root / "data" / "raw" / "dataset" / "data"

    # Trial to analyze
    TRIAL_NAME = "HS_1_1"  # Example: first trial of first healthy subject

    # Signal to analyze
    SIGNAL_NAME = "LF_Gyr_Y"  # Left foot gyroscope Y-axis

    # Output directory
    OUTPUT_DIR = project_root / "outputs"

    # =========================

    # Verify dataset path exists
    if not BASE_PATH.exists():
        print(f"ERROR: Dataset path not found: {BASE_PATH}")
        print(
            "\nPlease update the BASE_PATH variable in this script to point to your dataset."
        )
        print("Expected structure: dataset/data/healthy/HS/HS_1/HS_1_1/...")
        sys.exit(1)

    print("Phase 1 Pipeline Execution")
    print("=" * 70)
    print(f"Dataset path: {BASE_PATH}")
    print(f"Trial: {TRIAL_NAME}")
    print(f"Signal: {SIGNAL_NAME}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)
    print()

    # Run pipeline
    try:
        metrics = run_phase1_pipeline(
            base_path=str(BASE_PATH),
            trial_name=TRIAL_NAME,
            signal_name=SIGNAL_NAME,
            output_dir=str(OUTPUT_DIR),
        )

        # Display results
        print("\nRESULTS SUMMARY:")
        print("-" * 40)
        print(f"Dominant frequency: {metrics['dominant_freq_hz']:.3f} Hz")
        print(f"Peak power: {metrics['peak_power']:.2e}")
        print(f"Peak width: {metrics['peak_width_hz']:.3f} Hz")
        print(f"Energy ratio: {metrics['energy_ratio']:.3f}")
        print("-" * 40)

    except FileNotFoundError as e:
        print(f"\nERROR: File not found - {e}")
        print("\nPossible causes:")
        print("1. Dataset path is incorrect")
        print("2. Trial name does not exist")
        print("3. Signal name is not in processed data")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: Pipeline failed - {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
