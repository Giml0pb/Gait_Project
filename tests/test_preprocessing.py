import numpy as np
import pytest

from gait_project.preprocess.trial_signal import prepare_trial_signal
from gait_project.spectral.psd_analysis import compute_psd, compute_segmented_psd


def test_bilateral_edge_padding_uses_common_original_interval(synthetic_dataset):
    _, _, frame, metadata = synthetic_dataset
    left = prepare_trial_signal(frame, "LF_Gyr_Y", 100, metadata["uturnBoundaries"])
    right = prepare_trial_signal(frame, "RF_Gyr_Y", 100, metadata["uturnBoundaries"])
    assert left.trimmed_trailing == right.trimmed_trailing == 5
    np.testing.assert_array_equal(left.walking_time, right.walking_time)
    assert np.max(np.diff(left.walking_time)) > 2
    assert np.isfinite(left.walking).all()
    assert len(left.segments) == 2


def test_leading_padding_keeps_metadata_and_time_alignment(synthetic_dataset):
    _, _, frame, metadata = synthetic_dataset
    frame.loc[:6, "RF_Gyr_Y"] = np.nan
    result = prepare_trial_signal(frame, "LF_Gyr_Y", 100, metadata["uturnBoundaries"])
    assert result.trimmed_leading == 7
    assert result.time[0] == pytest.approx(0.07)
    assert result.walking_time[result.segments[1].start] == pytest.approx(12.2)


def test_internal_missing_sample_is_rejected_without_interpolation(synthetic_dataset):
    _, _, frame, metadata = synthetic_dataset
    frame.loc[100, "RF_Gyr_Y"] = np.nan
    with pytest.raises(ValueError, match="Internal missing"):
        prepare_trial_signal(frame, "LF_Gyr_Y", 100, metadata["uturnBoundaries"])


@pytest.mark.parametrize(
    "fs,bounds,buffer",
    [
        (0, [1000, 1200], 0.2),
        (100, [1200, 1000], 0.2),
        (100, [1000, 3000], 0.2),
        (100, [1000, 1200], -1),
    ],
)
def test_invalid_recording_parameters_are_rejected(
    synthetic_dataset, fs, bounds, buffer
):
    with pytest.raises(ValueError):
        prepare_trial_signal(synthetic_dataset[2], "LF_Gyr_Y", fs, bounds, buffer)


def test_segmented_psd_does_not_treat_offset_jump_as_observed_motion():
    fs = 100
    t = np.arange(1000) / fs
    signal = np.sin(2 * np.pi * 1.5625 * t)
    data = np.r_[signal, signal]
    f, psd = compute_segmented_psd(data, [slice(0, 1000), slice(1000, 2000)], fs)
    f_ref, psd_ref = compute_psd(signal, fs)
    np.testing.assert_allclose(f, f_ref)
    np.testing.assert_allclose(psd, psd_ref)
    assert f[np.argmax(psd)] == pytest.approx(1.5625)


def test_short_psd_handles_overlap_without_scipy_error():
    f, psd = compute_psd(np.sin(np.arange(32)), 100, nperseg=256, noverlap=128)
    assert len(f) == len(psd) == 17
