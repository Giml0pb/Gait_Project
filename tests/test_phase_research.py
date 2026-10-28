import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from gait_project.research.phase_estimators import estimate_fundamental, hilbert_phase
from gait_project.research.phase_reference import (
    circular_mae_deg,
    event_phase_reference,
)
from gait_project.research.phase_validation import (
    make_participant_folds,
    training_templates,
)
from gait_project.state_space.harmonic_ekf import (
    HarmonicTemplate,
    estimate_phase_ekf,
    fit_template,
)


def test_fundamental_estimator_recovers_weak_first_harmonic():
    fs = 25
    t = np.arange(25 * 24) / fs
    signal = np.cos(2 * np.pi * 0.9 * t) + 4 * np.cos(2 * np.pi * 1.8 * t)
    estimate = estimate_fundamental(signal, fs, [slice(0, len(t))])
    assert estimate.frequency_hz == pytest.approx(0.9, abs=0.015)
    assert estimate.spectral_resolution_hz == pytest.approx(1 / 24)


def test_fundamental_estimator_does_not_automatically_halve_sinusoid():
    t = np.arange(600) / 25
    estimate = estimate_fundamental(np.cos(2 * np.pi * 1.2 * t), 25, [slice(0, 600)])
    assert estimate.frequency_hz == pytest.approx(1.2, abs=0.015)


def test_reference_does_not_interpolate_across_a_turn():
    t = np.r_[np.arange(0, 3, 0.1), np.arange(10, 13, 0.1)]
    events = np.array([[0, 0], [9, 10], [19, 20], [109, 110], [119, 120]])
    reference, durations = event_phase_reference(
        t, events, 10, [slice(0, 30), slice(30, 60)]
    )
    assert np.isnan(reference[25])
    assert np.isnan(reference[30])
    assert np.isfinite(reference[45])
    np.testing.assert_allclose(durations, [1, 1, 1])


def test_reference_requires_ordered_events():
    with pytest.raises(ValueError, match="strictly increasing"):
        event_phase_reference(
            np.arange(100) / 10, [[1, 30], [2, 20]], 10, [slice(0, 100)]
        )


def test_circular_error_handles_wrap_boundary():
    assert circular_mae_deg(np.deg2rad([179]), np.deg2rad([-179])) == pytest.approx(2)


def test_even_harmonics_cannot_identify_half_cycle_branch():
    template = HarmonicTemplate([0, 0, 0, 1, 0.2, 0, 0])
    phase = np.linspace(0, 2 * np.pi, 100)
    np.testing.assert_allclose(
        template.evaluate(phase), template.evaluate(phase + np.pi), atol=1e-12
    )
    assert template.odd_power_fraction == 0


def test_ekf_tracks_known_phase_and_predicts_during_dropout():
    fs = 25
    t = np.arange(600) / fs
    truth = 0.4 + 2 * np.pi * 0.9 * t
    template = HarmonicTemplate([0, 1, 0.1, 0.6, 0.2, 0.1, 0])
    rng = np.random.default_rng(7)
    values = template.evaluate(truth) + rng.normal(0, 0.02, len(t))
    values[250:275] = np.nan
    result = estimate_phase_ekf(values, fs, 0.9, template)
    assert circular_mae_deg(result.phase, truth, result.score_mask) < 8
    assert np.isfinite(result.phase[250:275]).all()
    assert result.missing_prediction_count == 25
    assert result.variance_phase[274] > result.variance_phase[249]
    assert np.nanmin(result.variance_phase) >= 0
    assert not result.initialization_ambiguity
    stop = result.initialization_stop
    assert np.isnan(result.phase[:stop]).all()
    assert np.isnan(result.innovation[:stop]).all()
    assert result.update_count == np.isfinite(values[stop:]).sum()
    assert result.update_count + result.missing_prediction_count == len(values) - stop
    assert np.isnan(result.innovation[250:275]).all()
    assert np.isnan(result.innovation_variance[250:275]).all()
    assert np.isfinite(result.innovation[275])


def test_initialization_only_record_has_no_recursive_updates():
    template = HarmonicTemplate([0, 1, 0.1])
    time = np.arange(40) / 25
    result = estimate_phase_ekf(
        template.evaluate(2 * np.pi * 0.9 * time), 25, 0.9, template
    )
    assert result.initialization_stop == len(time)
    assert result.update_count == result.missing_prediction_count == 0
    assert np.isnan(result.phase).all()
    assert not result.score_mask.any()


def test_ekf_reports_even_harmonic_ambiguity():
    template = HarmonicTemplate([0, 0, 0, 1, 0, 0, 0])
    t = np.arange(400) / 25
    result = estimate_phase_ekf(
        template.evaluate(2 * np.pi * 0.9 * t), 25, 0.9, template
    )
    assert result.initialization_ambiguity


def test_hilbert_keeps_missing_observations_missing():
    t = np.arange(600) / 25
    values = np.cos(2 * np.pi * 0.9 * t)
    values[250:275] = np.nan
    phase, _ = hilbert_phase(values, 25, [slice(0, 600)], 0.9)
    assert np.isnan(phase[250:275]).all()


def test_harmonic_template_derivative_matches_finite_difference():
    template = HarmonicTemplate([0, 1, 0.2, 0.4, 0.1, 0.2, 0.3])
    x, step = 0.7, 1e-6
    expected = (template.evaluate(x + step) - template.evaluate(x - step)) / (2 * step)
    assert template.derivative(x) == pytest.approx(expected, rel=1e-7)


def test_fitted_template_uses_shared_heel_strike_phase_origin():
    phase = np.linspace(0, 20 * np.pi, 1000)
    original = HarmonicTemplate([0, 1, 0.2, 2, 0.3, 0.2, 0.1])
    fitted = fit_template(original.evaluate(phase), phase)
    np.testing.assert_allclose(fitted.coefficients, original.coefficients, atol=1e-10)


def test_participant_folds_are_reproducible_and_keep_each_person_once():
    participants = {f"p{i}": "CVA" if i < 6 else "HS" for i in range(12)}
    first = make_participant_folds(participants, 3, 7)
    assert first == make_participant_folds(participants, 3, 7)
    assert set(first) == set(participants)
    assert set(first.values()) == {0, 1, 2}


def test_held_out_annotations_cannot_change_training_template():
    from types import SimpleNamespace

    trials = [
        SimpleNamespace(
            subject="train",
            training_coefficients={
                s: np.array([0, 1, 0, 2, 0, 0, 0]) for s in ("left", "right")
            },
        ),
        SimpleNamespace(
            subject="test",
            training_coefficients={s: np.full(7, 999) for s in ("left", "right")},
        ),
    ]
    templates = training_templates(trials, {"train": 0, "test": 1}, 1)
    assert templates["left"].coefficients[1] == 1
    trials[1].training_coefficients["left"][:] = -999
    again = training_templates(trials, {"train": 0, "test": 1}, 1)
    np.testing.assert_array_equal(
        templates["left"].coefficients, again["left"].coefficients
    )


def test_study_cli_cross_fits_synthetic_participants(synthetic_dataset, tmp_path):
    base, folder, frame, metadata = synthetic_dataset
    fs = metadata["freq"]
    time = np.arange(len(frame)) / fs
    for index in (1, 2):
        name = f"HS_{index}_1"
        path = base / f"healthy/HS/HS_{index}/{name}"
        path.mkdir(parents=True, exist_ok=True)
        signal = np.cos(2 * np.pi * 0.9 * time) + 2 * np.cos(2 * np.pi * 1.8 * time)
        pd.DataFrame(
            {
                "LF_Gyr_Y": signal,
                "RF_Gyr_Y": np.cos(2 * np.pi * 0.9 * time - np.pi)
                + 2 * np.cos(2 * np.pi * 1.8 * time - 2 * np.pi),
            }
        ).to_csv(path / f"{name}_processed_data.txt", sep="\t", index=False)
        data = {**metadata, "subject": f"HS_{index}"}
        for side, offset in (("left", 0), ("right", 0.5 / 0.9)):
            strikes = np.arange(1 + offset, 23, 1 / 0.9)
            data[f"{side}GaitEvents"] = [
                [int((s - 0.4) * fs), int(s * fs)] for s in strikes
            ]
        (path / f"{name}_meta.json").write_text(json.dumps(data))
    root = Path(__file__).resolve().parents[1]
    destination = tmp_path / "phase_study"
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_phase_model.py"),
            "--data-dir",
            str(base),
            "--output-dir",
            str(destination),
            "--folds",
            "2",
            "--simulation-repetitions",
            "1",
            "--skip-figures",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((destination / "run_manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["summary"]["trials_compared"] == 2
    for fold in manifest["folds"].values():
        assert not set(fold["training_subjects"]) & set(fold["validation_subjects"])
    feet = pd.read_csv(destination / "tables/foot_phase_comparison.csv")
    assert set(feet.method) == {
        "dominant_hilbert",
        "fundamental_hilbert",
        "harmonic_ekf",
    }


def test_scoring_excludes_hilbert_edges_at_internal_gaps():
    from gait_project.research.phase_validation import estimate_methods

    t = np.arange(600) / 25
    template = HarmonicTemplate([0, 1, 0.1, 0.6, 0.1, 0.1, 0])
    values = template.evaluate(2 * np.pi * 0.9 * t)
    values[250:275] = np.nan
    _, _, mask, _, _ = estimate_methods(values, 25, [slice(0, 600)], 0.9, 0.9, template)
    assert not mask[225:300].any()
    assert mask[400]


def test_extra_phase_cycles_count_as_false_positive_events():
    from gait_project.research.phase_reference import heel_strike_scores

    fs = 100
    time = np.arange(0.01, 4.99, 1 / fs)
    mask = np.ones(len(time), dtype=bool)
    scores = heel_strike_scores(4 * np.pi * time, time, [1, 2, 3, 4], mask, fs)
    assert scores["event_true_positives"] == 4
    assert scores["event_false_positives"] == 5
    assert scores["event_false_negatives"] == 0
    assert scores["event_f1"] == pytest.approx(8 / 13)
    assert scores["matched_event_mae_s"] < 1e-6


def test_unobserved_reference_events_are_not_counted_as_false_negatives():
    from gait_project.research.phase_reference import heel_strike_scores

    time = np.arange(500) / 100
    mask = np.ones(500, dtype=bool)
    mask[150:250] = False
    scores = heel_strike_scores(2 * np.pi * time, time, [1, 2, 3, 4], mask, 100)
    assert scores["event_false_negatives"] == 0
    assert scores["n_reference_events"] == 3
