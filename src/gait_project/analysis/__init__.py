"""
Group-level analysis module.

This module provides tools for aggregating metrics across trials and subjects,
and for comparing groups (healthy, neuro, ortho).
"""

from gait_project.analysis.group_analysis import (
    compare_groups,
    compute_group_statistics,
)
from gait_project.analysis.subject_analysis import (
    aggregate_subject_metrics,
    export_metrics_to_csv,
)

__all__ = [
    "aggregate_subject_metrics",
    "export_metrics_to_csv",
    "compute_group_statistics",
    "compare_groups",
]
