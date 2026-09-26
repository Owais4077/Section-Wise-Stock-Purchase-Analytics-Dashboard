import pandas as pd

from src.filters import apply_filters


def test_apply_filters_combines_date_location_product_and_vendor_criteria():
    data = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-07-01", "2026-08-01", "2026-08-02"]),
            "Location": ["Rinas", "Rinas", "Gulberg"],
            "Particular": ["Tomato", "Potato", "Tomato"],
            "Vendor": ["Cash", "Cash", "Supplier"],
            "QTY": [1, 2, 3],
        }
    )

    filtered = apply_filters(
        data,
        start_date=pd.Timestamp("2026-08-01"),
        end_date=pd.Timestamp("2026-08-31"),
        locations=["Rinas"],
        products=["Potato"],
        vendors=["Cash"],
    )

    assert filtered.to_dict("records") == [
        {
            "Date": pd.Timestamp("2026-08-01"),
            "Location": "Rinas",
            "Particular": "Potato",
            "Vendor": "Cash",
            "QTY": 2,
        }
    ]
