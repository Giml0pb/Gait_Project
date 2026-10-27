"""Aggregation rules shared by participant summaries."""

import numpy as np


ANGLE_PERIODS = {
    "mean_phase_diff_deg": 360.0,
    "mean_phase_diff": 2 * np.pi,
    "circular_mean": 2 * np.pi,
}


def mean_metric(name, values):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if not len(values):
        return np.nan
    if name not in ANGLE_PERIODS:
        return float(values.mean())
    radians = values * (2 * np.pi / ANGLE_PERIODS[name])
    vector = np.mean(np.exp(1j * radians))
    # Antipodal or uniform directions have no identifiable mean direction.
    if abs(vector) < 1e-10:
        return np.nan
    return float(np.angle(vector) * ANGLE_PERIODS[name] / (2 * np.pi))
