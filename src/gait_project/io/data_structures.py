"""
Data structures for gait analysis project.

This module defines the core data structures used throughout the gait analysis pipeline,
from raw signal loading to final analysis results.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class GaitMetadata:
    """
    Metadata for a single gait trial.

    Attributes:
        subject: Subject identifier (e.g., "HS_1")
        age: Subject age in years
        gender: Subject gender ("M"/"F")
        height: Subject height in meters
        weight: Subject weight in kg
        bmi: Body Mass Index
        laterality: Dominant side ("left"/"right")
        group: Clinical group ("healthy"/"neuro"/"ortho")
        pathology: Full pathology description
        pathology_key: Pathology abbreviation (e.g., "HS", "PD", "KOA")
        clinical_deficit_side: Side affected by pathology (if applicable)
        evaluation_score_name: Name of clinical evaluation scale
        evaluation_score_value: Value of clinical evaluation
        session: Session number
        days_since_first_session: Days since first recording
        trial: Trial number
        freq: Sampling frequency in Hz
        sensor: Sensor model name
        protocol: Walking protocol description
        tug: Timed Up and Go test result
        visual_gait_assessment: Visual assessment score
        uturn_boundaries: [start_idx, end_idx] of U-turn segment
        left_gait_events: List of [toe_off_idx, heel_strike_idx] for left foot
        right_gait_events: List of [toe_off_idx, heel_strike_idx] for right foot
    """

    subject: str
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    laterality: str
    group: str
    pathology: str
    pathology_key: str
    clinical_deficit_side: Optional[str]
    evaluation_score_name: Optional[str]
    evaluation_score_value: Optional[float]
    session: int
    days_since_first_session: int
    trial: int
    freq: float
    sensor: str
    protocol: str
    tug: str
    visual_gait_assessment: float
    uturn_boundaries: List[int]
    left_gait_events: List[List[int]]
    right_gait_events: List[List[int]]

    @classmethod
    def from_dict(cls, metadata_dict: dict) -> "GaitMetadata":
        """Create GaitMetadata from metadata dictionary loaded from JSON."""
        return cls(
            subject=metadata_dict["subject"],
            age=metadata_dict["age"],
            gender=metadata_dict["gender"],
            height=metadata_dict["height"],
            weight=metadata_dict["weight"],
            bmi=metadata_dict["BMI"],
            laterality=metadata_dict["laterality"],
            group=metadata_dict["group"],
            pathology=metadata_dict["pathology"],
            pathology_key=metadata_dict["pathologyKey"],
            clinical_deficit_side=metadata_dict.get("clinicalDeficitSide"),
            evaluation_score_name=metadata_dict.get("evaluationScoreName"),
            evaluation_score_value=metadata_dict.get("evaluationScoreValue"),
            session=metadata_dict["session"],
            days_since_first_session=metadata_dict["daysSinceFirstSession"],
            trial=metadata_dict["trial"],
            freq=metadata_dict["freq"],
            sensor=metadata_dict["sensor"],
            protocol=metadata_dict["protocol"],
            tug=metadata_dict["TUG"],
            visual_gait_assessment=metadata_dict["visualGaitAssessment"],
            uturn_boundaries=metadata_dict["uturnBoundaries"],
            left_gait_events=metadata_dict["leftGaitEvents"],
            right_gait_events=metadata_dict["rightGaitEvents"],
        )


@dataclass
class RawSignalData:
    """
    Raw sensor signals for all four IMU sensors.

    Attributes:
        HE: Head sensor DataFrame (PacketCounter, Acc_X/Y/Z, Gyr_X/Y/Z, Mag_X/Y/Z)
        LB: Lower back sensor DataFrame
        LF: Left foot sensor DataFrame
        RF: Right foot sensor DataFrame
    """

    HE: Optional[pd.DataFrame]
    LB: Optional[pd.DataFrame]
    LF: Optional[pd.DataFrame]
    RF: Optional[pd.DataFrame]


@dataclass
class TrialData:
    """
    Complete data for a single gait trial.

    Attributes:
        trial_name: Trial identifier (e.g., "HS_1_1")
        data_raw: Raw sensor data for all sensors
        data_processed: Synchronized processed data (37 columns)
        metadata: Trial metadata
    """

    trial_name: str
    data_raw: RawSignalData
    data_processed: pd.DataFrame
    metadata: GaitMetadata

    @classmethod
    def from_load_trial(cls, trial_name: str, loaded_data: dict) -> "TrialData":
        """
        Create TrialData from the output of load_trial function.

        Args:
            trial_name: Name of the trial
            loaded_data: Dictionary returned by load_trial with keys:
                        'data_raw', 'data_processed', 'metadata'
        """
        raw_signal = RawSignalData(
            HE=loaded_data["data_raw"]["HE"],
            LB=loaded_data["data_raw"]["LB"],
            LF=loaded_data["data_raw"]["LF"],
            RF=loaded_data["data_raw"]["RF"],
        )
        metadata = GaitMetadata.from_dict(loaded_data["metadata"])

        return cls(
            trial_name=trial_name,
            data_raw=raw_signal,
            data_processed=loaded_data["data_processed"],
            metadata=metadata,
        )


@dataclass
class PreprocessedSignal:
    """
    Preprocessed gait signals ready for spectral analysis.

    Attributes:
        trial_name: Trial identifier
        lf_gyr_y: Left foot gyroscope Y-axis (preprocessed)
        rf_gyr_y: Right foot gyroscope Y-axis (preprocessed)
        time: Time vector in seconds
        freq: Sampling frequency in Hz
        metadata: Associated trial metadata
    """

    trial_name: str
    lf_gyr_y: np.ndarray
    rf_gyr_y: np.ndarray
    time: np.ndarray
    freq: float
    metadata: GaitMetadata


@dataclass
class SpectralFeatures:
    """
    Spectral characterization of gait signal.

    Attributes:
        trial_name: Trial identifier
        dominant_freq_lf: Dominant frequency for left foot (Hz)
        dominant_freq_rf: Dominant frequency for right foot (Hz)
        spectral_peak_width_lf: Width of spectral peak for left foot (Hz)
        spectral_peak_width_rf: Width of spectral peak for right foot (Hz)
        energy_ratio_lf: Ratio of energy in dominant band to total energy (left)
        energy_ratio_rf: Ratio of energy in dominant band to total energy (right)
        psd_freqs: Frequency vector for PSD
        psd_lf: Power spectral density for left foot
        psd_rf: Power spectral density for right foot
    """

    trial_name: str
    dominant_freq_lf: float
    dominant_freq_rf: float
    spectral_peak_width_lf: float
    spectral_peak_width_rf: float
    energy_ratio_lf: float
    energy_ratio_rf: float
    psd_freqs: np.ndarray
    psd_lf: np.ndarray
    psd_rf: np.ndarray


@dataclass
class PhaseAnalysis:
    """
    Instantaneous phase analysis for both feet.

    Attributes:
        trial_name: Trial identifier
        time: Time vector in seconds
        lf_amplitude: Instantaneous amplitude for left foot
        rf_amplitude: Instantaneous amplitude for right foot
        lf_phase: Instantaneous phase for left foot (radians)
        rf_phase: Instantaneous phase for right foot (radians)
        lf_frequency: Instantaneous frequency for left foot (Hz)
        rf_frequency: Instantaneous frequency for right foot (Hz)
        lf_phase_unwrapped: Unwrapped phase for left foot
        rf_phase_unwrapped: Unwrapped phase for right foot
    """

    trial_name: str
    time: np.ndarray
    lf_amplitude: np.ndarray
    rf_amplitude: np.ndarray
    lf_phase: np.ndarray
    rf_phase: np.ndarray
    lf_frequency: np.ndarray
    rf_frequency: np.ndarray
    lf_phase_unwrapped: np.ndarray
    rf_phase_unwrapped: np.ndarray


@dataclass
class SynchronizationMetrics:
    """
    Inter-foot phase synchronization metrics.

    Attributes:
        trial_name: Trial identifier
        time: Time vector in seconds
        phase_difference: Δφ(t) = φ_LF - φ_RF (radians)
        mean_relative_phase: Mean of phase difference (radians)
        circular_variance: Circular variance of phase difference
        plv_global: Global Phase Locking Value
        plv_windowed: PLV computed in sliding windows
        plv_time: Time vector for windowed PLV
        window_size: Window size used for windowed PLV (seconds)
    """

    trial_name: str
    time: np.ndarray
    phase_difference: np.ndarray
    mean_relative_phase: float
    circular_variance: float
    plv_global: float
    plv_windowed: Optional[np.ndarray] = None
    plv_time: Optional[np.ndarray] = None
    window_size: Optional[float] = None


@dataclass
class SubjectMetrics:
    """
    Aggregated metrics for a single subject across all trials.

    Attributes:
        subject: Subject identifier
        group: Clinical group
        pathology_key: Pathology abbreviation
        n_trials: Number of trials for this subject
        dominant_freq_mean: Mean dominant frequency across trials
        dominant_freq_std: Standard deviation of dominant frequency
        plv_mean: Mean PLV across trials
        plv_std: Standard deviation of PLV
        circular_variance_mean: Mean circular variance across trials
        circular_variance_std: Standard deviation of circular variance
        frequency_variability_mean: Mean frequency variability across trials
        frequency_variability_std: Standard deviation of frequency variability
    """

    subject: str
    group: str
    pathology_key: str
    n_trials: int
    dominant_freq_mean: float
    dominant_freq_std: float
    plv_mean: float
    plv_std: float
    circular_variance_mean: float
    circular_variance_std: float
    frequency_variability_mean: float
    frequency_variability_std: float


@dataclass
class GroupStatistics:
    """
    Summary statistics for a clinical group.

    Attributes:
        group: Group name ("healthy"/"neuro"/"ortho")
        n_subjects: Number of subjects in group
        metrics: Dictionary mapping metric names to (mean, std, median, q25, q75)
    """

    group: str
    n_subjects: int
    metrics: Dict[str, Tuple[float, float, float, float, float]]


@dataclass
class AnalysisPipeline:
    """
    Container for complete analysis pipeline results.

    This structure holds all intermediate and final results for a single trial,
    facilitating end-to-end reproducibility.

    Attributes:
        trial_data: Original trial data
        preprocessed: Preprocessed signals
        spectral: Spectral features
        phase: Phase analysis results
        synchronization: Synchronization metrics
    """

    trial_data: TrialData
    preprocessed: Optional[PreprocessedSignal] = None
    spectral: Optional[SpectralFeatures] = None
    phase: Optional[PhaseAnalysis] = None
    synchronization: Optional[SynchronizationMetrics] = None
