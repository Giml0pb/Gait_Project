"""
Phase synchronization analysis for coupled oscillators (gait coordination).

This module implements metrics for analyzing phase synchronization between
two oscillatory signals, specifically designed for gait analysis where
left and right feet are modeled as coupled oscillators.

Key concepts:
- Phase difference Δφ(t) = φ_L(t) - (φ_R(t) + π)  [shifted_right convention]
- Phase Locking Value (PLV): measure of phase synchronization
- Anti-phase coordination: Δφ ≈ π (normal gait pattern)

Phase Convention:
    The shifted_right convention Δφ = φ_L - (φ_R + π) is used to account for
    specular IMU sensor orientation. This ensures that normal anti-phase gait
    coordination is correctly represented as Δφ ≈ π (180°) rather than Δφ ≈ 0°.
    See DIAGNOSTICO_FASE_3.md for validation details.
"""

import numpy as np
from typing import Tuple, Dict
import warnings

from gait_project.analysis.circular_statistics import (
    wrap_angle,
    circular_mean,
    circular_variance,
    circular_std,
    angular_distance,
)


def compute_phase_difference(
    phase_left: np.ndarray, phase_right: np.ndarray
) -> np.ndarray:
    """
    Compute phase difference between two oscillators.

    For gait analysis:
    - phase_left: instantaneous phase of left foot
    - phase_right: instantaneous phase of right foot

    Convention: Δφ(t) = φ_L(t) - (φ_R(t) + π)

    This convention accounts for the specular orientation of IMU sensors
    on left and right feet. Since both sensors register the same biomechanical
    event with the same sign (due to mirrored Y-axis orientation), we add π
    to the right foot phase to correctly represent anti-phase gait coordination.

    Expected result for healthy gait: Δφ ≈ π (anti-phase)

    Args:
        phase_left: Wrapped phase of left foot [-π, π]
        phase_right: Wrapped phase of right foot [-π, π]

    Returns:
        phase_diff: Phase difference Δφ(t) wrapped to [-π, π]

    Note:
        This convention was validated through systematic diagnostic analysis
        of multiple healthy subjects (see DIAGNOSTICO_FASE_3.md). All healthy
        subjects showed in-phase signals (Δφ ≈ 0° with standard convention),
        indicating specular sensor orientation. The shifted_right convention
        corrects this to produce the expected anti-phase pattern (Δφ ≈ 180°).
    """
    # Compute difference with π shift for right foot
    # Δφ = φ_L - (φ_R + π) = φ_L - φ_R - π
    delta_phi = phase_left - (phase_right + np.pi)

    # Wrap to [-π, π] to account for circular topology
    delta_phi = wrap_angle(delta_phi)

    return delta_phi


def compute_plv(phase_diff: np.ndarray) -> float:
    """
    Compute Phase Locking Value (PLV).

    PLV = |⟨exp(i*Δφ(t))⟩|

    Interpretation:
    - PLV = 0: no phase synchronization
    - PLV = 1: perfect phase synchronization
    - Typical healthy gait: PLV ≈ 0.8 - 0.95

    The PLV is the magnitude of the mean resultant vector (Kuramoto order parameter).

    Args:
        phase_diff: Array of phase differences Δφ(t) in radians

    Returns:
        plv: Phase Locking Value in [0, 1]
    """
    # Convert phase differences to unit vectors on the circle
    z = np.exp(1j * phase_diff)

    # Mean of unit vectors
    mean_z = np.mean(z)

    # PLV is the magnitude of the mean
    plv = np.abs(mean_z)

    return plv


def compute_anti_phase_error(mean_phase_diff: float) -> float:
    """
    Compute deviation from anti-phase coordination.

    In normal gait, feet are in anti-phase: Δφ ≈ π.
    This function quantifies the deviation from this expected pattern.

    Formula: anti_phase_error = |angle(exp(i*(mean_phase_diff - π)))|

    This gives the shortest angular distance from the mean phase to π.

    Args:
        mean_phase_diff: Circular mean of phase difference (radians)

    Returns:
        anti_phase_error: Deviation from anti-phase in radians [0, π]
            0: perfect anti-phase
            small values: normal gait pattern
            large values: abnormal coordination
    """
    # Target for anti-phase is π
    target_antiphase = np.pi

    # Compute angular distance
    error = angular_distance(mean_phase_diff, target_antiphase)

    return error


def check_frequency_matching(
    freq_left: float,
    freq_right: float,
    tolerance: float = 0.03,
) -> Tuple[bool, float, float]:
    """
    Check if frequencies of both feet are compatible for phase analysis.

    Phase synchronization metrics (like PLV) are only interpretable when
    the frequencies of both oscillators are similar. If frequencies differ
    significantly, the phase difference will drift over time and PLV loses meaning.

    CORRECTED: Tolerance reduced from 5% to 3% for more conservative matching.
    Justification: Literature shows that frequency differences >3% indicate
    pathological asymmetry where 1:1 phase locking is unlikely (Pikovsky et al., 2001).

    Args:
        freq_left: Mean instantaneous frequency of left foot (Hz)
        freq_right: Mean instantaneous frequency of right foot (Hz)
        tolerance: Maximum relative frequency difference (default: 0.03 = 3%)

    Returns:
        is_matched: True if frequencies are compatible
        freq_diff: Absolute frequency difference (Hz)
        freq_ratio: Relative frequency difference (dimensionless)
    """
    # Absolute difference
    freq_diff = np.abs(freq_left - freq_right)

    # Mean frequency
    freq_mean = (freq_left + freq_right) / 2.0

    # Relative difference
    freq_ratio = freq_diff / freq_mean if freq_mean > 0 else np.inf

    # Check tolerance
    is_matched = freq_ratio < tolerance

    return is_matched, freq_diff, freq_ratio


def analyze_phase_synchronization(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    freq_left: float,
    freq_right: float,
    validity_mask: np.ndarray = None,
    freq_tolerance: float = 0.03,
) -> Dict:
    """
    Comprehensive phase synchronization analysis for gait coordination.

    This function integrates all synchronization metrics:
    1. Frequency matching check
    2. Phase difference computation
    3. Circular statistics
    4. Phase Locking Value
    5. Anti-phase error

    CORRECTED: Default tolerance reduced from 5% to 3% for more conservative matching.

    Args:
        phase_left: Wrapped phase of left foot [-π, π]
        phase_right: Wrapped phase of right foot [-π, π]
        freq_left: Mean instantaneous frequency of left foot (Hz)
        freq_right: Mean instantaneous frequency of right foot (Hz)
        validity_mask: Boolean mask for valid samples (optional)
        freq_tolerance: Tolerance for frequency matching (default: 0.03 = 3%)

    Returns:
        metrics: Dictionary with synchronization metrics
    """
    # Check frequency matching
    is_freq_matched, freq_diff, freq_ratio = check_frequency_matching(
        freq_left, freq_right, freq_tolerance
    )

    if not is_freq_matched:
        warnings.warn(
            f"Frequency mismatch detected: {freq_left:.3f} Hz vs {freq_right:.3f} Hz "
            f"({freq_ratio*100:.1f}% difference). PLV may not be reliable."
        )

    # Apply validity mask if provided
    if validity_mask is not None:
        phase_left = phase_left[validity_mask]
        phase_right = phase_right[validity_mask]
        valid_samples = np.sum(validity_mask)
        valid_fraction = valid_samples / len(validity_mask)
    else:
        valid_samples = len(phase_left)
        valid_fraction = 1.0

    # Compute phase difference
    phase_diff = compute_phase_difference(phase_left, phase_right)

    # Circular statistics on phase difference
    mean_phase_diff = circular_mean(phase_diff)
    circ_variance = circular_variance(phase_diff)
    circ_std = circular_std(phase_diff)

    # Phase Locking Value
    plv = compute_plv(phase_diff)

    # Anti-phase error
    anti_phase_error = compute_anti_phase_error(mean_phase_diff)

    # Compile metrics
    metrics = {
        # Frequency metrics
        "freq_left": freq_left,
        "freq_right": freq_right,
        "freq_diff": freq_diff,
        "freq_ratio": freq_ratio,
        "frequency_match_flag": is_freq_matched,
        # Phase synchronization metrics
        "plv": plv,
        "mean_phase_diff": mean_phase_diff,
        "anti_phase_error": anti_phase_error,
        "circular_variance": circ_variance,
        "circular_std": circ_std,
        # Validity metrics
        "valid_samples_sync": valid_samples,
        "valid_fraction_sync": valid_fraction,
    }

    return metrics
