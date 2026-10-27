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

    data = np.asarray(data, dtype=float)
    if data.ndim != 1 or len(data) < 4 or not np.isfinite(data).all():
        raise ValueError(
            "PSD requires a finite one-dimensional signal with at least four samples"
        )
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("Sampling frequency must be positive and finite")
    nperseg = min(nperseg, len(data))
    noverlap = min(noverlap, nperseg - 1)

    freqs, psd = signal.welch(
        data, fs=fs, nperseg=nperseg, noverlap=noverlap, window=window
    )

    return freqs, psd


def compute_segmented_psd(data, segments, fs, nperseg=256, noverlap=128):
    """Average Welch estimates without allowing a window to cross a turn."""
    nperseg = min(nperseg, *(len(data[segment]) for segment in segments))
    noverlap = min(noverlap, nperseg - 1)
    spectra, weights = [], []
    for segment in segments:
        part = data[segment]
        freqs, psd = compute_psd(part, fs, nperseg, noverlap)
        spectra.append(psd)
        weights.append(1 + (len(part) - nperseg) // (nperseg - noverlap))
    return freqs, np.average(spectra, axis=0, weights=weights)


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
