"""
Group comparison visualization functions.

Plots for comparing metrics across clinical groups.
"""

import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple


def plot_group_boxplot(
    data: pd.DataFrame,
    metric: str,
    group_column: str = "group",
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6),
) -> plt.Figure:
    """
    Create boxplot comparing a metric across groups.

    Args:
        data: DataFrame with subject-level metrics
        metric: Column name of metric to plot
        group_column: Column containing group labels
        title: Plot title (auto-generated if None)
        ylabel: Y-axis label (uses metric name if None)
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Prepare data for boxplot
    groups = data[group_column].unique()
    plot_data = [data[data[group_column] == group][metric].dropna() for group in groups]

    # Create boxplot
    bp = ax.boxplot(plot_data, labels=groups, patch_artist=True, notch=True)

    # Customize colors
    colors = ["lightblue", "lightgreen", "lightcoral"]
    for patch, color in zip(bp["boxes"], colors[: len(groups)]):
        patch.set_facecolor(color)

    # Labels
    ax.set_xlabel("Group")
    ax.set_ylabel(ylabel if ylabel else metric)
    ax.set_title(title if title else f"{metric} by Group")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    return fig


def plot_group_distributions(
    data: pd.DataFrame,
    metric: str,
    group_column: str = "group",
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    bins: int = 20,
) -> plt.Figure:
    """
    Plot overlapping histograms for each group.

    Args:
        data: DataFrame with subject-level metrics
        metric: Column name of metric to plot
        group_column: Column containing group labels
        title: Plot title
        xlabel: X-axis label
        figsize: Figure size
        bins: Number of histogram bins

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    groups = data[group_column].unique()
    colors = ["steelblue", "forestgreen", "firebrick"]

    for i, group in enumerate(groups):
        group_data = data[data[group_column] == group][metric].dropna()
        ax.hist(
            group_data,
            bins=bins,
            alpha=0.6,
            label=f"{group} (n={len(group_data)})",
            color=colors[i % len(colors)],
            edgecolor="black",
        )

    ax.set_xlabel(xlabel if xlabel else metric)
    ax.set_ylabel("Frequency")
    ax.set_title(title if title else f"Distribution of {metric} by Group")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    return fig


def plot_metric_comparison(
    data: pd.DataFrame,
    metrics: List[str],
    group_column: str = "group",
    figsize: Tuple[int, int] = (12, 8),
) -> plt.Figure:
    """
    Create multi-panel comparison of multiple metrics.

    Args:
        data: DataFrame with subject-level metrics
        metrics: List of metric column names to compare
        group_column: Column containing group labels
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    n_metrics = len(metrics)
    n_cols = 2
    n_rows = (n_metrics + 1) // 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten()

    groups = data[group_column].unique()

    for i, metric in enumerate(metrics):
        ax = axes[i]

        # Prepare data
        plot_data = [
            data[data[group_column] == group][metric].dropna() for group in groups
        ]

        # Boxplot
        bp = ax.boxplot(plot_data, labels=groups, patch_artist=True)

        # Colors
        colors = ["lightblue", "lightgreen", "lightcoral"]
        for patch, color in zip(bp["boxes"], colors[: len(groups)]):
            patch.set_facecolor(color)

        ax.set_title(metric)
        ax.grid(True, alpha=0.3, axis="y")

    # Remove extra subplots
    for i in range(n_metrics, len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()

    return fig


def plot_metric_scatter(
    data: pd.DataFrame,
    metric_x: str,
    metric_y: str,
    group_column: str = "group",
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 8),
) -> plt.Figure:
    """
    Scatter plot of two metrics, colored by group.

    Args:
        data: DataFrame with subject-level metrics
        metric_x: Column name for x-axis
        metric_y: Column name for y-axis
        group_column: Column containing group labels
        title: Plot title
        figsize: Figure size

    Returns:
        fig: Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    groups = data[group_column].unique()
    colors = ["steelblue", "forestgreen", "firebrick"]

    for i, group in enumerate(groups):
        group_data = data[data[group_column] == group]
        ax.scatter(
            group_data[metric_x],
            group_data[metric_y],
            label=group,
            color=colors[i % len(colors)],
            s=100,
            alpha=0.7,
            edgecolors="black",
        )

    ax.set_xlabel(metric_x)
    ax.set_ylabel(metric_y)
    ax.set_title(title if title else f"{metric_y} vs {metric_x}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig
