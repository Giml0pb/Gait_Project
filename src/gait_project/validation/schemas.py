"""
Pydantic schemas for data validation.

Validates inputs and outputs of each pipeline phase to catch errors early
and ensure data quality throughout the processing pipeline.
"""

import math

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class FiniteModel(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)


class TrialMetadataSchema(FiniteModel):
    """Validate trial metadata loaded from dataset."""

    subject: str = Field(..., min_length=1, description="Subject ID")
    freq: float = Field(..., gt=0, lt=1000, description="Sampling frequency (Hz)")
    uturn_boundaries: tuple[int, int] = Field(
        ..., description="U-turn start and end indices"
    )

    @field_validator("uturn_boundaries")
    @classmethod
    def validate_uturn_boundaries(cls, v):
        if v[0] >= v[1]:
            raise ValueError(f"U-turn start ({v[0]}) must be < end ({v[1]})")
        if v[0] < 0:
            raise ValueError(f"U-turn start must be >= 0, got {v[0]}")
        return v


class Phase1MetricsSchema(FiniteModel):
    """Validate Phase 1 (spectral analysis) output metrics."""

    dominant_freq_hz: float = Field(
        ..., ge=0.5, le=3.0, description="Dominant frequency (0.5-3.0 Hz)"
    )
    spectral_snr: float = Field(..., gt=0, description="Spectral SNR (positive)")
    peak_power: float = Field(..., gt=0, description="Peak power (positive)")
    peak_width_hz: float = Field(..., gt=0, description="Spectral peak width (Hz)")
    energy_ratio: float = Field(..., ge=0, le=1, description="Energy ratio (0-1)")
    signal_duration: float = Field(
        ..., gt=0, description="Signal duration (seconds, positive)"
    )


class Phase2MetricsSchema(FiniteModel):
    """Validate Phase 2 (instantaneous phase) output metrics."""

    mean_inst_freq_hz: float = Field(
        ..., gt=0, description="Mean instantaneous frequency (Hz)"
    )
    cv_inst_freq: float = Field(..., ge=0, description="CV of instantaneous frequency")
    valid_fraction: float = Field(..., ge=0, le=1, description="Valid fraction (0-1)")
    num_cycles: float = Field(
        ...,
        gt=0,
        validation_alias=AliasChoices("num_cycles", "n_cycles_estimated"),
        description="Number of cycles (positive)",
    )

    @field_validator("cv_inst_freq")
    @classmethod
    def validate_cv(cls, v):
        if v > 0.15:  # Warning threshold
            import warnings

            warnings.warn(f"CV={v:.1%} is high (>15%). Check signal quality.")
        return v


class Phase3MetricsSchema(FiniteModel):
    """Validate Phase 3 (bilateral synchronization) output metrics."""

    # Frequency metrics
    freq_left: float = Field(..., gt=0, description="Left foot frequency (Hz)")
    freq_right: float = Field(..., gt=0, description="Right foot frequency (Hz)")
    freq_diff: float = Field(
        ..., ge=0, description="Absolute frequency difference (Hz)"
    )
    freq_ratio: float = Field(
        ..., ge=0, le=2.0, description="Relative frequency difference (0-2)"
    )
    frequency_match_flag: bool = Field(..., description="Frequencies matched")

    # PLV metrics
    plv: float = Field(..., ge=0, le=1, description="Phase Locking Value (0-1)")
    mean_phase_diff: float = Field(
        ..., ge=-3.15, le=3.15, description="Mean phase difference (-π to π)"
    )
    anti_phase_error: float = Field(
        ..., ge=0, le=3.15, description="Anti-phase error (0 to π)"
    )
    circular_variance: float = Field(
        ..., ge=0, le=1, description="Circular variance (0-1)"
    )
    circular_std: float = Field(
        ...,
        ge=0,
        allow_inf_nan=True,
        description="Circular std (radians; infinity for zero resultant)",
    )

    # NEW: Temporal synchronization metrics
    phase_slip_rate: float = Field(
        ..., ge=0, description="Phase slip rate (slips/min, >=0)"
    )
    plv_mean_windowed: float = Field(
        ..., ge=0, le=1, description="Mean windowed PLV (0-1)"
    )
    plv_std_windowed: float = Field(
        ..., ge=0, le=1, description="Std of windowed PLV (0-1)"
    )
    plv_trend: float = Field(..., description="PLV temporal trend (slope)")
    n_windows: int = Field(..., gt=0, description="Number of analysis windows (>0)")

    # Validity metrics
    valid_samples_sync: int = Field(
        ..., gt=0, description="Valid samples for sync analysis"
    )
    valid_fraction_sync: float = Field(
        ..., ge=0, le=1, description="Valid fraction (0-1)"
    )

    @field_validator("plv")
    @classmethod
    def validate_plv(cls, v):
        if v < 0.5:
            import warnings

            warnings.warn(f"PLV={v:.3f} is low (<0.5). Check coordination quality.")
        return v

    @model_validator(mode="after")
    def validate_consistency(self):
        if not math.isclose(self.circular_variance, 1 - self.plv, abs_tol=1e-6):
            raise ValueError("Circular variance must equal 1 - PLV")
        if self.valid_fraction_sync <= 0:
            raise ValueError("Synchronization requires a positive valid fraction")
        return self


class MasterMetricsSchema(FiniteModel):
    """Validate complete trial metrics (all phases combined)."""

    trial: str = Field(..., min_length=1, description="Trial name")
    subject: str = Field(..., min_length=1, description="Subject ID")
    group: str = Field(
        ...,
        pattern=r"^(healthy|neuro|ortho)$",
        description="Group: healthy, neuro, or ortho",
    )

    # Phase 1
    f0_hz: float = Field(..., ge=0.5, le=3.0)
    spectral_snr: float = Field(..., gt=0)

    # Phase 2
    mean_inst_freq_left: float = Field(..., gt=0)
    mean_inst_freq_right: float = Field(..., gt=0)
    cv_inst_freq_left: float = Field(..., ge=0)
    cv_inst_freq_right: float = Field(..., ge=0)

    # Phase 3
    plv: float = Field(..., ge=0, le=1)
    anti_phase_error_deg: float = Field(..., ge=0, le=180)

    # NEW: Temporal metrics
    phase_slip_rate: float = Field(..., ge=0)
    plv_mean_windowed: float = Field(..., ge=0, le=1)
    plv_std_windowed: float = Field(..., ge=0, le=1)
    plv_trend: float

    frequency_match_flag: bool

    model_config = {
        "frozen": True,
        "extra": "allow",
    }  # Allow extra fields for flexibility


def validate_phase1_metrics(metrics: dict) -> Phase1MetricsSchema:
    """
    Validate Phase 1 metrics with detailed error messages.

    Args:
        metrics: Dictionary with Phase 1 metrics

    Returns:
        Validated Phase1MetricsSchema object

    Raises:
        ValidationError: If metrics are invalid
    """
    try:
        return Phase1MetricsSchema(**metrics)
    except Exception as e:
        raise ValueError(f"Phase 1 metrics validation failed: {e}")


def validate_phase2_metrics(metrics: dict) -> Phase2MetricsSchema:
    """
    Validate Phase 2 metrics with detailed error messages.

    Args:
        metrics: Dictionary with Phase 2 metrics

    Returns:
        Validated Phase2MetricsSchema object

    Raises:
        ValidationError: If metrics are invalid
    """
    try:
        return Phase2MetricsSchema(**metrics)
    except Exception as e:
        raise ValueError(f"Phase 2 metrics validation failed: {e}")


def validate_phase3_metrics(metrics: dict) -> Phase3MetricsSchema:
    """
    Validate Phase 3 metrics with detailed error messages.

    Args:
        metrics: Dictionary with Phase 3 metrics

    Returns:
        Validated Phase3MetricsSchema object

    Raises:
        ValidationError: If metrics are invalid
    """
    try:
        return Phase3MetricsSchema(**metrics)
    except Exception as e:
        raise ValueError(f"Phase 3 metrics validation failed: {e}")


def validate_master_metrics(metrics: dict) -> MasterMetricsSchema:
    """
    Validate complete trial metrics.

    Args:
        metrics: Dictionary with all metrics

    Returns:
        Validated MasterMetricsSchema object

    Raises:
        ValidationError: If metrics are invalid
    """
    try:
        return MasterMetricsSchema(**metrics)
    except Exception as e:
        raise ValueError(f"Master metrics validation failed: {e}")
