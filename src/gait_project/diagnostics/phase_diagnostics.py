"""
Phase Synchronization Diagnostic Tools

This module provides diagnostic functions to investigate potential issues
in phase difference calculations, including:
- Signal orientation verification
- Temporal alignment checking
- Cross-correlation analysis
- Peak detection and alternation
- Phase convention validation

DO NOT modify the main pipeline - these are diagnostic tools only.
"""

import numpy as np
from scipy import signal
from typing import Tuple, Dict, List, Optional
import matplotlib.pyplot as plt
from pathlib import Path


def compute_cross_correlation(
    signal_left: np.ndarray,
    signal_right: np.ndarray,
    fs: float = 100.0,
) -> Tuple[np.ndarray, np.ndarray, int, float]:
    """
    Compute cross-correlation between left and right foot signals.

    Args:
        signal_left: Left foot signal (narrowband filtered)
        signal_right: Right foot signal (narrowband filtered)
        fs: Sampling frequency (Hz)

    Returns:
        lags: Time lags (in seconds)
        correlation: Cross-correlation values (normalized)
        lag_at_max: Lag at maximum correlation (samples)
        max_corr: Maximum correlation value

    Interpretation:
        - lag ≈ 0 → signals are in-phase
        - lag ≈ T/2 (half period) → signals are anti-phase
    """
    # Normalize signals
    sig_left_norm = (signal_left - np.mean(signal_left)) / np.std(signal_left)
    sig_right_norm = (signal_right - np.mean(signal_right)) / np.std(signal_right)

    # Compute cross-correlation
    correlation = np.correlate(sig_left_norm, sig_right_norm, mode="full")
    correlation = correlation / len(signal_left)  # Normalize

    # Compute lags
    lags_samples = np.arange(-len(signal_left) + 1, len(signal_left))
    lags_time = lags_samples / fs

    # Find maximum correlation
    lag_at_max = lags_samples[np.argmax(correlation)]
    max_corr = np.max(correlation)

    return lags_time, correlation, lag_at_max, max_corr


def detect_peaks(
    signal_data: np.ndarray,
    fs: float = 100.0,
    prominence: float = 0.5,
    distance_samples: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect peaks in a gait signal.

    Args:
        signal_data: Input signal
        fs: Sampling frequency (Hz)
        prominence: Minimum peak prominence (relative to std)
        distance_samples: Minimum distance between peaks (samples)

    Returns:
        peak_indices: Indices of detected peaks
        peak_times: Times of detected peaks (seconds)
    """
    # Auto-set minimum distance if not provided (assume ~1 Hz gait)
    if distance_samples is None:
        distance_samples = int(fs * 0.4)  # At least 0.4s between peaks

    # Detect peaks
    peak_indices, _ = signal.find_peaks(
        signal_data,
        prominence=prominence * np.std(signal_data),
        distance=distance_samples,
    )

    peak_times = peak_indices / fs

    return peak_indices, peak_times


def check_peak_alternation(
    peaks_left: np.ndarray,
    peaks_right: np.ndarray,
    tolerance_s: float = 0.1,
) -> Tuple[bool, float, List[Tuple[float, float]]]:
    """
    Check if peaks from left and right feet alternate properly.

    Args:
        peaks_left: Peak times for left foot (seconds)
        peaks_right: Peak times for right foot (seconds)
        tolerance_s: Tolerance for considering peaks simultaneous (seconds)

    Returns:
        is_alternating: True if peaks alternate properly
        mean_offset: Mean time offset between left and right peaks (seconds)
        simultaneous_pairs: List of (left_peak, right_peak) that occur simultaneously

    Interpretation:
        - is_alternating=True, mean_offset ≈ T/2 → proper anti-phase gait
        - is_alternating=False, many simultaneous pairs → in-phase (abnormal)
    """
    # Find simultaneous peaks
    simultaneous_pairs = []

    for t_left in peaks_left:
        for t_right in peaks_right:
            if abs(t_left - t_right) < tolerance_s:
                simultaneous_pairs.append((t_left, t_right))

    # Compute mean offset
    all_peaks = np.sort(np.concatenate([peaks_left, peaks_right]))

    if len(all_peaks) > 1:
        # Check alternation: should be L-R-L-R or R-L-R-L
        # Compute inter-peak intervals
        intervals = np.diff(all_peaks)
        mean_offset = np.mean(intervals)
    else:
        mean_offset = 0.0

    # Decide if alternating
    # If >30% of peaks are simultaneous, not alternating
    total_peaks = min(len(peaks_left), len(peaks_right))
    if total_peaks > 0:
        is_alternating = len(simultaneous_pairs) / total_peaks < 0.3
    else:
        is_alternating = False

    return is_alternating, mean_offset, simultaneous_pairs


def compute_alternative_phase_differences(
    phase_left: np.ndarray,
    phase_right: np.ndarray,
) -> Dict[str, Dict[str, float]]:
    """
    Compute phase difference using different conventions.

    Args:
        phase_left: Left foot instantaneous phase (wrapped)
        phase_right: Right foot instantaneous phase (wrapped)

    Returns:
        Dictionary with different phase difference conventions and their metrics

    Conventions tested:
        - standard: Δφ = φ_L - φ_R
        - inverted_right: Δφ = φ_L - (−φ_R)
        - shifted_right: Δφ = φ_L - (φ_R + π)
        - inverted_left: Δφ = (−φ_L) - φ_R
    """
    from gait_project.analysis.circular_statistics import (
        wrap_angle,
        resultant_vector,
    )

    results = {}

    # Convention 1: Standard (current implementation)
    delta_phi_std = wrap_angle(phase_left - phase_right)
    R_std, plv_std, mean_std = resultant_vector(delta_phi_std)
    results["standard"] = {
        "mean_phase_diff_rad": mean_std,
        "mean_phase_diff_deg": np.degrees(mean_std),
        "plv": plv_std,
        "anti_phase_error_rad": abs(wrap_angle(mean_std - np.pi)),
    }

    # Convention 2: Inverted right
    delta_phi_inv_r = wrap_angle(phase_left - (-phase_right))
    R_inv_r, plv_inv_r, mean_inv_r = resultant_vector(delta_phi_inv_r)
    results["inverted_right"] = {
        "mean_phase_diff_rad": mean_inv_r,
        "mean_phase_diff_deg": np.degrees(mean_inv_r),
        "plv": plv_inv_r,
        "anti_phase_error_rad": abs(wrap_angle(mean_inv_r - np.pi)),
    }

    # Convention 3: Shifted right by π
    delta_phi_shift_r = wrap_angle(phase_left - (phase_right + np.pi))
    R_shift_r, plv_shift_r, mean_shift_r = resultant_vector(delta_phi_shift_r)
    results["shifted_right"] = {
        "mean_phase_diff_rad": mean_shift_r,
        "mean_phase_diff_deg": np.degrees(mean_shift_r),
        "plv": plv_shift_r,
        "anti_phase_error_rad": abs(wrap_angle(mean_shift_r - np.pi)),
    }

    # Convention 4: Inverted left
    delta_phi_inv_l = wrap_angle((-phase_left) - phase_right)
    R_inv_l, plv_inv_l, mean_inv_l = resultant_vector(delta_phi_inv_l)
    results["inverted_left"] = {
        "mean_phase_diff_rad": mean_inv_l,
        "mean_phase_diff_deg": np.degrees(mean_inv_l),
        "plv": plv_inv_l,
        "anti_phase_error_rad": abs(wrap_angle(mean_inv_l - np.pi)),
    }

    return results


def diagnose_phase_relationship(
    time: np.ndarray,
    signal_left: np.ndarray,
    signal_right: np.ndarray,
    phase_left: np.ndarray,
    phase_right: np.ndarray,
    freq_left: float,
    freq_right: float,
    fs: float = 100.0,
    output_dir: Optional[Path] = None,
) -> Dict:
    """
    Comprehensive diagnostic analysis of phase relationship between feet.

    Args:
        time: Time vector (seconds)
        signal_left: Filtered left foot signal
        signal_right: Filtered right foot signal
        phase_left: Instantaneous phase left (wrapped)
        phase_right: Instantaneous phase right (wrapped)
        freq_left: Dominant frequency left (Hz)
        freq_right: Dominant frequency right (Hz)
        fs: Sampling frequency (Hz)
        output_dir: Directory to save diagnostic plots (optional)

    Returns:
        Diagnostic report dictionary
    """
    report = {}

    # === CHECK 1: Cross-correlation ===
    lags, corr, lag_max, max_corr = compute_cross_correlation(
        signal_left, signal_right, fs
    )

    lag_time_max = lag_max / fs
    mean_freq = (freq_left + freq_right) / 2
    half_period = 0.5 / mean_freq if mean_freq > 0 else 0.0

    report["cross_correlation"] = {
        "lag_at_max_samples": int(lag_max),
        "lag_at_max_seconds": float(lag_time_max),
        "max_correlation": float(max_corr),
        "half_period_expected": float(half_period),
        "interpretation": (
            "in-phase"
            if abs(lag_time_max) < 0.1 * half_period
            else "anti-phase"
            if abs(lag_time_max - half_period) < 0.1 * half_period
            else "intermediate"
        ),
    }

    # === CHECK 2: Peak detection ===
    peaks_idx_left, peaks_time_left = detect_peaks(signal_left, fs)
    peaks_idx_right, peaks_time_right = detect_peaks(signal_right, fs)

    is_alt, mean_offset, simul_pairs = check_peak_alternation(
        peaks_time_left, peaks_time_right, tolerance_s=0.15
    )

    report["peak_detection"] = {
        "num_peaks_left": len(peaks_time_left),
        "num_peaks_right": len(peaks_time_right),
        "is_alternating": is_alt,
        "mean_inter_peak_interval": float(mean_offset),
        "num_simultaneous_pairs": len(simul_pairs),
        "interpretation": (
            "proper alternation (anti-phase)"
            if is_alt
            else "peaks are synchronized (in-phase)"
        ),
    }

    # === CHECK 3: Alternative phase conventions ===
    alt_phases = compute_alternative_phase_differences(phase_left, phase_right)
    report["alternative_conventions"] = alt_phases

    # Find best convention (closest to anti-phase)
    best_convention = None
    min_anti_phase_error = float("inf")
    for name, metrics in alt_phases.items():
        if metrics["anti_phase_error_rad"] < min_anti_phase_error:
            min_anti_phase_error = metrics["anti_phase_error_rad"]
            best_convention = name

    report["best_convention"] = {
        "name": best_convention,
        "anti_phase_error_rad": float(min_anti_phase_error),
        "mean_phase_diff_deg": float(
            alt_phases[best_convention]["mean_phase_diff_deg"]
        ),
    }

    # === CHECK 4: Frequency matching ===
    freq_diff = abs(freq_left - freq_right)
    freq_ratio = (
        freq_diff / ((freq_left + freq_right) / 2)
        if (freq_left + freq_right) > 0
        else 0.0
    )

    report["frequency_check"] = {
        "freq_left": float(freq_left),
        "freq_right": float(freq_right),
        "freq_diff": float(freq_diff),
        "freq_ratio_percent": float(freq_ratio * 100),
        "matched": freq_ratio < 0.05,
    }

    # === GENERATE PLOTS ===
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Plot 1: Filtered signals overlay
        fig1 = plot_filtered_signals_overlay(
            time, signal_left, signal_right, peaks_idx_left, peaks_idx_right
        )
        fig1.savefig(
            output_dir / "diagnostic_01_filtered_signals.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(fig1)

        # Plot 2: Cross-correlation
        fig2 = plot_cross_correlation(lags, corr, lag_time_max, half_period)
        fig2.savefig(
            output_dir / "diagnostic_02_cross_correlation.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(fig2)

        # Plot 3: Alternative phase conventions
        fig3 = plot_alternative_conventions(alt_phases)
        fig3.savefig(
            output_dir / "diagnostic_03_phase_conventions.png",
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(fig3)

        # Plot 4: Raw signal comparison (if available in caller)
        # This would need raw signals passed in

    return report


def plot_filtered_signals_overlay(
    time: np.ndarray,
    signal_left: np.ndarray,
    signal_right: np.ndarray,
    peaks_idx_left: np.ndarray,
    peaks_idx_right: np.ndarray,
) -> plt.Figure:
    """Plot filtered signals from both feet with detected peaks."""
    fig, ax = plt.subplots(figsize=(14, 5))

    ax.plot(
        time,
        signal_left,
        label="Left Foot (LF_Gyr_Y)",
        color="blue",
        alpha=0.7,
        linewidth=1.5,
    )
    ax.plot(
        time,
        signal_right,
        label="Right Foot (RF_Gyr_Y)",
        color="red",
        alpha=0.7,
        linewidth=1.5,
    )

    # Plot peaks
    if len(peaks_idx_left) > 0:
        ax.scatter(
            time[peaks_idx_left],
            signal_left[peaks_idx_left],
            color="blue",
            s=100,
            marker="o",
            edgecolors="black",
            linewidths=1.5,
            label="Left Peaks",
            zorder=5,
        )

    if len(peaks_idx_right) > 0:
        ax.scatter(
            time[peaks_idx_right],
            signal_right[peaks_idx_right],
            color="red",
            s=100,
            marker="^",
            edgecolors="black",
            linewidths=1.5,
            label="Right Peaks",
            zorder=5,
        )

    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Angular Velocity (rad/s)", fontsize=12)
    ax.set_title("Filtered Signals - Both Feet", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)

    return fig


def plot_cross_correlation(
    lags: np.ndarray,
    correlation: np.ndarray,
    lag_at_max: float,
    half_period: float,
) -> plt.Figure:
    """Plot cross-correlation between left and right foot signals."""
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(lags, correlation, color="black", linewidth=1.5)
    ax.axvline(
        lag_at_max,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Max at {lag_at_max:.3f}s",
    )
    ax.axvline(
        0,
        color="green",
        linestyle=":",
        linewidth=1.5,
        alpha=0.7,
        label="Zero lag (in-phase)",
    )

    if half_period > 0:
        ax.axvline(
            half_period,
            color="orange",
            linestyle=":",
            linewidth=1.5,
            alpha=0.7,
            label=f"Half period (anti-phase) ≈{half_period:.3f}s",
        )
        ax.axvline(
            -half_period, color="orange", linestyle=":", linewidth=1.5, alpha=0.7
        )

    ax.set_xlabel("Lag (s)", fontsize=12)
    ax.set_ylabel("Cross-correlation", fontsize=12)
    ax.set_title(
        "Cross-Correlation: Left vs Right Foot", fontsize=14, fontweight="bold"
    )
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-2, 2])  # Focus on ±2 seconds

    return fig


def plot_alternative_conventions(alt_phases: Dict[str, Dict[str, float]]) -> plt.Figure:
    """Plot comparison of different phase difference conventions."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    conventions = ["standard", "inverted_right", "shifted_right", "inverted_left"]
    titles = [
        "Standard: Δφ = φ_L - φ_R",
        "Inverted Right: Δφ = φ_L - (-φ_R)",
        "Shifted Right: Δφ = φ_L - (φ_R + π)",
        "Inverted Left: Δφ = (-φ_L) - φ_R",
    ]

    for idx, (conv, title) in enumerate(zip(conventions, titles)):
        ax = axes[idx]
        metrics = alt_phases[conv]

        # Bar plot showing mean phase diff and anti-phase error
        x_pos = [0, 1]
        values = [
            abs(metrics["mean_phase_diff_deg"]),
            np.degrees(metrics["anti_phase_error_rad"]),
        ]
        colors = ["steelblue", "coral"]
        labels = ["Mean Δφ", "Anti-phase error"]

        bars = ax.bar(x_pos, values, color=colors, alpha=0.7, edgecolor="black")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels)
        ax.set_ylabel("Degrees", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylim([0, 180])
        ax.axhline(
            180,
            color="red",
            linestyle="--",
            linewidth=1,
            alpha=0.5,
            label="Expected anti-phase",
        )
        ax.grid(True, alpha=0.3, axis="y")

        # Add text annotations
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 5,
                f"{val:.1f}°",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        # Add PLV annotation
        ax.text(
            0.98,
            0.95,
            f"PLV = {metrics['plv']:.3f}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def generate_diagnostic_summary(report: Dict) -> str:
    """
    Generate a text summary of diagnostic results.

    Args:
        report: Diagnostic report from diagnose_phase_relationship()

    Returns:
        Formatted text summary
    """
    lines = []
    lines.append("=" * 80)
    lines.append("PHASE SYNCHRONIZATION DIAGNOSTIC REPORT")
    lines.append("=" * 80)

    # Frequency check
    lines.append("\n[1] FREQUENCY MATCHING")
    lines.append("-" * 40)
    fc = report["frequency_check"]
    lines.append(f"Left foot frequency:  {fc['freq_left']:.3f} Hz")
    lines.append(f"Right foot frequency: {fc['freq_right']:.3f} Hz")
    lines.append(
        f"Difference:           {fc['freq_diff']:.4f} Hz ({fc['freq_ratio_percent']:.1f}%)"
    )
    lines.append(f"Matched (< 5%):       {'✓ YES' if fc['matched'] else '✗ NO'}")

    # Cross-correlation
    lines.append("\n[2] CROSS-CORRELATION ANALYSIS")
    lines.append("-" * 40)
    cc = report["cross_correlation"]
    lines.append(f"Maximum correlation:  {cc['max_correlation']:.3f}")
    lines.append(
        f"Lag at maximum:       {cc['lag_at_max_seconds']:.3f} s ({cc['lag_at_max_samples']} samples)"
    )
    lines.append(f"Half period expected: {cc['half_period_expected']:.3f} s")
    lines.append(f"Interpretation:       {cc['interpretation'].upper()}")

    # Peak detection
    lines.append("\n[3] PEAK ALTERNATION ANALYSIS")
    lines.append("-" * 40)
    pd = report["peak_detection"]
    lines.append(f"Peaks detected (left):  {pd['num_peaks_left']}")
    lines.append(f"Peaks detected (right): {pd['num_peaks_right']}")
    lines.append(f"Simultaneous pairs:     {pd['num_simultaneous_pairs']}")
    lines.append(f"Mean inter-peak time:   {pd['mean_inter_peak_interval']:.3f} s")
    lines.append(f"Interpretation:         {pd['interpretation'].upper()}")

    # Alternative conventions
    lines.append("\n[4] PHASE DIFFERENCE CONVENTIONS")
    lines.append("-" * 40)
    for name, metrics in report["alternative_conventions"].items():
        lines.append(f"\n  {name.upper()}:")
        lines.append(f"    Mean Δφ:          {metrics['mean_phase_diff_deg']:>7.1f}°")
        lines.append(
            f"    Anti-phase error: {np.degrees(metrics['anti_phase_error_rad']):>7.1f}°"
        )
        lines.append(f"    PLV:              {metrics['plv']:>7.3f}")

    # Best convention
    lines.append("\n[5] RECOMMENDATION")
    lines.append("-" * 40)
    best = report["best_convention"]
    lines.append(f"Best convention: {best['name'].upper()}")
    lines.append(f"  → Mean Δφ = {best['mean_phase_diff_deg']:.1f}°")
    lines.append(
        f"  → Anti-phase error = {np.degrees(best['anti_phase_error_rad']):.1f}°"
    )

    # Diagnostic conclusion
    lines.append("\n[6] DIAGNOSTIC CONCLUSION")
    lines.append("-" * 40)

    # Synthesize findings
    is_in_phase = cc["interpretation"] == "in-phase"
    peaks_in_phase = not pd["is_alternating"]
    standard_near_zero = (
        abs(report["alternative_conventions"]["standard"]["mean_phase_diff_deg"]) < 30
    )
    shifted_near_anti = (
        report["alternative_conventions"]["shifted_right"]["anti_phase_error_rad"] < 0.5
    )

    if is_in_phase and peaks_in_phase and standard_near_zero:
        lines.append("⚠ SIGNALS APPEAR IN-PHASE (Δφ ≈ 0°)")
        lines.append("")
        lines.append("Possible causes:")
        lines.append(
            "  1. Sensor orientation: LF and RF may have opposite Y-axis definitions"
        )
        lines.append("  2. Phase convention: May need to add π offset to one signal")
        lines.append(
            "  3. Signal selection: LF_Gyr_Y and RF_Gyr_Y may represent same gait event"
        )

        if shifted_near_anti:
            lines.append("")
            lines.append(
                "→ RECOMMENDATION: Use 'shifted_right' convention (Δφ = φ_L - (φ_R + π))"
            )
            lines.append("  This produces anti-phase coordination as expected in gait.")
    else:
        lines.append("✓ Signals show expected anti-phase relationship")

    lines.append("\n" + "=" * 80)

    return "\n".join(lines)
