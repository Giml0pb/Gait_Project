"""
Subject-level metric aggregation.

This module aggregates metrics across multiple trials for individual subjects.
"""

import numpy as np
import pandas as pd
from typing import List, Dict
from pathlib import Path

from gait_project.analysis.aggregation import ANGLE_PERIODS, mean_metric


def aggregate_trial_metrics(trial_metrics: List[Dict]) -> Dict:
    """
    Aggregate metrics from multiple trials of the same subject.

    Args:
        trial_metrics: List of metric dictionaries, one per trial

    Returns:
        aggregated_metrics: Dictionary with mean and std for each metric
    """
    if not trial_metrics:
        raise ValueError("Empty trial metrics list")

    # Extract metric names (excluding 'trial_name')
    metric_names = [
        key for key in trial_metrics[0].keys() if key not in ["trial_name", "subject"]
    ]

    aggregated = {}

    # Compute mean and std for each metric
    for metric in metric_names:
        values = [trial[metric] for trial in trial_metrics if metric in trial]

        if values and all(isinstance(v, (int, float, np.number)) for v in values):
            aggregated[f"{metric}_mean"] = mean_metric(metric, values)
            if metric in ANGLE_PERIODS:
                # Linear median, min, max and std are not angular summaries.
                continue
            aggregated[f"{metric}_std"] = np.std(values)
            aggregated[f"{metric}_median"] = np.median(values)
            aggregated[f"{metric}_min"] = np.min(values)
            aggregated[f"{metric}_max"] = np.max(values)

    # Add metadata
    aggregated["n_trials"] = len(trial_metrics)
    if "subject" in trial_metrics[0]:
        aggregated["subject"] = trial_metrics[0]["subject"]

    return aggregated


def aggregate_subject_metrics(
    all_trial_metrics: List[Dict], group_by: str = "subject"
) -> pd.DataFrame:
    """
    Aggregate metrics by subject across all trials.

    Args:
        all_trial_metrics: List of metric dictionaries from all trials
        group_by: Column to group by (default: "subject")

    Returns:
        subject_df: DataFrame with one row per subject
    """
    # Convert to DataFrame
    df = pd.DataFrame(all_trial_metrics)

    # Group by subject
    if group_by not in df.columns:
        raise ValueError(f"Column '{group_by}' not found in metrics")

    subjects = df[group_by].unique()
    aggregated_data = []

    for subject in subjects:
        subject_trials = df[df[group_by] == subject].to_dict("records")
        aggregated = aggregate_trial_metrics(subject_trials)
        aggregated[group_by] = subject

        # Add group info if available
        if "group" in subject_trials[0]:
            aggregated["group"] = subject_trials[0]["group"]
        if "pathology_key" in subject_trials[0]:
            aggregated["pathology_key"] = subject_trials[0]["pathology_key"]

        aggregated_data.append(aggregated)

    subject_df = pd.DataFrame(aggregated_data)

    return subject_df


def export_metrics_to_csv(
    metrics_df: pd.DataFrame, output_path: str | Path, index: bool = False
) -> None:
    """
    Export metrics DataFrame to CSV file.

    Args:
        metrics_df: DataFrame containing metrics
        output_path: Path to output CSV file
        index: Whether to include index in CSV (default: False)
    """
    output_path = Path(output_path)

    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to CSV
    metrics_df.to_csv(output_path, index=index)

    print(f"Metrics exported to: {output_path}")


def compute_subject_summary_statistics(subject_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute summary statistics across all subjects.

    Args:
        subject_df: DataFrame with subject-level metrics

    Returns:
        summary_df: DataFrame with summary statistics
    """
    # Select numeric columns
    numeric_cols = subject_df.select_dtypes(include=[np.number]).columns

    # Compute statistics
    summary = subject_df[numeric_cols].describe()

    return summary
