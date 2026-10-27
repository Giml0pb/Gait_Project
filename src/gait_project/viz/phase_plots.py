"""
Phase analysis visualization functions.

Plots for instantaneous phase, phase difference, and synchronization metrics.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def plot_instantaneous_phase(
    time: np.ndarray,
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    unwrap: bool = True,
    title: str = "Instantaneous Phase",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot instantaneous phase for both feet.

    Args:
        time: Time vector
        phase_left: Left foot instantaneous phase
        phase_right: Right foot instantaneous phase
        unwrap: Whether to unwrap phase
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    if unwrap:
        phase_left = np.unwrap(phase_left)
        phase_right = np.unwrap(phase_right)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, phase_left, label="Left Foot", linewidth=1.2, alpha=0.8)
    ax.plot(time, phase_right, label="Right Foot", linewidth=1.2, alpha=0.8)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Phase (radians)" if not unwrap else "Unwrapped Phase (radians)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_phase_difference(
    time: np.ndarray,
    phase_diff: np.ndarray,
    mean_phase: Optional[float] = None,
    title: str = "Inter-Foot Phase Difference",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot phase difference between feet.

    Args:
        time: Time vector
        phase_diff: Phase difference Δφ(t)
        mean_phase: Mean relative phase to mark (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, phase_diff, linewidth=1.0, color="purple", alpha=0.8)

    # Mark mean phase
    if mean_phase is not None:
        ax.axhline(
            mean_phase,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean Δφ = {mean_phase:.2f} rad",
        )
        ax.legend()

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Phase Difference Δφ (radians)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_plv_temporal(
    time: np.ndarray,
    plv_values: np.ndarray,
    global_plv: Optional[float] = None,
    title: str = "Temporal Phase Locking Value",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot windowed PLV over time.

    Args:
        time: Time vector (window centers)
        plv_values: PLV values over time
        global_plv: Global PLV to mark (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, plv_values, linewidth=2, color="darkgreen", marker="o", markersize=4)

    # Mark global PLV
    if global_plv is not None:
        ax.axhline(
            global_plv,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Global PLV = {global_plv:.3f}",
        )
        ax.legend()

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("PLV")
    ax.set_ylim([0, 1])
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_phase_portrait(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    title: str = "Phase Portrait",
    figsize: Tuple[int, int] = (8, 8),
) -> plt.Figure:
    """
    Plot phase portrait (phase space plot).

    Args:
        phase_left: Left foot phase
        phase_right: Right foot phase
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Wrap phases to [-π, π]
    phase_left_wrapped = np.arctan2(np.sin(phase_left), np.cos(phase_left))
    phase_right_wrapped = np.arctan2(np.sin(phase_right), np.cos(phase_right))

    # Plot trajectory
    scatter = ax.scatter(
        phase_left_wrapped,
        phase_right_wrapped,
        c=np.arange(len(phase_left)),
        cmap="viridis",
        s=10,
        alpha=0.6,
    )

    # Add colorbar for time
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Time (samples)")

    # Add diagonal (perfect synchrony)
    ax.plot([-np.pi, np.pi], [-np.pi, np.pi], "r--", linewidth=1.5, label="φ_L = φ_R")

    ax.set_xlabel("Left Foot Phase (radians)")
    ax.set_ylabel("Right Foot Phase (radians)")
    ax.set_xlim([-np.pi, np.pi])
    ax.set_ylim([-np.pi, np.pi])
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()

    return fig


def plot_instantaneous_frequency(
    time: np.ndarray,
    freq_left: np.ndarray,
    freq_right: np.ndarray,
    title: str = "Instantaneous Frequency",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot instantaneous frequency for both feet.

    Args:
        time: Time vector
        freq_left: Left foot instantaneous frequency
        freq_right: Right foot instantaneous frequency
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, freq_left, label="Left Foot", linewidth=1.0, alpha=0.8)
    ax.plot(time, freq_right, label="Right Foot", linewidth=1.0, alpha=0.8)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Instantaneous Frequency (Hz)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


# ==============================================================================
# PHASE 2 SPECIFIC VISUALIZATIONS
# ==============================================================================


def plot_signal_vs_filtered(
    time: np.ndarray,
    signal_original: np.ndarray,
    signal_filtered: np.ndarray,
    f0: float,
    bandwidth: float,
    title: str = "Original vs Narrowband Filtered Signal",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot original signal vs narrowband filtered signal.

    Args:
        time: Time vector
        signal_original: Original preprocessed signal
        signal_filtered: Narrowband filtered signal
        f0: Center frequency of filter (Hz)
        bandwidth: Filter bandwidth (Hz)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # Original signal
    axes[0].plot(time, signal_original, linewidth=0.8, color="steelblue", alpha=0.8)
    axes[0].set_ylabel("Angular Velocity (deg/s)")
    axes[0].set_title("Original Preprocessed Signal")
    axes[0].grid(True, alpha=0.3)

    # Filtered signal
    axes[1].plot(time, signal_filtered, linewidth=0.8, color="darkgreen")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Angular Velocity (deg/s)")
    axes[1].set_title(
        f"Narrowband Filtered [{f0 - bandwidth:.2f} - {f0 + bandwidth:.2f} Hz]"
    )
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    return fig


def plot_filtered_and_envelope(
    time: np.ndarray,
    signal_filtered: np.ndarray,
    amplitude: np.ndarray,
    title: str = "Filtered Signal with Instantaneous Amplitude Envelope",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot filtered signal with instantaneous amplitude envelope.

    Args:
        time: Time vector
        signal_filtered: Narrowband filtered signal
        amplitude: Instantaneous amplitude (envelope)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Filtered signal
    ax.plot(
        time,
        signal_filtered,
        linewidth=0.8,
        color="steelblue",
        alpha=0.7,
        label="Filtered signal",
    )

    # Envelope
    ax.plot(
        time, amplitude, linewidth=1.5, color="red", label="Instantaneous amplitude"
    )
    ax.plot(time, -amplitude, linewidth=1.5, color="red", linestyle="--", alpha=0.7)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Angular Velocity (deg/s)")
    ax.set_title(title, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_wrapped_phase(
    time: np.ndarray,
    phase_wrapped: np.ndarray,
    title: str = "Instantaneous Phase (Wrapped)",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot wrapped instantaneous phase.

    Args:
        time: Time vector
        phase_wrapped: Wrapped phase in radians [-π, π]
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(
        time,
        phase_wrapped,
        linewidth=1.0,
        color="purple",
        marker=".",
        markersize=2,
        alpha=0.7,
    )

    # Mark π boundaries
    ax.axhline(
        np.pi,
        color="red",
        linestyle="--",
        linewidth=1,
        alpha=0.5,
        label="±π boundaries",
    )
    ax.axhline(-np.pi, color="red", linestyle="--", linewidth=1, alpha=0.5)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Phase (radians)")
    ax.set_ylim([-np.pi - 0.5, np.pi + 0.5])
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_unwrapped_phase(
    time: np.ndarray,
    phase_unwrapped: np.ndarray,
    title: str = "Instantaneous Phase (Unwrapped)",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot unwrapped instantaneous phase.

    Args:
        time: Time vector
        phase_unwrapped: Unwrapped phase in radians
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, phase_unwrapped, linewidth=1.2, color="darkblue")

    # Calculate and show slope (should be approximately constant)
    slope = np.polyfit(time, phase_unwrapped, 1)[0]
    expected_freq = slope / (2 * np.pi)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Unwrapped Phase (radians)")
    ax.set_title(title, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Add text annotation
    ax.text(
        0.02,
        0.98,
        f"Slope: {slope:.2f} rad/s\nExpected freq: {expected_freq:.3f} Hz",
        transform=ax.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        fontsize=9,
    )

    plt.tight_layout()

    return fig


def plot_instantaneous_frequency_single(
    time: np.ndarray,
    inst_freq: np.ndarray,
    f0: Optional[float] = None,
    mean_freq: Optional[float] = None,
    validity_mask: Optional[np.ndarray] = None,
    title: str = "Instantaneous Frequency",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot instantaneous frequency for a single signal.

    Args:
        time: Time vector
        inst_freq: Instantaneous frequency in Hz
        f0: Spectral f0 to mark (optional)
        mean_freq: Mean instantaneous frequency to mark (optional)
        validity_mask: Boolean mask indicating valid samples (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot full instantaneous frequency
    ax.plot(
        time,
        inst_freq,
        linewidth=1.0,
        color="darkgreen",
        alpha=0.8,
        label="Instantaneous frequency",
    )

    # Highlight valid region if mask is provided
    if validity_mask is not None:
        # Find contiguous valid regions
        invalid_mask = ~validity_mask

        # Shade invalid regions
        if np.any(invalid_mask):
            # Create a copy of time and inst_freq for masking
            time_invalid = time.copy()
            time_invalid[validity_mask] = np.nan

            # Plot invalid regions with different style
            ax.plot(
                time_invalid,
                inst_freq,
                linewidth=1.0,
                color="gray",
                alpha=0.3,
                label="Excluded samples",
            )

            # Add vertical spans for excluded regions at edges
            # Find first and last valid indices
            valid_indices = np.where(validity_mask)[0]
            if len(valid_indices) > 0:
                first_valid = valid_indices[0]
                last_valid = valid_indices[-1]

                # Shade before first valid
                if first_valid > 0:
                    ax.axvspan(
                        time[0],
                        time[first_valid],
                        alpha=0.1,
                        color="red",
                        label="Edge artifacts" if first_valid > 0 else "",
                    )

                # Shade after last valid
                if last_valid < len(time) - 1:
                    ax.axvspan(time[last_valid], time[-1], alpha=0.1, color="red")

    # Mark f0 from spectral analysis
    if f0 is not None:
        ax.axhline(
            f0,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=f"Spectral f₀ = {f0:.3f} Hz",
        )

    # Mark mean instantaneous frequency
    if mean_freq is not None:
        ax.axhline(
            mean_freq,
            color="blue",
            linestyle=":",
            linewidth=2,
            alpha=0.7,
            label=f"Mean inst. freq = {mean_freq:.3f} Hz",
        )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Instantaneous Frequency (Hz)")
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)

    # Set reasonable y-limits (gait frequency range)
    ax.set_ylim([0, 3])

    plt.tight_layout()

    return fig


def plot_frequency_comparison(
    f0_spectral: float,
    mean_inst_freq: float,
    std_inst_freq: float,
    title: str = "Frequency Comparison: Spectral vs Hilbert",
    figsize: Tuple[int, int] = (8, 6),
) -> plt.Figure:
    """
    Plot comparison between spectral f0 and instantaneous frequency metrics.

    Args:
        f0_spectral: Dominant frequency from spectral analysis (Hz)
        mean_inst_freq: Mean instantaneous frequency (Hz)
        std_inst_freq: Standard deviation of instantaneous frequency (Hz)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    methods = ["Spectral\n(Welch PSD)", "Hilbert\n(Mean Inst. Freq)"]
    frequencies = [f0_spectral, mean_inst_freq]
    colors = ["steelblue", "darkgreen"]

    bars = ax.bar(
        methods, frequencies, color=colors, alpha=0.7, edgecolor="black", linewidth=1.5
    )

    # Add error bar for instantaneous frequency
    ax.errorbar(
        [1],
        [mean_inst_freq],
        yerr=[std_inst_freq],
        fmt="none",
        color="black",
        capsize=10,
        linewidth=2,
    )

    ax.set_ylabel("Frequency (Hz)", fontsize=12)
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar, freq in zip(bars, frequencies):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{freq:.3f} Hz",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11,
        )

    # Add coherence annotation
    relative_error = abs(f0_spectral - mean_inst_freq) / f0_spectral * 100
    coherence_text = f"Relative difference: {relative_error:.1f}%"
    if relative_error < 5:
        coherence_text += " (Excellent)"
        color = "green"
    elif relative_error < 15:
        coherence_text += " (Good)"
        color = "orange"
    else:
        coherence_text += " (Poor - check signal)"
        color = "red"

    ax.text(
        0.5,
        0.95,
        coherence_text,
        transform=ax.transAxes,
        ha="center",
        va="top",
        bbox=dict(boxstyle="round", facecolor=color, alpha=0.3),
        fontsize=10,
        fontweight="bold",
    )

    plt.tight_layout()

    return fig
