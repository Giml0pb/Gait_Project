# Documentation

## Technical entry points

| Document | Purpose |
| --- | --- |
| [Technical walkthrough](technical_walkthrough.md) | Follow the runnable demo through DSP, identification, EKF updates, uncertainty diagnostics and tests |
| [EKF formulation — ES](phase_state_space.md) | State, dynamics, Jacobian, covariance assumptions and identifiability |
| [Validation protocol — ES](phase_validation_protocol.md) | Participant splits, synthetic stress cases, masks and metrics |
| [Benchmark results — ES](phase_validation_results.md) | Full numerical comparison, retained failures and interpretation |
| [Dataset guide — ES](dataset_structure.md) | Optional source-data layout, loading API, processing conventions and attribution |

The synthetic demo is sufficient to run and inspect the main technical components. The optional research dataset is needed only to reproduce the full participant benchmark. Aggregate figures and summaries are committed; record-level data and local run folders are not included.

Earlier development reports and superseded instructions remain available in Git history.
