"""Monthly purchase metrics used throughout the dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd


METRIC_KEYS = ["Location", "Particular"]


def build_monthly_product_metrics(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Period | None, pd.Period | None]:
    """Return location-product metrics for the latest two selected calendar months.

    Quantities are aggregated by month before the comparison.  A missing prior
    month is treated as zero quantity; its percentage growth remains undefined.
    """
    if data.empty:
        return pd.DataFrame(), None, None

    working = data.copy()
    working["Month"] = pd.to_datetime(working["Date"]).dt.to_period("M")
    current_month = working["Month"].max()
    previous_month = current_month - 1

    monthly = (
        working.groupby(["Month", *METRIC_KEYS], as_index=False)
        .agg(Quantity=("QTY", "sum"))
    )
    current = monthly.loc[monthly["Month"] == current_month, [*METRIC_KEYS, "Quantity"]]
    current = current.rename(columns={"Quantity": "Current Month Quantity"})
    previous = monthly.loc[monthly["Month"] == previous_month, [*METRIC_KEYS, "Quantity"]]
    previous = previous.rename(columns={"Quantity": "Previous Month Quantity"})

    metrics = current.merge(previous, on=METRIC_KEYS, how="outer").fillna(0)
    metrics["Quantity Change"] = (
        metrics["Current Month Quantity"] - metrics["Previous Month Quantity"]
    )
    previous_qty = metrics["Previous Month Quantity"]
    metrics["Quantity Change %"] = np.where(
        previous_qty.ne(0), metrics["Quantity Change"] / previous_qty * 100, np.nan
    )
    metrics["Growth Status"] = np.select(
        [
            metrics["Quantity Change"].gt(0) & previous_qty.eq(0),
            metrics["Quantity Change"].gt(0),
            metrics["Quantity Change"].lt(0),
        ],
        ["New activity", "Increasing", "Decreasing"],
        default="No change",
    )

    aggregate = (
        working.groupby(METRIC_KEYS, as_index=False)
        .agg(
            **{
                "Purchase Amount": ("Amount", "sum"),
                "Purchase Frequency": ("Particular", "size"),
                "Active Months": ("Month", "nunique"),
                "Last Purchase Date": ("Date", "max"),
                "Total Quantity": ("QTY", "sum"),
            }
        )
    )
    valid_rates = working.loc[working["Rate"].gt(0)]
    weighted_rate = (
        valid_rates.groupby(METRIC_KEYS, as_index=False)
        .agg(_amount=("Amount", "sum"), _qty=("QTY", "sum"))
    )
    weighted_rate["Average Rate"] = weighted_rate["_amount"] / weighted_rate["_qty"]
    aggregate = aggregate.merge(
        weighted_rate[[*METRIC_KEYS, "Average Rate"]], on=METRIC_KEYS, how="left"
    )
    return metrics.merge(aggregate, on=METRIC_KEYS, how="left"), current_month, previous_month


def add_stock_review_signal(metrics: pd.DataFrame, current_month: pd.Period) -> pd.DataFrame:
    """Flag transparent, data-derived candidates for a stock review."""
    result = metrics.copy()
    result["Location Median Current Quantity"] = result.groupby("Location")[
        "Current Month Quantity"
    ].transform("median")
    last_purchase_month = pd.to_datetime(result["Last Purchase Date"]).dt.to_period("M")
    qualifies = (
        result["Quantity Change"].gt(0)
        & result["Active Months"].ge(2)
        & result["Current Month Quantity"].ge(result["Location Median Current Quantity"])
        & last_purchase_month.eq(current_month)
    )
    result["Increase Signal"] = np.where(
        qualifies, "Candidate for stock review", "Monitor"
    )
    return result
