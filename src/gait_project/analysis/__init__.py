"""Participant-level aggregation of trial metrics."""

from gait_project.analysis.subject_analysis import (
    aggregate_subject_metrics,
    export_metrics_to_csv,
)

__all__ = [
    "aggregate_subject_metrics",
    "export_metrics_to_csv",
]
