#!/usr/bin/env python3
"""Quick analysis of batch processing metrics."""

import pandas as pd

# Load data
df = pd.read_csv("outputs/tables/master_metrics.csv")

print("=" * 80)
print("BATCH PROCESSING METRICS ANALYSIS")
print("=" * 80)
print(f"\nTotal trials: {len(df)}")
print(f"Groups: {df['group'].value_counts().to_dict()}")
print()

# Group statistics
print("=" * 80)
print("KEY METRICS BY GROUP")
print("=" * 80)
print()

for group in ["healthy", "neuro", "ortho"]:
    group_data = df[df["group"] == group]

    print(f"\n{group.upper()} (n={len(group_data)})")
    print("-" * 40)

    # PLV (Phase Locking Value)
    plv_mean = group_data["plv"].mean()
    plv_std = group_data["plv"].std()
    print(f"PLV:                {plv_mean:.3f} ± {plv_std:.3f}")

    # Anti-phase error
    ape_mean = group_data["anti_phase_error_deg"].mean()
    ape_std = group_data["anti_phase_error_deg"].std()
    print(f"Anti-phase error:   {ape_mean:.1f}° ± {ape_std:.1f}°")

    # Mean phase difference
    mpd_mean = group_data["mean_phase_diff_deg"].mean()
    mpd_std = group_data["mean_phase_diff_deg"].std()
    print(f"Mean phase diff:    {mpd_mean:.1f}° ± {mpd_std:.1f}°")

    # Gait frequency
    f0_mean = group_data["f0_hz"].mean()
    f0_std = group_data["f0_hz"].std()
    print(f"Gait frequency:     {f0_mean:.2f} ± {f0_std:.2f} Hz")

    # Frequency variability (CV)
    cv_left_mean = group_data["cv_inst_freq_left"].mean()
    cv_right_mean = group_data["cv_inst_freq_right"].mean()
    print(f"Freq variability L: {cv_left_mean:.1%}")
    print(f"Freq variability R: {cv_right_mean:.1%}")

print("\n" + "=" * 80)
print("DISCRIMINATIVE POWER (HEALTHY vs PATHOLOGICAL)")
print("=" * 80)
print()

# Compare healthy vs pathological
healthy = df[df["group"] == "healthy"]
patho = df[df["group"].isin(["neuro", "ortho"])]

print(
    f"PLV:               Healthy={healthy['plv'].mean():.3f}, Patho={patho['plv'].mean():.3f}"
)
print(
    f"Anti-phase error:  Healthy={healthy['anti_phase_error_deg'].mean():.1f}°, Patho={patho['anti_phase_error_deg'].mean():.1f}°"
)
print(
    f"Freq CV (left):    Healthy={healthy['cv_inst_freq_left'].mean():.1%}, Patho={patho['cv_inst_freq_left'].mean():.1%}"
)

print("\n" + "=" * 80)
print("DATA QUALITY CHECKS")
print("=" * 80)
print()

# Quality checks
print(
    f"Valid PLV range [0,1]:         {(df['plv'] >= 0).all() and (df['plv'] <= 1).all()}"
)
print(
    f"Frequency matching:            {df['frequency_match_flag'].sum()}/{len(df)} trials"
)
print(f"Mean valid fraction (left):    {df['valid_fraction_left'].mean():.1%}")
print(f"Mean valid fraction (right):   {df['valid_fraction_right'].mean():.1%}")

print("\n" + "=" * 80)
