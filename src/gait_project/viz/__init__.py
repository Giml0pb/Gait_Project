"""
Visualization module for gait analysis.

This module provides plotting functions for signals, spectra and phase analysis.
"""

from gait_project.viz.signal_plots import (
    plot_raw_signal,
    plot_filtered_comparison,
    plot_dual_signals,
)
from gait_project.viz.spectral_plots import (
    plot_psd,
    plot_spectrogram,
    plot_dual_psd,
)
from gait_project.viz.phase_plots import (
    plot_instantaneous_phase,
    plot_phase_difference,
    plot_plv_temporal,
    plot_phase_portrait,
)

__all__ = [
    # Signal plots
    "plot_raw_signal",
    "plot_filtered_comparison",
    "plot_dual_signals",
    # Spectral plots
    "plot_psd",
    "plot_spectrogram",
    "plot_dual_psd",
    # Phase plots
    "plot_instantaneous_phase",
    "plot_phase_difference",
    "plot_plv_temporal",
    "plot_phase_portrait",
]
