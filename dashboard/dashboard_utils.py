"""Shared data-loading helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def data_path(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def load_csv(relative_path: str) -> pd.DataFrame:
    path = data_path(relative_path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_text(relative_path: str) -> str:
    path = data_path(relative_path)
    if not path.exists():
        return "Output has not been generated yet. Run python src/main.py --scenario phase5_all."
    return path.read_text(encoding="utf-8")


def available_configurations(results: pd.DataFrame) -> list[str]:
    if results.empty or "security_configuration" not in results:
        return []
    return sorted(results["security_configuration"].dropna().unique())


def round_numeric(frame: pd.DataFrame, digits: int = 4) -> pd.DataFrame:
    """Return a copy with numeric columns rounded for display."""
    if frame.empty:
        return frame
    rounded = frame.copy()
    numeric_columns = rounded.select_dtypes(include="number").columns
    rounded[numeric_columns] = rounded[numeric_columns].round(digits)
    return rounded


def file_inventory(relative_paths: list[str]) -> pd.DataFrame:
    """Build a simple file availability table for dashboard outputs."""
    rows = []
    for relative_path in relative_paths:
        path = data_path(relative_path)
        rows.append(
            {
                "file": relative_path,
                "exists": path.exists(),
                "path": str(path),
            }
        )
    return pd.DataFrame(rows)
