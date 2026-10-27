"""Atomic, deterministic table writes for a single processing writer."""

import os
from pathlib import Path
import tempfile

import pandas as pd


def write_csv_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            frame.to_csv(stream, index=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def upsert_csv(frame: pd.DataFrame, path: str | Path, keys: list[str]) -> None:
    """Replace existing rows with the same keys; never append duplicates."""
    path = Path(path)
    if frame.empty:
        return
    if frame[keys].isna().any().any():
        raise ValueError("Result identifiers must not be missing")
    if path.exists():
        existing = pd.read_csv(path)
        frame = pd.concat([existing, frame], ignore_index=True)
    frame = frame.drop_duplicates(subset=keys, keep="last")
    write_csv_atomic(frame, path)
