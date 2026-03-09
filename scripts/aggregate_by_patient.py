#!/usr/bin/env python3
"""
Aggregate trial-level metrics to patient-level metrics.

This script reads master_metrics.csv and aggregates multiple trials from the same
patient into a single row with averaged metrics and intra-subject variability.

Why aggregate by patient?
- Reduces intra-subject noise (fatigue, concentration, etc.)
- Provides statistically independent samples for group comparisons
- Better represents patient's "true" coordination characteristics
- Avoids pseudoreplication in statistical analyses

Output columns:
- Metadata: Preserved from first trial (age, gender, BMI, etc.)
- Metrics: Mean across all trials
- Key variability: Std for critical metrics (PLV, anti-phase error, phase slip rate, etc.)
- n_trials: Number of trials averaged

Usage:
    python scripts/aggregate_by_patient.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = project_root / "outputs" / "tables" / "master_metrics.csv"
OUTPUT_CSV = project_root / "outputs" / "tables" / "patient_aggregated_metrics.csv"

# Metadata columns to preserve (take from first trial)
METADATA_COLS = [
    "subject",
    "group",
    "pathology",
    "age",
    "gender",
    "BMI",
    "evaluation_score_value",
    "session",
]

# Metrics to average (all numeric columns except metadata)
# Will be auto-detected

# Key metrics for which we want to report std (intra-subject variability)
KEY_METRICS_FOR_STD = [
    "plv",
    "anti_phase_error_deg",
    "phase_slip_rate",
    "plv_mean_windowed",
    "plv_std_windowed",
    "mean_inst_freq_left",
    "mean_inst_freq_right",
    "cv_inst_freq_left",
    "cv_inst_freq_right",
]

# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================


def aggregate_by_patient(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate trial-level data to patient-level.

    Args:
        df: DataFrame with trial-level metrics

    Returns:
        DataFrame with patient-level aggregated metrics
    """
    # Identify numeric columns (to average)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Remove metadata from numeric columns
    metrics_to_avg = [c for c in numeric_cols if c not in METADATA_COLS]

    # Group by subject
    grouped = df.groupby("subject")

    aggregated_rows = []

    for subject_id, subject_df in grouped:
        n_trials = len(subject_df)

        # Start with metadata from first trial
        agg_row = {}
        for col in METADATA_COLS:
            if col in subject_df.columns:
                agg_row[col] = subject_df[col].iloc[0]

        # Add trial count
        agg_row["n_trials"] = n_trials

        # Average all numeric metrics
        for metric in metrics_to_avg:
            if metric in subject_df.columns:
                agg_row[metric] = subject_df[metric].mean()

        # Add std for key metrics
        for metric in KEY_METRICS_FOR_STD:
            if metric in subject_df.columns and n_trials > 1:
                agg_row[f"{metric}_std"] = subject_df[metric].std()
            elif metric in subject_df.columns:
                # Only 1 trial, std is 0
                agg_row[f"{metric}_std"] = 0.0

        # Handle boolean columns (frequency_match_flag) - use mode
        bool_cols = subject_df.select_dtypes(include=[bool]).columns
        for col in bool_cols:
            if col not in METADATA_COLS:
                agg_row[col] = (
                    subject_df[col].mode()[0]
                    if len(subject_df[col].mode()) > 0
                    else subject_df[col].iloc[0]
                )

        aggregated_rows.append(agg_row)

    # Create DataFrame
    df_agg = pd.DataFrame(aggregated_rows)

    return df_agg


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reorder columns for better readability:
    1. Metadata (subject, group, pathology, demographics)
    2. n_trials
    3. Phase 1 metrics
    4. Phase 2 metrics
    5. Phase 3 metrics
    6. Std columns for key metrics
    """
    # Define column order
    ordered_cols = []

    # 1. Metadata
    for col in METADATA_COLS:
        if col in df.columns:
            ordered_cols.append(col)

    # 2. n_trials
    if "n_trials" in df.columns:
        ordered_cols.append("n_trials")

    # 3. Remaining columns (metrics) in order
    metric_cols = [
        c for c in df.columns if c not in ordered_cols and not c.endswith("_std")
    ]
    ordered_cols.extend(sorted(metric_cols))

    # 4. Std columns at the end
    std_cols = [c for c in df.columns if c.endswith("_std")]
    ordered_cols.extend(sorted(std_cols))

    return df[ordered_cols]


def print_summary(df_trials: pd.DataFrame, df_patients: pd.DataFrame):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("AGGREGATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Input:  {len(df_trials)} trials")
    print(f"Output: {len(df_patients)} patients")
    print()

    # Trials per patient distribution
    trials_per_patient = df_patients["n_trials"]
    print("Trials per patient:")
    print(f"  Min:    {trials_per_patient.min()}")
    print(f"  Max:    {trials_per_patient.max()}")
    print(f"  Mean:   {trials_per_patient.mean():.1f}")
    print(f"  Median: {trials_per_patient.median():.0f}")
    print()

    # Patients per group
    print("Patients per group:")
    for group, count in df_patients["group"].value_counts().items():
        print(f"  {group.capitalize():12s}: {count:3d} patients")
    print()

    # Check for key metrics
    print("Key metrics with intra-subject variability (std):")
    for metric in KEY_METRICS_FOR_STD:
        std_col = f"{metric}_std"
        if std_col in df_patients.columns:
            mean_std = df_patients[std_col].mean()
            max_std = df_patients[std_col].max()
            print(f"  {metric:30s}: mean_std={mean_std:.4f}, max_std={max_std:.4f}")
    print()
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main aggregation workflow."""
    print("=" * 80)
    print("PATIENT-LEVEL AGGREGATION")
    print("=" * 80)
    print()

    # Check input file exists
    if not INPUT_CSV.exists():
        print(f"ERROR: Input file not found: {INPUT_CSV}")
        print("Run batch processing first to generate master_metrics.csv")
        return 1

    print("[1/4] Loading trial-level data...")
    print(f"      {INPUT_CSV}")
    df_trials = pd.read_csv(INPUT_CSV)
    print(f"      Loaded {len(df_trials)} trials")
    print()

    print("[2/4] Aggregating by patient...")
    df_patients = aggregate_by_patient(df_trials)
    print(f"      Aggregated to {len(df_patients)} patients")
    print()

    print("[3/4] Reordering columns...")
    df_patients = reorder_columns(df_patients)
    print(f"      Total columns: {len(df_patients.columns)}")
    print()

    print("[4/4] Saving to CSV...")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_patients.to_csv(OUTPUT_CSV, index=False)
    print(f"      ✓ Saved: {OUTPUT_CSV}")
    print()

    # Print summary
    print_summary(df_trials, df_patients)

    print("\n✓ Patient aggregation complete!")
    print(f"Output: {OUTPUT_CSV}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
