import numpy as np
import pandas as pd
import pytest

from scripts.aggregate_by_patient import aggregate_by_patient
from gait_project.analysis.subject_analysis import aggregate_subject_metrics


def test_patient_angle_mean_handles_wrap_boundary():
    frame = pd.DataFrame({"subject": ["a", "a"], "mean_phase_diff_deg": [179, -179]})
    result = aggregate_by_patient(frame)
    assert abs(result.mean_phase_diff_deg.iloc[0]) == pytest.approx(180)


def test_antipodal_angles_have_no_identifiable_mean():
    frame = pd.DataFrame({"subject": ["a", "a"], "mean_phase_diff_deg": [0, 180]})
    assert np.isnan(aggregate_by_patient(frame).mean_phase_diff_deg.iloc[0])


def test_repeated_sessions_are_reported_and_single_trial_std_is_unknown():
    frame = pd.DataFrame(
        {"subject": ["a", "a", "b"], "session": [1, 2, 1], "plv": [0.9, 0.8, 0.9]}
    )
    result = aggregate_by_patient(frame).set_index("subject")
    assert result.loc["a", "n_sessions"] == 2
    assert np.isnan(result.loc["a", "session"])
    assert np.isnan(result.loc["b", "plv_std"])


def test_generic_aggregation_skips_string_metadata_and_uses_circular_mean():
    result = aggregate_subject_metrics(
        [
            {"subject": "a", "group": "healthy", "mean_phase_diff_deg": 179},
            {"subject": "a", "group": "healthy", "mean_phase_diff_deg": -179},
        ]
    )
    assert result.group.iloc[0] == "healthy"
    assert abs(result.mean_phase_diff_deg_mean.iloc[0]) == pytest.approx(180)


def test_conflicting_participant_metadata_is_rejected():
    with pytest.raises(ValueError, match="Conflicting group"):
        aggregate_by_patient(
            pd.DataFrame({"subject": ["a", "a"], "group": ["healthy", "neuro"]})
        )


def test_duplicate_trials_are_rejected():
    with pytest.raises(ValueError, match="Duplicate trials"):
        aggregate_by_patient(pd.DataFrame({"subject": ["a", "a"], "trial": ["x", "x"]}))
