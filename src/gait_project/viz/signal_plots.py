"""
Signal plotting functions.

Visualizations for time-domain signals (raw, filtered, comparison plots).
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def plot_raw_signal(
    time: np.ndarray,
    signal: np.ndarray,
    title: str = "Signal",
    xlabel: str = "Time (s)",
    ylabel: str = "Amplitude",
    figsize: Tuple[int, int] = (12, 4),
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """
    Plot a single time-domain signal.

    Args:
        time: Time vector
        signal: Signal values
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        ax: Existing axes to plot on (optional)

    Returns:
        fig: Matplotlib figure object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    ax.plot(time, signal, linewidth=0.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_filtered_comparison(
    time: np.ndarray,
    raw_signal: np.ndarray,
    filtered_signal: np.ndarray,
    title: str = "Raw vs Filtered Signal",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot raw and filtered signals for comparison.

    Args:
        time: Time vector
        raw_signal: Raw signal
        filtered_signal: Filtered signal
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # Raw signal
    axes[0].plot(time, raw_signal, linewidth=0.8, color="steelblue")
    axes[0].set_ylabel("Raw Amplitude")
    axes[0].set_title("Raw Signal")
    axes[0].grid(True, alpha=0.3)

    # Filtered signal
    axes[1].plot(time, filtered_signal, linewidth=0.8, color="darkgreen")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Filtered Amplitude")
    axes[1].set_title("Filtered Signal")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    return fig


def plot_dual_signals(
    time: np.ndarray,
    signal1: np.ndarray,
    signal2: np.ndarray,
    label1: str = "Left Foot",
    label2: str = "Right Foot",
    title: str = "Dual Signal Comparison",
    ylabel: str = "Angular Velocity (deg/s)",
    figsize: Tuple[int, int] = (12, 6),
) -> plt.Figure:
    """
    Plot two signals on the same axes for comparison.

    Args:
        time: Time vector
        signal1: First signal (e.g., left foot)
        signal2: Second signal (e.g., right foot)
        label1: Label for first signal
        label2: Label for second signal
        title: Plot title
        ylabel: Y-axis label
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, signal1, label=label1, linewidth=0.8, alpha=0.8)
    ax.plot(time, signal2, label=label2, linewidth=0.8, alpha=0.8)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_signal_with_events(
    time: np.ndarray,
    signal: np.ndarray,
    event_indices: list,
    event_labels: Optional[list] = None,
    title: str = "Signal with Gait Events",
    figsize: Tuple[int, int] = (12, 4),
) -> plt.Figure:
    """
    Plot signal with marked gait events.

    Args:
        time: Time vector
        signal: Signal values
        event_indices: List of event indices
        event_labels: Labels for events (optional)
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(time, signal, linewidth=0.8, color="steelblue")

    # Mark events
    for i, idx in enumerate(event_indices):
        if idx < len(time):
            label = event_labels[i] if event_labels else None
            ax.axvline(time[idx], color="red", linestyle="--", alpha=0.6, label=label)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    if event_labels:
        ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig
