"""
PHASE 3 Pipeline: Phase Synchronization Analysis Between Feet

This module implements the Phase 3 pipeline for gait coordination analysis:
1. Load phase data from Phase 2 (both feet)
2. Check frequency matching between feet
3. Compute phase difference Δφ(t) = φ_L(t) - φ_R(t)
4. Calculate synchronization metrics (PLV, circular statistics)
5. Compute anti-phase error (deviation from expected Δφ ≈ π)
6. Generate visualizations
7. Export metrics to CSV

Scientific foundation:
- Gait is modeled as two coupled oscillators
- Normal gait shows anti-phase coordination (Δφ ≈ π)
- PLV quantifies phase synchronization strength
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional

from gait_project.pipeline_phase2 import Phase2Pipeline
from gait_project.io.results import upsert_csv
from gait_project.validation import validate_phase3_metrics
from gait_project.synchronization.phase_sync import analyze_phase_synchronization
from gait_project.viz.sync_plots import (
    plot_phase_signals,
    plot_phase_difference,
    plot_phase_histogram,
    plot_phase_complex_plane,
)


class Phase3Pipeline:
    """
    Phase 3 pipeline for phase synchronization analysis between feet.

    This pipeline analyzes coordination between left and right feet by:
    - Computing phase difference
    - Measuring phase locking
    - Quantifying anti-phase coordination
    - Generating specialized visualizations
    """

    def __init__(
        self,
        base_path: str,
        output_dir: str = "outputs",
        bandwidth: float = 0.3,
        buffer_time: float = 0.2,
    ):
        """
        Initialize Phase 3 pipeline.

        Args:
            base_path: Path to dataset root
            output_dir: Directory for outputs (default: "outputs")
            bandwidth: Narrowband filter bandwidth for Phase 2 (default: 0.3 Hz)
            buffer_time: Buffer around turn removal for Phase 2 (default: 0.2 s)
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
        self.phase2_pipeline = None
        self.trial_name: Optional[str] = None
        self.time: Optional[np.ndarray] = None
        self.phase_left: Optional[np.ndarray] = None
        self.phase_right: Optional[np.ndarray] = None
        self.freq_left: Optional[float] = None
        self.freq_right: Optional[float] = None
        self.validity_mask_left: Optional[np.ndarray] = None
        self.validity_mask_right: Optional[np.ndarray] = None
        self.validity_mask_sync: Optional[np.ndarray] = None
        self.phase_diff: Optional[np.ndarray] = None
        self.metrics: Optional[Dict] = None
        self.generate_figures: bool = True  # Can be overridden externally
        self.subject: Optional[str] = None

    def run(
        self,
        trial_name: str,
        signal_left: str = "LF_Gyr_Y",
        signal_right: str = "RF_Gyr_Y",
    ) -> Dict:
        """
        Run complete Phase 3 pipeline on a trial.

        Args:
            trial_name: Name of trial to process (e.g., "HS_1_1")
            signal_left: Left foot signal (default: "LF_Gyr_Y")
            signal_right: Right foot signal (default: "RF_Gyr_Y")

        Returns:
            metrics: Dictionary with synchronization metrics
        """
        self.trial_name = trial_name

        print("=" * 70)
        print(f"PHASE 3 PIPELINE - Trial: {trial_name}")
        print("=" * 70)

        # Step 1: Run Phase 2 for both feet
        print("\n[1/6] Running Phase 2 for both feet...")
        self._run_phase2_both_feet(trial_name, signal_left, signal_right)

        # Step 2: Check temporal alignment and create sync mask
        print("[2/6] Aligning temporal data and creating sync mask...")
        self._create_sync_mask()

        # Step 3: Compute phase difference
        print("[3/6] Computing phase difference...")
        self._compute_phase_difference()

        # Step 4: Analyze synchronization
        print("[4/6] Analyzing phase synchronization...")
        self._analyze_synchronization()

        self._validate_metrics()
        self.phase2_left._export_results(trial_name, signal_left)
        self.phase2_right._export_results(trial_name, signal_right)

        # Step 5: Generate visualizations
        print("[5/6] Generating visualizations...")
        if self.generate_figures:
            self._generate_figures(trial_name)

        # Step 6: Export results
        print("[6/6] Exporting results...")
        self._export_results(trial_name)

        print(f"\n{'=' * 70}")
        print("Phase 3 pipeline completed!")
        print(f"PLV:                {self.metrics['plv']:.3f}")
        print(f"Mean phase diff:    {self.metrics['mean_phase_diff']:.3f} rad")
        print(f"Anti-phase error:   {self.metrics['anti_phase_error']:.3f} rad")
        print(
            f"Freq matching:      {'✓ MATCHED' if self.metrics['frequency_match_flag'] else '⚠ MISMATCH'}"
        )
        print(f"Figures saved to:   {self.figures_dir}")
        print(f"{'=' * 70}\n")

        return self.metrics

    def _run_phase2_both_feet(
        self, trial_name: str, signal_left: str, signal_right: str
    ) -> None:
        """Run Phase 2 pipeline for both feet to extract phase data."""
        self.phase2_left = Phase2Pipeline(
            self.base_path, self.output_dir, self.bandwidth, self.buffer_time
        )
        self.phase2_right = Phase2Pipeline(
            self.base_path, self.output_dir, self.bandwidth, self.buffer_time
        )
        for pipeline in (self.phase2_left, self.phase2_right):
            pipeline.generate_figures = self.generate_figures
            pipeline.save_tables = False
        metrics_left = self.phase2_left.run(trial_name, signal_left)
        metrics_right = self.phase2_right.run(trial_name, signal_right)
        self.phase2_pipeline = (
            self.phase2_right
        )  # Backwards-compatible diagnostic access.
        if not np.array_equal(self.phase2_left.time, self.phase2_right.time):
            raise ValueError(
                "Left and right phases do not share the same sample timeline"
            )
        self.time = self.phase2_left.time
        self.phase_left = self.phase2_left.phase_wrapped
        self.phase_right = self.phase2_right.phase_wrapped
        self.freq_left = metrics_left["mean_inst_freq_hz"]
        self.freq_right = metrics_right["mean_inst_freq_hz"]
        self.validity_mask_left = self.phase2_left.validity_mask
        self.validity_mask_right = self.phase2_right.validity_mask
        self.subject = self.phase2_left.trial_data.metadata.subject

    def _create_sync_mask(self) -> None:
        """
        Create synchronized validity mask.

        Only samples that are valid for both feet should be used
        for synchronization analysis.
        """
        # Combine masks with AND operation
        self.validity_mask_sync = self.validity_mask_left & self.validity_mask_right

        valid_count = np.sum(self.validity_mask_sync)
        total_count = len(self.validity_mask_sync)

        print(
            f"   Sync mask: {valid_count}/{total_count} samples "
            f"({valid_count / total_count * 100:.1f}%)"
        )

    def _compute_phase_difference(self) -> None:
        """Compute phase difference Δφ(t) = φ_L(t) - φ_R(t)."""
        from gait_project.synchronization.phase_sync import compute_phase_difference

        self.phase_diff = compute_phase_difference(self.phase_left, self.phase_right)

    def _analyze_synchronization(self) -> None:
        """Perform comprehensive synchronization analysis."""
        from gait_project.synchronization.phase_sync import (
            compute_phase_difference,
        )
        from gait_project.synchronization.temporal_sync import (
            analyze_temporal_synchronization,
        )

        # Compute phase difference for full signal (for visualization)
        self.phase_diff = compute_phase_difference(self.phase_left, self.phase_right)

        # Comprehensive analysis using only valid samples
        # CORRECTED: Reduced freq_tolerance from 0.05 to 0.03 (more conservative)
        self.metrics = analyze_phase_synchronization(
            self.phase_left,
            self.phase_right,
            self.freq_left,
            self.freq_right,
            validity_mask=self.validity_mask_sync,
            freq_tolerance=0.03,
        )

        # NEW: Temporal synchronization analysis
        # Only analyze on valid samples
        fs = self.phase2_pipeline.trial_data.metadata.freq

        # Window size: 2 seconds at sampling rate (e.g., 256 samples at 128 Hz)
        window_size = int(2.0 * fs)
        step_size = window_size // 2  # 50% overlap

        temporal_metrics = analyze_temporal_synchronization(
            self.phase_left,
            self.phase_right,
            fs,
            window_size=window_size,
            step_size=step_size,
            time=self.time,
            validity_mask=self.validity_mask_sync,
        )

        # Add temporal metrics to main metrics dict
        self.metrics.update(
            {
                "phase_slip_rate": temporal_metrics["phase_slip_rate"],
                "plv_mean_windowed": temporal_metrics["plv_mean_windowed"],
                "plv_std_windowed": temporal_metrics["plv_std_windowed"],
                "plv_trend": temporal_metrics["plv_trend"],
                "n_windows": temporal_metrics["n_windows"],
            }
        )

        # Store temporal timeseries for visualization
        self.temporal_metrics = temporal_metrics

        # Add temporal asymmetry metrics (clinical relevance)
        # Stride time asymmetry in seconds
        stride_time_left = 1.0 / self.freq_left
        stride_time_right = 1.0 / self.freq_right
        self.metrics["stride_time_left_s"] = stride_time_left
        self.metrics["stride_time_right_s"] = stride_time_right
        self.metrics["stride_time_asymmetry_s"] = abs(
            stride_time_left - stride_time_right
        )

        # Stride time asymmetry as percentage (normalized)
        mean_stride_time = (stride_time_left + stride_time_right) / 2.0
        self.metrics["stride_time_asymmetry_pct"] = (
            abs(stride_time_left - stride_time_right) / mean_stride_time * 100
        )

        # Print summary
        print(f"   PLV (global): {self.metrics['plv']:.3f}")
        print(
            f"   PLV (windowed mean): {self.metrics['plv_mean_windowed']:.3f} ± {self.metrics['plv_std_windowed']:.3f}"
        )
        print(f"   Phase slip rate: {self.metrics['phase_slip_rate']:.2f} slips/min")
        print(f"   Mean Δφ: {self.metrics['mean_phase_diff']:.3f} rad")
        print(f"   Anti-phase error: {self.metrics['anti_phase_error']:.3f} rad")
        print(f"   Frequency ratio: {self.metrics['freq_ratio'] * 100:.1f}%")

    def _generate_figures(self, trial_name: str) -> None:
        """Generate all Phase 3 figures."""
        # Apply sync mask to time and phases for visualization
        time_sync = self.time[self.validity_mask_sync]
        phase_left_sync = self.phase_left[self.validity_mask_sync]
        phase_right_sync = self.phase_right[self.validity_mask_sync]
        phase_diff_sync = self.phase_diff[self.validity_mask_sync]

        # Figure 1: Both phases
        fig = plot_phase_signals(
            time_sync,
            phase_left_sync,
            phase_right_sync,
            title=f"Instantaneous Phase - Both Feet - {trial_name}",
        )
        filename = f"{trial_name}_phase3_01_both_phases.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 2: Phase difference
        fig = plot_phase_difference(
            time_sync,
            phase_diff_sync,
            mean_phase_diff=self.metrics["mean_phase_diff"],
            title=f"Phase Difference - {trial_name}",
        )
        filename = f"{trial_name}_phase3_02_phase_diff.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 3: Histogram
        fig = plot_phase_histogram(
            phase_diff_sync,
            mean_phase_diff=self.metrics["mean_phase_diff"],
            title=f"Phase Difference Distribution - {trial_name}",
        )
        filename = f"{trial_name}_phase3_03_histogram.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 4: Kuramoto plot (complex plane)
        fig = plot_phase_complex_plane(
            phase_diff_sync,
            plv=self.metrics["plv"],
            mean_phase_diff=self.metrics["mean_phase_diff"],
            anti_phase_error=self.metrics["anti_phase_error"],
            title=f"Phase Difference on Unit Circle - {trial_name}",
        )
        filename = f"{trial_name}_phase3_04_kuramoto.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # NEW FIGURES: Temporal dynamics

        # Figure 5: Phase portrait
        from gait_project.viz.sync_plots import plot_phase_portrait

        fig = plot_phase_portrait(
            phase_left_sync,
            phase_right_sync,
            time=time_sync,
            title=f"Phase Portrait - {trial_name}",
        )
        filename = f"{trial_name}_phase3_05_phase_portrait.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 6: Windowed PLV timeseries
        from gait_project.viz.sync_plots import plot_windowed_plv_timeseries

        fig = plot_windowed_plv_timeseries(
            self.temporal_metrics["time_centers"],
            self.temporal_metrics["plv_timeseries"],
            plv_mean=self.metrics["plv_mean_windowed"],
            plv_trend=self.metrics["plv_trend"],
            title=f"Temporal Evolution of PLV - {trial_name}",
        )
        filename = f"{trial_name}_phase3_06_plv_temporal.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

        # Figure 7: Phase slip events
        from gait_project.viz.sync_plots import plot_phase_slip_events

        fig = plot_phase_slip_events(
            self.time,
            np.where(self.validity_mask_sync, self.phase_diff, np.nan),
            fs=self.phase2_pipeline.trial_data.metadata.freq,
            slip_threshold=np.pi / 2,
            title=f"Phase Slip Events - {trial_name}",
        )
        filename = f"{trial_name}_phase3_07_phase_slips.png"
        fig.savefig(self.figures_dir / filename, dpi=150, bbox_inches="tight")
        plt.close(fig)

    def _export_results(self, trial_name: str) -> None:
        """Export synchronization metrics to CSV."""
        # Create results dataframe
        results = {
            "subject": self.subject,
            "trial": trial_name,
            "freq_left": self.metrics["freq_left"],
            "freq_right": self.metrics["freq_right"],
            "freq_diff": self.metrics["freq_diff"],
            "freq_ratio": self.metrics["freq_ratio"],
            "frequency_match_flag": self.metrics["frequency_match_flag"],
            "plv": self.metrics["plv"],
            "mean_phase_diff": self.metrics["mean_phase_diff"],
            "anti_phase_error": self.metrics["anti_phase_error"],
            "circular_variance": self.metrics["circular_variance"],
            "circular_std": self.metrics["circular_std"],
            "valid_samples_sync": self.metrics["valid_samples_sync"],
            "valid_fraction_sync": self.metrics["valid_fraction_sync"],
            # NEW: Temporal synchronization metrics
            "phase_slip_rate": self.metrics["phase_slip_rate"],
            "plv_mean_windowed": self.metrics["plv_mean_windowed"],
            "plv_std_windowed": self.metrics["plv_std_windowed"],
            "plv_trend": self.metrics["plv_trend"],
            "n_windows": self.metrics["n_windows"],
        }

        df_new = pd.DataFrame([results])

        # Save to CSV
        csv_path = self.tables_dir / "synchronization_summary.csv"

        upsert_csv(df_new, csv_path, ["subject", "trial"])

        print(f"   Results saved to: {csv_path}")

    def _validate_metrics(self) -> None:
        """Validate Phase 3 metrics using Pydantic schemas."""
        validate_phase3_metrics(self.metrics)


def run_phase3_pipeline(
    base_path: str,
    trial_name: str,
    signal_left: str = "LF_Gyr_Y",
    signal_right: str = "RF_Gyr_Y",
    output_dir: str = "outputs",
    bandwidth: float = 0.3,
    generate_figures: bool = True,
) -> Dict:
    """
    Convenience function to run Phase 3 pipeline on a single trial.

    Args:
        base_path: Path to dataset root
        trial_name: Name of trial to process
        signal_left: Left foot signal (default: "LF_Gyr_Y")
        signal_right: Right foot signal (default: "RF_Gyr_Y")
        output_dir: Output directory (default: "outputs")
        bandwidth: Narrowband filter bandwidth (default: 0.3 Hz)
        generate_figures: Whether to generate visualization plots (default: True)

    Returns:
        metrics: Dictionary with synchronization metrics
    """
    pipeline = Phase3Pipeline(base_path, output_dir, bandwidth)
    pipeline.generate_figures = generate_figures
    metrics = pipeline.run(trial_name, signal_left, signal_right)
    return metrics
