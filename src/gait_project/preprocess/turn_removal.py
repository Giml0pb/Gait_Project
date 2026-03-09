"""
U-turn segment removal functions.

This module provides functions to exclude the turning segment from gait trials,
leaving only the straight walking portions for analysis.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List


def exclude_uturn(
    data: np.ndarray,
    uturn_boundaries: List[int],
    buffer_time: float = 0.0,
    fs: float = 100.0,
) -> np.ndarray:
    """
    Remove U-turn segment from signal, keeping only straight walking.

    The function excludes samples between uturn_boundaries[0] and uturn_boundaries[1],
    and concatenates the before and after segments. Optionally removes a buffer
    around the concatenation point to avoid discontinuity artifacts.

    Args:
        data: Input signal array
        uturn_boundaries: [start_idx, end_idx] of U-turn segment
        buffer_time: Time buffer to remove around concatenation point in seconds (default: 0.0)
        fs: Sampling frequency in Hz (default: 100.0)

    Returns:
        straight_walking_signal: Signal with U-turn removed
    """
    if len(uturn_boundaries) != 2:
        raise ValueError(
            "uturn_boundaries must contain exactly 2 elements [start, end]"
        )

    start_idx, end_idx = uturn_boundaries

    # Validate indices
    if start_idx < 0 or end_idx > len(data):
        raise ValueError(
            f"U-turn boundaries [{start_idx}, {end_idx}] outside data range [0, {len(data)}]"
        )

    if start_idx >= end_idx:
        raise ValueError(
            f"Start index {start_idx} must be less than end index {end_idx}"
        )

    # Calculate buffer samples
    buffer_samples = int(buffer_time * fs)

    # Extract before and after segments with buffer
    before_end = max(0, start_idx - buffer_samples)
    after_start = min(len(data), end_idx + buffer_samples)

    before_uturn = data[:before_end]
    after_uturn = data[after_start:]

    # Concatenate
    straight_walking = np.concatenate([before_uturn, after_uturn])

    return straight_walking


def exclude_uturn_dataframe(
    df: pd.DataFrame,
    uturn_boundaries: List[int],
) -> pd.DataFrame:
    """
    Remove U-turn segment from DataFrame, keeping only straight walking.

    Args:
        df: Input DataFrame
        uturn_boundaries: [start_idx, end_idx] of U-turn segment

    Returns:
        straight_walking_df: DataFrame with U-turn rows removed
    """
    if len(uturn_boundaries) != 2:
        raise ValueError(
            "uturn_boundaries must contain exactly 2 elements [start, end]"
        )

    start_idx, end_idx = uturn_boundaries

    # Validate indices
    if start_idx < 0 or end_idx > len(df):
        raise ValueError(
            f"U-turn boundaries [{start_idx}, {end_idx}] outside DataFrame range [0, {len(df)}]"
        )

    # Extract before and after segments
    before_uturn = df.iloc[:start_idx]
    after_uturn = df.iloc[end_idx:]

    # Concatenate
    straight_walking_df = pd.concat([before_uturn, after_uturn], ignore_index=True)

    return straight_walking_df


def extract_straight_walking(
    data: np.ndarray,
    uturn_boundaries: List[int],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract the two straight walking segments separately.

    Args:
        data: Input signal
        uturn_boundaries: [start_idx, end_idx] of U-turn segment

    Returns:
        first_segment: Signal before U-turn
        second_segment: Signal after U-turn
    """
    if len(uturn_boundaries) != 2:
        raise ValueError("uturn_boundaries must contain exactly 2 elements")

    start_idx, end_idx = uturn_boundaries

    first_segment = data[:start_idx]
    second_segment = data[end_idx:]

    return first_segment, second_segment


def get_valid_gait_events(
    gait_events: List[List[int]],
    uturn_boundaries: List[int],
    offset_after_uturn: int = 0,
) -> Tuple[List[List[int]], List[List[int]]]:
    """
    Separate gait events into before and after U-turn.

    Optionally adjusts indices of events after U-turn to account for
    the removed segment.

    Args:
        gait_events: List of [toe_off, heel_strike] pairs
        uturn_boundaries: [start_idx, end_idx] of U-turn
        offset_after_uturn: Offset to subtract from post-uturn events
                           (typically uturn_boundaries[1])

    Returns:
        events_before: Events occurring before U-turn
        events_after: Events occurring after U-turn (optionally offset-corrected)
    """
    start_idx, end_idx = uturn_boundaries

    events_before = []
    events_after = []

    for event in gait_events:
        toe_off, heel_strike = event

        # Event is before U-turn if heel_strike < start_idx
        if heel_strike < start_idx:
            events_before.append(event)

        # Event is after U-turn if toe_off >= end_idx
        elif toe_off >= end_idx:
            if offset_after_uturn > 0:
                # Adjust indices
                adjusted_event = [
                    toe_off - offset_after_uturn,
                    heel_strike - offset_after_uturn,
                ]
                events_after.append(adjusted_event)
            else:
                events_after.append(event)

    return events_before, events_after
