# Section-wise Stock & Purchase Analytics

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Upload an Excel workbook or CSV with these fields: `Date`, `Particular`, `QTY`, `Rate`, `Amount`, `Vendor`, and `Location`.

The application uses purchase history to surface stock-review candidates. It does not calculate or claim profit because selling-price and margin data are absent.
