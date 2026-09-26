import pandas as pd
import pytest

from src.analytics import build_monthly_product_metrics, add_stock_review_signal


def test_monthly_metrics_aggregate_transactions_before_calculating_growth():
    data = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-07-02", "2026-07-12", "2026-08-05"]),
            "Location": ["Rinas", "Rinas", "Rinas"],
            "Particular": ["Tomato", "Tomato", "Tomato"],
            "QTY": [10, 15, 40],
            "Amount": [100, 150, 440],
            "Rate": [10, 10, 11],
            "Vendor": ["Cash", "Cash", "Cash"],
        }
    )

    metrics, current_month, previous_month = build_monthly_product_metrics(data)

    row = metrics.iloc[0]
    assert current_month == pd.Period("2026-08", freq="M")
    assert previous_month == pd.Period("2026-07", freq="M")
    assert row["Current Month Quantity"] == 40
    assert row["Previous Month Quantity"] == 25
    assert row["Quantity Change"] == 15
    assert row["Quantity Change %"] == pytest.approx(60.0)


def test_monthly_metrics_marks_growth_percentage_missing_when_previous_quantity_is_zero():
    data = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-08-05"]),
            "Location": ["Rinas"],
            "Particular": ["Tomato"],
            "QTY": [40],
            "Amount": [440],
            "Rate": [11],
            "Vendor": ["Cash"],
        }
    )

    metrics, _, _ = build_monthly_product_metrics(data)

    assert metrics.iloc[0]["Previous Month Quantity"] == 0
    assert metrics.iloc[0]["Quantity Change"] == 40
    assert pd.isna(metrics.iloc[0]["Quantity Change %"])
    assert metrics.iloc[0]["Growth Status"] == "New activity"


def test_stock_review_signal_requires_growth_recent_activity_consistency_and_significant_quantity():
    metrics = pd.DataFrame(
        {
            "Location": ["Rinas", "Rinas", "Rinas"],
            "Particular": ["A", "B", "C"],
            "Current Month Quantity": [50, 10, 60],
            "Previous Month Quantity": [30, 5, 50],
            "Quantity Change": [20, 5, 10],
            "Active Months": [3, 1, 3],
            "Last Purchase Date": pd.to_datetime(["2026-08-20", "2026-08-25", "2026-07-30"]),
        }
    )

    result = add_stock_review_signal(metrics, pd.Period("2026-08", freq="M"))

    assert result.loc[result["Particular"] == "A", "Increase Signal"].item() == "Candidate for stock review"
    assert result.loc[result["Particular"] == "B", "Increase Signal"].item() == "Monitor"
    assert result.loc[result["Particular"] == "C", "Increase Signal"].item() == "Monitor"
