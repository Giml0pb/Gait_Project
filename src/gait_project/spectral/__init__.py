"""
Spectral analysis module for gait signals.

This module provides tools for frequency-domain characterization of gait signals,
including power spectral density estimation and dominant frequency detection.
"""

from gait_project.spectral.dominant_frequency import (
    compute_spectral_metrics,
    find_dominant_frequency,
)
from gait_project.spectral.psd_analysis import compute_psd, compute_spectrogram

__all__ = [
    "compute_psd",
    "compute_spectrogram",
    "find_dominant_frequency",
    "compute_spectral_metrics",
]
