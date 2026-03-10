#!/usr/bin/env python3
"""
Phase 4: Batch Processing Pipeline

Process all trials in the dataset and generate a master CSV with consolidated metrics.

This script is designed to be simple but extensible:
- Modular functions for easy enhancement
- Configurable parameters at the top
- Clear separation of concerns (scan, process, save, report)

Usage:
    # Process 8 trials per group (default)
    python scripts/run_batch_processing.py

    # Process all available trials
    python scripts/run_batch_processing.py --all

    # Process specific number per group
    python scripts/run_batch_processing.py --target 20

    # Process specific groups only
    python scripts/run_batch_processing.py --groups healthy neuro

Future extensions:
- Add multiprocessing: modify process_all_trials() to use Pool
- Add caching: modify process_single_trial() to check cache
- Add progress bar: wrap enumerate() with tqdm
- Add more metadata: modify extract_metadata()
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import json
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gait_project.pipeline_phase1 import run_phase1_pipeline
from gait_project.pipeline_phase2 import run_phase2_pipeline
from gait_project.pipeline_phase3 import run_phase3_pipeline


# ============================================================================
# CONFIGURATION - Modify these parameters as needed
# ============================================================================

BASE_PATH = project_root / "data" / "raw" / "dataset" / "data"
OUTPUT_DIR = project_root / "outputs"

# Incremental save: save every N trials
SAVE_EVERY_N_TRIALS = 20

# Signals to analyze
SIGNAL_LEFT = "LF_Gyr_Y"
SIGNAL_RIGHT = "RF_Gyr_Y"

# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class TrialInfo:
    """Information about a trial to process."""

    trial_name: str
    group: str  # "healthy", "neuro", "ortho"
    pathology: str  # "HS", "CIPN", "CVA", "PD", etc.
    subject_id: str
    trial_path: Path

    def to_dict(self) -> Dict:
        """Convert to dictionary for CSV export."""
        return {
            "trial": self.trial_name,
            "subject": self.subject_id,
            "group": self.group,
            "pathology": self.pathology,
        }


# ============================================================================
# STEP 1: DATASET SCANNING
# ============================================================================


def scan_dataset(base_path: Path) -> List[TrialInfo]:
    """
    Scan the dataset directory structure and collect all trials.

    Expected structure:
        data/
        ├── healthy/HS/HS_1/HS_1_1/
        ├── neuro/{CIPN,CVA,PD,RIL}/...
        └── ortho/{ACL,HOA,KOA}/...

    Args:
        base_path: Root path to dataset

    Returns:
        List of TrialInfo objects

    Future extension:
        - Add filtering by group/pathology
        - Add date range filtering
        - Add random sampling option
    """
    trials = []

    # Group directories
    group_dirs = {
        "healthy": base_path / "healthy",
        "neuro": base_path / "neuro",
        "ortho": base_path / "ortho",
    }

    for group_name, group_path in group_dirs.items():
        if not group_path.exists():
            print(f"Warning: {group_name} directory not found at {group_path}")
            continue

        # Pathology directories (e.g., HS, CIPN, CVA, etc.)
        for pathology_dir in sorted(group_path.iterdir()):
            if not pathology_dir.is_dir():
                continue

            pathology_name = pathology_dir.name

            # Subject directories (e.g., HS_1, CVA_2, etc.)
            for subject_dir in sorted(pathology_dir.iterdir()):
                if not subject_dir.is_dir():
                    continue

                subject_id = subject_dir.name

                # Trial directories (e.g., HS_1_1, HS_1_2, etc.)
                for trial_dir in sorted(subject_dir.iterdir()):
                    if not trial_dir.is_dir():
                        continue

                    trial_name = trial_dir.name

                    # Verify it has processed data
                    processed_file = trial_dir / f"{trial_name}_processed_data.txt"
                    if not processed_file.exists():
                        continue

                    trials.append(
                        TrialInfo(
                            trial_name=trial_name,
                            group=group_name,
                            pathology=pathology_name,
                            subject_id=subject_id,
                            trial_path=trial_dir,
                        )
                    )

    return trials


# ============================================================================
# STEP 2: METADATA EXTRACTION
# ============================================================================


def extract_metadata(trial_info: TrialInfo) -> Dict:
    """
    Extract relevant metadata from trial JSON.

    Args:
        trial_info: Trial information

    Returns:
        Dictionary with metadata fields

    Future extension:
        - Add more clinical fields
        - Add conditional fields based on pathology
        - Add derived features (e.g., age groups)
    """
    metadata_file = trial_info.trial_path / f"{trial_info.trial_name}_meta.json"

    # Default values
    metadata = {
        "age": None,
        "gender": None,
        "BMI": None,
        "evaluation_score_value": None,
        "session": None,
    }

    if not metadata_file.exists():
        return metadata

    try:
        with open(metadata_file, "r") as f:
            data = json.load(f)

        # Extract fields (handle missing gracefully)
        metadata["age"] = data.get("age")
        metadata["gender"] = data.get("gender")
        metadata["BMI"] = data.get("BMI")
        metadata["evaluation_score_value"] = data.get("evaluationScoreValue")
        metadata["session"] = data.get("session")

    except Exception as e:
        print(f"  Warning: Could not load metadata for {trial_info.trial_name}: {e}")

    return metadata


# ============================================================================
# STEP 3: PIPELINE EXECUTION
# ============================================================================


def process_single_trial(trial_info: TrialInfo, base_path: Path) -> Dict:
    """
    Run complete pipeline (Phase 1, 2, 3) on a single trial.

    Args:
        trial_info: Trial information
        base_path: Dataset base path

    Returns:
        Dictionary with all metrics

    Raises:
        Exception: If any phase fails

    Future extension:
        - Add phase-level error recovery
        - Add metric validation
        - Add caching of intermediate results
    """
    # Phase 1: Spectral analysis (left foot only - f0 is same for both)
    metrics_p1 = run_phase1_pipeline(
        base_path=str(base_path),
        trial_name=trial_info.trial_name,
        signal_name=SIGNAL_LEFT,
        output_dir=str(OUTPUT_DIR),
        generate_figures=False,  # Disable figures for batch processing
    )

    # Phase 2: Instantaneous phase (both feet)
    metrics_p2_left = run_phase2_pipeline(
        base_path=str(base_path),
        trial_name=trial_info.trial_name,
        signal_name=SIGNAL_LEFT,
        output_dir=str(OUTPUT_DIR),
        generate_figures=False,  # Disable figures for batch processing
    )

    metrics_p2_right = run_phase2_pipeline(
        base_path=str(base_path),
        trial_name=trial_info.trial_name,
        signal_name=SIGNAL_RIGHT,
        output_dir=str(OUTPUT_DIR),
        generate_figures=False,  # Disable figures for batch processing
    )

    # Phase 3: Synchronization
    metrics_p3 = run_phase3_pipeline(
        base_path=str(base_path),
        trial_name=trial_info.trial_name,
        signal_left=SIGNAL_LEFT,
        signal_right=SIGNAL_RIGHT,
        output_dir=str(OUTPUT_DIR),
        generate_figures=False,  # Disable figures for batch processing
    )

    # Extract metadata
    metadata = extract_metadata(trial_info)

    # Consolidate - ONLY ESSENTIAL METRICS (with scientific rounding)
    result = {
        # Identification
        **trial_info.to_dict(),
        # Metadata
        **metadata,
        # Phase 1: Spectral (3 decimals for frequencies, 2 for SNR)
        "f0_hz": round(metrics_p1["dominant_freq_hz"], 3),
        "spectral_snr": round(metrics_p1["spectral_snr"], 2),
        # Phase 2: Instantaneous phase (3 decimals for freq, 4 for CV as it's a ratio)
        "mean_inst_freq_left": round(metrics_p2_left["mean_inst_freq_hz"], 3),
        "mean_inst_freq_right": round(metrics_p2_right["mean_inst_freq_hz"], 3),
        "cv_inst_freq_left": round(metrics_p2_left["cv_inst_freq"], 4),
        "cv_inst_freq_right": round(metrics_p2_right["cv_inst_freq"], 4),
        "valid_fraction_left": round(metrics_p2_left["valid_fraction"], 3),
        "valid_fraction_right": round(metrics_p2_right["valid_fraction"], 3),
        # Phase 2: Clinical temporal metrics (1 decimal for cadence, 3 for stride time)
        "cadence_steps_per_min_left": round(
            metrics_p2_left["cadence_steps_per_min"], 1
        ),
        "cadence_steps_per_min_right": round(
            metrics_p2_right["cadence_steps_per_min"], 1
        ),
        "stride_time_left_s": round(metrics_p2_left["stride_time_s"], 3),
        "stride_time_right_s": round(metrics_p2_right["stride_time_s"], 3),
        # Phase 3: Synchronization (3 decimals for PLV, 1 for angles, 3 for circular_std)
        "plv": round(metrics_p3["plv"], 3),
        "circular_variance": round(metrics_p3["circular_variance"], 3),
        "circular_std": round(metrics_p3["circular_std"], 3),
        "mean_phase_diff_deg": round(metrics_p3["mean_phase_diff"] * 180 / 3.14159, 1),
        "anti_phase_error_deg": round(
            metrics_p3["anti_phase_error"] * 180 / 3.14159, 1
        ),
        # Phase 3: Frequency metrics (3 decimals for Hz, 4 for ratios)
        "freq_left": round(metrics_p3["freq_left"], 3),
        "freq_right": round(metrics_p3["freq_right"], 3),
        "freq_diff": round(metrics_p3["freq_diff"], 3),
        "freq_ratio": round(metrics_p3["freq_ratio"], 4),
        "frequency_match_flag": metrics_p3["frequency_match_flag"],
        # Phase 3: Temporal asymmetry metrics (3 decimals for seconds, 1 for percentage)
        "stride_time_asymmetry_s": round(metrics_p3["stride_time_asymmetry_s"], 3),
        "stride_time_asymmetry_pct": round(metrics_p3["stride_time_asymmetry_pct"], 1),
        # Phase 3: NEW Temporal synchronization metrics
        "phase_slip_rate": round(metrics_p3["phase_slip_rate"], 2),
        "plv_mean_windowed": round(metrics_p3["plv_mean_windowed"], 3),
        "plv_std_windowed": round(metrics_p3["plv_std_windowed"], 4),
        "plv_trend": round(metrics_p3["plv_trend"], 6),
        "n_windows": metrics_p3["n_windows"],
        # Phase 3: Validity metrics
        "valid_samples_sync": metrics_p3["valid_samples_sync"],
        "valid_fraction_sync": round(metrics_p3["valid_fraction_sync"], 3),
    }

    return result


# ============================================================================
# STEP 4: BATCH PROCESSING
# ============================================================================


def process_until_target(
    all_trials: List[TrialInfo],
    base_path: Path,
    target_per_group: int = 8,
    groups_to_process: Optional[List[str]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Process trials until we have target number of successful trials per group.

    Args:
        all_trials: All available trials
        base_path: Dataset base path
        target_per_group: Target number of successful trials per group (default: 8)
        groups_to_process: List of groups to process (default: all groups)
                          Options: ["healthy", "neuro", "ortho"]

    Returns:
        Tuple of (successful_results, errors)

    Future extension:
        - Add multiprocessing: use Pool.map()
        - Add progress estimation
        - Add resume from checkpoint
    """
    results = []
    errors = []

    # Default to all groups if not specified
    if groups_to_process is None:
        groups_to_process = ["healthy", "neuro", "ortho"]

    # Track successful count per group
    success_count = {group: 0 for group in groups_to_process}

    # Group trials by type
    trials_by_group = {
        "healthy": [t for t in all_trials if t.group == "healthy"],
        "neuro": [t for t in all_trials if t.group == "neuro"],
        "ortho": [t for t in all_trials if t.group == "ortho"],
    }

    master_csv = OUTPUT_DIR / "tables" / "master_metrics.csv"
    trial_counter = 0

    print(f"\nTarget: {target_per_group} successful trials per group")
    print(f"Groups to process: {', '.join(groups_to_process)}")
    print(
        f"Available: healthy={len(trials_by_group['healthy'])}, neuro={len(trials_by_group['neuro'])}, ortho={len(trials_by_group['ortho'])}"
    )
    print()

    # Process each group until target is reached
    for group_name in groups_to_process:
        print(f"\n{'='*70}")
        print(f"PROCESSING GROUP: {group_name.upper()}")
        print(f"{'='*70}")

        for trial_info in trials_by_group[group_name]:
            # Stop if we've reached the target for this group
            if success_count[group_name] >= target_per_group:
                break

            trial_counter += 1
            print(
                f"\n[Trial {trial_counter}] {trial_info.trial_name} ({trial_info.group}/{trial_info.pathology})"
            )
            print(
                f"  Group progress: {success_count[group_name]}/{target_per_group} successful"
            )

            try:
                # Process trial
                result = process_single_trial(trial_info, base_path)
                results.append(result)
                success_count[group_name] += 1
                print(f"  ✓ Success - PLV: {result['plv']:.3f}")

                # Incremental save
                if len(results) % SAVE_EVERY_N_TRIALS == 0:
                    save_results_incremental(results, master_csv)
                    print(f"  💾 Saved checkpoint ({len(results)} trials)")

            except Exception as e:
                error_info = {
                    "trial": trial_info.trial_name,
                    "group": trial_info.group,
                    "pathology": trial_info.pathology,
                    "error_message": str(e)[:200],  # Truncate long errors
                }
                errors.append(error_info)
                print(f"  ✗ Failed: {str(e)[:100]}")
                continue

        print(
            f"\n{group_name.capitalize()} group completed: {success_count[group_name]}/{target_per_group} successful"
        )

    return results, errors


# ============================================================================
# STEP 5: SAVING RESULTS
# ============================================================================


def save_results_incremental(results: List[Dict], csv_path: Path, append: bool = True):
    """
    Save results to CSV (incrementally or full).

    Args:
        results: List of result dictionaries
        csv_path: Path to CSV file
        append: If True, append to existing file

    Future extension:
        - Add compression for large datasets
        - Add versioning
        - Add backup before overwrite
    """
    df_new = pd.DataFrame(results)

    if append and csv_path.exists():
        # Append to existing
        df_existing = pd.read_csv(csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(csv_path, index=False)
    else:
        # Create new
        df_new.to_csv(csv_path, index=False)


def remove_duplicates_from_csv(csv_path: Path):
    """
    Remove duplicate entries from master CSV based on trial name.

    Args:
        csv_path: Path to CSV file

    Future extension:
        - Add smart duplicate resolution (keep newest)
        - Add duplicate reporting
    """
    if not csv_path.exists():
        return

    df = pd.read_csv(csv_path)
    original_count = len(df)

    # Remove duplicates, keeping last occurrence
    df_clean = df.drop_duplicates(subset=["trial"], keep="last")

    df_clean.to_csv(csv_path, index=False)

    removed = original_count - len(df_clean)
    if removed > 0:
        print(f"\n  Removed {removed} duplicate entries from master CSV")


# ============================================================================
# STEP 6: REPORTING
# ============================================================================


def save_error_log(errors: List[Dict], output_dir: Path):
    """Save error log as CSV."""
    if not errors:
        return

    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    df_errors = pd.DataFrame(errors)
    error_path = tables_dir / "processing_errors.csv"
    df_errors.to_csv(error_path, index=False)

    print(f"\n✓ Error log saved: {error_path}")


def save_summary_report(
    results: List[Dict], errors: List[Dict], total_attempted: int, output_dir: Path
):
    """
    Save minimal processing summary.

    Args:
        results: List of successful results
        errors: List of errors
        total_attempted: Total number of trials attempted
        output_dir: Output directory

    Future extension:
        - Add timing statistics
        - Add quality metrics distribution
        - Add group-specific summaries
    """
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    successful = len(results)
    failed = len(errors)

    # Count successful by group
    success_by_group = {}
    for result in results:
        group = result["group"]
        success_by_group[group] = success_by_group.get(group, 0) + 1

    # Generate report
    lines = []
    lines.append("=" * 80)
    lines.append("BATCH PROCESSING SUMMARY")
    lines.append("=" * 80)
    lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"Total trials attempted: {total_attempted}")
    lines.append(
        f"Successfully processed: {successful} ({successful/total_attempted*100:.1f}%)"
    )
    lines.append(f"Failed: {failed} ({failed/total_attempted*100:.1f}%)")
    lines.append("")
    lines.append("Successful by group:")
    for group in sorted(success_by_group.keys()):
        success_group = success_by_group[group]
        lines.append(f"  {group.capitalize():12s}: {success_group:3d} trials")
    lines.append("")
    lines.append("=" * 80)

    report_path = reports_dir / "batch_processing_summary.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    # Also print to console
    print("\n" + "\n".join(lines))
    print(f"\n✓ Summary report saved: {report_path}")


# ============================================================================
# STEP 4.5: TRIAL SELECTION (FOR LIMITED RUNS)
# ============================================================================


def select_limited_trials(
    all_trials: List[TrialInfo], limit_per_group: int = 8
) -> List[TrialInfo]:
    """
    Select limited number of trials per group for testing.

    Args:
        all_trials: All available trials
        limit_per_group: Number of trials per group (default: 8)

    Returns:
        List of selected TrialInfo objects

    Future extension:
        - Add random sampling option
        - Add stratified sampling by pathology
        - Add quality-based selection
    """
    # Group trials by medical condition
    healthy_trials = [t for t in all_trials if t.group == "healthy"]
    neuro_trials = [t for t in all_trials if t.group == "neuro"]
    ortho_trials = [t for t in all_trials if t.group == "ortho"]

    # Select first N from each group
    selected = (
        healthy_trials[:limit_per_group]
        + neuro_trials[:limit_per_group]
        + ortho_trials[:limit_per_group]
    )

    return selected


# ============================================================================
# ARGUMENT PARSING
# ============================================================================


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch process gait analysis trials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process 8 trials per group (default)
  python scripts/run_batch_processing.py

  # Process all available trials
  python scripts/run_batch_processing.py --all

  # Process 20 trials per group
  python scripts/run_batch_processing.py --target 20

  # Process only healthy and neuro groups
  python scripts/run_batch_processing.py --groups healthy neuro

  # Process all neuro trials
  python scripts/run_batch_processing.py --all --groups neuro
        """,
    )

    parser.add_argument(
        "--target",
        type=int,
        default=8,
        help="Target number of successful trials per group (default: 8)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available trials (overrides --target)",
    )

    parser.add_argument(
        "--groups",
        nargs="+",
        choices=["healthy", "neuro", "ortho"],
        default=None,
        help="Groups to process (default: all groups)",
    )

    return parser.parse_args()


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main batch processing workflow."""
    # Parse command-line arguments
    args = parse_args()

    # Determine target
    if args.all:
        target = 999999  # Process all available
        mode = "ALL AVAILABLE TRIALS"
    else:
        target = args.target
        mode = f"TARGET: {target} SUCCESSFUL PER GROUP"

    # Determine groups
    groups = args.groups if args.groups else ["healthy", "neuro", "ortho"]

    print("=" * 80)
    print(f"PHASE 4: BATCH PROCESSING ({mode})")
    print("=" * 80)
    print()

    # Step 1: Scan dataset
    print("[1/5] Scanning dataset...")
    all_trials = scan_dataset(BASE_PATH)
    print(f"  Found {len(all_trials)} total trials")

    if len(all_trials) == 0:
        print("\nERROR: No trials found in dataset!")
        print(f"Checked path: {BASE_PATH}")
        return

    # Step 2: Process trials until target is reached
    print("\n[2/5] Processing trials...")
    print(f"  (Saving checkpoint every {SAVE_EVERY_N_TRIALS} trials)")
    results, errors = process_until_target(
        all_trials, BASE_PATH, target_per_group=target, groups_to_process=groups
    )

    # Step 3: Final save and cleanup
    print("\n[3/5] Finalizing master CSV...")
    master_csv = OUTPUT_DIR / "tables" / "master_metrics.csv"

    # Save any remaining results
    if results:
        save_results_incremental(results, master_csv, append=True)

    # Remove duplicates
    remove_duplicates_from_csv(master_csv)
    print(f"  ✓ Master CSV saved: {master_csv}")

    # Step 4: Save error log
    print("\n[4/5] Saving error log...")
    save_error_log(errors, OUTPUT_DIR)

    # Step 5: Generate summary report
    print("\n[5/5] Generating summary report...")
    total_attempted = len(results) + len(errors)
    save_summary_report(results, errors, total_attempted, OUTPUT_DIR)

    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\nSuccessful: {len(results)} trials")
    print(f"Failed: {len(errors)} trials")
    print(f"Total attempted: {total_attempted} trials")
    print(f"Master CSV: {master_csv}")
    print()


if __name__ == "__main__":
    main()
