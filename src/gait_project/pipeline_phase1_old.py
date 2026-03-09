"""
PHASE 1 Pipeline: Spectral Analysis of Gait Signals

This module implements the complete Phase 1 pipeline for gait analysis:
1. Load trial data
2. Select signal (LF_Gyr_Y)
3. Preprocess signal
4. Remove turning segment
5. Compute PSD
6. Estimate dominant frequency
7. Generate visualizations and export results
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional

from gait_project.io.load_data import load_trial
from gait_project.io.data_structures import TrialData
from gait_project.preprocess.signal_cleaning import detrend_signal, remove_mean
from gait_project.preprocess.turn_removal import exclude_uturn
from gait_project.spectral.psd_analysis import compute_psd, compute_spectrogram
from gait_project.spectral.dominant_frequency import (
    find_dominant_frequency,
    compute_spectral_metrics,
)


class Phase1Pipeline:
    """
    Phase 1 pipeline for spectral gait analysis.

    This pipeline processes a single trial through all steps of spectral analysis
    and generates visualizations and metrics.
    """

    def __init__(self, base_path: str, output_dir: str = "outputs"):
        """
        Initialize pipeline.

        Args:
            base_path: Path to dataset root
            output_dir: Directory for outputs (default: "outputs")
        """
        self.base_path = base_path
        self.output_dir = Path(output_dir)
        self.figures_dir = self.output_dir / "figures"
        self.tables_dir = self.output_dir / "tables"

        # Create output directories
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline state
        self.trial_data: Optional[TrialData] = None
        self.signal_raw: Optional[np.ndarray] = None
        self.signal_cleaned: Optional[np.ndarray] = None
        self.signal_no_turn: Optional[np.ndarray] = None
        self.time_vector: Optional[np.ndarray] = None
        self.psd_freqs: Optional[np.ndarray] = None
        self.psd_values: Optional[np.ndarray] = None
        self.dominant_freq: Optional[float] = None
        self.metrics: Optional[Dict] = None

    def run(self, trial_name: str, signal_name: str = "LF_Gyr_Y") -> Dict:
        """
        Run complete Phase 1 pipeline on a single trial.

        Args:
            trial_name: Name of trial to process (e.g., "HS_1_1")
            signal_name: Signal column to analyze (default: "LF_Gyr_Y")

        Returns:
            metrics: Dictionary with computed metrics
        """
        print("=" * 60)
        print(f"PHASE 1 PIPELINE - Trial: {trial_name}")
        print("=" * 60)

        # Step 1: Load trial data
        print("\n[1/7] Loading trial data...")
        self._load_trial(trial_name)

        # Step 2: Select signal
        print(f"[2/7] Selecting signal: {signal_name}")
        self._select_signal(signal_name)

        # Step 3: Preprocess signal
        print("[3/7] Preprocessing signal...")
        self._preprocess_signal()

        # Step 4: Remove turning segment
        print("[4/7] Removing turning segment...")
        self._remove_turn()

        # Step 5: Compute PSD
        print("[5/7] Computing power spectral density...")
        self._compute_psd()

        # Step 6: Estimate dominant frequency
        print("[6/7] Estimating dominant frequency...")
        self._estimate_dominant_frequency()

        # Step 7: Generate outputs
        print("[7/7] Generating visualizations and tables...")
        self._generate_figures(trial_name, signal_name)
        self._export_results(trial_name, signal_name)

        print(f"\n{'=' * 60}")
        print("Pipeline completed successfully!")
        print(f"Dominant frequency: {self.dominant_freq:.3f} Hz")
        print(f"Figures saved to: {self.figures_dir}")
        print(f"Results saved to: {self.tables_dir}")
        print(f"{'=' * 60}\n")

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
        """Remove U-turn segment using metadata boundaries."""
        uturn_boundaries = self.trial_data.metadata.uturn_boundaries

        # Remove turn from signal
        self.signal_no_turn = exclude_uturn(self.signal_cleaned, uturn_boundaries)

        # Update time vector for signal without turn
        fs = self.trial_data.metadata.freq
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
        """Estimate dominant gait frequency from PSD."""
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

        # Find peak power
        mask = (self.psd_freqs >= freq_range[0]) & (self.psd_freqs <= freq_range[1])
        peak_power = np.max(self.psd_values[mask])

        # Store metrics
        self.metrics = {
            "dominant_freq_hz": self.dominant_freq,
            "peak_power": peak_power,
            "peak_width_hz": peak_width,
            "energy_ratio": energy_ratio,
        }

    def _generate_figures(self, trial_name: str, signal_name: str) -> None:
        """Generate all required figures for Phase 1."""
        # Figure 1: Raw vs cleaned signal
        self._plot_raw_vs_cleaned(trial_name, signal_name)

        # Figure 2: Signal with turning segment highlighted
        self._plot_signal_with_turn(trial_name, signal_name)

        # Figure 3: Signal after turn removal
        self._plot_signal_no_turn(trial_name, signal_name)

        # Figure 4: Power spectral density
        self._plot_psd(trial_name, signal_name)

        # Figure 5 (optional): Spectrogram
        self._plot_spectrogram(trial_name, signal_name)

    def _plot_raw_vs_cleaned(self, trial_name: str, signal_name: str) -> None:
        """Figure 1: Raw signal vs cleaned signal."""
        fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

        # Raw signal
        axes[0].plot(
            self.time_vector, self.signal_raw, linewidth=0.8, color="steelblue"
        )
        axes[0].set_ylabel("Angular Velocity (deg/s)")
        axes[0].set_title("Raw Signal")
        axes[0].grid(True, alpha=0.3)

        # Cleaned signal
        axes[1].plot(
            self.time_vector, self.signal_cleaned, linewidth=0.8, color="darkgreen"
        )
        axes[1].set_xlabel("Time (s)")
        axes[1].set_ylabel("Angular Velocity (deg/s)")
        axes[1].set_title("Preprocessed Signal (detrended + zero-mean)")
        axes[1].grid(True, alpha=0.3)

        fig.suptitle(
            f"Signal Preprocessing - {trial_name} - {signal_name}",
            fontsize=14,
            fontweight="bold",
        )
        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_01_raw_vs_cleaned.png"
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

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angular Velocity (deg/s)")
        ax.set_title(
            f"Signal with U-turn Segment - {trial_name} - {signal_name}",
            fontweight="bold",
        )
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_02_with_turn_segment.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_signal_no_turn(self, trial_name: str, signal_name: str) -> None:
        """Figure 3: Signal after turn removal."""
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(self.time_no_turn, self.signal_no_turn, linewidth=0.8, color="darkblue")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angular Velocity (deg/s)")
        ax.set_title(
            f"Signal After U-turn Removal - {trial_name} - {signal_name}",
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_03_no_turn.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_psd(self, trial_name: str, signal_name: str) -> None:
        """Figure 4: Power spectral density with dominant frequency marked."""
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot PSD
        ax.plot(self.psd_freqs, self.psd_values, linewidth=1.5, color="navy")

        # Mark dominant frequency
        ax.axvline(
            self.dominant_freq,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"f₀ = {self.dominant_freq:.3f} Hz",
        )

        # Restrict to gait frequency range for better visualization
        ax.set_xlim([0, 5])

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power Spectral Density (deg²/s² / Hz)")
        ax.set_title(
            f"Power Spectral Density - {trial_name} - {signal_name}", fontweight="bold"
        )
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_04_psd.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _plot_spectrogram(self, trial_name: str, signal_name: str) -> None:
        """Figure 5 (optional): Spectrogram of the signal."""
        fs = self.trial_data.metadata.freq

        # Compute spectrogram
        freqs, times, Sxx = compute_spectrogram(
            self.signal_no_turn, fs=fs, nperseg=256, noverlap=128
        )

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot spectrogram
        im = ax.pcolormesh(
            times, freqs, 10 * np.log10(Sxx + 1e-10), shading="gouraud", cmap="viridis"
        )

        # Limit frequency range to gait frequencies
        ax.set_ylim([0, 5])

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title(f"Spectrogram - {trial_name} - {signal_name}", fontweight="bold")

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Power (dB)")

        plt.tight_layout()

        # Save figure
        filename = f"{trial_name}_{signal_name}_05_spectrogram.png"
        plt.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def _export_results(self, trial_name: str, signal_name: str) -> None:
        """Export metrics to CSV table."""
        # Create results dataframe
        results = {
            "subject": self.trial_data.metadata.subject,
            "trial": trial_name,
            "signal": signal_name,
            "f0_hz": self.metrics["dominant_freq_hz"],
            "peak_power": self.metrics["peak_power"],
            "peak_width_hz": self.metrics["peak_width_hz"],
            "energy_ratio": self.metrics["energy_ratio"],
        }

        df = pd.DataFrame([results])

        # Save to CSV
        csv_path = self.tables_dir / "frequency_summary.csv"

        # Append if file exists, otherwise create new
        if csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            df_combined = pd.concat([df_existing, df], ignore_index=True)
            df_combined.to_csv(csv_path, index=False)
        else:
            df.to_csv(csv_path, index=False)

        print(f"   Results appended to: {csv_path}")


def run_phase1_pipeline(
    base_path: str,
    trial_name: str,
    signal_name: str = "LF_Gyr_Y",
    output_dir: str = "outputs",
) -> Dict:
    """
    Convenience function to run Phase 1 pipeline on a single trial.

    Args:
        base_path: Path to dataset root
        trial_name: Name of trial to process
        signal_name: Signal to analyze (default: "LF_Gyr_Y")
        output_dir: Output directory (default: "outputs")

    Returns:
        metrics: Dictionary with computed metrics
    """
    pipeline = Phase1Pipeline(base_path, output_dir)
    metrics = pipeline.run(trial_name, signal_name)
    return metrics
