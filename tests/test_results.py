import pandas as pd
import pytest

from gait_project.io.results import upsert_csv
from scripts.run_batch_processing import (
    save_results_incremental,
    save_error_log,
    save_summary_report,
)


def test_repeated_checkpoints_replace_identical_trial_keys(tmp_path):
    path = tmp_path / "metrics.csv"
    rows = [{"subject": "a", "trial": "x", "plv": 0.9}]
    save_results_incremental(rows, path)
    save_results_incremental(rows + [{"subject": "a", "trial": "y", "plv": 0.8}], path)
    assert len(pd.read_csv(path)) == 2
    upsert_csv(
        pd.DataFrame([{"subject": "a", "trial": "x", "plv": 0.7}]),
        path,
        ["subject", "trial"],
    )
    assert pd.read_csv(path).set_index("trial").loc["x", "plv"] == 0.7
    assert not list(tmp_path.glob("*.tmp"))


def test_failed_update_preserves_existing_csv(tmp_path):
    path = tmp_path / "metrics.csv"
    original = pd.DataFrame([{"subject": "a", "trial": "x"}])
    upsert_csv(original, path, ["subject", "trial"])
    before = path.read_bytes()
    with pytest.raises(ValueError):
        upsert_csv(
            pd.DataFrame([{"subject": None, "trial": "x"}]), path, ["subject", "trial"]
        )
    assert path.read_bytes() == before


def test_empty_error_log_clears_stale_errors(tmp_path):
    save_error_log([{"trial": "x", "error_message": "old"}], tmp_path)
    save_error_log([], tmp_path)
    assert pd.read_csv(tmp_path / "tables/processing_errors.csv").empty


def test_empty_summary_does_not_divide_by_zero(tmp_path):
    save_summary_report([], [], 0, tmp_path)
    assert (
        "Total trials attempted: 0"
        in (tmp_path / "reports/batch_processing_summary.txt").read_text()
    )


def test_interrupted_csv_write_preserves_last_complete_table(tmp_path, monkeypatch):
    from gait_project.io.results import write_csv_atomic

    path = tmp_path / "metrics.csv"
    original = pd.DataFrame([{"trial": "x", "plv": 0.9}])
    write_csv_atomic(original, path)
    before = path.read_bytes()

    def interrupted(self, stream, **kwargs):
        stream.write("partial output")
        raise OSError("simulated interruption")

    monkeypatch.setattr(pd.DataFrame, "to_csv", interrupted)
    with pytest.raises(OSError, match="simulated interruption"):
        write_csv_atomic(original, path)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))
