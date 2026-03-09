"""
Phase analysis module for gait oscillator characterization.

This module provides tools for extracting instantaneous phase, amplitude, and
frequency from narrowband gait signals using the Hilbert transform.
"""

from gait_project.phase.hilbert_transform import (
    compute_analytic_signal,
    compute_instantaneous_amplitude,
    compute_instantaneous_frequency,
    compute_instantaneous_phase,
)
from gait_project.phase.narrowband_filter import apply_narrowband_filter
from gait_project.phase.phase_metrics import (
    compute_frequency_variability,
    compute_phase_stability,
    unwrap_phase,
)

__all__ = [
    "apply_narrowband_filter",
    "compute_analytic_signal",
    "compute_instantaneous_phase",
    "compute_instantaneous_amplitude",
    "compute_instantaneous_frequency",
    "unwrap_phase",
    "compute_phase_stability",
    "compute_frequency_variability",
]
