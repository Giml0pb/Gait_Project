"""
Hilbert transform for instantaneous phase and amplitude extraction.

This module implements the analytic signal approach for extracting
instantaneous attributes from narrowband oscillatory signals.
"""

import numpy as np
from scipy import signal


def compute_analytic_signal(data: np.ndarray) -> np.ndarray:
    """
    Compute the analytic signal using Hilbert transform.

    The analytic signal z(t) = x(t) + i*H[x(t)] is a complex-valued
    signal from which instantaneous amplitude and phase can be extracted.

    Args:
        data: Real-valued input signal

    Returns:
        analytic_signal: Complex-valued analytic signal
    """
    analytic_signal = signal.hilbert(data)
    return analytic_signal


def compute_instantaneous_amplitude(analytic_signal: np.ndarray) -> np.ndarray:
    """
    Extract instantaneous amplitude from analytic signal.

    Args:
        analytic_signal: Complex-valued analytic signal

    Returns:
        amplitude: Instantaneous amplitude (envelope)
    """
    amplitude = np.abs(analytic_signal)
    return amplitude


def compute_instantaneous_phase(
    analytic_signal: np.ndarray, unwrap: bool = False
) -> np.ndarray:
    """
    Extract instantaneous phase from analytic signal.

    Args:
        analytic_signal: Complex-valued analytic signal
        unwrap: If True, unwrap phase to avoid 2π discontinuities

    Returns:
        phase: Instantaneous phase in radians
    """
    phase = np.angle(analytic_signal)

    if unwrap:
        phase = np.unwrap(phase)

    return phase


def compute_instantaneous_frequency(
    analytic_signal: np.ndarray, fs: float, unwrap: bool = True
) -> np.ndarray:
    """
    Compute instantaneous frequency from analytic signal.

    Instantaneous frequency is the time derivative of the unwrapped phase,
    scaled by 1/(2π). Uses central differences (gradient) for better
    noise performance compared to forward differences.

    Args:
        analytic_signal: Complex-valued analytic signal
        fs: Sampling frequency in Hz
        unwrap: If True, unwrap phase before differentiation (recommended)

    Returns:
        inst_freq: Instantaneous frequency in Hz
    """
    # Extract and unwrap phase
    phase = np.angle(analytic_signal)
    if unwrap:
        phase = np.unwrap(phase)

    # Compute time derivative of phase using central differences
    # np.gradient is more robust to noise than np.diff
    dt = 1.0 / fs
    phase_derivative = np.gradient(phase, dt)

    # Instantaneous frequency in Hz
    inst_freq = phase_derivative / (2 * np.pi)

    return inst_freq


def compute_all_instantaneous_attributes(
    data: np.ndarray, fs: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute all instantaneous attributes in one call.

    Args:
        data: Real-valued input signal
        fs: Sampling frequency in Hz

    Returns:
        amplitude: Instantaneous amplitude
        phase: Instantaneous phase (wrapped, radians)
        phase_unwrapped: Unwrapped phase (radians)
        frequency: Instantaneous frequency (Hz)
    """
    analytic_signal = compute_analytic_signal(data)
    amplitude = compute_instantaneous_amplitude(analytic_signal)
    phase = compute_instantaneous_phase(analytic_signal, unwrap=False)
    phase_unwrapped = np.unwrap(phase)
    frequency = compute_instantaneous_frequency(analytic_signal, fs, unwrap=True)

    return amplitude, phase, phase_unwrapped, frequency
