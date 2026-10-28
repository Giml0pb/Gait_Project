# Reproducible synthetic example

Generated using the installed `gait-lab` command, without clinical data:

```bash
uv run gait-lab demo --seed 42 --noise 0.1 --harmonic-ratio 3
uv run python scripts/export_showcase.py
```

`summary.json` records per-scenario metrics, identified templates and uncertainty summaries. `metrics.csv` is a compact numerical comparison; `uncertainty_runs.csv` retains all 40 runs of the fixed/changing-waveform uncertainty check, without retuning EKF noise. `manifest.json` records the environment, seeds, parameter values and package source hashes. The report, figures and full time series are regenerated under `outputs/demo/`.

The calibration record uses a distinct seed. Its phase is known because the record is synthetic. Test-record ground truth is used only for evaluation. The morphology-drift scenario intentionally violates the fixed-template observation model.
