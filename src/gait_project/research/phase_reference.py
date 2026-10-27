"""Event-normalized phase conventions, not independent biomechanical truth."""

import numpy as np


def event_phase_reference(time, events, fs, segments):
    """Interpolate phase between ipsilateral heel strikes within each segment.

    Each complete heel-strike interval is assigned one cycle. No interpolation
    crosses a recording gap or a turn. Input events are [toe-off, heel-strike].
    Returns a phase array with NaNs outside complete annotated strides, and
    durations of those strides. These events are algorithm-derived references.
    """
    time = np.asarray(time, dtype=float)
    events = np.asarray(events, dtype=float)
    if events.ndim != 2 or events.shape[1] != 2 or not np.isfinite(events).all():
        raise ValueError(
            "Gait events must be a finite array of toe-off/heel-strike pairs"
        )
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("Sampling frequency must be positive and finite")
    strikes = events[:, 1] / fs
    if len(strikes) > 1 and np.any(np.diff(strikes) <= 0):
        raise ValueError("Heel strikes must be strictly increasing")
    phase = np.full(len(time), np.nan)
    durations = []
    for segment in segments:
        t = time[segment]
        for index, (first, last) in enumerate(zip(strikes[:-1], strikes[1:])):
            if first < t[0] or last > t[-1]:
                continue
            mask = (t >= first) & (t <= last)
            local = phase[segment]
            local[mask] = 2 * np.pi * (index + (t[mask] - first) / (last - first))
            durations.append(last - first)
    return phase, np.asarray(durations)


def circular_mae_deg(estimate, reference, mask=None):
    estimate, reference = np.asarray(estimate), np.asarray(reference)
    valid = np.isfinite(estimate) & np.isfinite(reference)
    if mask is not None:
        valid &= mask
    if not valid.any():
        return np.nan
    error = np.angle(np.exp(1j * (estimate[valid] - reference[valid])))
    return float(np.rad2deg(np.abs(error).mean()))


def heel_strike_scores(phase, time, strikes, mask, fs, tolerance_s=0.15):
    """Match phase-zero crossings one-to-one to eligible annotated heel strikes.

    Both predicted and reference events must fall within adjacent scored sample
    intervals. Unmatched crossings count as false positives; nearest-neighbor
    timing alone would conceal a doubled cycle count.
    """
    from scipy.optimize import linear_sum_assignment

    phase, time, mask = np.asarray(phase), np.asarray(time), np.asarray(mask)
    eligible = mask[:-1] & mask[1:] & np.isfinite(phase[:-1]) & np.isfinite(phase[1:])
    eligible &= np.isclose(np.diff(time), 1 / fs, rtol=1e-5, atol=1e-9)
    predicted = []
    for index in np.flatnonzero(eligible):
        first, last = phase[index], phase[index + 1]
        if last <= first:
            continue
        start_cycle, stop_cycle = (
            int(np.floor(first / (2 * np.pi))) + 1,
            int(np.floor(last / (2 * np.pi))),
        )
        for cycle in range(start_cycle, stop_cycle + 1):
            fraction = (2 * np.pi * cycle - first) / (last - first)
            predicted.append(time[index] + fraction * (time[index + 1] - time[index]))
    reference = []
    for strike in strikes:
        index = int(np.searchsorted(time, strike, side="right")) - 1
        if 0 <= index < len(eligible) and eligible[index] and strike <= time[index + 1]:
            reference.append(strike)
    predicted, reference = np.asarray(predicted), np.asarray(reference)
    errors = []
    if len(predicted) and len(reference):
        distance = np.abs(predicted[:, None] - reference[None, :])
        row, col = linear_sum_assignment(
            np.where(distance <= tolerance_s, distance, 1e6)
        )
        errors = distance[row, col][distance[row, col] <= tolerance_s]
    matched = len(errors)
    return {
        "event_true_positives": matched,
        "event_false_positives": len(predicted) - matched,
        "event_false_negatives": len(reference) - matched,
        "n_reference_events": len(reference),
        "event_f1": 2 * matched / (len(predicted) + len(reference))
        if len(predicted) + len(reference)
        else np.nan,
        "matched_event_mae_s": float(np.mean(errors)) if len(errors) else np.nan,
    }
