"""
Circular statistics for angular data analysis.

This module provides functions for computing statistics on circular/angular data,
such as phase differences in oscillatory signals. Standard statistics (mean, variance)
are not appropriate for circular data, which requires specialized methods.

Key concept: angles are periodic with period 2π, so π and -π are the same point.
"""

import numpy as np
from typing import Tuple


def wrap_angle(angles: np.ndarray) -> np.ndarray:
    """
    Wrap angles to the range [-π, π].

    This is the standard wrapping for phase differences.

    Args:
        angles: Array of angles in radians

    Returns:
        wrapped_angles: Angles wrapped to [-π, π]
    """
    return np.arctan2(np.sin(angles), np.cos(angles))


def circular_mean(angles: np.ndarray) -> float:
    """
    Compute circular mean of angles.

    The circular mean is the direction of the mean resultant vector.
    Formula: angle(mean(exp(i*θ)))

    Args:
        angles: Array of angles in radians

    Returns:
        mean_angle: Circular mean in radians [-π, π]
    """
    # Convert to unit vectors on the circle
    z = np.exp(1j * angles)

    # Mean of unit vectors
    mean_z = np.mean(z)

    # Extract angle
    mean_angle = np.angle(mean_z)

    return mean_angle


def circular_variance(angles: np.ndarray) -> float:
    """
    Compute circular variance.

    Circular variance V = 1 - R, where R is the mean resultant length.
    Range: [0, 1]
    V = 0: perfect concentration (no variability)
    V = 1: uniform distribution (maximum variability)

    Args:
        angles: Array of angles in radians

    Returns:
        variance: Circular variance in [0, 1]
    """
    # Convert to unit vectors
    z = np.exp(1j * angles)

    # Mean resultant vector
    mean_z = np.mean(z)

    # Mean resultant length
    R = np.abs(mean_z)

    # Circular variance
    V = 1.0 - R

    return V


def circular_std(angles: np.ndarray) -> float:
    """
    Compute circular standard deviation.

    Circular std σ = sqrt(-2 * ln(R)), where R is the mean resultant length.
    Range: [0, ∞]
    σ = 0: perfect concentration
    σ → ∞: uniform distribution

    Args:
        angles: Array of angles in radians

    Returns:
        std: Circular standard deviation in radians
    """
    # Convert to unit vectors
    z = np.exp(1j * angles)

    # Mean resultant length
    R = np.abs(np.mean(z))

    # Circular standard deviation
    # Note: R can be 0 for uniform distribution, handle this case
    if R < 1e-10:
        return np.inf

    sigma = np.sqrt(-2.0 * np.log(R))

    return sigma


def resultant_vector(angles: np.ndarray) -> Tuple[complex, float, float]:
    """
    Compute the mean resultant vector (order parameter in Kuramoto theory).

    The resultant vector R = ⟨exp(i*θ)⟩ captures both:
    - Direction: circular mean = angle(R)
    - Concentration: |R| ∈ [0, 1]

    Args:
        angles: Array of angles in radians

    Returns:
        R: Mean resultant vector (complex number)
        magnitude: |R| (mean resultant length)
        direction: angle(R) (circular mean)
    """
    # Convert to unit vectors
    z = np.exp(1j * angles)

    # Mean resultant vector
    R = np.mean(z)

    # Extract magnitude and direction
    magnitude = np.abs(R)
    direction = np.angle(R)

    return R, magnitude, direction


def angular_distance(angle1: float, angle2: float) -> float:
    """
    Compute shortest angular distance between two angles on the circle.

    This accounts for the circular topology: distance from π to -π is 0.

    Args:
        angle1: First angle in radians
        angle2: Second angle in radians

    Returns:
        distance: Shortest angular distance in radians [0, π]
    """
    # Compute difference and wrap to [-π, π]
    diff = wrap_angle(angle1 - angle2)

    # Take absolute value (distance is always positive)
    distance = np.abs(diff)

    return distance


def compute_circular_statistics(angles: np.ndarray) -> dict:
    """
    Compute comprehensive circular statistics for an array of angles.

    Args:
        angles: Array of angles in radians

    Returns:
        stats: Dictionary with circular statistics
            - circular_mean: Mean direction
            - circular_variance: Variance (1 - R)
            - circular_std: Standard deviation
            - mean_resultant_length: R (concentration measure)
            - resultant_vector: Complex number R
    """
    R, magnitude, direction = resultant_vector(angles)

    stats = {
        "circular_mean": direction,
        "circular_variance": 1.0 - magnitude,
        "circular_std": circular_std(angles),
        "mean_resultant_length": magnitude,
        "resultant_vector": R,
    }

    return stats
