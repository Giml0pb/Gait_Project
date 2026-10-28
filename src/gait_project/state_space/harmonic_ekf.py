"""Experimental four-state EKF with a periodic Fourier observation model.

The states are phase (rad), angular frequency (rad/s), positive amplitude and
bias. Feet are estimated independently; no antiphase or coupling is imposed.
Initialization profiles the first two nominal cycles of active observations.
Those samples are reserved for initialization and never corrected a second time.
The benchmark is offline: its initial frequency uses the full observed signal.
"""

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter1d


@dataclass
class HarmonicTemplate:
    coefficients: np.ndarray

    def __post_init__(self):
        self.coefficients = np.asarray(self.coefficients, dtype=float).copy()
        if (
            self.coefficients.ndim != 1
            or len(self.coefficients) < 3
            or len(self.coefficients) % 2 != 1
            or not np.isfinite(self.coefficients).all()
        ):
            raise ValueError(
                "Fourier coefficients must be finite: [bias, cos1, sin1, ...]"
            )

    def evaluate(self, phase):
        result = np.zeros_like(np.asarray(phase), dtype=float) + self.coefficients[0]
        for k in range(1, (len(self.coefficients) + 1) // 2):
            result += self.coefficients[2 * k - 1] * np.cos(
                k * phase
            ) + self.coefficients[2 * k] * np.sin(k * phase)
        return result

    def derivative(self, phase):
        result = 0.0
        for k in range(1, (len(self.coefficients) + 1) // 2):
            result += k * (
                -self.coefficients[2 * k - 1] * np.sin(k * phase)
                + self.coefficients[2 * k] * np.cos(k * phase)
            )
        return result

    def phase_offset(self, harmonic=1):
        return float(
            np.arctan2(
                self.coefficients[2 * harmonic], self.coefficients[2 * harmonic - 1]
            )
        )

    @property
    def odd_power_fraction(self):
        powers = self.coefficients[1:].reshape(-1, 2) ** 2
        return float(powers[::2].sum() / max(powers.sum(), np.finfo(float).eps))


def fit_template(values, phase, harmonics=3):
    """Fit only on the caller's training references; never on held-out events."""
    values, phase = np.asarray(values), np.asarray(phase)
    valid = np.isfinite(values) & np.isfinite(phase)
    if valid.sum() < 10 * (2 * harmonics + 1):
        raise ValueError("Insufficient annotated training samples for a template")
    phase, values = phase[valid], values[valid]
    columns = [np.ones(len(phase))]
    for k in range(1, harmonics + 1):
        columns.extend([np.cos(k * phase), np.sin(k * phase)])
    design = np.column_stack(columns)
    coefficients = np.linalg.lstsq(design, values, rcond=None)[0]
    coefficients[0] = 0  # The filter estimates its own recording-specific bias.
    return HarmonicTemplate(coefficients)


@dataclass
class EKFResult:
    phase: np.ndarray
    frequency_hz: np.ndarray
    variance_phase: np.ndarray
    score_mask: np.ndarray
    initialization_ambiguity: bool
    update_count: int
    missing_prediction_count: int
    frequency_bound_hits: int
    amplitude_bound_hits: int
    initialization_stop: int
    innovation: np.ndarray
    innovation_variance: np.ndarray


def normalized_signal(values):
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if not len(finite):
        raise ValueError("No finite signal observations")
    scale = np.percentile(np.abs(finite), 95)
    if scale <= np.finfo(float).eps:
        raise ValueError("No observable signal variation")
    return values / scale


def estimate_phase_ekf(
    values,
    fs,
    initial_frequency_hz,
    template,
    observation_std=0.15,
    frequency_diffusion=0.025,
    amplitude_diffusion=0.03,
    bias_diffusion=0.03,
):
    """Estimate one continuous segment; NaNs trigger prediction-only steps.

    Covariances are approximate EKF uncertainties, not calibrated confidence
    intervals. A weak odd-harmonic template is explicitly flagged as ambiguous.
    """
    values = normalized_signal(values)
    if not np.isfinite(fs) or fs <= 0 or not 0.25 <= initial_frequency_hz <= 2.0:
        raise ValueError("Invalid sampling rate or initial frequency")
    noise = np.array(
        [observation_std, frequency_diffusion, amplitude_diffusion, bias_diffusion]
    )
    if not np.isfinite(noise).all() or observation_std <= 0 or (noise[1:] < 0).any():
        raise ValueError("Noise standard deviations must be valid")
    n = len(values)
    finite = np.isfinite(values)
    power = uniform_filter1d(np.where(finite, values, 0.0) ** 2, max(1, int(0.25 * fs)))
    envelope = np.sqrt(np.maximum(power, 0.0))
    active = np.flatnonzero((envelope > 0.15 * np.percentile(envelope, 95)) & finite)
    if not len(active):
        raise ValueError("No active observations for EKF initialization")
    start = int(active[0])
    warmup = max(int(2 * fs / initial_frequency_hz), int(2 * fs))
    stop = min(n, start + warmup)
    if stop - start < fs or finite[start:stop].sum() < fs:
        raise ValueError("Insufficient active observations for EKF initialization")
    times = np.arange(stop - start) / fs
    valid = finite[start:stop]
    # Profile amplitude/bias over a phase grid; no test events enter this search.
    candidates = np.linspace(-np.pi, np.pi, 96, endpoint=False)
    errors, parameters = [], []
    for offset in candidates:
        model = template.evaluate(offset + 2 * np.pi * initial_frequency_hz * times)
        design = np.column_stack([model[valid], np.ones(valid.sum())])
        amplitude, bias = np.linalg.lstsq(
            design, values[start:stop][valid], rcond=None
        )[0]
        amplitude = max(0.05, amplitude)
        errors.append(
            np.mean((values[start:stop][valid] - amplitude * model[valid] - bias) ** 2)
        )
        parameters.append((amplitude, bias))
    best = int(np.argmin(errors))
    opposite = (best + len(candidates) // 2) % len(candidates)
    ambiguous = template.odd_power_fraction < 0.05 or errors[opposite] <= 1.05 * max(
        errors[best], 1e-12
    )
    amplitude, bias = parameters[best]
    # Place the fitted state at the LAST initialization sample. Corrections
    # start at `stop`, after one prediction; the bootstrap data are not reused.
    omega = 2 * np.pi * initial_frequency_hz
    state = np.array([candidates[best] + omega * times[-1], omega, amplitude, bias])
    # Operational uncertainty at the bootstrap boundary, not a fitted posterior.
    covariance = np.diag([0.3**2, (2 * np.pi * 0.1) ** 2, 0.3**2, 0.2**2])
    dt = 1 / fs
    transition = np.eye(4)
    transition[0, 1] = dt
    process = np.diag(
        [
            0,
            (2 * np.pi * frequency_diffusion) ** 2 * dt,
            amplitude_diffusion**2 * dt,
            bias_diffusion**2 * dt,
        ]
    )
    identity = np.eye(4)
    phases, frequencies, variances = [np.full(n, np.nan) for _ in range(3)]
    innovations, innovation_variances = [np.full(n, np.nan) for _ in range(2)]
    updates, predictions, frequency_hits, amplitude_hits = 0, 0, 0, 0
    orders = np.arange(1, (len(template.coefficients) + 1) // 2)
    cos_coeff = template.coefficients[1::2]
    sin_coeff = template.coefficients[2::2]
    for index in range(stop, n):
        state = transition @ state
        covariance = transition @ covariance @ transition.T + process
        if finite[index]:
            phi, _, amplitude, bias = state
            angles = orders * phi
            cosine, sine = np.cos(angles), np.sin(angles)
            shape = template.coefficients[0] + cos_coeff @ cosine + sin_coeff @ sine
            derivative = (orders * sin_coeff) @ cosine - (orders * cos_coeff) @ sine
            prediction = bias + amplitude * shape
            jacobian = np.array([amplitude * derivative, 0, shape, 1.0])
            innovation_variance = float(
                jacobian @ covariance @ jacobian + observation_std**2
            )
            innovation = values[index] - prediction
            innovations[index] = innovation
            innovation_variances[index] = innovation_variance
            gain = covariance @ jacobian / innovation_variance
            state += gain * innovation
            correction = identity - np.outer(gain, jacobian)
            # Joseph update preserves covariance symmetry/positive semidefiniteness.
            covariance = (
                correction @ covariance @ correction.T
                + np.outer(gain, gain) * observation_std**2
            )
            frequency_hits += int(not 2 * np.pi * 0.25 <= state[1] <= 2 * np.pi * 2.0)
            amplitude_hits += int(not 0.05 <= state[2] <= 5.0)
            state[1] = min(max(state[1], 2 * np.pi * 0.25), 2 * np.pi * 2.0)
            state[2] = min(max(state[2], 0.05), 5.0)
            covariance = (covariance + covariance.T) / 2
            updates += 1
        else:
            predictions += 1
        phases[index], frequencies[index], variances[index] = (
            state[0],
            state[1] / (2 * np.pi),
            covariance[0, 0],
        )
    mask = (np.arange(n) >= stop) & (np.arange(n) < n - int(fs))
    return EKFResult(
        phases,
        frequencies,
        variances,
        mask,
        bool(ambiguous),
        updates,
        predictions,
        frequency_hits,
        amplitude_hits,
        stop,
        innovations,
        innovation_variances,
    )
