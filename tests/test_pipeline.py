import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from gait_project.pipeline_phase3 import Phase3Pipeline
from gait_project.pipeline_phase1 import Phase1Pipeline
from gait_project.validation import validate_phase3_metrics


def test_complete_pipeline_retains_alignment_and_exports_once(
    synthetic_dataset, tmp_path
):
    pipeline = Phase3Pipeline(str(synthetic_dataset[0]), str(tmp_path / "outputs"))
    pipeline.generate_figures = False
    metrics = pipeline.run("HS_1_1")
    assert metrics["plv"] > 0.99
    assert metrics["anti_phase_error"] < 0.01
    assert pipeline.phase2_left.prepared.trimmed_trailing == 5
    np.testing.assert_array_equal(pipeline.phase2_left.time, pipeline.phase2_right.time)
    for part in pipeline.phase2_left.prepared.segments:
        assert not pipeline.validity_mask_left[part.start]
        assert not pipeline.validity_mask_left[part.stop - 1]
    pipeline.run("HS_1_1")
    assert (
        len(pd.read_csv(tmp_path / "outputs/tables/synchronization_summary.csv")) == 1
    )
    assert len(pd.read_csv(tmp_path / "outputs/tables/phase_summary.csv")) == 2


def test_invalid_sync_metrics_are_not_exported(
    synthetic_dataset, tmp_path, monkeypatch
):
    output = tmp_path / "invalid"
    pipeline = Phase3Pipeline(str(synthetic_dataset[0]), str(output))
    pipeline.generate_figures = False
    original = pipeline._analyze_synchronization

    def corrupt():
        original()
        pipeline.metrics["plv"] = np.nan

    monkeypatch.setattr(pipeline, "_analyze_synchronization", corrupt)
    with pytest.raises(ValueError, match="validation failed"):
        pipeline.run("HS_1_1")
    assert not list(output.rglob("*.csv"))


def test_phase1_zero_signal_is_not_exported(synthetic_dataset, tmp_path):
    base, folder, frame, _ = synthetic_dataset
    frame[:] = 0
    frame.to_csv(folder / "HS_1_1_processed_data.txt", sep="\t", index=False)
    pipeline = Phase1Pipeline(str(base), str(tmp_path / "invalid"))
    pipeline.generate_figures = False
    with pytest.raises(ValueError):
        pipeline.run("HS_1_1")
    assert not list((tmp_path / "invalid").rglob("*.csv"))


def test_schema_enforces_cross_metric_consistency(synthetic_dataset, tmp_path):
    pipeline = Phase3Pipeline(str(synthetic_dataset[0]), str(tmp_path / "outputs"))
    pipeline.generate_figures = False
    metrics = pipeline.run("HS_1_1")
    with pytest.raises(ValueError, match="Circular variance"):
        validate_phase3_metrics({**metrics, "circular_variance": 0.5})


def test_batch_cli_records_provenance_and_refuses_run_mixing(
    synthetic_dataset, tmp_path
):
    output = tmp_path / "run"
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        str(root / "scripts/run_batch_processing.py"),
        "--target",
        "1",
        "--groups",
        "healthy",
        "--data-dir",
        str(synthetic_dataset[0]),
        "--output-dir",
        str(output),
    ]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((output / "run_manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["successful"] == 1
    assert manifest["source_sha256"]
    master = pd.read_csv(output / "tables/master_metrics.csv")
    assert len(master.input_sha256.iloc[0]) == 64
    assert len(pd.read_csv(output / "tables/patient_aggregated_metrics.csv")) == 1
    second = subprocess.run(command, cwd=root, capture_output=True, text=True)
    assert second.returncode == 1
    assert "already contains a run" in second.stdout
