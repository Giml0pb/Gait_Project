"""Signal-only spectral selection and segment-aware Hilbert comparators."""

from dataclasses import dataclass

import numpy as np
from scipy import signal

from gait_project.phase.hilbert_transform import compute_all_instantaneous_attributes
from gait_project.phase.narrowband_filter import apply_narrowband_filter
from gait_project.spectral.dominant_frequency import find_dominant_frequency
from gait_project.spectral.psd_analysis import compute_segmented_psd


@dataclass
class FrequencyEstimate:
    frequency_hz: float
    fundamental_power_fraction: float
    weak_fundamental: bool
    spectral_resolution_hz: float


def finite_segments(values, segments, minimum=32):
    """Split at missing observations rather than interpolate them."""
    result = []
    for part in segments:
        valid = np.isfinite(values[part])
        boundaries = np.diff(np.r_[False, valid, False].astype(int))
        for first, stop in zip(
            np.flatnonzero(boundaries == 1), np.flatnonzero(boundaries == -1)
        ):
            if stop - first >= minimum:
                result.append(slice(part.start + first, part.start + stop))
    if not result:
        raise ValueError("No sufficiently long finite signal segments")
    return result


def estimate_fundamental(
    values, fs, segments, frequency_range=(0.25, 2.0), harmonics=3
):
    """Maximize a spectral harmonic sum without consulting reference events.

    The first three harmonics have equal weights, with a 0.1% first-harmonic
    tie preference to avoid choosing unsupported subharmonics of a sinusoid.
    The fraction of their power
    at the fundamental is exposed as an ambiguity diagnostic. Zero padding
    refines the search grid, not the independent frequency resolution.
    """
    values = np.asarray(values, dtype=float)
    segments = finite_segments(values, segments, minimum=max(32, int(2 * fs)))
    nperseg = min(len(values[s]) for s in segments)
    nfft = max(4096, 1 << int(np.ceil(np.log2(4 * nperseg))))
    spectra, weights = [], []
    for part in segments:
        freqs, power = signal.welch(
            values[part], fs=fs, nperseg=nperseg, noverlap=nperseg // 2, nfft=nfft
        )
        spectra.append(power)
        weights.append(1 + (len(values[part]) - nperseg) // (nperseg - nperseg // 2))
    power = np.average(spectra, weights=weights, axis=0)
    if power.max() <= np.finfo(float).eps:
        raise ValueError("Cannot identify frequency from a constant signal")
    lower, upper = frequency_range
    if not 0 < lower < upper or harmonics < 1 or upper * harmonics >= fs / 2:
        raise ValueError("Invalid fundamental frequency search settings")
    candidates = np.arange(lower, upper + 0.0025, 0.005)
    components = np.array(
        [np.interp(k * candidates, freqs, power) for k in range(1, harmonics + 1)]
    )
    total = components.sum(axis=0)
    score = total + 0.001 * components[0]
    best = int(np.argmax(score))
    fraction = float(components[0, best] / total[best])
    return FrequencyEstimate(
        float(candidates[best]), fraction, fraction < 0.05, fs / nperseg
    )


def legacy_dominant(values, fs, segments):
    parts = finite_segments(values, segments, minimum=max(32, int(2 * fs)))
    freqs, power = compute_segmented_psd(values, parts, fs, 256, 128)
    return float(find_dominant_frequency(freqs, power, (0.5, 3.0)))


def hilbert_phase(values, fs, segments, frequency_hz, phase_offset=0.0):
    """Filter each observed segment; outputs remain missing across dropouts."""
    phase = np.full(len(values), np.nan)
    frequency = np.full(len(values), np.nan)
    for part in finite_segments(values, segments, minimum=max(32, int(2 * fs))):
        bandwidth = min(0.3, 0.45 * frequency_hz)
        filtered = apply_narrowband_filter(values[part], fs, frequency_hz, bandwidth)
        _, _, unwrapped, instantaneous = compute_all_instantaneous_attributes(
            filtered, fs
        )
        phase[part] = unwrapped + phase_offset
        frequency[part] = instantaneous
    return phase, frequency
