"""Headless engineering plots for synthetic state-estimation demonstrations."""

from pathlib import Path

import numpy as np

from gait_project.research.phase_estimators import finite_segments
from gait_project.spectral.psd_analysis import compute_segmented_psd

BLUE, ORANGE, PURPLE = "#176c9c", "#c35625", "#75569a"


def plot_case(summary, data, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fs = 25.0
    time = data.time_s.to_numpy()
    signal = data.right_observation.to_numpy()
    truth = data.right_reference_phase_rad.to_numpy()
    ekf = data.right_harmonic_ekf_phase_rad.to_numpy()
    hilbert = data.right_fundamental_hilbert_phase_rad.to_numpy()
    visible = (time >= 3) & (time < time[-1] - 1)
    gap = ~np.isfinite(signal)

    def phase_error(phase):
        return np.rad2deg(np.angle(np.exp(1j * (phase - truth))))

    with plt.rc_context(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.labelcolor": "#334155",
            "text.color": "#172d42",
            "axes.edgecolor": "#cbd5e1",
            "grid.color": "#dbe4ec",
        }
    ):
        fig, axes = plt.subplots(3, 2, figsize=(13, 10), layout="constrained")
        fig.suptitle(
            f"{summary['title']}\nSynthetic IMU signals · calibrated harmonic EKF · known reference",
            fontsize=17,
            fontweight="bold",
        )
        ax = axes[0, 0]
        ax.plot(time, signal, color=BLUE, linewidth=0.8)
        ax.set(title="01  Observations", ylabel="Angular-velocity proxy (a.u.)")
        ax = axes[0, 1]
        freqs, power = compute_segmented_psd(
            signal, finite_segments(signal, [slice(0, len(signal))], 50), fs
        )
        ax.semilogy(freqs, np.maximum(power, 1e-8), color=BLUE, linewidth=1.2)
        selection = summary["frequency_selection"]["right"]
        ax.axvline(
            selection["dominant_hz"],
            color="0.5",
            linestyle=":",
            label=f"Dominant {selection['dominant_hz']:.2f} Hz",
        )
        ax.axvline(
            selection["fundamental_hz"],
            color=ORANGE,
            linestyle="--",
            label=f"Fundamental {selection['fundamental_hz']:.2f} Hz",
        )
        ax.set(
            title="02  Welch spectrum and harmonic selection",
            xlabel="Frequency (Hz)",
            ylabel="PSD",
            xlim=(0, 4),
        )
        ax.legend(fontsize=8)
        ax = axes[1, 0]
        reference_frequency = np.gradient(truth, 1 / fs) / (2 * np.pi)
        ax.plot(
            time[visible],
            reference_frequency[visible],
            color="#1d2939",
            linewidth=1.7,
            label="Reference",
        )
        ax.plot(
            time[visible],
            data.right_fundamental_hilbert_frequency_hz.to_numpy()[visible],
            color=BLUE,
            linewidth=1,
            label="Hilbert",
        )
        ax.plot(
            time[visible],
            data.right_harmonic_ekf_frequency_hz.to_numpy()[visible],
            color=ORANGE,
            linewidth=1,
            label="EKF",
        )
        ax.set(title="03  Frequency tracking", ylabel="Cycles / second")
        ax.legend(fontsize=8)
        ax = axes[1, 1]
        ax.axhline(0, color="0.25", linewidth=1)
        ax.plot(
            time[visible],
            phase_error(hilbert)[visible],
            color=BLUE,
            linewidth=1,
            label="Hilbert fundamental",
        )
        ax.plot(
            time[visible],
            phase_error(ekf)[visible],
            color=ORANGE,
            linewidth=1,
            label="Harmonic EKF",
        )
        ax.set(title="04  Right-foot phase error", ylabel="Circular error (degrees)")
        ax.legend(fontsize=8)
        ax = axes[2, 0]
        reference_delta = data.left_reference_phase_rad.to_numpy() - truth
        ax.axhline(0, color="0.25", linewidth=1)
        for method, label, color in (
            ("fundamental_hilbert", "Hilbert fundamental", BLUE),
            ("harmonic_ekf", "Harmonic EKF", ORANGE),
        ):
            delta = (
                data[f"left_{method}_phase_rad"].to_numpy()
                - data[f"right_{method}_phase_rad"].to_numpy()
            )
            error = np.rad2deg(np.angle(np.exp(1j * (delta - reference_delta))))
            ax.plot(
                time[visible], error[visible], linewidth=1, color=color, label=label
            )
        ax.set(
            title="05  Bilateral timing error", ylabel="Relative phase error (degrees)"
        )
        ax.legend(fontsize=8)
        ax = axes[2, 1]
        sigma = np.rad2deg(
            np.sqrt(np.maximum(data.right_ekf_phase_variance_rad2.to_numpy(), 0))
        )
        ax.fill_between(
            time[visible],
            -1.96 * sigma[visible],
            1.96 * sigma[visible],
            color=PURPLE,
            alpha=0.2,
            label="Local ±1.96σ (approximate)",
        )
        ax.plot(
            time[visible],
            phase_error(ekf)[visible],
            color=ORANGE,
            linewidth=1,
            label="EKF phase error",
        )
        ax.axhline(0, color="0.25", linewidth=0.7)
        ax.set(title="06  Prediction uncertainty", ylabel="Degrees")
        ax.legend(fontsize=8)
        if gap.any():
            first, last = time[gap][0], time[gap][-1] + 1 / fs
            for ax in (axes[0, 0], axes[1, 0], axes[1, 1], axes[2, 0], axes[2, 1]):
                ax.axvspan(first, last, color="#e8b15d", alpha=0.2)
        for index, ax in enumerate(axes.flat):
            ax.grid(True, alpha=0.55, linewidth=0.6)
            ax.spines[["top", "right"]].set_visible(False)
            if index != 1:
                ax.set_xlabel("Time (s)")
        fig.savefig(Path(destination), dpi=150, facecolor="white")
        plt.close(fig)


def plot_uncertainty_check(runs, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from gait_project.demo.uncertainty import CONDITIONS

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    fig.suptitle(
        "Uncertainty diagnostics · fixed EKF noise settings", fontweight="bold"
    )
    for ax, metric, title, reference in zip(
        axes,
        ("phase_mae_deg", "coverage_95", "mean_nis"),
        ("Phase MAE (degrees)", "Coverage of local ±1.96σ", "Mean innovation NIS"),
        (None, 0.95, 1.0),
    ):
        for index, (scenario, label) in enumerate(CONDITIONS.items()):
            values = runs.loc[runs.scenario == scenario, metric].to_numpy()
            positions = index + np.linspace(-0.12, 0.12, len(values))
            ax.scatter(positions, values, color=(BLUE, ORANGE)[index], alpha=0.65, s=18)
            ax.plot([index - 0.2, index + 0.2], [np.median(values)] * 2, color="black")
        if reference is not None:
            ax.axhline(reference, color=PURPLE, linestyle="--", linewidth=1)
        if metric == "coverage_95":
            ax.set_ylim(0, 1.05)
        ax.set_title(title, fontsize=11)
        ax.set_xticks([0, 1], list(CONDITIONS.values()), fontsize=9)
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(Path(destination), dpi=150, facecolor="white")
    plt.close(fig)
