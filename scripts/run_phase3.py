#!/usr/bin/env python3
"""
Phase 3 Execution Script

This script runs the Phase 3 pipeline on a single trial to demonstrate
phase synchronization analysis between left and right feet.

Usage:
    python scripts/run_phase3.py

You can modify the parameters below to analyze different trials.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase3 import run_phase3_pipeline


def main():
    """Run Phase 3 pipeline on a sample trial."""

    # ===== CONFIGURATION =====
    # Modify these parameters as needed

    # Path to dataset (adjust to your local path)
    BASE_PATH = project_root / "data" / "raw" / "dataset" / "data"

    # Trial to analyze
    TRIAL_NAME = "HS_1_1"  # Example: first trial of first healthy subject

    # Signals to analyze
    SIGNAL_LEFT = "LF_Gyr_Y"  # Left foot gyroscope Y-axis
    SIGNAL_RIGHT = "RF_Gyr_Y"  # Right foot gyroscope Y-axis

    # Output directory
    OUTPUT_DIR = project_root / "outputs"

    # Narrowband filter bandwidth (Hz)
    BANDWIDTH = 0.3  # Default: ±0.3 Hz around f0

    # =========================

    # Verify dataset path exists
    if not BASE_PATH.exists():
        print(f"ERROR: Dataset path not found: {BASE_PATH}")
        print(
            "\nPlease update the BASE_PATH variable in this script to point to your dataset."
        )
        print("Expected structure: dataset/data/healthy/HS/HS_1/HS_1_1/...")
        sys.exit(1)

    print("Phase 3 Pipeline Execution")
    print("=" * 70)
    print(f"Dataset path: {BASE_PATH}")
    print(f"Trial: {TRIAL_NAME}")
    print(f"Left foot signal: {SIGNAL_LEFT}")
    print(f"Right foot signal: {SIGNAL_RIGHT}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Filter bandwidth: ±{BANDWIDTH} Hz")
    print("=" * 70)
    print()

    # Run pipeline
    try:
        metrics = run_phase3_pipeline(
            base_path=str(BASE_PATH),
            trial_name=TRIAL_NAME,
            signal_left=SIGNAL_LEFT,
            signal_right=SIGNAL_RIGHT,
            output_dir=str(OUTPUT_DIR),
            bandwidth=BANDWIDTH,
        )

        # Display results
        print("\nRESULTS SUMMARY:")
        print("-" * 50)
        print(f"Frequency left:       {metrics['freq_left']:.3f} Hz")
        print(f"Frequency right:      {metrics['freq_right']:.3f} Hz")
        print(f"Frequency difference: {metrics['freq_diff']:.4f} Hz")
        print(f"Frequency ratio:      {metrics['freq_ratio']*100:.2f}%")
        print(
            f"Frequency matched:    {'✓ YES' if metrics['frequency_match_flag'] else '✗ NO'}"
        )
        print()
        print(f"PLV:                  {metrics['plv']:.3f}")
        print(f"Mean phase diff:      {metrics['mean_phase_diff']:.3f} rad")
        print(f"Anti-phase error:     {metrics['anti_phase_error']:.3f} rad")
        print(f"Circular variance:    {metrics['circular_variance']:.3f}")
        print(f"Circular std:         {metrics['circular_std']:.3f} rad")
        print()
        print(f"Valid samples sync:   {metrics['valid_samples_sync']}")
        print(f"Valid fraction sync:  {metrics['valid_fraction_sync']*100:.1f}%")
        print("-" * 50)

        # Quality assessment
        print("\nQUALITY ASSESSMENT:")

        if not metrics["frequency_match_flag"]:
            print("⚠ Frequency mismatch - PLV may not be reliable")
        else:
            print("✓ Frequencies matched")

        if metrics["plv"] > 0.9:
            print("✓ Synchronization: EXCELLENT")
        elif metrics["plv"] > 0.7:
            print("✓ Synchronization: GOOD")
        else:
            print("⚠ Synchronization: MODERATE/LOW")

        if metrics["anti_phase_error"] < 0.2:
            print("✓ Anti-phase coordination: EXCELLENT")
        elif metrics["anti_phase_error"] < 0.5:
            print("✓ Anti-phase coordination: GOOD")
        else:
            print("⚠ Anti-phase coordination: POOR")

    except FileNotFoundError as e:
        print(f"\nERROR: File not found - {e}")
        print("\nPossible causes:")
        print("1. Dataset path is incorrect")
        print("2. Trial name does not exist")
        print("3. Signal names are not in processed data")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: Pipeline failed - {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
