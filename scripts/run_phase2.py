#!/usr/bin/env python3
"""
Phase 2 Execution Script

This script runs the Phase 2 pipeline on a single trial to demonstrate
instantaneous phase analysis of gait signals.

Usage:
    python scripts/run_phase2.py

You can modify the parameters below to analyze different trials.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase2 import run_phase2_pipeline


def main():
    """Run Phase 2 pipeline on a sample trial."""

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

    print("Phase 2 Pipeline Execution")
    print("=" * 70)
    print(f"Dataset path: {BASE_PATH}")
    print(f"Trial: {TRIAL_NAME}")
    print(f"Signal: {SIGNAL_NAME}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Filter bandwidth: ±{BANDWIDTH} Hz")
    print("=" * 70)
    print()

    # Run pipeline
    try:
        metrics = run_phase2_pipeline(
            base_path=str(BASE_PATH),
            trial_name=TRIAL_NAME,
            signal_name=SIGNAL_NAME,
            output_dir=str(OUTPUT_DIR),
            bandwidth=BANDWIDTH,
        )

        # Display results
        print("\nRESULTS SUMMARY:")
        print("-" * 50)
        print(f"Spectral f₀:              {metrics['f0_hz']:.3f} Hz")
        print(f"Mean inst. frequency:     {metrics['mean_inst_freq_hz']:.3f} Hz")
        print(f"Median inst. frequency:   {metrics['median_inst_freq_hz']:.3f} Hz")
        print(f"Std inst. frequency:      {metrics['std_inst_freq_hz']:.4f} Hz")
        print(f"CV inst. frequency:       {metrics['cv_inst_freq']:.4f}")
        print(f"Mean amplitude:           {metrics['amplitude_mean']:.2f}")
        print(f"Std amplitude:            {metrics['amplitude_std']:.2f}")
        print(f"Number of cycles:         {metrics['num_cycles']:.1f}")
        print(f"Freq coherence error:     {metrics['freq_coherence_error']*100:.1f}%")
        print("-" * 50)

        # Quality assessment
        print("\nQUALITY ASSESSMENT:")
        if metrics["freq_coherence_error"] < 0.05:
            print("✓ Frequency coherence: EXCELLENT")
        elif metrics["freq_coherence_error"] < 0.15:
            print("✓ Frequency coherence: GOOD")
        else:
            print("⚠ Frequency coherence: POOR - check signal quality")

        if metrics["cv_inst_freq"] < 0.1:
            print("✓ Rhythm stability: EXCELLENT")
        elif metrics["cv_inst_freq"] < 0.2:
            print("✓ Rhythm stability: GOOD")
        else:
            print("⚠ Rhythm stability: MODERATE - variable rhythm")

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
