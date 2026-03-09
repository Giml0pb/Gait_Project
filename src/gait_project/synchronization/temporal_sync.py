"""
Temporal analysis of phase synchronization.

This module extends the static PLV analysis (phase_sync.py) with temporal
dynamics to capture evolution of coordination during trials.

Key concepts:
- Phase slip rate: Frequency of abrupt phase discontinuities (instability)
- Windowed PLV: Temporal evolution of coordination strength
- PLV stability: Variability and trends in coordination over time

These metrics capture temporal dynamics that global PLV cannot detect,
such as fatigue, adaptation, or progressive instability.
"""

import numpy as np
from typing import Dict, Tuple

from gait_project.analysis.circular_statistics import wrap_angle
from gait_project.synchronization.phase_sync import (
    compute_phase_difference,
    compute_plv,
)


def compute_phase_slip_rate(
    phase_diff: np.ndarray,
    fs: float,
    threshold: float = np.pi / 2,
) -> float:
    """
    Compute phase slip rate (instability metric).

    A "phase slip" occurs when the phase difference changes abruptly by more
    than a threshold (default: π/2 = 90°) between consecutive samples. This
    indicates loss of synchronization or momentary instability.

    High slip rates suggest unstable coordination, possibly due to:
    - Gait asymmetry
    - Compensatory strategies
    - Fatigue
    - Pathological instability

    Args:
        phase_diff: Phase difference time series Δφ(t) in radians
        fs: Sampling frequency (Hz)
        threshold: Minimum angular change to count as slip (default: π/2 rad = 90°)

    Returns:
        slip_rate: Number of phase slips per minute

    Example:
        >>> phase_diff = np.array([0, 0.1, 0.2, 2.0, 2.1])  # Slip at index 3
        >>> slip_rate = compute_phase_slip_rate(phase_diff, fs=128)
    """
    # Compute change in phase difference
    delta_phase = np.diff(phase_diff)

    # Wrap to [-π, π] to handle circular boundaries correctly
    delta_phase_wrapped = wrap_angle(delta_phase)

    # Count slips (abrupt changes > threshold)
    slips = np.sum(np.abs(delta_phase_wrapped) > threshold)

    # Normalize by trial duration (slips per minute)
    duration_min = len(phase_diff) / (fs * 60)
    slip_rate = slips / duration_min if duration_min > 0 else 0.0

    return slip_rate


def compute_windowed_plv(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    window_size: int,
    step_size: int = None,
) -> Dict:
    """
    Compute PLV in sliding temporal windows to assess coordination stability.

    This function reveals temporal dynamics that global PLV cannot capture:
    - Does coordination improve or deteriorate during the trial?
    - Is coordination stable or fluctuating?
    - Are there periods of loss of synchronization?

    Args:
        phase_left: Instantaneous phase of left foot (radians)
        phase_right: Instantaneous phase of right foot (radians)
        window_size: Window size in samples (e.g., 256 samples ≈ 2 sec at 128 Hz)
        step_size: Step between windows (default: window_size // 2 for 50% overlap)

    Returns:
        results: Dictionary with:
            - plv_timeseries: PLV value for each window
            - time_centers: Time point (seconds) for each window center
            - plv_mean_windowed: Mean PLV across all windows
            - plv_std_windowed: Std of PLV (temporal variability)
            - plv_trend: Linear trend (slope) of PLV over time
            - n_windows: Number of windows analyzed

    Example:
        >>> results = compute_windowed_plv(phase_left, phase_right,
        ...                                 window_size=256, step_size=128)
        >>> print(f"PLV temporal std: {results['plv_std_windowed']:.3f}")
    """
    if step_size is None:
        step_size = window_size // 2  # 50% overlap by default

    n_samples = len(phase_left)
    plv_values = []
    time_centers = []

    # Slide window across signal
    for start in range(0, n_samples - window_size + 1, step_size):
        end = start + window_size

        # Extract window
        phase_left_window = phase_left[start:end]
        phase_right_window = phase_right[start:end]

        # Compute phase difference for this window
        phase_diff_window = compute_phase_difference(
            phase_left_window, phase_right_window
        )

        # Compute PLV for this window
        plv_window = compute_plv(phase_diff_window)
        plv_values.append(plv_window)

        # Time center of window (in samples)
        time_center = (start + end) / 2
        time_centers.append(time_center)

    plv_values = np.array(plv_values)
    time_centers = np.array(time_centers)

    # Summary statistics
    plv_mean = np.mean(plv_values)
    plv_std = np.std(plv_values)

    # Temporal trend (linear regression)
    # Positive slope = improving coordination
    # Negative slope = deteriorating coordination
    if len(plv_values) > 1:
        x = np.arange(len(plv_values))
        slope, intercept = np.polyfit(x, plv_values, 1)
        plv_trend = slope
    else:
        plv_trend = 0.0

    return {
        "plv_timeseries": plv_values,
        "time_centers": time_centers,
        "plv_mean_windowed": plv_mean,
        "plv_std_windowed": plv_std,
        "plv_trend": plv_trend,
        "n_windows": len(plv_values),
    }


def analyze_temporal_synchronization(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    fs: float,
    window_size: int = 256,
    step_size: int = None,
    slip_threshold: float = np.pi / 2,
) -> Dict:
    """
    Comprehensive temporal analysis of phase synchronization.

    Combines:
    1. Phase slip rate (instability)
    2. Windowed PLV (temporal evolution)
    3. PLV stability metrics

    Args:
        phase_left: Instantaneous phase of left foot (radians)
        phase_right: Instantaneous phase of right foot (radians)
        fs: Sampling frequency (Hz)
        window_size: Window size for PLV analysis (samples)
        step_size: Step size for sliding window (default: 50% overlap)
        slip_threshold: Threshold for phase slip detection (default: π/2)

    Returns:
        metrics: Dictionary with temporal synchronization metrics
    """
    # Compute phase difference
    phase_diff = compute_phase_difference(phase_left, phase_right)

    # 1. Phase slip rate
    slip_rate = compute_phase_slip_rate(phase_diff, fs, slip_threshold)

    # 2. Windowed PLV analysis
    windowed_results = compute_windowed_plv(
        phase_left, phase_right, window_size, step_size
    )

    # Compile metrics
    metrics = {
        # Phase slip metrics
        "phase_slip_rate": slip_rate,
        # Windowed PLV metrics
        "plv_mean_windowed": windowed_results["plv_mean_windowed"],
        "plv_std_windowed": windowed_results["plv_std_windowed"],
        "plv_trend": windowed_results["plv_trend"],
        "n_windows": windowed_results["n_windows"],
        # Timeseries (for visualization)
        "plv_timeseries": windowed_results["plv_timeseries"],
        "time_centers": windowed_results["time_centers"],
    }

    return metrics


def compute_plv_coefficient_of_variation(plv_timeseries: np.ndarray) -> float:
    """
    Compute coefficient of variation of windowed PLV.

    CV = std / mean

    Interpretation:
    - Low CV: Stable coordination throughout trial
    - High CV: Fluctuating coordination

    Args:
        plv_timeseries: Array of PLV values from windowed analysis

    Returns:
        cv: Coefficient of variation (dimensionless)
    """
    mean_plv = np.mean(plv_timeseries)
    std_plv = np.std(plv_timeseries)

    cv = std_plv / mean_plv if mean_plv > 0 else 0.0

    return cv


def detect_coordination_breakdown(
    plv_timeseries: np.ndarray,
    threshold: float = 0.7,
) -> Tuple[int, float]:
    """
    Detect windows where coordination breaks down (PLV < threshold).

    This can indicate:
    - Momentary loss of synchronization
    - Gait perturbations
    - Fatigue-related instability

    Args:
        plv_timeseries: Array of PLV values from windowed analysis
        threshold: PLV threshold for "breakdown" (default: 0.7)

    Returns:
        n_breakdowns: Number of windows below threshold
        breakdown_fraction: Fraction of time with poor coordination
    """
    n_breakdowns = np.sum(plv_timeseries < threshold)
    breakdown_fraction = n_breakdowns / len(plv_timeseries)

    return n_breakdowns, breakdown_fraction
