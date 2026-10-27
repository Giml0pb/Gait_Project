"""Leakage-aware comparison of periodic phase estimators.

Events enter only training-template fits and scoring. Held-out estimators
receive signals, timestamps, signal-selected frequencies and training templates.
All comparisons use identical time samples and reference coverage.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import resample_poly

from gait_project.research.phase_estimators import (
    estimate_fundamental,
    finite_segments,
    hilbert_phase,
    legacy_dominant,
)
from gait_project.research.phase_reference import (
    circular_mae_deg,
    event_phase_reference,
    heel_strike_scores,
)
from gait_project.state_space.harmonic_ekf import (
    HarmonicTemplate,
    estimate_phase_ekf,
    fit_template,
    normalized_signal,
)

METHODS = ("dominant_hilbert", "fundamental_hilbert", "harmonic_ekf")


@dataclass
class StudyTrial:
    trial: str
    subject: str
    group: str
    pathology: str
    session: int
    fs: float
    time: np.ndarray
    segments: list[slice]
    signals: dict
    references: dict
    durations: dict
    dominant: dict
    fundamentals: dict
    training_coefficients: dict
    input_sha256: str
    heel_strike_times: dict


def make_participant_folds(participants, n_folds=5, seed=20261026):
    """Stratify participants by pathology, keeping all their sessions together."""
    if n_folds < 2 or len(participants) < n_folds:
        raise ValueError(
            "Cross-fitting requires at least two folds and one participant per fold"
        )
    rng = np.random.default_rng(seed)
    folds = {}
    offset = 0
    for pathology in sorted(set(participants.values())):
        subjects = sorted(s for s, p in participants.items() if p == pathology)
        rng.shuffle(subjects)
        for index, subject in enumerate(subjects):
            folds[subject] = (offset + index) % n_folds
        offset = (offset + len(subjects)) % n_folds
    if len(set(folds.values())) != n_folds:
        raise ValueError("Empty validation fold")
    return folds


def resample_walking(prepared, source_fs, target_fs=25.0):
    factor = int(round(source_fs / target_fs))
    if factor < 1 or not np.isclose(source_fs / factor, target_fs):
        raise ValueError("Analysis rate must divide the recording sampling rate")
    values, times, segments = [], [], []
    offset = 0
    for part in prepared.segments:
        data = resample_poly(prepared.walking[part], 1, factor, padtype="line")
        values.append(data)
        times.append(
            prepared.walking_time[part.start] + np.arange(len(data)) / target_fs
        )
        segments.append(slice(offset, offset + len(data)))
        offset += len(data)
    return np.concatenate(values), np.concatenate(times), segments


def prepare_study_trial(info, metadata, prepared, input_sha256, target_fs=25.0):
    signals, references, durations, dominant, fundamentals, coefficients = (
        {},
        {},
        {},
        {},
        {},
        {},
    )
    for side in ("left", "right"):
        source = prepared[side]
        values, time, segments = resample_walking(source, metadata["freq"], target_fs)
        signals[side] = values
        reference, stride_durations = event_phase_reference(
            time,
            metadata[f"{side}GaitEvents"],
            metadata["freq"],
            segments,
        )
        references[side], durations[side] = reference, stride_durations
        dominant[side] = legacy_dominant(
            source.walking, metadata["freq"], source.segments
        )
        fundamentals[side] = estimate_fundamental(values, target_fs, segments)
        coefficients[side] = fit_template(
            normalized_signal(values), reference
        ).coefficients
    return StudyTrial(
        info.trial_name,
        info.subject_id,
        info.group,
        info.pathology,
        metadata["session"],
        target_fs,
        time,
        segments,
        signals,
        references,
        durations,
        dominant,
        fundamentals,
        coefficients,
        input_sha256,
        {
            side: np.asarray(metadata[f"{side}GaitEvents"], dtype=float)[:, 1]
            / metadata["freq"]
            for side in ("left", "right")
        },
    )


def training_templates(trials, folds, held_out_fold):
    """Average trials within person, then people; held-out events never enter."""
    templates = {}
    for side in ("left", "right"):
        by_subject = {}
        for trial in trials:
            if folds[trial.subject] != held_out_fold:
                by_subject.setdefault(trial.subject, []).append(
                    trial.training_coefficients[side]
                )
        if not by_subject:
            raise ValueError("No training participants outside the held-out fold")
        mean = np.mean(
            [np.mean(coefs, axis=0) for coefs in by_subject.values()], axis=0
        )
        templates[side] = HarmonicTemplate(mean)
    return templates


def estimate_methods(values, fs, segments, dominant_hz, fundamental_hz, template):
    """No reference annotations are accepted by this interface."""
    phases, frequencies = {}, {}
    phases["dominant_hilbert"], frequencies["dominant_hilbert"] = hilbert_phase(
        values, fs, segments, dominant_hz, template.phase_offset(2)
    )
    phases["fundamental_hilbert"], frequencies["fundamental_hilbert"] = hilbert_phase(
        values, fs, segments, fundamental_hz, template.phase_offset(1)
    )
    ekf_phase, ekf_frequency, ekf_variance = [
        np.full(len(values), np.nan) for _ in range(3)
    ]
    mask = np.zeros(len(values), dtype=bool)
    diagnostics = {
        "initialization_ambiguous": False,
        "frequency_bound_hits": 0,
        "amplitude_bound_hits": 0,
        "missing_prediction_count": 0,
    }
    for part in segments:
        result = estimate_phase_ekf(values[part], fs, fundamental_hz, template)
        ekf_phase[part], ekf_frequency[part], ekf_variance[part] = (
            result.phase,
            result.frequency_hz,
            result.variance_phase,
        )
        mask[part] = result.score_mask
        diagnostics["initialization_ambiguous"] |= result.initialization_ambiguity
        for field in (
            "frequency_bound_hits",
            "amplitude_bound_hits",
            "missing_prediction_count",
        ):
            diagnostics[field] += getattr(result, field)
    phases["harmonic_ekf"], frequencies["harmonic_ekf"] = ekf_phase, ekf_frequency
    # Match support across all estimators; the warm-up is excluded for every one.
    for method in METHODS:
        mask &= np.isfinite(phases[method])
    observed_support = np.zeros(len(values), dtype=bool)
    edge = int(fs)
    for part in finite_segments(values, segments, minimum=max(32, int(2 * fs))):
        if part.stop - part.start > 2 * edge:
            observed_support[part.start + edge : part.stop - edge] = True
    mask &= observed_support
    return phases, frequencies, mask, ekf_variance, diagnostics


def score_trial(trial, templates, fold):
    audit, foot_rows, pair_rows = [], [], []
    estimates, rates, masks = {}, {}, {}
    diagnostics, variances = {}, {}
    for side in ("left", "right"):
        estimate = trial.fundamentals[side]
        reference_frequency = (
            1 / np.median(trial.durations[side])
            if len(trial.durations[side])
            else np.nan
        )
        audit.append(
            {
                "trial": trial.trial,
                "subject": trial.subject,
                "group": trial.group,
                "pathology": trial.pathology,
                "side": side,
                "fold": fold,
                "dominant_hz": trial.dominant[side],
                "fundamental_hz": estimate.frequency_hz,
                "event_stride_hz": reference_frequency,
                "dominant_to_event_ratio": trial.dominant[side] / reference_frequency,
                "fundamental_to_event_ratio": estimate.frequency_hz
                / reference_frequency,
                "fundamental_power_fraction": estimate.fundamental_power_fraction,
                "weak_fundamental": estimate.weak_fundamental,
                "spectral_resolution_hz": estimate.spectral_resolution_hz,
                "n_reference_strides": len(trial.durations[side]),
                "input_sha256": trial.input_sha256,
            }
        )
        phases, frequency, mask, variance, diag = estimate_methods(
            trial.signals[side],
            trial.fs,
            trial.segments,
            trial.dominant[side],
            estimate.frequency_hz,
            templates[side],
        )
        mask &= np.isfinite(trial.references[side])
        (
            estimates[side],
            rates[side],
            masks[side],
            diagnostics[side],
            variances[side],
        ) = phases, frequency, mask, diag, variance
        for method in METHODS:
            usable = int(mask.sum()) >= int(trial.fs)
            event_scores = heel_strike_scores(
                phases[method],
                trial.time,
                trial.heel_strike_times[side],
                mask,
                trial.fs,
                tolerance_s=0.15,
            )
            foot_rows.append(
                {
                    "trial": trial.trial,
                    "subject": trial.subject,
                    "group": trial.group,
                    "pathology": trial.pathology,
                    "session": trial.session,
                    "fold": fold,
                    "side": side,
                    "method": method,
                    "n_scored_samples": int(mask.sum()),
                    "score_duration_s": mask.sum() / trial.fs,
                    "phase_mae_deg": circular_mae_deg(
                        phases[method], trial.references[side], mask
                    )
                    if usable
                    else np.nan,
                    "mean_frequency_hz": float(np.mean(frequency[method][mask]))
                    if usable
                    else np.nan,
                    "event_stride_hz": reference_frequency,
                    "evaluation_status": "scored" if usable else "insufficient_support",
                    **event_scores,
                    **(diag if method == "harmonic_ekf" else {}),
                }
            )
    common = masks["left"] & masks["right"]
    reference_difference = trial.references["left"] - trial.references["right"]
    usable = int(common.sum()) >= int(trial.fs)
    for method in METHODS:
        # The dominant comparator preserves the legacy extra right-foot pi shift.
        shift = np.pi if method == "dominant_hilbert" else 0.0
        difference = estimates["left"][method] - estimates["right"][method] - shift
        if usable:
            mean_vector = np.mean(np.exp(1j * difference[common]))
            reference_vector = np.mean(np.exp(1j * reference_difference[common]))
        pair_rows.append(
            {
                "trial": trial.trial,
                "subject": trial.subject,
                "group": trial.group,
                "pathology": trial.pathology,
                "session": trial.session,
                "fold": fold,
                "method": method,
                "n_scored_samples": int(common.sum()),
                "score_duration_s": common.sum() / trial.fs,
                "relative_phase_mae_deg": circular_mae_deg(
                    difference, reference_difference, common
                )
                if usable
                else np.nan,
                "plv": abs(mean_vector) if usable else np.nan,
                "reference_plv": abs(reference_vector) if usable else np.nan,
                "anti_phase_error_deg": abs(np.rad2deg(np.angle(-mean_vector)))
                if usable
                else np.nan,
                "evaluation_status": "scored" if usable else "insufficient_support",
            }
        )
    return audit, foot_rows, pair_rows
