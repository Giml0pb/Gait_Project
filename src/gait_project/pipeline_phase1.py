"""
PHASE 1 Pipeline (Improved): Spectral Analysis of Gait Signals

This module implements the improved Phase 1 pipeline with:
- Concatenation artifact handling
- Spectral SNR metric
- Enhanced visualizations
- Extended metrics table
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional
import warnings

from gait_project.io.load_data import load_trial
from gait_project.io.data_structures import TrialData
from gait_project.preprocess.signal_cleaning import detrend_signal, remove_mean
from gait_project.preprocess.turn_removal import exclude_uturn
from gait_project.spectral.psd_analysis import compute_psd, compute_spectrogram
from gait_project.spectral.dominant_frequency import (
    find_dominant_frequency,
    compute_spectral_metrics,
    compute_spectral_snr,
)


class Phase1Pipeline:
    """
    Phase 1 pipeline for spectral gait analysis (improved version).

    Improvements:
    - Handles concatenation artifacts with buffer removal
    - Computes spectral SNR
    - Enhanced visualizations for reporting
    - Extended metrics table
    """

    def __init__(
        self,
        base_path: str,
        output_dir: str = "outputs",
        buffer_time: float = 0.2,
    ):
        """
        Initialize pipeline.

        Args:
            base_path: Path to dataset root
            output_dir: Directory for outputs (default: "outputs")
            buffer_time: Buffer time around concatenation point in seconds (default: 0.2)
        """
        self.base_path = base_path
        self.output_dir = Path(output_dir)
        self.figures_dir = self.output_dir / "figures"
        self.tables_dir = self.output_dir / "tables"
        self.buffer_time = buffer_time

        # Create output directories
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline state
        self.trial_data: Optional[TrialData] = None
        self.signal_raw: Optional[np.ndarray] = None
        self.signal_cleaned: Optional[np.ndarray] = None
        self.signal_no_turn_raw: Optional[np.ndarray] = None  # Without buffer
        self.signal_no_turn: Optional[np.ndarray] = None  # With buffer removed
        self.time_vector: Optional[np.ndarray] = None
        self.psd_freqs: Optional[np.ndarray] = None
        self.psd_values: Optional[np.ndarray] = None
        self.dominant_freq: Optional[float] = None
        self.spectral_snr: Optional[float] = None
        self.metrics: Optional[Dict] = None
        self.generate_figures: bool = True  # Can be overridden externally

    def run(self, trial_name: str, signal_name: str = "LF_Gyr_Y") -> Dict:
        """
        Run complete Phase 1 pipeline on a single trial.

        Args:
            trial_name: Name of trial to process (e.g., "HS_1_1")
            signal_name: Signal column to analyze (default: "LF_Gyr_Y")

        Returns:
            metrics: Dictionary with computed metrics
        """
        print("=" * 70)
        print(f"PHASE 1 PIPELINE (IMPROVED) - Trial: {trial_name}")
        print("=" * 70)

        # Step 1: Load trial data
        print("\n[1/7] Loading trial data...")
        self._load_trial(trial_name)

        # Step 2: Select signal
        print(f"[2/7] Selecting signal: {signal_name}")
        self._select_signal(signal_name)

        # Step 3: Preprocess signal
        print("[3/7] Preprocessing signal...")
        self._preprocess_signal()

        # Step 4: Remove turning segment (with and without buffer)
        print(f"[4/7] Removing turning segment (buffer={self.buffer_time}s)...")
        self._remove_turn()

        # Step 5: Compute PSD
        print("[5/7] Computing power spectral density...")
        self._compute_psd()

        # Step 6: Estimate dominant frequency and SNR
        print("[6/7] Estimating dominant frequency and spectral SNR...")
        self._estimate_dominant_frequency()

        # Step 7: Generate outputs
        print("[7/7] Generating visualizations and tables...")
        if self.generate_figures:
            self._generate_figures(trial_name, signal_name)
        self._export_results(trial_name, signal_name)

        print(f"\n{'=' * 70}")
        print("Pipeline completed successfully!")
        print(f"Dominant frequency: {self.dominant_freq:.3f} Hz")
        print(f"Spectral SNR:       {self.spectral_snr:.2f}")
        print(f"Signal duration:    {self.metrics['signal_duration']:.2f} s")
        print(f"Figures saved to:   {self.figures_dir}")
        print(f"Results saved to:   {self.tables_dir}")
        print(f"{'=' * 70}\n")

        return self.metrics

    def _load_trial(self, trial_name: str) -> None:
        """Load trial data from dataset."""
        loaded_data = load_trial(self.base_path, trial_name)
        self.trial_data = TrialData.from_load_trial(trial_name, loaded_data)

    def _select_signal(self, signal_name: str) -> None:
        """Extract specified signal from processed data."""
        if signal_name not in self.trial_data.data_processed.columns:
            raise ValueError(
                f"Signal '{signal_name}' not found in processed data columns"
            )

        self.signal_raw = self.trial_data.data_processed[signal_name].values

        # Create time vector
        fs = self.trial_data.metadata.freq
        n_samples = len(self.signal_raw)
        self.time_vector = np.arange(n_samples) / fs

    def _preprocess_signal(self) -> None:
        """Preprocess signal: detrend and remove mean."""
        # Detrend
        signal_detrended = detrend_signal(self.signal_raw, method="linear")

        # Remove mean
        self.signal_cleaned = remove_mean(signal_detrended)

    def _remove_turn(self) -> None:
        """Remove U-turn segment with buffer to avoid concatenation artifacts."""
        uturn_boundaries = self.trial_data.metadata.uturn_boundaries
        fs = self.trial_data.metadata.freq

        # First, remove turn without buffer (for visualization)
        self.signal_no_turn_raw = exclude_uturn(
            self.signal_cleaned, uturn_boundaries, buffer_time=0.0, fs=fs
        )

        # Then, remove turn with buffer (for analysis)
        self.signal_no_turn = exclude_uturn(
            self.signal_cleaned, uturn_boundaries, buffer_time=self.buffer_time, fs=fs
        )

        # Update time vector for final signal
        n_samples_no_turn = len(self.signal_no_turn)
        self.time_no_turn = np.arange(n_samples_no_turn) / fs

    def _compute_psd(self) -> None:
        """Compute power spectral density using Welch's method."""
        fs = self.trial_data.metadata.freq

        # Welch parameters as specified in Fase 1
        nperseg = 256
        noverlap = 128

        self.psd_freqs, self.psd_values = compute_psd(
            self.signal_no_turn, fs=fs, nperseg=nperseg, noverlap=noverlap
        )

    def _estimate_dominant_frequency(self) -> None:
        """Estimate dominant gait frequency and compute spectral SNR."""
        # Search range as specified in Fase 1
        freq_range = (0.5, 3.0)

        # Find dominant frequency
        self.dominant_freq = find_dominant_frequency(
            self.psd_freqs, self.psd_values, freq_range=freq_range
        )

        # Compute additional spectral metrics
        dominant_freq, peak_width, energy_ratio = compute_spectral_metrics(
            self.psd_freqs, self.psd_values, freq_range=freq_range
        )

        # Compute spectral SNR
        self.spectral_snr = compute_spectral_snr(
            self.psd_freqs, self.psd_values, self.dominant_freq, freq_range=freq_range
        )

        # Find peak power
        mask = (self.psd_freqs >= freq_range[0]) & (self.psd_freqs <= freq_range[1])
        peak_power = np.max(self.psd_values[mask])

        # Compute signal duration
        fs = self.trial_data.metadata.freq
        signal_duration = len(self.signal_no_turn) / fs

        # Store metrics
        self.metrics = {
            "dominant_freq_hz": self.dominant_freq,
            "peak_power": peak_power,
            "peak_width_hz": peak_width,
            "energy_ratio": energy_ratio,
            "spectral_snr": self.spectral_snr,
            "signal_duration": signal_duration,
        }

    def _generate_figures(self, trial_name: str, signal_name: str) -> None:
        """Generate all required figures for Phase 1."""
        # Figure 0: True raw vs preprocessed (left foot only)
        self._plot_true_raw_vs_preprocessed(trial_name, signal_name)

        # Figure 1: Bilateral signals (left + right feet)
        self._plot_bilateral_signals(trial_name, signal_name)

        # Figure 2: Signal with turning segment highlighted
        self._plot_signal_with_turn(trial_name, signal_name)

        # Figure 3: Signal after turn removal (without buffer)
        self._plot_signal_no_turn_raw(trial_name, signal_name)

        # Figure 4: Signal after turn removal with buffer (artifact corrected)
        self._plot_signal_no_turn_buffered(trial_name, signal_name)

        # Figure 5: Power spectral density (improved)
        self._plot_psd_improved(trial_name, signal_name)

        # Figure 6: Spectrogram (improved)
        self._plot_spectrogram_improved(trial_name, signal_name)

    def _plot_bilateral_signals(self, trial_name: str, signal_name: str) -> None:
        """Figure 1: Bilateral signals (left + right feet)."""
        # Determine the opposite foot signal name
        if signal_name.startswith("LF_"):
            signal_name_right = signal_name.replace("LF_", "RF_")
        elif signal_name.startswith("RF_"):
            signal_name_left = signal_name.replace("RF_", "LF_")
            signal_name_right = signal_name
            signal_name = signal_name_left
        else:
            # If signal doesn't follow LF_/RF_ convention, skip bilateral plot
            print(
                f"  Warning: Signal '{signal_name}' doesn't follow LF_/RF_ convention. Skipping bilateral plot."
            )
            return

        # Check if opposite signal exists
        if signal_name_right not in self.trial_data.data_processed.columns:
            print(
                f"  Warning: Opposite foot signal '{signal_name_right}' not found. Skipping bilateral plot."
            )
            return

        # Get both signals (preprocessed: detrended + zero-mean)
        signal_left_raw = self.trial_data.data_processed[signal_name].values
        signal_right_raw = self.trial_data.data_processed[signal_name_right].values

        # Apply same preprocessing to both
        from gait_project.preprocess.signal_cleaning import detrend_signal, remove_mean

        signal_left = remove_mean(detrend_signal(signal_left_raw, method="linear"))
        signal_right = remove_mean(detrend_signal(signal_right_raw, method="linear"))

        # Create time vector
        fs = self.trial_data.metadata.freq
        time_vector = np.arange(len(signal_left)) / fs

        # Plot
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Left foot
        axes[0].plot(
            time_vector, signal_left, linewidth=0.8, color="blue", label="Left foot"
        )
        axes[0].set_ylabel("Angular Velocity (deg/s)", fontsize=11)
        axes[0].set_title(f"Left Foot - {signal_name}", fontsize=12, fontweight="bold")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(loc="upper right")

        # Right foot
        axes[1].plot(
            time_vector, signal_right, linewidth=0.8, color="red", label="Right foot"
        )
        axes[1].set_xlabel("Time (s)", fontsize=11)
        axes[1].set_ylabel("Angular Velocity (deg/s)", fontsize=11)
        axes[1].set_title(
            f"Right Foot - {signal_name_right}", fontsize=12, fontweight="bold"
        )
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(loc="upper right")

        fig.suptitle(
            f"Bilateral Gait Signals - {trial_name}",
            fontsize=14,
            fontweight="bold",
            y=0.995,
        )
        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_bilateral_01_left_right_signals.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_true_raw_vs_preprocessed(self, trial_name: str, signal_name: str) -> None:
        """Figure: True raw signal vs preprocessed signal (left foot only)."""
        # Only plot for left foot signals
        if not signal_name.startswith("LF_"):
            return

        # Extract sensor and axis from signal name (e.g., "LF_Gyr_Y" -> sensor="LF", axis="Gyr_Y")
        parts = signal_name.split("_", 1)
        if len(parts) != 2:
            print(
                f"  Warning: Cannot parse signal name '{signal_name}'. Skipping true raw plot."
            )
            return

        sensor = parts[0]  # "LF"
        axis = parts[1]  # "Gyr_Y"

        # Get true raw signal from data_raw
        if sensor == "LF":
            raw_data = self.trial_data.data_raw.LF
        else:
            print(
                f"  Warning: Sensor '{sensor}' not supported for true raw plot. Skipping."
            )
            return

        if axis not in raw_data.columns:
            print(
                f"  Warning: Axis '{axis}' not found in raw data. Skipping true raw plot."
            )
            return

        true_raw_signal = raw_data[axis].values

        # Create time vector for raw signal (may have different length than processed)
        fs = self.trial_data.metadata.freq
        time_raw = np.arange(len(true_raw_signal)) / fs

        # For preprocessed signal, use the one we already computed
        time_preprocessed = self.time_vector
        preprocessed_signal = self.signal_cleaned

        # Plot both signals overlaid
        fig, ax = plt.subplots(figsize=(14, 6))

        # True raw signal
        ax.plot(
            time_raw,
            true_raw_signal,
            linewidth=0.7,
            color="steelblue",
            alpha=0.7,
            label="True raw signal",
        )

        # Preprocessed signal
        ax.plot(
            time_preprocessed,
            preprocessed_signal,
            linewidth=0.9,
            color="darkgreen",
            alpha=0.8,
            label="Preprocessed (detrended + zero-mean)",
        )

        ax.set_xlabel("Time (s)", fontsize=11)
        ax.set_ylabel("Angular Velocity (deg/s)", fontsize=11)
        ax.set_title(
            f"True Raw vs Preprocessed Signal - {trial_name} - {signal_name}",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(loc="upper right", fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_00_true_raw_vs_preprocessed.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_signal_with_turn(self, trial_name: str, signal_name: str) -> None:
        """Figure 2: Signal with turning segment highlighted."""
        fig, ax = plt.subplots(figsize=(12, 5))

        # Plot signal
        ax.plot(self.time_vector, self.signal_cleaned, linewidth=0.8, color="black")

        # Highlight turning segment
        uturn_start, uturn_end = self.trial_data.metadata.uturn_boundaries
        fs = self.trial_data.metadata.freq
        time_start = uturn_start / fs
        time_end = uturn_end / fs

        ax.axvspan(time_start, time_end, alpha=0.3, color="red", label="U-turn segment")

        # Mark buffer zones
        buffer_samples = int(self.buffer_time * fs)
        buffer_start = max(0, uturn_start - buffer_samples) / fs
        buffer_end = min(len(self.signal_cleaned), uturn_end + buffer_samples) / fs

        ax.axvspan(
            buffer_start,
            time_start,
            alpha=0.2,
            color="orange",
            label=f"Buffer ({self.buffer_time}s)",
        )
        ax.axvspan(time_end, buffer_end, alpha=0.2, color="orange")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angular Velocity (deg/s)")
        ax.set_title(
            f"Signal with U-turn Segment and Buffers - {trial_name} - {signal_name}",
            fontweight="bold",
        )
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_02_with_turn_segment.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_signal_no_turn_raw(self, trial_name: str, signal_name: str) -> None:
        """Figure 3: Signal after turn removal (without buffer)."""
        fs = self.trial_data.metadata.freq
        time_no_turn_raw = np.arange(len(self.signal_no_turn_raw)) / fs

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            time_no_turn_raw, self.signal_no_turn_raw, linewidth=0.8, color="darkblue"
        )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angular Velocity (deg/s)")
        ax.set_title(
            f"Signal After U-turn Removal (no buffer) - {trial_name} - {signal_name}",
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_03_no_turn_raw.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_signal_no_turn_buffered(self, trial_name: str, signal_name: str) -> None:
        """Figure 4: Signal after turn removal with buffer (artifact corrected)."""
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            self.time_no_turn, self.signal_no_turn, linewidth=0.8, color="darkgreen"
        )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angular Velocity (deg/s)")
        ax.set_title(
            f"Signal After U-turn Removal with Buffer ({self.buffer_time}s) - {trial_name} - {signal_name}",
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)

        # Add text annotation
        ax.text(
            0.02,
            0.98,
            f"Concatenation artifacts removed\nBuffer: ±{self.buffer_time}s",
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            fontsize=9,
        )

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_04_no_turn_buffered.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_psd_improved(self, trial_name: str, signal_name: str) -> None:
        """Figure 5: Power spectral density (professional paper style)."""
        fig, ax = plt.subplots(figsize=(8, 5))

        # Plot PSD
        ax.plot(self.psd_freqs, self.psd_values, linewidth=1.2, color="black")

        # Mark dominant frequency with vertical line
        ax.axvline(
            self.dominant_freq,
            color="red",
            linestyle="--",
            linewidth=1.0,
            alpha=0.8,
        )

        # Add small text annotation for f0
        f0_idx = np.argmin(np.abs(self.psd_freqs - self.dominant_freq))
        f0_power = self.psd_values[f0_idx]

        ax.text(
            self.dominant_freq,
            f0_power * 1.05,
            f"$f_0$ = {self.dominant_freq:.2f} Hz",
            ha="center",
            va="bottom",
            fontsize=9,
            color="red",
        )

        # Axes labels
        ax.set_xlabel("Frequency (Hz)", fontsize=11)
        ax.set_ylabel("PSD (deg$^2$/s$^2$/Hz)", fontsize=11)

        # Set limits
        ax.set_xlim([0, 4])
        ax.set_ylim(bottom=0)

        # Clean grid
        ax.grid(True, alpha=0.2, linestyle=":", linewidth=0.5)

        # Spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_05_psd.png"
        plt.savefig(self.figures_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()

    def _plot_spectrogram_improved(self, trial_name: str, signal_name: str) -> None:
        """Figure 6: Spectrogram (improved)."""
        fs = self.trial_data.metadata.freq

        # Compute spectrogram
        freqs, times, Sxx = compute_spectrogram(
            self.signal_no_turn, fs=fs, nperseg=256, noverlap=128
        )

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot spectrogram in dB scale
        Sxx_db = 10 * np.log10(Sxx + 1e-10)
        im = ax.pcolormesh(times, freqs, Sxx_db, shading="gouraud", cmap="viridis")

        # Limit frequency range to gait frequencies
        ax.set_ylim([0, 5])

        ax.set_xlabel("Time (s)", fontsize=12)
        ax.set_ylabel("Frequency (Hz)", fontsize=12)
        ax.set_title(
            f"Spectrogram - {trial_name} - {signal_name}",
            fontweight="bold",
            fontsize=14,
        )

        # Add colorbar with better label
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Power (dB)", fontsize=11)

        # Add horizontal line at f0
        ax.axhline(
            self.dominant_freq,
            color="red",
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
            label=f"f₀ = {self.dominant_freq:.3f} Hz",
        )
        ax.legend(loc="upper right", fontsize=10)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_06_spectrogram.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _export_results(self, trial_name: str, signal_name: str) -> None:
        """Export metrics to CSV table with deduplication."""
        # Create results dataframe
        results = {
            "subject": self.trial_data.metadata.subject,
            "trial": trial_name,
            "signal": signal_name,
            "f0_hz": self.metrics["dominant_freq_hz"],
            "peak_power": self.metrics["peak_power"],
            "peak_width_hz": self.metrics["peak_width_hz"],
            "energy_ratio": self.metrics["energy_ratio"],
            "spectral_snr": self.metrics["spectral_snr"],
            "signal_duration": self.metrics["signal_duration"],
        }

        df_new = pd.DataFrame([results])

        # Save to CSV
        csv_path = self.tables_dir / "frequency_summary.csv"

        # Append if file exists, otherwise create new
        if csv_path.exists():
            df_existing = pd.read_csv(csv_path)

            # Check for duplicates before appending
            # Unique key: (subject, trial, signal)
            duplicate_mask = (
                (df_existing["subject"] == results["subject"])
                & (df_existing["trial"] == results["trial"])
                & (df_existing["signal"] == results["signal"])
            )

            if duplicate_mask.any():
                warnings.warn(
                    f"Duplicate entry found for ({results['subject']}, {results['trial']}, "
                    f"{results['signal']}). Replacing old entry with new one."
                )
                # Remove old entry
                df_existing = df_existing[~duplicate_mask]

            # Append new entry
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(csv_path, index=False)
        else:
            df_new.to_csv(csv_path, index=False)

        print(f"   Results saved to: {csv_path}")


def run_phase1_pipeline(
    base_path: str,
    trial_name: str,
    signal_name: str = "LF_Gyr_Y",
    output_dir: str = "outputs",
    buffer_time: float = 0.2,
    generate_figures: bool = True,
) -> Dict:
    """
    Convenience function to run improved Phase 1 pipeline on a single trial.

    Args:
        base_path: Path to dataset root
        trial_name: Name of trial to process
        signal_name: Signal to analyze (default: "LF_Gyr_Y")
        output_dir: Output directory (default: "outputs")
        buffer_time: Buffer around concatenation point in seconds (default: 0.2)
        generate_figures: Whether to generate visualization plots (default: True)

    Returns:
        metrics: Dictionary with computed metrics
    """
    pipeline = Phase1Pipeline(base_path, output_dir, buffer_time)
    pipeline.generate_figures = generate_figures
    metrics = pipeline.run(trial_name, signal_name)
    return metrics
