# Vercel-Native Stock Dashboard Design

## Goal

Replace the Streamlit runtime with a static Next.js dashboard that Vercel can deploy while preserving the existing purchase-analysis and stock-review workflows.

## Constraints

- The dashboard must run on Vercel without a persistent Python process.
- Users upload their own Excel or CSV file; purchase data is not committed to Git.
- The dashboard must continue to use purchase data only and must not claim profit.
- Calculations must aggregate quantity by month, location, and product before comparing months.

## Architecture

The application will use Next.js with a client-rendered dashboard. The browser will parse Excel files with SheetJS (`xlsx`), normalize the purchase-data fields, and retain all calculation state in memory. No API route or database is required because uploaded data is analyzed only in the user’s browser.

`lib/purchase-data.ts` will own validation, cleaning, filtering, monthly aggregation, quality profiling, and stock-review signals. `app/page.tsx` will own dashboard state, upload selection, filters, and tab composition. Presentational chart and table components will receive already-derived data and remain free of business calculation logic.

## Data Flow

1. A user uploads Excel or CSV data.
2. The parser identifies eligible worksheets with `Date`, `Particular`, `QTY`, `Rate`, `Amount`, `Vendor`, and `Location` columns.
3. Data is normalized conservatively: only fully blank rows and columns are removed; invalid or duplicate records are reported rather than silently deleted.
4. Sidebar filters create the active dataset.
5. Derived metrics compute quality summaries, KPIs, location/vendor summaries, product-month comparisons, and review candidates.
6. Tabs visualize and download the active data and derived product table.

## Stock-Review Signal

The dashboard will show `Candidate for stock review` when a location-product combination has all of the following:

- Positive month-over-month quantity change.
- A purchase in the latest selected calendar month.
- Activity in at least two months of the selected range.
- Current-month quantity at or above the median product quantity in that location.

The dashboard will display this criterion verbatim. It is a review signal, not an automatic purchase instruction or prediction of profit.

## User Experience

The page will provide upload guidance first, followed by a persistent filter panel and seven analysis tabs: Executive Summary, Section Analysis, Product Analysis, Stock Increase Analysis, Vendor Analysis, Purchase Cost Analysis, and Data Quality. Empty or incomplete input will produce readable validation messages. Every chart will have a distinct React key and accessible title.

## Testing and Deployment

Unit tests will cover parsing eligibility, conservative cleaning, filters, month-over-month calculations, zero denominators, and the stock-review criteria. A page-level test will cover the upload-empty state. Vercel will detect Next.js using `package.json` and build with `next build`; no `vercel.json` Python configuration will remain.
