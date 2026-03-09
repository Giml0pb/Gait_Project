"""
Dominant frequency detection for gait rhythm analysis.

This module identifies the dominant gait frequency and computes related
spectral characteristics (peak width, energy concentration).
"""

import numpy as np
from typing import Tuple


def find_dominant_frequency(
    freqs: np.ndarray,
    psd: np.ndarray,
    freq_range: Tuple[float, float] = (0.5, 3.0),
) -> float:
    """
    Find the dominant frequency within the physiological gait range.

    Args:
        freqs: Frequency vector from PSD
        psd: Power spectral density
        freq_range: Physiological range for gait frequency (default: 0.5-3.0 Hz)

    Returns:
        dominant_freq: Dominant frequency in Hz
    """
    # Restrict search to physiological range
    mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
    freqs_range = freqs[mask]
    psd_range = psd[mask]

    # Find peak
    peak_idx = np.argmax(psd_range)
    dominant_freq = freqs_range[peak_idx]

    return dominant_freq


def compute_spectral_peak_width(
    freqs: np.ndarray, psd: np.ndarray, dominant_freq: float, threshold: float = 0.5
) -> float:
    """
    Compute the width of the spectral peak at a given threshold.

    Args:
        freqs: Frequency vector
        psd: Power spectral density
        dominant_freq: Dominant frequency (peak location)
        threshold: Relative threshold for width computation (default: 0.5 = half-max)

    Returns:
        peak_width: Width of the spectral peak in Hz
    """
    # Find closest index to dominant frequency
    peak_idx = np.argmin(np.abs(freqs - dominant_freq))
    peak_value = psd[peak_idx]

    # Find indices where PSD > threshold * peak_value
    threshold_value = threshold * peak_value
    above_threshold = psd > threshold_value

    # Find contiguous region around peak
    # Search left
    left_idx = peak_idx
    while left_idx > 0 and above_threshold[left_idx]:
        left_idx -= 1

    # Search right
    right_idx = peak_idx
    while right_idx < len(psd) - 1 and above_threshold[right_idx]:
        right_idx += 1

    # Compute width
    peak_width = freqs[right_idx] - freqs[left_idx]

    return peak_width


def compute_energy_ratio(
    freqs: np.ndarray,
    psd: np.ndarray,
    dominant_freq: float,
    bandwidth: float = 0.5,
) -> float:
    """
    Compute the ratio of energy in the dominant band to total energy.

    Args:
        freqs: Frequency vector
        psd: Power spectral density
        dominant_freq: Dominant frequency
        bandwidth: Bandwidth around dominant frequency (default: ±0.5 Hz)

    Returns:
        energy_ratio: Ratio of band energy to total energy (0-1)
    """
    # Define band around dominant frequency
    lower_bound = dominant_freq - bandwidth
    upper_bound = dominant_freq + bandwidth

    # Compute energy in band
    band_mask = (freqs >= lower_bound) & (freqs <= upper_bound)
    band_energy = np.trapezoid(psd[band_mask], freqs[band_mask])

    # Compute total energy
    total_energy = np.trapezoid(psd, freqs)

    # Energy ratio
    energy_ratio = band_energy / total_energy if total_energy > 0 else 0.0

    return energy_ratio


def compute_spectral_snr(
    freqs: np.ndarray,
    psd: np.ndarray,
    dominant_freq: float,
    freq_range: Tuple[float, float] = (0.5, 3.0),
    peak_window: float = 0.2,
) -> float:
    """
    Compute spectral signal-to-noise ratio.

    SNR is defined as the ratio of power at the dominant frequency to the
    mean power outside the peak window within the locomotor band.

    Args:
        freqs: Frequency vector
        psd: Power spectral density
        dominant_freq: Dominant frequency
        freq_range: Locomotor frequency band (default: 0.5-3.0 Hz)
        peak_window: Exclusion window around f0 in Hz (default: ±0.2 Hz)

    Returns:
        snr: Spectral signal-to-noise ratio
    """
    # Find power at dominant frequency
    f0_idx = np.argmin(np.abs(freqs - dominant_freq))
    power_at_f0 = psd[f0_idx]

    # Define locomotor band mask
    band_mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])

    # Define peak exclusion window
    peak_mask = (freqs >= dominant_freq - peak_window) & (
        freqs <= dominant_freq + peak_window
    )

    # Combine: inside band but outside peak
    background_mask = band_mask & (~peak_mask)

    # Compute mean background power
    mean_background_power = np.mean(psd[background_mask])

    # SNR
    snr = power_at_f0 / mean_background_power if mean_background_power > 0 else 0.0

    return snr


def compute_spectral_metrics(
    freqs: np.ndarray,
    psd: np.ndarray,
    freq_range: Tuple[float, float] = (0.5, 3.0),
    threshold: float = 0.5,
    bandwidth: float = 0.5,
) -> Tuple[float, float, float]:
    """
    Compute all spectral metrics for gait analysis.

    Args:
        freqs: Frequency vector
        psd: Power spectral density
        freq_range: Physiological range for gait frequency
        threshold: Threshold for peak width computation
        bandwidth: Bandwidth for energy ratio computation

    Returns:
        dominant_freq: Dominant frequency in Hz
        peak_width: Width of spectral peak in Hz
        energy_ratio: Ratio of band energy to total energy
    """
    dominant_freq = find_dominant_frequency(freqs, psd, freq_range)
    peak_width = compute_spectral_peak_width(freqs, psd, dominant_freq, threshold)
    energy_ratio = compute_energy_ratio(freqs, psd, dominant_freq, bandwidth)

    return dominant_freq, peak_width, energy_ratio
