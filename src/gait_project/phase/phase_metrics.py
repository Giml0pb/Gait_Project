"""
Phase-based metrics for gait rhythm stability assessment.

This module computes metrics that characterize the stability and variability
of instantaneous phase and frequency.
"""

import numpy as np
from typing import Dict, Tuple


def unwrap_phase(phase: np.ndarray) -> np.ndarray:
    """
    Unwrap phase to remove 2π discontinuities.

    Args:
        phase: Wrapped phase in radians

    Returns:
        unwrapped_phase: Continuous unwrapped phase
    """
    return np.unwrap(phase)


def compute_phase_stability(phase: np.ndarray) -> float:
    """
    Compute phase stability as the inverse of phase variability.

    Higher values indicate more stable oscillation.

    Args:
        phase: Unwrapped instantaneous phase

    Returns:
        stability: Phase stability metric
    """
    # Compute phase derivative (angular velocity)
    phase_derivative = np.diff(phase)

    # Variability of phase derivative
    phase_variability = np.std(phase_derivative)

    # Stability as inverse (avoid division by zero)
    stability = 1.0 / (phase_variability + 1e-10)

    return stability


def compute_frequency_variability(inst_frequency: np.ndarray) -> float:
    """
    Compute variability of instantaneous frequency.

    Lower values indicate more rhythmic, stable gait.

    Args:
        inst_frequency: Instantaneous frequency in Hz

    Returns:
        freq_variability: Standard deviation of instantaneous frequency
    """
    freq_variability = np.std(inst_frequency)
    return freq_variability


def compute_coefficient_of_variation(inst_frequency: np.ndarray) -> float:
    """
    Compute coefficient of variation of instantaneous frequency.

    Normalized measure of frequency variability (CV = std / mean).

    Args:
        inst_frequency: Instantaneous frequency in Hz

    Returns:
        cv: Coefficient of variation (dimensionless)
    """
    mean_freq = np.mean(inst_frequency)
    std_freq = np.std(inst_frequency)

    cv = std_freq / mean_freq if mean_freq > 0 else 0.0

    return cv


def detect_phase_discontinuities(
    phase: np.ndarray, threshold: float = 0.5
) -> np.ndarray:
    """
    Detect abrupt phase discontinuities (jumps).

    Args:
        phase: Unwrapped phase
        threshold: Threshold for detecting discontinuities (in radians/sample)

    Returns:
        discontinuity_indices: Indices where discontinuities occur
    """
    phase_diff = np.abs(np.diff(phase))
    discontinuities = np.where(phase_diff > threshold)[0]

    return discontinuities


def validate_phase_monotonicity(
    phase_unwrapped: np.ndarray, tolerance: float = 0.05
) -> tuple[bool, float]:
    """
    Validate that unwrapped phase is monotonically increasing.

    For a valid oscillation, the unwrapped phase should always increase
    (i.e., dφ/dt > 0 for all t).

    Args:
        phase_unwrapped: Unwrapped phase in radians
        tolerance: Fraction of samples allowed to violate monotonicity (default: 0.05 = 5%)

    Returns:
        is_valid: True if phase is sufficiently monotonic
        monotonic_fraction: Fraction of samples with dφ/dt > 0
    """
    phase_derivative = np.gradient(phase_unwrapped)
    increasing_samples = np.sum(phase_derivative > 0)
    total_samples = len(phase_derivative)

    monotonic_fraction = (
        increasing_samples / total_samples if total_samples > 0 else 0.0
    )
    is_valid = monotonic_fraction >= (1.0 - tolerance)

    return is_valid, monotonic_fraction


def validate_frequency_coherence(
    f0: float, mean_inst_freq: float, tolerance: float = 0.15
) -> tuple[bool, float]:
    """
    Validate coherence between spectral f0 and mean instantaneous frequency.

    These two estimates should be consistent for a well-extracted signal.

    Args:
        f0: Dominant frequency from spectral analysis (Hz)
        mean_inst_freq: Mean instantaneous frequency from Hilbert (Hz)
        tolerance: Maximum relative difference allowed (default: 0.15 = 15%)

    Returns:
        is_coherent: True if frequencies are coherent within tolerance
        relative_error: Relative difference between frequencies
    """
    relative_error = abs(f0 - mean_inst_freq) / f0 if f0 > 0 else 1.0
    is_coherent = relative_error <= tolerance

    return is_coherent, relative_error


def summarize_phase_metrics(
    amplitude: np.ndarray,
    phase_wrapped: np.ndarray,
    phase_unwrapped: np.ndarray,
    inst_freq: np.ndarray,
) -> dict:
    """
    Compute summary metrics for phase analysis.

    Args:
        amplitude: Instantaneous amplitude
        phase_wrapped: Wrapped phase in radians
        phase_unwrapped: Unwrapped phase in radians
        inst_freq: Instantaneous frequency in Hz

    Returns:
        metrics: Dictionary with summary statistics
    """
    metrics = {
        # Frequency metrics
        "mean_inst_freq_hz": np.mean(inst_freq),
        "median_inst_freq_hz": np.median(inst_freq),
        "std_inst_freq_hz": np.std(inst_freq),
        "cv_inst_freq": compute_coefficient_of_variation(inst_freq),
        # Amplitude metrics
        "amplitude_mean": np.mean(amplitude),
        "amplitude_std": np.std(amplitude),
        "amplitude_cv": np.std(amplitude) / np.mean(amplitude)
        if np.mean(amplitude) > 0
        else 0.0,
        # Phase metrics
        "phase_range_rad": np.max(phase_unwrapped) - np.min(phase_unwrapped),
        "num_cycles": (np.max(phase_unwrapped) - np.min(phase_unwrapped)) / (2 * np.pi),
        # Quality metrics
        "freq_variability": compute_frequency_variability(inst_freq),
    }

    return metrics


# ==============================================================================
# VALIDITY MASK STRATEGIES (Phase 2 Improvements)
# ==============================================================================


def create_mask_all_samples(n_samples: int) -> np.ndarray:
    """
    Strategy A: Use all samples (baseline).

    Args:
        n_samples: Number of samples

    Returns:
        mask: Boolean array (all True)
    """
    return np.ones(n_samples, dtype=bool)


def create_mask_exclude_edges(
    n_samples: int, fs: float, edge_time: float = 1.0
) -> np.ndarray:
    """
    Strategy B: Exclude edges affected by filter artifacts.

    Narrowband filtering (especially Butterworth) produces transient artifacts
    at the beginning and end of the signal due to:
    - Initial conditions of the filter state
    - Edge effects in zero-phase filtering (filtfilt)

    Args:
        n_samples: Number of samples
        fs: Sampling frequency (Hz)
        edge_time: Time to exclude from each edge (seconds, default: 1.0)

    Returns:
        mask: Boolean array (False at edges, True in center)
    """
    edge_samples = int(edge_time * fs)
    mask = np.zeros(n_samples, dtype=bool)

    if n_samples > 2 * edge_samples:
        mask[edge_samples:-edge_samples] = True
    else:
        # If signal is too short, use all samples
        mask[:] = True

    return mask


def create_mask_amplitude_threshold(
    amplitude: np.ndarray, percentile: float = 20.0
) -> np.ndarray:
    """
    Strategy C: Exclude regions with very low amplitude.

    Instantaneous frequency becomes unreliable when amplitude is low because:
    - Numerical instability in phase derivative
    - Noise dominates the signal
    - Hilbert transform assumptions break down

    Args:
        amplitude: Instantaneous amplitude array
        percentile: Percentile threshold (default: 20, excludes lowest 20%)

    Returns:
        mask: Boolean array (True where amplitude is above threshold)
    """
    threshold = np.percentile(amplitude, percentile)
    mask = amplitude >= threshold
    return mask


def create_mask_combined(
    amplitude: np.ndarray,
    fs: float,
    edge_time: float = 1.0,
    amplitude_percentile: float = 20.0,
) -> np.ndarray:
    """
    Strategy D: Combine edge exclusion and amplitude threshold.

    Most conservative approach: exclude both filter artifacts and low-amplitude regions.

    Args:
        amplitude: Instantaneous amplitude array
        fs: Sampling frequency (Hz)
        edge_time: Time to exclude from edges (seconds, default: 1.0)
        amplitude_percentile: Amplitude percentile threshold (default: 20)

    Returns:
        mask: Boolean array (True where both conditions are met)
    """
    n_samples = len(amplitude)

    mask_edges = create_mask_exclude_edges(n_samples, fs, edge_time)
    mask_amplitude = create_mask_amplitude_threshold(amplitude, amplitude_percentile)

    # Combine with AND operation
    mask = mask_edges & mask_amplitude

    return mask


def evaluate_mask_strategy(
    inst_freq: np.ndarray, mask: np.ndarray, f0: float
) -> Tuple[float, int, float]:
    """
    Evaluate a masking strategy by comparing mean inst. freq with spectral f0.

    The best strategy should minimize the relative error between:
    - f0 (from spectral analysis)
    - mean(inst_freq) over valid samples

    Args:
        inst_freq: Instantaneous frequency array (Hz)
        mask: Boolean validity mask
        f0: Spectral dominant frequency (Hz)

    Returns:
        relative_error: |mean(inst_freq[mask]) - f0| / f0
        valid_count: Number of valid samples
        valid_fraction: Fraction of samples that are valid
    """
    if not np.any(mask):
        # No valid samples
        return np.inf, 0, 0.0

    valid_freq = inst_freq[mask]
    mean_freq = np.mean(valid_freq)

    relative_error = abs(mean_freq - f0) / f0 if f0 > 0 else np.inf
    valid_count = np.sum(mask)
    valid_fraction = valid_count / len(mask)

    return relative_error, valid_count, valid_fraction


def select_best_mask_strategy(
    inst_freq: np.ndarray,
    amplitude: np.ndarray,
    f0: float,
    fs: float,
    edge_time: float = 1.0,
    amplitude_percentile: float = 20.0,
) -> Tuple[np.ndarray, str, Dict[str, float]]:
    """
    Automatically select the best masking strategy.

    CORRECTED: Now minimizes a composite metric that includes BOTH:
    - Relative error between mean inst. freq and spectral f0
    - CV (coefficient of variation) of inst. freq

    This prevents selecting masks that include high-variability regions
    (e.g., edge artifacts) just because they minimize the mean error.

    Args:
        inst_freq: Instantaneous frequency (Hz)
        amplitude: Instantaneous amplitude
        f0: Spectral dominant frequency (Hz)
        fs: Sampling frequency (Hz)
        edge_time: Time to exclude from edges (seconds)
        amplitude_percentile: Percentile for amplitude threshold

    Returns:
        best_mask: Selected validity mask
        strategy_name: Name of selected strategy
        metrics: Dictionary with error, valid_count, valid_fraction for each strategy
    """
    n_samples = len(inst_freq)

    # CORRECTION 2: Remove "all_samples" strategy (always includes artifacts)
    # Define strategies (now excluding all_samples)
    strategies = {
        "exclude_edges": create_mask_exclude_edges(n_samples, fs, edge_time),
        "amplitude_threshold": create_mask_combined(
            amplitude, fs, edge_time=1.0, amplitude_percentile=30.0
        ),
        "combined": create_mask_combined(
            amplitude, fs, edge_time, amplitude_percentile
        ),
    }

    # Evaluate each strategy
    results = {}
    for name, mask in strategies.items():
        error, count, fraction = evaluate_mask_strategy(inst_freq, mask, f0)

        # CORRECTION 1: Calculate CV for valid samples
        if np.sum(mask) > 0:
            valid_freq = inst_freq[mask]
            mean_freq = np.mean(valid_freq)
            std_freq = np.std(valid_freq)
            cv_valid = std_freq / mean_freq if mean_freq > 0 else np.inf
        else:
            cv_valid = np.inf

        # CORRECTION 1: Composite cost function
        # Minimizes BOTH error and variability
        composite_cost = cv_valid + error

        # Penalize if valid fraction is too low (< 50%)
        if fraction < 0.5:
            composite_cost *= 2.0

        results[name] = {
            "relative_error": error,
            "cv": cv_valid,
            "cost": composite_cost,
            "valid_count": count,
            "valid_fraction": fraction,
            "mask": mask,
        }

    # CORRECTION 1: Select strategy with minimum composite cost (not just error)
    best_strategy_name = min(results.keys(), key=lambda k: results[k]["cost"])
    best_mask = results[best_strategy_name]["mask"]

    # Prepare metrics dictionary
    metrics = {
        f"{name}_error": results[name]["relative_error"] for name in strategies.keys()
    }
    metrics.update(
        {
            f"{name}_valid_fraction": results[name]["valid_fraction"]
            for name in strategies.keys()
        }
    )
    # Add CV metrics for transparency
    metrics.update({f"{name}_cv": results[name]["cv"] for name in strategies.keys()})
    metrics.update(
        {f"{name}_cost": results[name]["cost"] for name in strategies.keys()}
    )

    return best_mask, best_strategy_name, metrics


def compute_robust_statistics(
    data: np.ndarray, mask: np.ndarray = None
) -> Dict[str, float]:
    """
    Compute robust statistics for instantaneous frequency.

    Includes median-based metrics (MAD, IQR) in addition to mean/std.

    Args:
        data: Data array (e.g., instantaneous frequency)
        mask: Optional validity mask (if None, use all samples)

    Returns:
        stats_dict: Dictionary with robust statistics
    """
    if mask is not None:
        data = data[mask]

    if len(data) == 0:
        return {
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "mad": np.nan,
            "iqr": np.nan,
            "q25": np.nan,
            "q75": np.nan,
        }

    # Central tendency
    mean_val = np.mean(data)
    median_val = np.median(data)

    # Dispersion
    std_val = np.std(data)

    # Robust dispersion: MAD (Median Absolute Deviation)
    mad = np.median(np.abs(data - median_val))

    # Interquartile range
    q25 = np.percentile(data, 25)
    q75 = np.percentile(data, 75)
    iqr = q75 - q25

    return {
        "mean": mean_val,
        "median": median_val,
        "std": std_val,
        "mad": mad,
        "iqr": iqr,
        "q25": q25,
        "q75": q75,
    }


def summarize_phase_metrics_robust(
    amplitude: np.ndarray,
    phase_wrapped: np.ndarray,
    phase_unwrapped: np.ndarray,
    inst_freq: np.ndarray,
    f0: float,
    fs: float,
    validity_mask: np.ndarray = None,
    mask_strategy: str = "unknown",
) -> Dict:
    """
    Compute summary metrics for phase analysis with robust statistics.

    Extended version that includes:
    - Validity masking
    - Robust statistics (median, MAD, IQR)
    - Strategy metadata

    Args:
        amplitude: Instantaneous amplitude
        phase_wrapped: Wrapped phase in radians
        phase_unwrapped: Unwrapped phase in radians
        inst_freq: Instantaneous frequency in Hz
        f0: Spectral dominant frequency (Hz)
        fs: Sampling frequency (Hz)
        validity_mask: Boolean mask for valid samples (if None, use all)
        mask_strategy: Name of the masking strategy used

    Returns:
        metrics: Dictionary with summary statistics
    """
    # If no mask provided, use all samples
    if validity_mask is None:
        validity_mask = np.ones(len(inst_freq), dtype=bool)

    # Compute robust statistics for instantaneous frequency
    freq_stats = compute_robust_statistics(inst_freq, validity_mask)

    # Amplitude statistics (always use full signal for amplitude)
    amplitude_mean = np.mean(amplitude)
    amplitude_std = np.std(amplitude)
    amplitude_cv = amplitude_std / amplitude_mean if amplitude_mean > 0 else 0.0

    # Compute CV using valid samples only
    cv_inst_freq = (
        freq_stats["std"] / freq_stats["mean"] if freq_stats["mean"] > 0 else 0.0
    )

    # Phase metrics (use full signal)
    phase_range_rad = np.max(phase_unwrapped) - np.min(phase_unwrapped)
    num_cycles = phase_range_rad / (2 * np.pi)

    # Validity metrics
    valid_count = np.sum(validity_mask)
    valid_fraction = valid_count / len(validity_mask)

    metrics = {
        # Frequency metrics (robust)
        "mean_inst_freq_hz": freq_stats["mean"],
        "median_inst_freq_hz": freq_stats["median"],
        "std_inst_freq_hz": freq_stats["std"],
        "mad_inst_freq_hz": freq_stats["mad"],
        "iqr_inst_freq_hz": freq_stats["iqr"],
        "cv_inst_freq": cv_inst_freq,
        # Amplitude metrics
        "amplitude_mean": amplitude_mean,
        "amplitude_std": amplitude_std,
        "amplitude_cv": amplitude_cv,
        # Phase metrics
        "phase_range_rad": phase_range_rad,
        "num_cycles": num_cycles,
        # Validity metrics
        "mask_strategy": mask_strategy,
        "valid_samples": valid_count,
        "valid_fraction": valid_fraction,
        # Frequency variability (legacy)
        "freq_variability": freq_stats["std"],
    }

    return metrics
