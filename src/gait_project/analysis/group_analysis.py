"""
Group-level statistical comparison.

This module performs statistical comparisons between clinical groups
(healthy, neuro, ortho).
"""

import numpy as np
import pandas as pd
from typing import List
from scipy import stats


def compute_group_statistics(
    subject_df: pd.DataFrame, group_column: str = "group"
) -> pd.DataFrame:
    """
    Compute descriptive statistics for each group.

    Args:
        subject_df: DataFrame with subject-level metrics
        group_column: Column name containing group labels

    Returns:
        group_stats: DataFrame with statistics per group
    """
    if group_column not in subject_df.columns:
        raise ValueError(f"Column '{group_column}' not found in DataFrame")

    # Select numeric columns
    numeric_cols = subject_df.select_dtypes(include=[np.number]).columns

    # Group by clinical group
    grouped = subject_df.groupby(group_column)

    # Compute statistics
    stats_list = []

    for group_name, group_data in grouped:
        group_stats = {
            "group": group_name,
            "n_subjects": len(group_data),
        }

        for col in numeric_cols:
            if col in group_data.columns:
                values = group_data[col].dropna()
                group_stats[f"{col}_mean"] = np.mean(values)
                group_stats[f"{col}_std"] = np.std(values)
                group_stats[f"{col}_median"] = np.median(values)
                group_stats[f"{col}_q25"] = np.percentile(values, 25)
                group_stats[f"{col}_q75"] = np.percentile(values, 75)

        stats_list.append(group_stats)

    group_stats_df = pd.DataFrame(stats_list)

    return group_stats_df


def compare_groups(
    subject_df: pd.DataFrame,
    metric_columns: List[str],
    group_column: str = "group",
    test_type: str = "kruskal",
) -> pd.DataFrame:
    """
    Perform statistical tests comparing groups.

    Args:
        subject_df: DataFrame with subject-level metrics
        metric_columns: List of metric column names to compare
        group_column: Column containing group labels
        test_type: Statistical test to use ('kruskal' or 'anova')

    Returns:
        results_df: DataFrame with test results for each metric
    """
    if group_column not in subject_df.columns:
        raise ValueError(f"Column '{group_column}' not found")

    groups = subject_df[group_column].unique()

    results = []

    for metric in metric_columns:
        if metric not in subject_df.columns:
            print(f"Warning: Metric '{metric}' not found, skipping")
            continue

        # Extract data for each group
        group_data = [
            subject_df[subject_df[group_column] == group][metric].dropna().values
            for group in groups
        ]

        # Remove empty groups
        group_data = [g for g in group_data if len(g) > 0]

        if len(group_data) < 2:
            print(f"Warning: Not enough groups for metric '{metric}', skipping")
            continue

        # Perform statistical test
        if test_type == "kruskal":
            statistic, p_value = stats.kruskal(*group_data)
            test_name = "Kruskal-Wallis"
        elif test_type == "anova":
            statistic, p_value = stats.f_oneway(*group_data)
            test_name = "One-way ANOVA"
        else:
            raise ValueError(f"Unknown test type: {test_type}")

        results.append(
            {
                "metric": metric,
                "test": test_name,
                "statistic": statistic,
                "p_value": p_value,
                "significant": p_value < 0.05,
            }
        )

    results_df = pd.DataFrame(results)

    return results_df


def pairwise_group_comparison(
    subject_df: pd.DataFrame,
    metric: str,
    group_column: str = "group",
    test_type: str = "mannwhitneyu",
) -> pd.DataFrame:
    """
    Perform pairwise comparisons between all groups for a single metric.

    Args:
        subject_df: DataFrame with subject-level metrics
        metric: Metric column name to compare
        group_column: Column containing group labels
        test_type: Test to use ('mannwhitneyu' or 't-test')

    Returns:
        pairwise_results: DataFrame with pairwise comparison results
    """
    groups = subject_df[group_column].unique()
    results = []

    for i, group1 in enumerate(groups):
        for group2 in groups[i + 1 :]:
            # Extract data
            data1 = subject_df[subject_df[group_column] == group1][metric].dropna()
            data2 = subject_df[subject_df[group_column] == group2][metric].dropna()

            if len(data1) == 0 or len(data2) == 0:
                continue

            # Perform test
            if test_type == "mannwhitneyu":
                statistic, p_value = stats.mannwhitneyu(
                    data1, data2, alternative="two-sided"
                )
                test_name = "Mann-Whitney U"
            elif test_type == "t-test":
                statistic, p_value = stats.ttest_ind(data1, data2)
                test_name = "Independent t-test"
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            results.append(
                {
                    "metric": metric,
                    "group1": group1,
                    "group2": group2,
                    "test": test_name,
                    "statistic": statistic,
                    "p_value": p_value,
                    "significant": p_value < 0.05,
                    "mean1": np.mean(data1),
                    "mean2": np.mean(data2),
                }
            )

    pairwise_df = pd.DataFrame(results)

    return pairwise_df


def compute_effect_size(
    subject_df: pd.DataFrame,
    metric: str,
    group1: str,
    group2: str,
    group_column: str = "group",
) -> float:
    """
    Compute Cohen's d effect size between two groups.

    Args:
        subject_df: DataFrame with subject-level metrics
        metric: Metric to compare
        group1: First group name
        group2: Second group name
        group_column: Column containing group labels

    Returns:
        cohens_d: Effect size
    """
    data1 = subject_df[subject_df[group_column] == group1][metric].dropna()
    data2 = subject_df[subject_df[group_column] == group2][metric].dropna()

    # Compute means and pooled standard deviation
    mean1, mean2 = np.mean(data1), np.mean(data2)
    std1, std2 = np.std(data1, ddof=1), np.std(data2, ddof=1)
    n1, n2 = len(data1), len(data2)

    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0

    return cohens_d
