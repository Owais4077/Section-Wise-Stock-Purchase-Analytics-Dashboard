# Section-wise Stock & Purchase Analytics

A Vercel-ready Next.js dashboard for location-wise purchase activity and stock-review analysis.

## Run locally

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`, then upload an Excel workbook or CSV containing: `Date`, `Particular`, `QTY`, `Rate`, `Amount`, `Vendor`, and `Location`.

## Deploy on Vercel

Import this repository into Vercel and deploy the `main` branch. Vercel detects Next.js from `package.json`; no framework override or Python function configuration is required.

The dashboard analyzes uploaded purchase history entirely in the browser. It surfaces candidates for stock review but does not calculate or claim profit because selling-price and margin data are absent.
