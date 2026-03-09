"""
Visualization module for gait analysis.

This module provides plotting functions for signals, spectra, phase analysis,
and group comparisons.
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
from gait_project.viz.group_plots import (
    plot_group_boxplot,
    plot_group_distributions,
    plot_metric_comparison,
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
    # Group plots
    "plot_group_boxplot",
    "plot_group_distributions",
    "plot_metric_comparison",
]
