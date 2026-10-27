"""Small synthetic dataset; tests do not require private participant recordings."""

import json
import os

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/gait-tests-mpl")

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_dataset(tmp_path):
    fs = 100.0
    t = np.arange(2400) / fs
    signal = np.sin(2 * np.pi * 1.6 * t)
    right = signal.copy()
    signal[-3:] = np.nan
    right[-5:] = np.nan
    data = pd.DataFrame({"LF_Gyr_Y": signal, "RF_Gyr_Y": right})
    metadata = {
        "subject": "HS_1",
        "age": 30,
        "gender": "F",
        "height": 1.7,
        "weight": 65,
        "BMI": 22.5,
        "laterality": "right",
        "group": "healthy",
        "pathology": "Synthetic",
        "pathologyKey": "HS",
        "session": 1,
        "daysSinceFirstSession": 0,
        "trial": 1,
        "freq": fs,
        "sensor": "synthetic",
        "protocol": "synthetic",
        "TUG": "NA",
        "visualGaitAssessment": 0,
        "uturnBoundaries": [1000, 1200],
        "leftGaitEvents": [],
        "rightGaitEvents": [],
    }
    base = tmp_path / "dataset"
    folder = base / "healthy/HS/HS_1/HS_1_1"
    folder.mkdir(parents=True)
    data.to_csv(folder / "HS_1_1_processed_data.txt", sep="\t", index=False)
    (folder / "HS_1_1_meta.json").write_text(json.dumps(metadata))
    # Only the optional raw/preprocessed comparison uses these files.
    for sensor in ("LF", "RF", "HE", "LB"):
        pd.DataFrame({"Gyr_Y": np.nan_to_num(signal)}).to_csv(
            folder / f"HS_1_1_{sensor}.txt", sep="\t", index=False
        )
    return base, folder, data, metadata
