from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from gait_project.demo.uncertainty import run_uncertainty_check, uncertainty_metrics


def test_coverage_uses_circular_errors_and_nis_excludes_missing_updates():
    result = SimpleNamespace(
        phase=np.array([np.nan, 2 * np.pi + 0.1, 0.3, 0.1]),
        variance_phase=np.full(4, 0.01),
        score_mask=np.array([False, True, True, True]),
        innovation=np.array([np.nan, 2, np.nan, 4]),
        innovation_variance=np.array([np.nan, 4, np.nan, 4]),
    )
    metrics = uncertainty_metrics(result, np.zeros(4))
    assert metrics["coverage_95"] == pytest.approx(2 / 3)
    assert metrics["mean_nis"] == pytest.approx(2.5)
    assert metrics["scored_samples"] == 3
    assert metrics["innovation_samples"] == 2
    assert metrics["innovation_lag1"] is None


def test_uncertainty_experiment_is_reproducible_and_retains_mismatch():
    summary, runs = run_uncertainty_check(repetitions=3)
    repeated, again = run_uncertainty_check(repetitions=3)
    pd.testing.assert_frame_equal(runs, again)
    assert summary == repeated
    assert len(runs) == 6
    assert not summary["noise_parameters_retuned"]
    fixed, changed = summary["conditions"]
    assert (
        fixed["metrics"]["coverage_95"]["median"]
        > changed["metrics"]["coverage_95"]["median"]
    )
    assert (
        fixed["metrics"]["phase_mae_deg"]["median"]
        < changed["metrics"]["phase_mae_deg"]["median"]
    )
    assert (
        runs.groupby("scenario").seed.apply(list).iloc[0]
        == runs.groupby("scenario").seed.apply(list).iloc[1]
    )
