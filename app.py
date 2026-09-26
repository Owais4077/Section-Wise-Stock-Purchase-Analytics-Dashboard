"""Section-wise Stock & Purchase Analytics Streamlit application."""

from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import add_stock_review_signal, build_monthly_product_metrics
from src.data_loader import (
    clean_purchase_data,
    find_purchase_sheets,
    load_purchase_sheet,
    profile_data_quality,
    valid_for_metrics,
)
from src.filters import apply_filters


st.set_page_config(page_title="Section-wise Stock & Purchase Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def load_uploaded_data(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    return clean_purchase_data(load_purchase_sheet(io.BytesIO(file_bytes), sheet_name))


def csv_download(data: pd.DataFrame) -> bytes:
    return data.to_csv(index=False).encode("utf-8")


def money(value: float) -> str:
    return f"{value:,.2f}"


def render_kpis(data: pd.DataFrame) -> None:
    columns = st.columns(6)
    values = [
        ("Total Purchase Quantity", f"{data['QTY'].sum():,.2f}"),
        ("Total Purchase Amount", money(data["Amount"].sum())),
        ("Unique Products", f"{data['Particular'].nunique():,}"),
        ("Locations / Sections", f"{data['Location'].nunique():,}"),
        ("Vendors", f"{data['Vendor'].nunique():,}"),
        ("Average Purchase Rate", money(data.loc[data["Rate"].gt(0), "Rate"].mean())),
    ]
    for column, (label, value) in zip(columns, values):
        column.metric(label, value)


def location_summary(data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        data.groupby("Location", as_index=False)
        .agg(
            **{
                "Total Quantity": ("QTY", "sum"),
                "Purchase Amount": ("Amount", "sum"),
                "Number of Products": ("Particular", "nunique"),
                "Amount for Rate": ("Amount", "sum"),
                "Quantity for Rate": ("QTY", "sum"),
            }
        )
    )
    summary["Average Purchase Rate"] = summary["Amount for Rate"] / summary["Quantity for Rate"]
    return summary.drop(columns=["Amount for Rate", "Quantity for Rate"])


def monthly_totals(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.assign(Month=data["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)
        .agg(**{"Total Quantity": ("QTY", "sum"), "Purchase Amount": ("Amount", "sum")})
    )


def vendor_summary(data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        data.groupby("Vendor", as_index=False)
        .agg(
            **{
                "Total Quantity": ("QTY", "sum"),
                "Purchase Amount": ("Amount", "sum"),
                "Products Supplied": ("Particular", "nunique"),
                "Purchase Transaction Count": ("Particular", "size"),
            }
        )
    )
    rates = data.loc[data["Rate"].gt(0)].groupby("Vendor", as_index=False).agg(
        **{"Average Rate": ("Rate", "mean")}
    )
    return summary.merge(rates, on="Vendor", how="left")


def rate_review_flags(data: pd.DataFrame, metrics: pd.DataFrame, current_month: pd.Period | None) -> pd.DataFrame:
    if current_month is None or metrics.empty:
        return pd.DataFrame()
    rates = data.loc[data["Rate"].gt(0)].copy()
    rates["Month"] = rates["Date"].dt.to_period("M")
    grouped = rates.groupby(["Month", "Location", "Particular"], as_index=False).agg(
        Amount=("Amount", "sum"), Quantity=("QTY", "sum")
    )
    grouped["Weighted Rate"] = grouped["Amount"] / grouped["Quantity"]
    current = grouped.loc[grouped["Month"].eq(current_month), ["Location", "Particular", "Weighted Rate"]]
    current = current.rename(columns={"Weighted Rate": "Current Average Rate"})
    previous = grouped.loc[grouped["Month"].eq(current_month - 1), ["Location", "Particular", "Weighted Rate"]]
    previous = previous.rename(columns={"Weighted Rate": "Previous Average Rate"})
    result = metrics.merge(current, on=["Location", "Particular"], how="left").merge(
        previous, on=["Location", "Particular"], how="left"
    )
    return result.loc[
        result["Quantity Change"].gt(0)
        & result["Current Average Rate"].gt(result["Previous Average Rate"])
    ].sort_values("Quantity Change", ascending=False)


def main() -> None:
    st.title("Section-wise Stock & Purchase Analytics")
    st.caption("Data-driven analysis of purchase quantity, stock activity, and product trends")
    st.info("Purchase Amount represents purchase cost. Selling price and profit-margin data are not available, so this dashboard does not calculate profit.")

    upload = st.sidebar.file_uploader("Upload purchase Excel or CSV file", type=["xlsx", "xls", "csv"])
    if upload is None:
        st.warning("Upload an Excel or CSV purchase-data file to begin.")
        return
    file_bytes = upload.getvalue()
    if upload.name.lower().endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(file_bytes))
        data = clean_purchase_data(raw)
        source_name = "CSV upload"
    else:
        try:
            sheets = find_purchase_sheets(io.BytesIO(file_bytes))
        except Exception as exc:
            st.error(f"The workbook could not be read: {exc}")
            return
        if not sheets:
            st.error("No sheet contains all required columns: Date, Particular, QTY, Rate, Amount, Vendor, Location.")
            return
        sheet = st.sidebar.selectbox("Purchase-data sheet", sheets)
        data = load_uploaded_data(file_bytes, sheet)
        source_name = sheet

    metric_data = valid_for_metrics(data)
    if metric_data.empty:
        st.error("No records contain the required Date, Product, Quantity, Amount, and Location values.")
        return

    min_date, max_date = metric_data["Date"].min().date(), metric_data["Date"].max().date()
    if "date_range" not in st.session_state:
        st.session_state.date_range = (min_date, max_date)
    if st.sidebar.button("Reset Filters"):
        st.session_state.date_range = (min_date, max_date)
        st.session_state.location_filter = []
        st.session_state.product_filter = []
        st.session_state.vendor_filter = []
        st.rerun()
    selected_dates = st.sidebar.date_input("Date range", key="date_range", min_value=min_date, max_value=max_date)
    if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
        st.warning("Select both a start and end date.")
        return
    locations = st.sidebar.multiselect("Location / Section", sorted(metric_data["Location"].dropna().unique()), key="location_filter")
    products = st.sidebar.multiselect("Particular / Product", sorted(metric_data["Particular"].dropna().unique()), key="product_filter")
    vendors = st.sidebar.multiselect("Vendor", sorted(metric_data["Vendor"].dropna().unique()), key="vendor_filter")
    filtered = apply_filters(
        metric_data,
        pd.Timestamp(selected_dates[0]),
        pd.Timestamp(selected_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1),
        locations,
        products,
        vendors,
    )
    if filtered.empty:
        st.warning("No valid purchase records match the selected filters.")
        return

    st.sidebar.download_button("Download filtered data (CSV)", csv_download(filtered), "filtered_purchase_data.csv", "text/csv")
    render_kpis(filtered)
    st.caption(f"Source: {source_name} · Selected range: {selected_dates[0]} to {selected_dates[1]} · Locations: {', '.join(locations) if locations else 'All'} · Products: {', '.join(products) if products else 'All'}")
    metrics, current_month, previous_month = build_monthly_product_metrics(filtered)
    metrics = add_stock_review_signal(metrics, current_month) if current_month is not None else metrics
    tabs = st.tabs(["Executive Summary", "Section Analysis", "Product Analysis", "Stock Increase Analysis", "Vendor Analysis", "Purchase Cost Analysis", "Data Quality"])

    with tabs[0]:
        trends = monthly_totals(filtered)
        left, right = st.columns(2)
        left.plotly_chart(px.line(trends, x="Month", y="Total Quantity", markers=True, title="Monthly Total Quantity"), use_container_width=True, key="executive_monthly_quantity")
        right.plotly_chart(px.line(trends, x="Month", y="Purchase Amount", markers=True, title="Monthly Purchase Amount"), use_container_width=True, key="executive_monthly_amount")
        st.subheader("Current month comparison")
        st.write(f"Current: **{current_month}** · Previous: **{previous_month}**. Growth percentage is unavailable where the prior-month quantity is zero.")

    with tabs[1]:
        summary = location_summary(filtered)
        growth = metrics.groupby("Location", as_index=False).agg(**{"Quantity Change": ("Quantity Change", "sum"), "Previous": ("Previous Month Quantity", "sum")})
        growth["Quantity Growth %"] = growth["Quantity Change"].div(growth["Previous"].replace(0, pd.NA)).mul(100)
        summary = summary.merge(growth[["Location", "Quantity Growth %"]], on="Location", how="left")
        left, right = st.columns(2)
        left.plotly_chart(px.bar(summary, x="Location", y="Total Quantity", title="Quantity by Location"), use_container_width=True, key="section_quantity_by_location")
        right.plotly_chart(px.bar(summary, x="Location", y="Purchase Amount", title="Purchase Amount by Location"), use_container_width=True, key="section_amount_by_location")
        st.dataframe(summary.sort_values("Total Quantity", ascending=False), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Product Quantity Trend")
        daily = filtered.groupby(["Date", "Particular", "Location"], as_index=False).agg(**{"Daily Quantity": ("QTY", "sum")})
        st.plotly_chart(px.line(daily, x="Date", y="Daily Quantity", color="Particular", line_dash="Location", title="Daily Quantity Trend"), use_container_width=True, key="product_daily_quantity_trend")
        monthly_product = (filtered.assign(Month=filtered["Date"].dt.to_period("M").dt.to_timestamp()).groupby(["Month", "Particular", "Location"], as_index=False).agg(**{"Monthly Quantity": ("QTY", "sum")}))
        st.plotly_chart(px.line(monthly_product, x="Month", y="Monthly Quantity", color="Particular", line_dash="Location", title="Monthly Quantity Trend"), use_container_width=True, key="product_monthly_quantity_trend")
        st.subheader("Products with Increasing Quantity")
        increasing = metrics.loc[metrics["Quantity Change"].gt(0)].sort_values("Quantity Change", ascending=False)
        st.plotly_chart(px.bar(increasing.head(20), x="Particular", y="Quantity Change", color="Location", title="Top Products with Increasing Quantity"), use_container_width=True, key="product_increasing_quantity")
        st.dataframe(increasing, use_container_width=True, hide_index=True)
        st.subheader("Products with Decreasing Quantity")
        decreasing = metrics.loc[metrics["Quantity Change"].lt(0)].sort_values("Quantity Change")
        st.dataframe(decreasing, use_container_width=True, hide_index=True)
        st.subheader("Location + Product Quantity Matrix")
        matrix = pd.pivot_table(filtered, index="Location", columns="Particular", values="QTY", aggfunc="sum", fill_value=0)
        st.dataframe(matrix, use_container_width=True)
        st.download_button("Download product comparison (CSV)", csv_download(metrics), "product_comparison.csv", "text/csv")

    with tabs[3]:
        st.subheader("Stock Increase Candidates")
        st.caption("A candidate has positive quantity growth, purchase activity in the latest month, activity across at least two months, and current-month quantity at or above its location’s median product quantity. This is a review signal—not an automatic purchase decision.")
        candidates = metrics.loc[metrics["Increase Signal"].eq("Candidate for stock review")].sort_values("Quantity Change", ascending=False)
        st.dataframe(candidates, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(candidates.head(20), x="Particular", y="Quantity Change", color="Location", title="Top Candidate Quantity Growth"), use_container_width=True, key="stock_candidate_quantity_growth")

    with tabs[4]:
        vendors_summary = vendor_summary(filtered).sort_values("Purchase Amount", ascending=False)
        left, right = st.columns(2)
        left.plotly_chart(px.bar(vendors_summary, x="Vendor", y="Total Quantity", title="Vendor-wise Quantity"), use_container_width=True, key="vendor_quantity")
        right.plotly_chart(px.bar(vendors_summary, x="Vendor", y="Purchase Amount", title="Vendor-wise Purchase Amount"), use_container_width=True, key="vendor_purchase_amount")
        st.dataframe(vendors_summary, use_container_width=True, hide_index=True)

    with tabs[5]:
        product_cost = filtered.groupby("Particular", as_index=False).agg(**{"Purchase Amount": ("Amount", "sum")}).sort_values("Purchase Amount", ascending=False)
        left, right = st.columns(2)
        left.plotly_chart(px.bar(product_cost.head(20), x="Particular", y="Purchase Amount", title="Top Products by Purchase Amount"), use_container_width=True, key="cost_top_products")
        right.plotly_chart(px.bar(location_summary(filtered), x="Location", y="Purchase Amount", title="Purchase Amount by Location"), use_container_width=True, key="cost_amount_by_location")
        rate_source = filtered.loc[filtered["Rate"].gt(0)].copy()
        rate_source["Month"] = rate_source["Date"].dt.to_period("M").dt.to_timestamp()
        product_rates = rate_source.groupby("Particular", as_index=False).agg(**{"Average Rate": ("Rate", "mean")}).sort_values("Average Rate", ascending=False)
        vendor_rates = rate_source.groupby("Vendor", as_index=False).agg(**{"Average Rate": ("Rate", "mean")}).sort_values("Average Rate", ascending=False)
        location_rates = rate_source.groupby("Location", as_index=False).agg(**{"Average Rate": ("Rate", "mean")}).sort_values("Average Rate", ascending=False)
        rate_trend = rate_source.groupby("Month", as_index=False).agg(**{"Average Rate": ("Rate", "mean")})
        st.subheader("Purchase Rate Analysis")
        rate_left, rate_right = st.columns(2)
        rate_left.plotly_chart(px.bar(product_rates.head(20), x="Particular", y="Average Rate", title="Average Rate by Product"), use_container_width=True, key="rate_by_product")
        rate_right.plotly_chart(px.line(rate_trend, x="Month", y="Average Rate", markers=True, title="Average Purchase Rate Trend"), use_container_width=True, key="rate_monthly_trend")
        st.dataframe(vendor_rates, use_container_width=True, hide_index=True)
        st.dataframe(location_rates, use_container_width=True, hide_index=True)
        rate_flags = rate_review_flags(filtered, metrics, current_month)
        st.subheader("Increasing Quantity and Increasing Purchase Rate")
        st.caption("These items require purchasing review because both purchase activity and the observed weighted purchase rate increased; this does not indicate profit changes.")
        st.dataframe(rate_flags, use_container_width=True, hide_index=True)

    with tabs[6]:
        quality = profile_data_quality(data)
        profile = pd.DataFrame({"Metric": list(quality), "Count": list(quality.values())})
        st.subheader("Data Quality Summary")
        st.dataframe(profile, use_container_width=True, hide_index=True)
        st.write({"Total records": len(data), "Date range": f"{min_date} to {max_date}", "Products": data["Particular"].nunique(), "Locations": data["Location"].nunique(), "Vendors": data["Vendor"].nunique(), "Total quantity": float(data["QTY"].sum()), "Total purchase amount": float(data["Amount"].sum())})
        st.caption("Completely empty rows and columns are removed. Other meaningful records, including duplicates and invalid values, are retained and reported; unusable records are excluded only from time-based metric calculations.")


if __name__ == "__main__":
    main()
