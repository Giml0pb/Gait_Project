# Aggregate dataset benchmark

`summary.json` records the aggregate output of the optional phase-validity study over 1,356 trials from 260 participants. It contains no participant-level signals or identifiers.

To reproduce the benchmark, obtain the source dataset described in [the dataset guide](../../docs/dataset_structure.md), then run:

```bash
uv run python scripts/validate_phase_model.py --output-dir outputs/phase_validation
uv run python scripts/export_showcase.py --study-dir outputs/phase_validation
```

The [results document](../../docs/phase_validation_results.md) explains event-reference limitations, participant splits, exclusions and estimator failures.
