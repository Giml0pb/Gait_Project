import numpy as np
import pytest

from gait_project.synchronization.temporal_sync import (
    analyze_temporal_synchronization,
    compute_phase_slip_rate,
    compute_windowed_plv,
)
from gait_project.synchronization.phase_sync import analyze_phase_synchronization


def test_mask_gap_cannot_create_a_slip():
    phase = np.r_[np.zeros(5), np.ones(5), np.full(5, 2.0)]
    mask = np.r_[
        np.ones(5, dtype=bool), np.zeros(5, dtype=bool), np.ones(5, dtype=bool)
    ]
    assert compute_phase_slip_rate(phase, 100, validity_mask=mask) == 0


def test_turn_gap_cannot_create_a_slip():
    phase = np.r_[np.zeros(5), np.full(5, 2.0)]
    time = np.r_[np.arange(5) / 100, 5 + np.arange(5) / 100]
    assert compute_phase_slip_rate(phase, 100, time=time) == 0


def test_real_slip_is_normalized_by_observed_adjacent_intervals():
    assert compute_phase_slip_rate(np.array([0, 0, 2, 2, 2]), 2) == pytest.approx(30)


def test_circular_boundary_crossing_is_not_a_slip():
    assert compute_phase_slip_rate(np.array([3.1, -3.1, -3.0]), 100) == 0


def test_window_centers_are_seconds_and_windows_never_cross_turn():
    time = np.r_[np.arange(8) / 4, 10 + np.arange(8) / 4]
    left, right = np.zeros(16), np.r_[np.zeros(8), np.full(8, 2.0)]
    result = compute_windowed_plv(left, right, 8, fs=4, time=time)
    np.testing.assert_allclose(result["time_centers"], [0.875, 10.875])
    np.testing.assert_allclose(result["plv_timeseries"], [1, 1])


def test_windows_keep_masked_samples_on_original_timeline():
    mask = np.tile([True, False], 8)
    result = compute_windowed_plv(
        np.zeros(16), np.zeros(16), 8, 8, fs=4, validity_mask=mask
    )
    np.testing.assert_allclose(result["time_centers"], [0.875, 2.875])
    assert result["n_windows"] == 2


def test_plv_trend_has_units_per_second():
    left = np.r_[np.zeros(4), np.zeros(4)]
    right = np.r_[np.zeros(4), [0, np.pi, 0, np.pi]]
    result = compute_windowed_plv(left, right, 4, 4, fs=2)
    assert result["plv_trend"] == pytest.approx(-0.5)


@pytest.mark.parametrize("window,step", [(1, 1), (4, 0), (4, -1)])
def test_invalid_window_parameters(window, step):
    with pytest.raises(ValueError):
        compute_windowed_plv(np.zeros(10), np.zeros(10), window, step)


def test_no_eligible_window_fails_explicitly():
    with pytest.raises(ValueError, match="No eligible temporal windows"):
        analyze_temporal_synchronization(np.zeros(3), np.zeros(3), 100, window_size=200)


def test_empty_sync_mask_fails_before_exportable_metrics_exist():
    with pytest.raises(ValueError, match="No valid synchronization"):
        analyze_phase_synchronization(
            np.zeros(10), np.zeros(10), 1, 1, np.zeros(10, dtype=bool)
        )


def test_shifted_sensor_convention_preserves_expected_antiphase():
    metrics = analyze_phase_synchronization(np.zeros(100), np.zeros(100), 1, 1)
    assert metrics["plv"] == pytest.approx(1)
    assert metrics["anti_phase_error"] == pytest.approx(0)
