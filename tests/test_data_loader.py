import pandas as pd

from src.data_loader import clean_purchase_data, profile_data_quality


def test_clean_purchase_data_removes_only_fully_empty_rows_and_columns():
    raw = pd.DataFrame(
        {
            "Date": ["2026-08-01", None],
            "Particular": [" Tomato ", None],
            "QTY": ["10", None],
            "Rate": ["25", None],
            "Amount": ["250", None],
            "Vendor": [" Cash ", None],
            "Location": [" Rinas ", None],
            "Empty": [None, None],
        }
    )

    cleaned = clean_purchase_data(raw)

    assert list(cleaned.columns) == [
        "Date", "Particular", "QTY", "Rate", "Amount", "Vendor", "Location"
    ]
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["Particular"] == "Tomato"
    assert cleaned.iloc[0]["Vendor"] == "Cash"
    assert cleaned.iloc[0]["Location"] == "Rinas"
    assert cleaned.iloc[0]["QTY"] == 10


def test_quality_profile_counts_invalid_records_without_removing_them():
    data = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-08-01", None, "2026-08-01"]),
            "Particular": ["Tomato", None, "Tomato"],
            "QTY": [10, -1, 10],
            "Rate": [25, 0, 25],
            "Amount": [250, -2, 250],
            "Vendor": ["Cash", "Cash", "Cash"],
            "Location": ["Rinas", "Rinas", "Rinas"],
        }
    )

    profile = profile_data_quality(data)

    assert profile["Missing dates"] == 1
    assert profile["Missing products"] == 1
    assert profile["Negative quantities"] == 1
    assert profile["Non-positive rates"] == 1
    assert profile["Negative amounts"] == 1
    assert profile["Duplicate rows"] == 1
