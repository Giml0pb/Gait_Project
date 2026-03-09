"""
Signal cleaning and preprocessing functions.

This module implements detrending, mean removal, and filtering operations
for gait signal preprocessing.
"""

import numpy as np
from scipy import signal
from typing import Optional


def detrend_signal(data: np.ndarray, method: str = "linear") -> np.ndarray:
    """
    Remove trend from signal.

    Args:
        data: Input signal
        method: Detrending method ('linear' or 'constant')

    Returns:
        detrended_signal: Signal with trend removed
    """
    if method == "linear":
        detrended = signal.detrend(data, type="linear")
    elif method == "constant":
        detrended = signal.detrend(data, type="constant")
    else:
        raise ValueError(f"Unknown detrending method: {method}")

    return detrended


def remove_mean(data: np.ndarray) -> np.ndarray:
    """
    Remove mean (center signal at zero).

    Args:
        data: Input signal

    Returns:
        centered_signal: Zero-mean signal
    """
    return data - np.mean(data)


def bandpass_filter(
    data: np.ndarray,
    fs: float,
    lowcut: float,
    highcut: float,
    filter_order: int = 4,
) -> np.ndarray:
    """
    Apply bandpass filter to signal.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        lowcut: Low cutoff frequency in Hz
        highcut: High cutoff frequency in Hz
        filter_order: Order of Butterworth filter

    Returns:
        filtered_signal: Bandpass filtered signal
    """
    nyquist = fs / 2

    if highcut >= nyquist:
        raise ValueError(
            f"High cutoff {highcut} Hz must be less than Nyquist frequency {nyquist} Hz"
        )

    if lowcut >= highcut:
        raise ValueError(
            f"Low cutoff {lowcut} Hz must be less than high cutoff {highcut} Hz"
        )

    # Design Butterworth filter
    sos = signal.butter(
        filter_order, [lowcut, highcut], btype="band", fs=fs, output="sos"
    )

    # Apply zero-phase filter
    filtered_signal = signal.sosfiltfilt(sos, data)

    return filtered_signal


def lowpass_filter(
    data: np.ndarray, fs: float, cutoff: float, filter_order: int = 4
) -> np.ndarray:
    """
    Apply lowpass filter to signal.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        cutoff: Cutoff frequency in Hz
        filter_order: Order of Butterworth filter

    Returns:
        filtered_signal: Lowpass filtered signal
    """
    nyquist = fs / 2

    if cutoff >= nyquist:
        raise ValueError(
            f"Cutoff {cutoff} Hz must be less than Nyquist frequency {nyquist} Hz"
        )

    sos = signal.butter(filter_order, cutoff, btype="low", fs=fs, output="sos")
    filtered_signal = signal.sosfiltfilt(sos, data)

    return filtered_signal


def highpass_filter(
    data: np.ndarray, fs: float, cutoff: float, filter_order: int = 4
) -> np.ndarray:
    """
    Apply highpass filter to signal.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        cutoff: Cutoff frequency in Hz
        filter_order: Order of Butterworth filter

    Returns:
        filtered_signal: Highpass filtered signal
    """
    nyquist = fs / 2

    if cutoff >= nyquist:
        raise ValueError(
            f"Cutoff {cutoff} Hz must be less than Nyquist frequency {nyquist} Hz"
        )

    sos = signal.butter(filter_order, cutoff, btype="high", fs=fs, output="sos")
    filtered_signal = signal.sosfiltfilt(sos, data)

    return filtered_signal


def preprocess_signal(
    data: np.ndarray,
    fs: float,
    detrend: bool = True,
    center: bool = True,
    filter_type: Optional[str] = None,
    filter_params: Optional[dict] = None,
) -> np.ndarray:
    """
    Apply complete preprocessing pipeline to signal.

    Args:
        data: Input signal
        fs: Sampling frequency in Hz
        detrend: Whether to detrend signal
        center: Whether to remove mean
        filter_type: Type of filter ('bandpass', 'lowpass', 'highpass', or None)
        filter_params: Dictionary of filter parameters (e.g., {'lowcut': 0.5, 'highcut': 5.0})

    Returns:
        processed_signal: Preprocessed signal
    """
    processed = data.copy()

    # Detrend
    if detrend:
        processed = detrend_signal(processed, method="linear")

    # Center
    if center:
        processed = remove_mean(processed)

    # Filter
    if filter_type is not None and filter_params is not None:
        if filter_type == "bandpass":
            lowcut = filter_params.get("lowcut")
            highcut = filter_params.get("highcut")
            order = filter_params.get("order", 4)
            if lowcut is None or highcut is None:
                raise ValueError(
                    "Bandpass filter requires 'lowcut' and 'highcut' parameters"
                )
            processed = bandpass_filter(processed, fs, lowcut, highcut, order)

        elif filter_type == "lowpass":
            cutoff = filter_params.get("cutoff")
            order = filter_params.get("order", 4)
            if cutoff is None:
                raise ValueError("Lowpass filter requires 'cutoff' parameter")
            processed = lowpass_filter(processed, fs, cutoff, order)

        elif filter_type == "highpass":
            cutoff = filter_params.get("cutoff")
            order = filter_params.get("order", 4)
            if cutoff is None:
                raise ValueError("Highpass filter requires 'cutoff' parameter")
            processed = highpass_filter(processed, fs, cutoff, order)

        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

    return processed
