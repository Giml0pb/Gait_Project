import json
import subprocess
import sys

import pandas as pd
import pytest

from gait_project.cli import main
from gait_project.demo.run import compute_case, run_demo


def test_synthetic_demo_is_reproducible_with_independent_calibration():
    first, frame1, _ = compute_case("sensor_dropout", seed=42)
    second, frame2, _ = compute_case("sensor_dropout", seed=42)
    pd.testing.assert_frame_equal(frame1, frame2)
    assert first == second
    assert first["metrics"]["harmonic_ekf"]["gap_prediction_coverage"] == 1
    assert first["metrics"]["fundamental_hilbert"]["gap_prediction_coverage"] == 0
    assert first["metrics"]["harmonic_ekf"]["relative_phase_mae_deg"] < 5
    gap = frame1.right_observation.isna()
    assert gap.any()
    assert frame1.loc[gap, "right_harmonic_ekf_phase_rad"].notna().all()
    assert frame1.loc[gap, "right_fundamental_hilbert_phase_rad"].isna().all()


def test_model_mismatch_is_exposed_instead_of_hiding_failure():
    summary, _, _ = compute_case("morphology_drift", seed=42)
    assert (
        summary["metrics"]["harmonic_ekf"]["relative_phase_mae_deg"]
        > summary["metrics"]["fundamental_hilbert"]["relative_phase_mae_deg"]
    )


def test_output_guard_preserves_unrelated_files(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("Keep this")
    with pytest.raises(ValueError, match="empty output directory"):
        run_demo(tmp_path)
    assert path.read_text() == "Keep this"


def test_numerical_export_is_dataset_free_and_repeatable(tmp_path):
    result = run_demo(tmp_path, scenario="sensor_dropout", figures=False)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["parameters"]["seed"] != manifest["parameters"]["calibration_seed"]
    assert manifest["source_sha256"]
    assert len(pd.read_csv(tmp_path / "metrics.csv")) == 3
    assert result == run_demo(tmp_path, scenario="sensor_dropout", figures=False)
    assert not (tmp_path / "report.html").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["--seed", "-1"],
        ["--noise", "nan"],
        ["--noise", "-1"],
        ["--harmonic-ratio", "0"],
    ],
)
def test_invalid_demo_parameters_fail_before_writing(arguments, tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["demo", "--output-dir", str(tmp_path), *arguments])
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())


def test_installed_module_exports_self_contained_report(tmp_path):
    destination = tmp_path / "report"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "gait_project",
            "demo",
            "--scenario",
            "sensor_dropout",
            "--output-dir",
            str(destination),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = (destination / "report.html").read_text()
    assert "data:image/png;base64," in report
    assert '<script src="http' not in report
    assert "Missing sensor observations" in report
    assert (destination / "sensor_dropout.png").stat().st_size > 1000
    assert (
        json.loads((destination / "summary.json").read_text())["parameters"][
            "sampling_rate_hz"
        ]
        == 25
    )
