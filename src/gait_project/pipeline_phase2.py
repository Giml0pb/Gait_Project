"""
PHASE 2 Pipeline: Instantaneous Phase Analysis of Gait Signals

This module implements the Phase 2 pipeline for gait analysis:
1. Load results from Phase 1 (or run Phase 1 if needed)
2. Apply narrowband filtering around f0
3. Compute analytic signal via Hilbert transform
4. Extract instantaneous amplitude, phase, and frequency
5. Validate phase quality
6. Generate visualizations and export metrics

Scientific corrections applied:
- Bandwidth reduced to ±0.3 Hz (not ±0.5 Hz) for better selectivity
- Instantaneous frequency uses np.gradient (not np.diff) for noise robustness
- Phase monotonicity and frequency coherence validation
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
from gait_project.spectral.psd_analysis import compute_psd
from gait_project.spectral.dominant_frequency import find_dominant_frequency
from gait_project.phase.narrowband_filter import apply_narrowband_filter
from gait_project.phase.hilbert_transform import compute_all_instantaneous_attributes
from gait_project.phase.phase_metrics import (
    summarize_phase_metrics_robust,
    validate_phase_monotonicity,
    validate_frequency_coherence,
    select_best_mask_strategy,
)
from gait_project.viz.phase_plots import (
    plot_signal_vs_filtered,
    plot_filtered_and_envelope,
    plot_wrapped_phase,
    plot_unwrapped_phase,
    plot_instantaneous_frequency_single,
    plot_frequency_comparison,
)


class Phase2Pipeline:
    """
    Phase 2 pipeline for instantaneous phase analysis of gait signals.

    This pipeline extracts temporal evolution of gait oscillation through:
    - Narrowband filtering around dominant frequency
    - Hilbert transform for analytic signal
    - Instantaneous attributes (amplitude, phase, frequency)
    - Quality validation
    """

    def __init__(
        self,
        base_path: str,
        output_dir: str = "outputs",
        bandwidth: float = 0.3,
        buffer_time: float = 0.2,
    ):
        """
        Initialize Phase 2 pipeline.

        Args:
            base_path: Path to dataset root
            output_dir: Directory for outputs (default: "outputs")
            bandwidth: Narrowband filter bandwidth in Hz (default: 0.3)
                      Recommendation: 0.25-0.4 Hz for typical gait
            buffer_time: Buffer around turn removal (default: 0.2 s)
        """
        self.base_path = base_path
        self.output_dir = Path(output_dir)
        self.figures_dir = self.output_dir / "figures"
        self.tables_dir = self.output_dir / "tables"
        self.bandwidth = bandwidth
        self.buffer_time = buffer_time

        # Create output directories
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline state
        self.trial_data: Optional[TrialData] = None
        self.signal_cleaned: Optional[np.ndarray] = None
        self.signal_no_turn: Optional[np.ndarray] = None
        self.f0: Optional[float] = None
        self.signal_filtered: Optional[np.ndarray] = None
        self.amplitude: Optional[np.ndarray] = None
        self.phase_wrapped: Optional[np.ndarray] = None
        self.phase_unwrapped: Optional[np.ndarray] = None
        self.inst_freq: Optional[np.ndarray] = None
        self.time: Optional[np.ndarray] = None
        self.validity_mask: Optional[np.ndarray] = None
        self.mask_strategy: Optional[str] = None
        self.metrics: Optional[Dict] = None
        self.generate_figures: bool = True  # Can be overridden externally

    def run(
        self,
        trial_name: str,
        signal_name: str = "LF_Gyr_Y",
        f0_provided: Optional[float] = None,
    ) -> Dict:
        """
        Run complete Phase 2 pipeline on a single trial.

        Args:
            trial_name: Name of trial to process (e.g., "HS_1_1")
            signal_name: Signal column to analyze (default: "LF_Gyr_Y")
            f0_provided: Dominant frequency (if None, will be estimated)

        Returns:
            metrics: Dictionary with phase analysis metrics
        """
        print("=" * 70)
        print(f"PHASE 2 PIPELINE - Trial: {trial_name}, Signal: {signal_name}")
        print("=" * 70)

        # Step 1: Prepare signal (run Phase 1 steps if needed)
        print("\n[1/7] Preparing signal...")
        self._prepare_signal(trial_name, signal_name, f0_provided)

        # Step 2: Narrowband filtering
        print(f"[2/7] Applying narrowband filter around f0={self.f0:.3f} Hz...")
        self._apply_narrowband_filter()

        # Step 3: Compute analytic signal
        print("[3/7] Computing analytic signal via Hilbert transform...")
        self._compute_analytic_signal()

        # Step 4: Extract instantaneous attributes
        print("[4/7] Extracting instantaneous phase and frequency...")
        # Already done in step 3

        # Step 5: Validate phase quality
        print("[5/7] Validating phase quality...")
        self._validate_phase_quality()

        # Step 6: Compute summary metrics
        print("[6/7] Computing summary metrics...")
        self._compute_metrics()

        # Step 7: Generate outputs
        print("[7/7] Generating visualizations and tables...")
        if self.generate_figures:
            self._generate_figures(trial_name, signal_name)
        self._export_results(trial_name, signal_name)

        print(f"\n{'=' * 70}")
        print("Phase 2 pipeline completed!")
        print(f"Spectral f₀:        {self.f0:.3f} Hz")
        print(f"Mean inst. freq:    {self.metrics['mean_inst_freq_hz']:.3f} Hz")
        print(f"Freq variability:   {self.metrics['std_inst_freq_hz']:.4f} Hz")
        print(f"Number of cycles:   {self.metrics['num_cycles']:.1f}")
        print(f"Figures saved to:   {self.figures_dir}")
        print(f"{'=' * 70}\n")

        return self.metrics

    def _prepare_signal(
        self, trial_name: str, signal_name: str, f0_provided: Optional[float]
    ) -> None:
        """Prepare signal by running Phase 1 preprocessing steps."""
        # Load trial
        loaded_data = load_trial(self.base_path, trial_name)
        self.trial_data = TrialData.from_load_trial(trial_name, loaded_data)

        # Extract signal
        if signal_name not in self.trial_data.data_processed.columns:
            raise ValueError(f"Signal '{signal_name}' not found")

        signal_raw = self.trial_data.data_processed[signal_name].values

        # Preprocess
        signal_detrended = detrend_signal(signal_raw, method="linear")
        self.signal_cleaned = remove_mean(signal_detrended)

        # Remove U-turn with buffer
        fs = self.trial_data.metadata.freq
        uturn_boundaries = self.trial_data.metadata.uturn_boundaries
        self.signal_no_turn = exclude_uturn(
            self.signal_cleaned,
            uturn_boundaries,
            buffer_time=self.buffer_time,
            fs=fs,
        )

        # Create time vector
        n_samples = len(self.signal_no_turn)
        self.time = np.arange(n_samples) / fs

        # Estimate f0 if not provided
        if f0_provided is None:
            psd_freqs, psd_values = compute_psd(
                self.signal_no_turn, fs=fs, nperseg=256, noverlap=128
            )
            self.f0 = find_dominant_frequency(
                psd_freqs, psd_values, freq_range=(0.5, 3.0)
            )
        else:
            self.f0 = f0_provided

    def _apply_narrowband_filter(self) -> None:
        """Apply narrowband bandpass filter around f0."""
        fs = self.trial_data.metadata.freq

        self.signal_filtered = apply_narrowband_filter(
            self.signal_no_turn,
            fs=fs,
            center_freq=self.f0,
            bandwidth=self.bandwidth,
            filter_order=4,
        )

    def _compute_analytic_signal(self) -> None:
        """Compute analytic signal and instantaneous attributes."""
        fs = self.trial_data.metadata.freq

        (
            self.amplitude,
            self.phase_wrapped,
            self.phase_unwrapped,
            self.inst_freq,
        ) = compute_all_instantaneous_attributes(self.signal_filtered, fs)

    def _validate_phase_quality(self) -> None:
        """Validate phase quality with warnings for potential issues."""
        # Check phase monotonicity
        is_monotonic, monotonic_frac = validate_phase_monotonicity(
            self.phase_unwrapped, tolerance=0.05
        )
        if not is_monotonic:
            warnings.warn(
                f"Phase is not sufficiently monotonic ({monotonic_frac*100:.1f}% increasing). "
                f"Expected >95%. Signal may have discontinuities or noise."
            )

        # Check frequency coherence
        mean_freq = np.mean(self.inst_freq)
        is_coherent, rel_error = validate_frequency_coherence(
            self.f0, mean_freq, tolerance=0.15
        )
        if not is_coherent:
            warnings.warn(
                f"Frequency coherence poor: f₀={self.f0:.3f} Hz vs "
                f"mean(f_inst)={mean_freq:.3f} Hz ({rel_error*100:.1f}% difference). "
                f"Phase analysis may be unreliable."
            )

    def _compute_metrics(self) -> None:
        """Compute summary metrics for phase analysis with automatic mask selection."""
        fs = self.trial_data.metadata.freq

        # Automatically select best masking strategy
        print("   Testing validity mask strategies...")
        self.validity_mask, self.mask_strategy, strategy_metrics = (
            select_best_mask_strategy(
                self.inst_freq,
                self.amplitude,
                self.f0,
                fs,
                edge_time=1.0,
                amplitude_percentile=20.0,
            )
        )

        print(f"   Selected strategy: {self.mask_strategy}")
        print(
            f"   Valid samples: {np.sum(self.validity_mask)}/{len(self.validity_mask)} "
            f"({np.sum(self.validity_mask)/len(self.validity_mask)*100:.1f}%)"
        )

        # Compute robust metrics using selected mask
        self.metrics = summarize_phase_metrics_robust(
            self.amplitude,
            self.phase_wrapped,
            self.phase_unwrapped,
            self.inst_freq,
            self.f0,
            fs,
            validity_mask=self.validity_mask,
            mask_strategy=self.mask_strategy,
        )

        # Add f0 for reference
        self.metrics["f0_hz"] = self.f0

        # Add coherence check (using masked metrics)
        _, rel_error = validate_frequency_coherence(
            self.f0, self.metrics["mean_inst_freq_hz"]
        )
        self.metrics["freq_coherence_error"] = rel_error

        # Add clinical metrics
        # Cadence in steps per minute (standard clinical metric)
        self.metrics["cadence_steps_per_min"] = self.metrics["mean_inst_freq_hz"] * 60

        # Stride time in seconds (inverse of frequency)
        self.metrics["stride_time_s"] = 1.0 / self.metrics["mean_inst_freq_hz"]

        # Add strategy comparison metrics
        self.metrics.update(strategy_metrics)

    def _generate_figures(self, trial_name: str, signal_name: str) -> None:
        """Generate all Phase 2 figures."""
        # Figure 1: Original vs filtered
        fig = plot_signal_vs_filtered(
            self.time,
            self.signal_no_turn,
            self.signal_filtered,
            self.f0,
            self.bandwidth,
            title=f"Original vs Narrowband Filtered - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_01_filtered.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 2: Filtered + envelope
        fig = plot_filtered_and_envelope(
            self.time,
            self.signal_filtered,
            self.amplitude,
            title=f"Filtered Signal + Envelope - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_02_envelope.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 3: Wrapped phase
        fig = plot_wrapped_phase(
            self.time,
            self.phase_wrapped,
            title=f"Instantaneous Phase (Wrapped) - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_03_phase_wrapped.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 4: Unwrapped phase
        fig = plot_unwrapped_phase(
            self.time,
            self.phase_unwrapped,
            title=f"Instantaneous Phase (Unwrapped) - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_04_phase_unwrapped.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 5: Instantaneous frequency (with validity mask visualization)
        fig = plot_instantaneous_frequency_single(
            self.time,
            self.inst_freq,
            f0=self.f0,
            mean_freq=self.metrics["mean_inst_freq_hz"],
            validity_mask=self.validity_mask,
            title=f"Instantaneous Frequency - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_05_inst_freq.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 6: Frequency comparison
        fig = plot_frequency_comparison(
            self.f0,
            self.metrics["mean_inst_freq_hz"],
            self.metrics["std_inst_freq_hz"],
            title=f"Frequency Validation - {trial_name} - {signal_name}",
        )
        filename = f"{trial_name}_{signal_name}_phase2_06_freq_comparison.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def _export_results(self, trial_name: str, signal_name: str) -> None:
        """Export metrics to CSV table with deduplication."""
        # Create results dataframe with extended metrics
        results = {
            "subject": self.trial_data.metadata.subject,
            "trial": trial_name,
            "signal": signal_name,
            "f0_hz": self.metrics["f0_hz"],
            "mean_inst_freq_hz": self.metrics["mean_inst_freq_hz"],
            "median_inst_freq_hz": self.metrics["median_inst_freq_hz"],
            "std_inst_freq_hz": self.metrics["std_inst_freq_hz"],
            "mad_inst_freq_hz": self.metrics["mad_inst_freq_hz"],
            "iqr_inst_freq_hz": self.metrics["iqr_inst_freq_hz"],
            "cv_inst_freq": self.metrics["cv_inst_freq"],
            "amplitude_mean": self.metrics["amplitude_mean"],
            "amplitude_std": self.metrics["amplitude_std"],
            "amplitude_cv": self.metrics["amplitude_cv"],
            "num_cycles": self.metrics["num_cycles"],
            "freq_coherence_error": self.metrics["freq_coherence_error"],
            "mask_strategy": self.metrics["mask_strategy"],
            "valid_samples": self.metrics["valid_samples"],
            "valid_fraction": self.metrics["valid_fraction"],
        }

        df_new = pd.DataFrame([results])

        # Save to CSV
        csv_path = self.tables_dir / "phase_summary.csv"

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


def run_phase2_pipeline(
    base_path: str,
    trial_name: str,
    signal_name: str = "LF_Gyr_Y",
    output_dir: str = "outputs",
    bandwidth: float = 0.3,
    f0_provided: Optional[float] = None,
    generate_figures: bool = True,
) -> Dict:
    """
    Convenience function to run Phase 2 pipeline on a single trial.

    Args:
        base_path: Path to dataset root
        trial_name: Name of trial to process
        signal_name: Signal to analyze (default: "LF_Gyr_Y")
        output_dir: Output directory (default: "outputs")
        bandwidth: Narrowband filter bandwidth in Hz (default: 0.3)
        f0_provided: Dominant frequency if already known (optional)
        generate_figures: Whether to generate visualization plots (default: True)

    Returns:
        metrics: Dictionary with computed metrics
    """
    pipeline = Phase2Pipeline(base_path, output_dir, bandwidth)
    pipeline.generate_figures = generate_figures
    metrics = pipeline.run(trial_name, signal_name, f0_provided)
    return metrics
