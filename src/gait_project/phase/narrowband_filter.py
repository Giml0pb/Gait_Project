"""
Narrowband filtering for quasi-monocomponent signal extraction.

This module implements bandpass filtering around the dominant gait frequency
to obtain a narrowband signal suitable for Hilbert transform analysis.
"""

import numpy as np
from scipy import signal


def apply_narrowband_filter(
    data: np.ndarray,
    fs: float,
    center_freq: float,
    bandwidth: float = 0.3,
    filter_order: int = 4,
) -> np.ndarray:
    """
    Apply narrowband bandpass filter around dominant frequency.

    Creates a quasi-monocomponent signal by filtering around the dominant
    gait frequency, which is suitable for Hilbert transform analysis.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        center_freq: Center frequency (dominant frequency) in Hz
        bandwidth: Bandwidth on each side of center frequency (default: 0.3 Hz)
                  Recommended: 0.25-0.4 Hz for typical gait signals
        filter_order: Order of Butterworth filter (default: 4)

    Returns:
        filtered_signal: Narrowband filtered signal
    """
    # Define bandpass range
    lowcut = center_freq - bandwidth
    highcut = center_freq + bandwidth

    # Validate frequency bounds
    if lowcut <= 0:
        raise ValueError(
            f"Low cutoff frequency {lowcut} Hz must be positive. "
            f"Reduce bandwidth or increase center frequency."
        )

    # Ensure frequencies are within Nyquist limit
    nyquist = fs / 2
    if highcut >= nyquist:
        raise ValueError(
            f"High cutoff frequency {highcut} Hz exceeds Nyquist frequency {nyquist} Hz"
        )

    # Design Butterworth bandpass filter
    sos = signal.butter(
        filter_order, [lowcut, highcut], btype="band", fs=fs, output="sos"
    )

    # Apply zero-phase filter (filtfilt to avoid phase distortion)
    filtered_signal = signal.sosfiltfilt(sos, data)

    return filtered_signal


def design_narrowband_filter(
    fs: float,
    center_freq: float,
    bandwidth: float = 0.5,
    filter_order: int = 4,
) -> np.ndarray:
    """
    Design narrowband bandpass filter coefficients.

    Useful for applying the same filter to multiple signals.

    Args:
        fs: Sampling frequency in Hz
        center_freq: Center frequency in Hz
        bandwidth: Bandwidth on each side of center frequency
        filter_order: Order of Butterworth filter

    Returns:
        sos: Second-order sections representation of filter
    """
    lowcut = center_freq - bandwidth
    highcut = center_freq + bandwidth

    nyquist = fs / 2
    if highcut >= nyquist:
        raise ValueError(
            f"High cutoff frequency {highcut} Hz exceeds Nyquist frequency {nyquist} Hz"
        )

    sos = signal.butter(
        filter_order, [lowcut, highcut], btype="band", fs=fs, output="sos"
    )

    return sos
