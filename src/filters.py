"""Shared filtering behavior for all dashboard views."""

from __future__ import annotations

import pandas as pd


def apply_filters(
    data: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    locations: list[str] | None = None,
    products: list[str] | None = None,
    vendors: list[str] | None = None,
) -> pd.DataFrame:
    """Return records matching the selected inclusive dates and dimensions."""
    result = data.loc[data["Date"].between(start_date, end_date)].copy()
    if locations:
        result = result.loc[result["Location"].isin(locations)]
    if products:
        result = result.loc[result["Particular"].isin(products)]
    if vendors:
        result = result.loc[result["Vendor"].isin(vendors)]
    return result
