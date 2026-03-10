#!/usr/bin/env python3
"""
Simple script to run complete pipeline on a single trial.
Useful for exploration and validation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase3 import run_phase3_pipeline


def main():
    """Run pipeline on single trial."""
    # Default trial
    trial_name = "HS_1_1"

    # Check if user provided trial name
    if len(sys.argv) > 1:
        trial_name = sys.argv[1]

    # Dataset path
    base_path = "data/raw/dataset/data"

    print("=" * 80)
    print(f"RUNNING COMPLETE PIPELINE ON TRIAL: {trial_name}")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Run Phase 1 (spectral analysis)")
    print("  2. Run Phase 2 (instantaneous phase) for both feet")
    print("  3. Run Phase 3 (bilateral synchronization)")
    print("  4. Generate all figures")
    print("  5. Save metrics to CSV files")
    print()
    print("Output directory: outputs/")
    print()
    print("=" * 80)
    print()

    try:
        # Run complete pipeline
        metrics = run_phase3_pipeline(
            base_path=base_path,
            trial_name=trial_name,
            output_dir="outputs",
            generate_figures=True,  # Generate all figures
        )

        print()
        print("=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print()
        print("Results:")
        print("  Figures saved to:  outputs/figures/")
        print("  Metrics saved to:  outputs/tables/")
        print()
        print("Key metrics:")
        print(f"  PLV (synchronization):    {metrics['plv']:.3f}")
        print(
            f"  Anti-phase error:         {metrics['anti_phase_error']*180/3.14159:.1f}°"
        )
        print(f"  Gait frequency (left):    {metrics['freq_left']:.2f} Hz")
        print(f"  Gait frequency (right):   {metrics['freq_right']:.2f} Hz")
        print()
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print(f"Failed to process trial '{trial_name}'")
        print(f"Error: {e}")
        print()
        print("Possible causes:")
        print("  - Trial name incorrect (check dataset)")
        print("  - Data contains NaN/Inf values")
        print("  - Missing signals (LF_Gyr_Y or RF_Gyr_Y)")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
