"""
Power Spectral Density analysis for gait signals.

This module implements Welch's method for PSD estimation and time-frequency
analysis via spectrograms.
"""

import numpy as np
from scipy import signal
from typing import Tuple


def compute_psd(
    data: np.ndarray,
    fs: float,
    nperseg: int = 256,
    noverlap: int = None,
    window: str = "hann",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Power Spectral Density using Welch's method.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        nperseg: Length of each segment for Welch's method
        noverlap: Number of points to overlap between segments (default: nperseg // 2)
        window: Window function to use

    Returns:
        freqs: Frequency vector
        psd: Power spectral density
    """
    if noverlap is None:
        noverlap = nperseg // 2

    freqs, psd = signal.welch(
        data, fs=fs, nperseg=nperseg, noverlap=noverlap, window=window
    )

    return freqs, psd


def compute_spectrogram(
    data: np.ndarray,
    fs: float,
    nperseg: int = 256,
    noverlap: int = None,
    window: str = "hann",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute spectrogram (time-frequency representation).

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        nperseg: Length of each segment
        noverlap: Number of points to overlap between segments
        window: Window function to use

    Returns:
        freqs: Frequency vector
        times: Time vector
        Sxx: Spectrogram (2D array)
    """
    if noverlap is None:
        noverlap = nperseg // 2

    freqs, times, Sxx = signal.spectrogram(
        data, fs=fs, nperseg=nperseg, noverlap=noverlap, window=window
    )

    return freqs, times, Sxx
