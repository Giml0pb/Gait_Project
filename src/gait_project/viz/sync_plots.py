"""
Visualization functions for phase synchronization analysis.

This module provides specialized plots for analyzing coordination between
two oscillatory signals (left and right foot in gait analysis).
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def plot_phase_signals(
    time: np.ndarray,
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    title: str = "Instantaneous Phase - Both Feet",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot instantaneous phase of both feet over time.

    Args:
        time: Time vector (seconds)
        phase_left: Wrapped phase of left foot [-π, π]
        phase_right: Wrapped phase of right foot [-π, π]
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, phase_left, label="Left Foot", linewidth=1.2, alpha=0.8, color="blue")
    ax.plot(
        time, phase_right, label="Right Foot", linewidth=1.2, alpha=0.8, color="red"
    )

    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Phase (radians)", fontsize=12)
    ax.set_ylim([-np.pi - 0.3, np.pi + 0.3])
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_phase_difference(
    time: np.ndarray,
    phase_diff: np.ndarray,
    mean_phase_diff: Optional[float] = None,
    title: str = "Phase Difference Between Feet",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot phase difference Δφ(t) = φ_L(t) - φ_R(t) over time.

    Args:
        time: Time vector (seconds)
        phase_diff: Phase difference [-π, π]
        mean_phase_diff: Circular mean of phase difference (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, phase_diff, linewidth=1.0, color="purple", alpha=0.7, label="Δφ(t)")

    # Reference line at π (expected for anti-phase)
    ax.axhline(
        np.pi,
        color="red",
        linestyle="--",
        linewidth=2,
        alpha=0.7,
        label="Expected anti-phase (π)",
    )

    # Mean phase difference
    if mean_phase_diff is not None:
        ax.axhline(
            mean_phase_diff,
            color="darkblue",
            linestyle=":",
            linewidth=2,
            alpha=0.7,
            label=f"Mean Δφ = {mean_phase_diff:.3f} rad",
        )

    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Phase Difference Δφ (radians)", fontsize=12)
    ax.set_ylim([-np.pi - 0.3, np.pi + 0.3])
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_phase_histogram(
    phase_diff: np.ndarray,
    mean_phase_diff: Optional[float] = None,
    title: str = "Phase Difference Distribution",
    figsize: Tuple[int, int] = (10, 6),
    bins: int = 36,
) -> plt.Figure:
    """
    Plot circular histogram of phase difference.

    Args:
        phase_diff: Phase difference array [-π, π]
        mean_phase_diff: Circular mean to mark (optional)
        title: Plot title
        figsize: Figure size
        bins: Number of bins for histogram

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Create histogram
    counts, bin_edges = np.histogram(phase_diff, bins=bins, range=(-np.pi, np.pi))

    # Bin centers
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Plot as bar chart
    ax.bar(
        bin_centers,
        counts,
        width=2 * np.pi / bins,
        color="steelblue",
        alpha=0.7,
        edgecolor="black",
        linewidth=0.5,
    )

    # Mark expected anti-phase at π
    ax.axvline(
        np.pi,
        color="red",
        linestyle="--",
        linewidth=2,
        alpha=0.8,
        label="Expected anti-phase (π)",
    )

    # Mark mean phase difference
    if mean_phase_diff is not None:
        ax.axvline(
            mean_phase_diff,
            color="darkblue",
            linestyle=":",
            linewidth=2,
            alpha=0.8,
            label=f"Mean Δφ = {mean_phase_diff:.3f} rad",
        )

    ax.set_xlabel("Phase Difference Δφ (radians)", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    ax.set_xlim([-np.pi, np.pi])
    ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_xticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    return fig


def plot_phase_complex_plane(
    phase_diff: np.ndarray,
    plv: float,
    mean_phase_diff: float,
    anti_phase_error: float,
    title: str = "Phase Difference on Unit Circle (Kuramoto Representation)",
    figsize: Tuple[int, int] = (9, 9),
) -> plt.Figure:
    """
    Plot phase difference on the unit circle (Kuramoto-style representation).

    This visualization shows:
    - Each sample as a point exp(i*Δφ) on the unit circle
    - Mean resultant vector (order parameter)
    - Visual interpretation of PLV (concentration of points)

    Args:
        phase_diff: Phase difference array [-π, π]
        plv: Phase Locking Value
        mean_phase_diff: Circular mean of phase difference
        anti_phase_error: Deviation from anti-phase
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection="polar"))

    # Convert phase differences to points on unit circle
    # In polar plot: theta=phase, r=1
    ax.scatter(
        phase_diff,
        np.ones_like(phase_diff),
        c="steelblue",
        alpha=0.3,
        s=20,
        label="Phase difference samples",
    )

    # Plot mean resultant vector (order parameter)
    # This vector has direction=mean_phase_diff and magnitude=PLV
    ax.arrow(
        0,
        0,
        mean_phase_diff,
        plv,
        head_width=0.15,
        head_length=0.08,
        fc="red",
        ec="red",
        linewidth=3,
        alpha=0.8,
        label=f"Mean vector (PLV={plv:.3f})",
    )

    # Mark expected anti-phase direction (π)
    ax.plot(
        [np.pi, np.pi],
        [0, 1.0],
        color="darkgreen",
        linestyle="--",
        linewidth=2,
        alpha=0.7,
        label="Expected anti-phase (π)",
    )

    # Configure polar plot
    ax.set_ylim([0, 1.1])
    ax.set_theta_zero_location("E")  # 0 at right
    ax.set_theta_direction(1)  # counterclockwise
    ax.set_title(title, fontweight="bold", fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)

    # Add text annotation with metrics
    textstr = "\n".join(
        [
            f"PLV = {plv:.3f}",
            f"Mean Δφ = {mean_phase_diff:.3f} rad",
            f"Anti-phase error = {anti_phase_error:.3f} rad",
        ]
    )
    ax.text(
        0.02,
        0.98,
        textstr,
        transform=fig.transFigure,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        fontsize=11,
        fontfamily="monospace",
    )

    plt.tight_layout()

    return fig


def plot_phase_portrait(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    time: Optional[np.ndarray] = None,
    title: str = "Phase Portrait (Left vs Right)",
    figsize: Tuple[int, int] = (8, 8),
) -> plt.Figure:
    """
    Plot phase portrait: φ_L vs φ_R with temporal colormap.

    Phase portraits visualize the relationship between two oscillators in
    phase space. For anti-phase coordination, points should cluster around
    the anti-diagonal (φ_L = -φ_R + π).

    Args:
        phase_left: Instantaneous phase of left foot [-π, π]
        phase_right: Instantaneous phase of right foot [-π, π]
        time: Time vector for colormap (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # If time provided, use it for colormap (early = blue, late = red)
    if time is not None:
        scatter = ax.scatter(
            phase_right,
            phase_left,
            c=time,
            cmap="viridis",
            s=10,
            alpha=0.6,
            edgecolors="none",
        )
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Time (s)", fontsize=11)
    else:
        ax.scatter(
            phase_right, phase_left, c="blue", s=10, alpha=0.5, edgecolors="none"
        )

    # Reference lines
    # Anti-phase line: φ_L = -φ_R + π
    x_line = np.linspace(-np.pi, np.pi, 100)
    y_antiphase = -x_line + np.pi
    y_antiphase = np.where(y_antiphase > np.pi, y_antiphase - 2 * np.pi, y_antiphase)
    ax.plot(
        x_line, y_antiphase, "r--", linewidth=2, alpha=0.7, label="Perfect anti-phase"
    )

    # In-phase line: φ_L = φ_R
    ax.plot(x_line, x_line, "g--", linewidth=1.5, alpha=0.5, label="In-phase")

    # Formatting
    ax.set_xlabel("Right Foot Phase (radians)", fontsize=12)
    ax.set_ylabel("Left Foot Phase (radians)", fontsize=12)
    ax.set_xlim([-np.pi, np.pi])
    ax.set_ylim([-np.pi, np.pi])
    ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_xticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()

    return fig


def plot_windowed_plv_timeseries(
    time_centers: np.ndarray,
    plv_timeseries: np.ndarray,
    plv_mean: Optional[float] = None,
    plv_trend: Optional[float] = None,
    title: str = "Temporal Evolution of PLV",
    figsize: Tuple[int, int] = (12, 5),
) -> plt.Figure:
    """
    Plot PLV evolution over time using windowed analysis.

    This visualization reveals temporal dynamics of coordination:
    - Is coordination stable or fluctuating?
    - Does coordination improve or deteriorate during the trial?
    - Are there periods of breakdown?

    Args:
        time_centers: Original time points for each window in seconds
        plv_timeseries: PLV values for each window
        plv_mean: Mean PLV across windows (optional)
        plv_trend: Linear trend slope in PLV units per second (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot PLV timeseries
    ax.plot(
        time_centers,
        plv_timeseries,
        linewidth=2,
        color="darkblue",
        marker="o",
        markersize=4,
        alpha=0.7,
        label="Windowed PLV",
    )

    # Mean line
    if plv_mean is not None:
        ax.axhline(
            plv_mean,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=f"Mean PLV = {plv_mean:.3f}",
        )

    # Trend line
    if plv_trend is not None and len(plv_timeseries) > 1:
        mean = np.mean(plv_timeseries) if plv_mean is None else plv_mean
        trend_line = mean + plv_trend * (time_centers - np.mean(time_centers))
        ax.plot(
            time_centers,
            trend_line,
            color="orange",
            linestyle=":",
            linewidth=2,
            alpha=0.8,
            label=f"Trend (slope={plv_trend:.4f})",
        )

    # Reference line for "good" PLV
    ax.axhline(
        0.8,
        color="green",
        linestyle="-.",
        linewidth=1.5,
        alpha=0.5,
        label="Reference (PLV=0.8)",
    )

    # Formatting
    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Phase Locking Value", fontsize=12)
    ax.set_ylim([0, 1.05])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_phase_slip_events(
    time: np.ndarray,
    phase_diff: np.ndarray,
    slip_threshold: float = np.pi / 2,
    title: str = "Phase Difference with Slip Events",
    figsize: Tuple[int, int] = (12, 5),
    fs: Optional[float] = None,
) -> plt.Figure:
    """
    Plot phase difference highlighting slip events (abrupt changes).

    Phase slips indicate momentary loss of synchronization or instability.
    This visualization helps identify when and how often they occur.

    Args:
        time: Time vector (seconds)
        phase_diff: Phase difference Δφ(t) in radians
        slip_threshold: Threshold for slip detection (default: π/2)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    from gait_project.analysis.circular_statistics import wrap_angle

    fig, ax = plt.subplots(figsize=figsize)

    # Plot phase difference
    ax.plot(time, phase_diff, linewidth=1.0, color="purple", alpha=0.7, label="Δφ(t)")

    # Detect slip events
    delta_phase = np.diff(phase_diff)
    delta_phase_wrapped = wrap_angle(delta_phase)
    adjacent = np.isfinite(phase_diff[:-1]) & np.isfinite(phase_diff[1:])
    if fs is not None:
        adjacent &= np.isclose(np.diff(time), 1 / fs, rtol=1e-5, atol=1e-9)
    slip_indices = (
        np.where((np.abs(delta_phase_wrapped) > slip_threshold) & adjacent)[0] + 1
    )

    # Mark slip events
    if len(slip_indices) > 0:
        ax.scatter(
            time[slip_indices],
            phase_diff[slip_indices],
            c="red",
            s=100,
            marker="x",
            linewidths=2,
            label=f"Slip events (n={len(slip_indices)})",
            zorder=5,
        )

    # Reference lines
    ax.axhline(
        np.pi,
        color="red",
        linestyle="--",
        linewidth=1.5,
        alpha=0.5,
        label="Expected anti-phase (π)",
    )
    ax.axhline(
        0, color="green", linestyle="-.", linewidth=1.5, alpha=0.5, label="In-phase (0)"
    )

    # Formatting
    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Phase Difference Δφ (radians)", fontsize=12)
    ax.set_ylim([-np.pi - 0.3, np.pi + 0.3])
    ax.set_yticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    ax.set_yticklabels(["-π", "-π/2", "0", "π/2", "π"])
    ax.set_title(title, fontweight="bold", fontsize=14)
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig
