"""Data loading, conservative cleaning, and quality profiling."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = {"Date", "Particular", "QTY", "Rate", "Amount", "Vendor", "Location"}
TEXT_COLUMNS = ["Particular", "Vendor", "Location"]
NUMERIC_COLUMNS = ["QTY", "Rate", "Amount"]


def find_purchase_sheets(source: str | Path | BinaryIO) -> list[str]:
    """Return workbook sheets containing all expected purchase columns."""
    workbook = pd.ExcelFile(source)
    matches: list[str] = []
    for sheet in workbook.sheet_names:
        headers = pd.read_excel(workbook, sheet_name=sheet, nrows=0).columns
        normalized = {str(column).strip() for column in headers}
        if REQUIRED_COLUMNS.issubset(normalized):
            matches.append(sheet)
    return matches


def load_purchase_sheet(source: str | Path | BinaryIO, sheet_name: str) -> pd.DataFrame:
    """Load a selected sheet and normalize its header whitespace."""
    data = pd.read_excel(source, sheet_name=sheet_name)
    data.columns = [str(column).strip() for column in data.columns]
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Selected sheet is missing required columns: {', '.join(sorted(missing))}")
    return data


def clean_purchase_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Perform non-destructive cleaning appropriate for dashboard calculations."""
    data = raw.copy()
    data.columns = [str(column).strip() for column in data.columns]
    data = data.dropna(axis=0, how="all").dropna(axis=1, how="all")
    for column in TEXT_COLUMNS:
        if column in data:
            data[column] = data[column].astype("string").str.strip().replace("", pd.NA)
    if "Date" in data:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data


def profile_data_quality(data: pd.DataFrame) -> dict[str, int]:
    """Count quality issues without modifying records."""
    return {
        "Missing dates": int(data["Date"].isna().sum()),
        "Missing products": int(data["Particular"].isna().sum()),
        "Missing quantities": int(data["QTY"].isna().sum()),
        "Negative quantities": int(data["QTY"].lt(0).sum()),
        "Zero quantities": int(data["QTY"].eq(0).sum()),
        "Non-positive rates": int(data["Rate"].le(0).sum()),
        "Negative amounts": int(data["Amount"].lt(0).sum()),
        "Duplicate rows": int(data.duplicated().sum()),
    }


def valid_for_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Exclude only records unusable for time-based quantity calculations."""
    required = ["Date", "Particular", "QTY", "Amount", "Location"]
    return data.dropna(subset=required).copy()
