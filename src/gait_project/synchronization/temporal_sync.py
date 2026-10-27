"""Temporal synchronization on the original sample timeline.

Windows never cross recording gaps or turns. Invalid phase estimates remain
on the timeline and contribute neither to PLV nor to slip detection.
"""

from typing import Dict, Tuple

import numpy as np

from gait_project.analysis.circular_statistics import wrap_angle
from gait_project.synchronization.phase_sync import (
    compute_phase_difference,
    compute_plv,
)


def _timeline(n, fs, time=None, validity_mask=None):
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("Sampling frequency must be finite and positive")
    time = (
        np.arange(n, dtype=float) / fs
        if time is None
        else np.asarray(time, dtype=float)
    )
    mask = (
        np.ones(n, dtype=bool) if validity_mask is None else np.asarray(validity_mask)
    )
    if time.shape != (n,) or mask.shape != (n,) or mask.dtype != bool:
        raise ValueError("Time and boolean validity mask must match the phase arrays")
    if n < 2 or not np.isfinite(time).all() or np.any(np.diff(time) <= 0):
        raise ValueError(
            "Time must contain at least two finite, strictly increasing values"
        )
    contiguous = np.isclose(np.diff(time), 1 / fs, rtol=1e-5, atol=1e-9)
    return time, mask, contiguous


def compute_phase_slip_rate(
    phase_diff: np.ndarray,
    fs: float,
    threshold: float = np.pi / 2,
    *,
    validity_mask=None,
    time=None,
) -> float:
    """Count jumps only between adjacent valid samples, per observed minute.

    Exposure is the sum of eligible adjacent sample intervals. Neither removed
    intervals nor isolated valid samples are counted as observed exposure.
    """
    phase_diff = np.asarray(phase_diff, dtype=float)
    if phase_diff.ndim != 1:
        raise ValueError("Phase difference must be one-dimensional")
    _, mask, contiguous = _timeline(len(phase_diff), fs, time, validity_mask)
    if not np.isfinite(phase_diff[mask]).all():
        raise ValueError("Valid phase samples must be finite")
    if not np.isfinite(threshold) or not 0 < threshold <= np.pi:
        raise ValueError("Slip threshold must be in (0, pi]")
    eligible = mask[:-1] & mask[1:] & contiguous
    duration = np.count_nonzero(eligible) / fs
    if duration == 0:
        raise ValueError("No adjacent valid samples for temporal synchronization")
    jumps = np.abs(wrap_angle(np.diff(phase_diff))) > threshold
    return float(np.count_nonzero(jumps & eligible) * 60 / duration)


def compute_windowed_plv(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    window_size: int,
    step_size: int = None,
    *,
    fs: float = 1.0,
    time=None,
    validity_mask=None,
    min_valid_fraction: float = 0.5,
) -> Dict:
    """Compute fixed-duration windows within continuous recording segments.

    A window needs at least 50% valid samples by default. PLV uses those valid
    samples in place, retaining the window's original time center in seconds.
    The trend is measured in PLV units per second.
    """
    left, right = (
        np.asarray(phase_left, dtype=float),
        np.asarray(phase_right, dtype=float),
    )
    if left.ndim != 1 or right.shape != left.shape:
        raise ValueError(
            "Left and right phases must be matching one-dimensional arrays"
        )
    if not isinstance(window_size, (int, np.integer)) or window_size < 2:
        raise ValueError("Window size must be an integer of at least two samples")
    step_size = max(1, window_size // 2) if step_size is None else step_size
    if not isinstance(step_size, (int, np.integer)) or step_size <= 0:
        raise ValueError("Step size must be a positive integer")
    if not 0 < min_valid_fraction <= 1:
        raise ValueError("Minimum valid fraction must be in (0, 1]")
    time, mask, contiguous = _timeline(len(left), fs, time, validity_mask)
    if not (np.isfinite(left[mask]).all() and np.isfinite(right[mask]).all()):
        raise ValueError("Valid phase samples must be finite")
    bounds = np.r_[0, np.flatnonzero(~contiguous) + 1, len(left)]
    plvs, centers = [], []
    for first, stop in zip(bounds[:-1], bounds[1:]):
        for start in range(first, stop - window_size + 1, step_size):
            end = start + window_size
            valid = mask[start:end]
            if np.count_nonzero(valid) < max(
                2, int(np.ceil(window_size * min_valid_fraction))
            ):
                continue
            difference = compute_phase_difference(
                left[start:end][valid], right[start:end][valid]
            )
            plvs.append(compute_plv(difference))
            centers.append((time[start] + time[end - 1]) / 2)
    if not plvs:
        raise ValueError(
            "No eligible temporal windows: need a continuous window with at least 50% valid samples"
        )
    plvs, centers = np.asarray(plvs), np.asarray(centers)
    trend = (
        float(np.polyfit(centers - centers.mean(), plvs, 1)[0])
        if len(plvs) > 1
        else 0.0
    )
    return {
        "plv_timeseries": plvs,
        "time_centers": centers,
        "plv_mean_windowed": float(plvs.mean()),
        "plv_std_windowed": float(plvs.std()),
        "plv_trend": trend,
        "n_windows": len(plvs),
    }


def analyze_temporal_synchronization(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    fs: float,
    window_size: int = 256,
    step_size: int = None,
    slip_threshold: float = np.pi / 2,
    *,
    time=None,
    validity_mask=None,
) -> Dict:
    windowed = compute_windowed_plv(
        phase_left,
        phase_right,
        window_size,
        step_size,
        fs=fs,
        time=time,
        validity_mask=validity_mask,
    )
    difference = compute_phase_difference(
        np.asarray(phase_left), np.asarray(phase_right)
    )
    windowed["phase_slip_rate"] = compute_phase_slip_rate(
        difference, fs, slip_threshold, time=time, validity_mask=validity_mask
    )
    return windowed


def compute_plv_coefficient_of_variation(plv_timeseries: np.ndarray) -> float:
    values = np.asarray(plv_timeseries)
    if not len(values):
        raise ValueError("PLV series must not be empty")
    return float(values.std() / values.mean()) if values.mean() > 0 else 0.0


def detect_coordination_breakdown(
    plv_timeseries: np.ndarray, threshold: float = 0.7
) -> Tuple[int, float]:
    """Count windows below an exploratory, user-selected PLV threshold."""
    if not len(plv_timeseries):
        raise ValueError("PLV series must not be empty")
    n = int(np.count_nonzero(np.asarray(plv_timeseries) < threshold))
    return n, n / len(plv_timeseries)
