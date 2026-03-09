"""
Validation module for gait analysis pipeline.

Provides Pydantic schemas for validating inputs and outputs of each phase.
"""

from gait_project.validation.schemas import (
    TrialMetadataSchema,
    Phase1MetricsSchema,
    Phase2MetricsSchema,
    Phase3MetricsSchema,
    MasterMetricsSchema,
    validate_phase1_metrics,
    validate_phase2_metrics,
    validate_phase3_metrics,
    validate_master_metrics,
)

__all__ = [
    "TrialMetadataSchema",
    "Phase1MetricsSchema",
    "Phase2MetricsSchema",
    "Phase3MetricsSchema",
    "MasterMetricsSchema",
    "validate_phase1_metrics",
    "validate_phase2_metrics",
    "validate_phase3_metrics",
    "validate_master_metrics",
]
