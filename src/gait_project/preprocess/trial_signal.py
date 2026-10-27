"""Prepare aligned walking intervals without interpolating missing observations."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from gait_project.preprocess.signal_cleaning import detrend_signal, remove_mean
from gait_project.validation.schemas import TrialMetadataSchema


@dataclass
class PreparedSignal:
    raw: np.ndarray
    cleaned: np.ndarray
    time: np.ndarray
    walking: np.ndarray
    walking_time: np.ndarray
    segments: list[slice]
    trimmed_leading: int
    trimmed_trailing: int


def prepare_trial_signal(
    data: pd.DataFrame,
    signal_name: str,
    fs: float,
    uturn_boundaries: list[int],
    buffer_time: float = 0.2,
) -> PreparedSignal:
    """Trim common bilateral edge padding and retain original walking times.

    Missing samples at recording edges are removed using the common finite
    interval of both feet. Internal missing samples are rejected explicitly.
    The turn and its buffers separate two independent analysis segments.
    """
    TrialMetadataSchema(subject="signal", freq=fs, uturn_boundaries=uturn_boundaries)
    if not np.isfinite(buffer_time) or buffer_time < 0:
        raise ValueError("buffer_time must be finite and nonnegative")
    if signal_name not in data:
        raise ValueError(f"Signal {signal_name!r} not found")
    columns = list(
        dict.fromkeys(
            [signal_name] + [c for c in ("LF_Gyr_Y", "RF_Gyr_Y") if c in data]
        )
    )
    values = data[columns].to_numpy(dtype=float)
    finite = np.all(np.isfinite(values), axis=1)
    indices = np.flatnonzero(finite)
    if len(indices) == 0:
        raise ValueError("No common finite samples for the selected bilateral signals")
    first, stop = int(indices[0]), int(indices[-1]) + 1
    if not finite[first:stop].all():
        missing = int((~finite[first:stop]).sum())
        raise ValueError(
            f"Internal missing/nonfinite data: {missing} bilateral samples; interpolation disabled"
        )
    start_turn, end_turn = uturn_boundaries
    if end_turn > len(data):
        raise ValueError("U-turn boundaries exceed the recording length")
    raw = data[signal_name].to_numpy(dtype=float)[first:stop]
    cleaned = remove_mean(detrend_signal(raw, method="linear"))
    time = np.arange(first, stop, dtype=float) / fs
    buffer = int(buffer_time * fs)
    intervals = [
        (first, min(stop, start_turn - buffer)),
        (max(first, end_turn + buffer), stop),
    ]
    parts, times, segments = [], [], []
    offset = 0
    for start, end in intervals:
        if end <= start:
            continue
        # At least two seconds, leaving samples after the one-second edge mask.
        if end - start <= max(32, int(2 * fs)):
            raise ValueError(
                "Straight-walking segment too short: requires more than two seconds"
            )
        parts.append(cleaned[start - first : end - first])
        times.append(np.arange(start, end, dtype=float) / fs)
        segments.append(slice(offset, offset + end - start))
        offset += end - start
    if not parts:
        raise ValueError("No straight-walking samples remain after turn exclusion")
    return PreparedSignal(
        raw,
        cleaned,
        time,
        np.concatenate(parts),
        np.concatenate(times),
        segments,
        first,
        len(data) - stop,
    )
