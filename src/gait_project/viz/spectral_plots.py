"""
Spectral analysis visualization functions.

Plots for power spectral density and time-frequency representations.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def plot_psd(
    freqs: np.ndarray,
    psd: np.ndarray,
    dominant_freq: Optional[float] = None,
    freq_range: Optional[Tuple[float, float]] = None,
    title: str = "Power Spectral Density",
    figsize: Tuple[int, int] = (10, 5),
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """
    Plot power spectral density.

    Args:
        freqs: Frequency vector
        psd: Power spectral density values
        dominant_freq: Dominant frequency to mark (optional)
        freq_range: Frequency range to display (optional)
        title: Plot title
        figsize: Figure size
        ax: Existing axes (optional)

    Returns:
        fig: Matplotlib figure object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    ax.plot(freqs, psd, linewidth=1.5, color="navy")

    # Mark dominant frequency
    if dominant_freq is not None:
        ax.axvline(
            dominant_freq,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"f₀ = {dominant_freq:.2f} Hz",
        )
        ax.legend()

    # Set frequency range
    if freq_range is not None:
        ax.set_xlim(freq_range)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power Spectral Density")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_dual_psd(
    freqs: np.ndarray,
    psd1: np.ndarray,
    psd2: np.ndarray,
    label1: str = "Left Foot",
    label2: str = "Right Foot",
    dominant_freq1: Optional[float] = None,
    dominant_freq2: Optional[float] = None,
    freq_range: Optional[Tuple[float, float]] = (0, 5),
    title: str = "Power Spectral Density Comparison",
    figsize: Tuple[int, int] = (10, 5),
) -> plt.Figure:
    """
    Plot two PSDs for comparison.

    Args:
        freqs: Frequency vector
        psd1: First PSD
        psd2: Second PSD
        label1: Label for first PSD
        label2: Label for second PSD
        dominant_freq1: Dominant frequency for first signal
        dominant_freq2: Dominant frequency for second signal
        freq_range: Frequency range to display
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(freqs, psd1, linewidth=1.5, label=label1, alpha=0.8)
    ax.plot(freqs, psd2, linewidth=1.5, label=label2, alpha=0.8)

    # Mark dominant frequencies
    if dominant_freq1 is not None:
        ax.axvline(dominant_freq1, color="C0", linestyle=":", linewidth=2, alpha=0.7)
    if dominant_freq2 is not None:
        ax.axvline(dominant_freq2, color="C1", linestyle=":", linewidth=2, alpha=0.7)

    if freq_range is not None:
        ax.set_xlim(freq_range)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power Spectral Density")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_spectrogram(
    freqs: np.ndarray,
    times: np.ndarray,
    Sxx: np.ndarray,
    freq_range: Optional[Tuple[float, float]] = (0, 5),
    title: str = "Spectrogram",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot time-frequency spectrogram.

    Args:
        freqs: Frequency vector
        times: Time vector
        Sxx: Spectrogram matrix (2D)
        freq_range: Frequency range to display
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot spectrogram
    im = ax.pcolormesh(
        times, freqs, 10 * np.log10(Sxx), shading="gouraud", cmap="viridis"
    )

    # Set frequency range
    if freq_range is not None:
        ax.set_ylim(freq_range)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(title)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Power (dB)")

    plt.tight_layout()

    return fig
