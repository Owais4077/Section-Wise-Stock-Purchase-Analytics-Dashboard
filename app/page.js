"use client";

import { useMemo, useState } from "react";
import * as XLSX from "xlsx";
import { BarChart, Bar, CartesianGrid, Legend, LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { REQUIRED_COLUMNS, buildMetrics, filterRows, locationSummary, normalizeRows, qualityProfile } from "@/lib/purchase-data";

const tabs = ["Executive Summary", "Section Analysis", "Product Analysis", "Stock Increase Analysis", "Vendor Analysis", "Purchase Cost Analysis", "Data Quality"];
const number = (value) => Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

function Download({ rows, filename, label }) {
  function download() {
    const sheet = XLSX.utils.json_to_sheet(rows); const workbook = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(workbook, sheet, "Analysis");
    XLSX.writeFile(workbook, filename);
  }
  return <button className="secondary" onClick={download}>{label}</button>;
}

function Chart({ children }) { return <div className="chart"><ResponsiveContainer width="100%" height={300}>{children}</ResponsiveContainer></div>; }

export default function Home() {
  const [rows, setRows] = useState([]); const [sheetOptions, setSheetOptions] = useState([]); const [sheet, setSheet] = useState("");
  const [workbook, setWorkbook] = useState(null); const [error, setError] = useState(""); const [tab, setTab] = useState(tabs[0]);
  const [filters, setFilters] = useState({ startDate: "", endDate: "", locations: [], products: [], vendors: [] });
  function loadSheet(book, sheetName) {
    const parsed = XLSX.utils.sheet_to_json(book.Sheets[sheetName], { defval: null });
    const clean = normalizeRows(parsed); setRows(clean); setSheet(sheetName); setError("");
    const dates = clean.map((r) => r.Date).filter(Boolean).sort(); setFilters({ startDate: dates[0] ?? "", endDate: dates.at(-1) ?? "", locations: [], products: [], vendors: [] });
  }
  async function upload(event) {
    const file = event.target.files?.[0]; if (!file) return; setError("");
    try { const data = await file.arrayBuffer(); const book = XLSX.read(data, { type: "array", cellDates: true }); const eligible = book.SheetNames.filter((name) => { const headers = XLSX.utils.sheet_to_json(book.Sheets[name], { header: 1, range: 0 })[0] ?? []; return REQUIRED_COLUMNS.every((column) => headers.map((h) => String(h).trim()).includes(column)); });
      if (!eligible.length) throw new Error(`No worksheet has all required columns: ${REQUIRED_COLUMNS.join(", ")}.`);
      setWorkbook(book); setSheetOptions(eligible); loadSheet(book, eligible[0]);
    } catch (cause) { setRows([]); setError(cause.message || "Unable to read this file."); }
  }
  const options = useMemo(() => ({ locations: [...new Set(rows.map((r) => r.Location).filter(Boolean))].sort(), products: [...new Set(rows.map((r) => r.Particular).filter(Boolean))].sort(), vendors: [...new Set(rows.map((r) => r.Vendor).filter(Boolean))].sort() }), [rows]);
  const filtered = useMemo(() => filterRows(rows, filters), [rows, filters]); const analysis = useMemo(() => buildMetrics(filtered), [filtered]); const quality = useMemo(() => qualityProfile(rows), [rows]);
  const summary = useMemo(() => locationSummary(filtered), [filtered]);
  const candidates = analysis.metrics.filter((r) => r.increaseSignal === "Candidate for stock review");
  const selectMany = (name, values) => setFilters((old) => ({ ...old, [name]: [...values].filter(Boolean) }));
  const reset = () => { const dates = rows.map((r) => r.Date).filter(Boolean).sort(); setFilters({ startDate: dates[0] ?? "", endDate: dates.at(-1) ?? "", locations: [], products: [], vendors: [] }); };
  const totalAmount = filtered.reduce((sum, r) => sum + r.Amount, 0); const totalQty = filtered.reduce((sum, r) => sum + r.QTY, 0);
  return <main>
    <header><p className="eyebrow">PURCHASE DECISION SUPPORT</p><h1>Section-wise Stock &amp; Purchase Analytics</h1><p>Purchase activity analysis by location. Purchase Amount is cost—not profit.</p></header>
    {!rows.length && <section className="upload-card"><h2>Upload purchase data</h2><p>Excel or CSV columns required: Date, Particular, QTY, Rate, Amount, Vendor, Location.</p><input type="file" accept=".xlsx,.xls,.csv" onChange={upload} />{error && <p className="error">{error}</p>}</section>}
    {!!rows.length && <div className="layout">
      <aside><h2>Filters</h2>{sheetOptions.length > 1 && <label>Worksheet<select value={sheet} onChange={(e) => loadSheet(workbook, e.target.value)}>{sheetOptions.map((name) => <option key={name}>{name}</option>)}</select></label>}
      <label>Start date<input type="date" value={filters.startDate} onChange={(e) => setFilters({ ...filters, startDate: e.target.value })} /></label><label>End date<input type="date" value={filters.endDate} onChange={(e) => setFilters({ ...filters, endDate: e.target.value })} /></label>
      <label>Location<select multiple value={filters.locations} onChange={(e) => selectMany("locations", [...e.target.selectedOptions].map((o) => o.value))}>{options.locations.map((v) => <option key={v}>{v}</option>)}</select></label>
      <label>Product<select multiple value={filters.products} onChange={(e) => selectMany("products", [...e.target.selectedOptions].map((o) => o.value))}>{options.products.map((v) => <option key={v}>{v}</option>)}</select></label>
      <label>Vendor<select multiple value={filters.vendors} onChange={(e) => selectMany("vendors", [...e.target.selectedOptions].map((o) => o.value))}>{options.vendors.map((v) => <option key={v}>{v}</option>)}</select></label>
      <button onClick={reset}>Reset filters</button><Download rows={filtered} filename="filtered-purchase-data.xlsx" label="Download filtered data" /></aside>
      <section className="content"><div className="kpis"><div><span>Total quantity</span><strong>{number(totalQty)}</strong></div><div><span>Purchase Amount</span><strong>{number(totalAmount)}</strong></div><div><span>Products</span><strong>{new Set(filtered.map((r) => r.Particular)).size}</strong></div><div><span>Locations</span><strong>{new Set(filtered.map((r) => r.Location)).size}</strong></div></div>
      <nav>{tabs.map((name) => <button className={tab === name ? "active" : ""} key={name} onClick={() => setTab(name)}>{name}</button>)}</nav>
      {tab === "Executive Summary" && <><h2>Monthly purchase activity</h2><p>Latest comparison: {analysis.currentMonth || "—"} vs {analysis.previousMonth || "—"}</p><Chart><BarChart data={summary}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="location" /><YAxis /><Tooltip /><Legend /><Bar dataKey="totalQuantity" fill="#2563eb" name="Quantity" /><Bar dataKey="purchaseAmount" fill="#14b8a6" name="Purchase Amount" /></BarChart></Chart></>}
      {tab === "Section Analysis" && <><h2>Location performance</h2><Chart><BarChart data={summary}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="location" /><YAxis /><Tooltip /><Bar dataKey="purchaseAmount" fill="#0f766e" /></BarChart></Chart><DataTable rows={summary} /></>}
      {tab === "Product Analysis" && <><h2>Products with increasing quantity</h2><Chart><BarChart data={analysis.metrics.filter((r) => r.quantityChange > 0).slice(0, 20)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="particular" /><YAxis /><Tooltip /><Bar dataKey="quantityChange" fill="#2563eb" /></BarChart></Chart><DataTable rows={analysis.metrics} /><Download rows={analysis.metrics} filename="product-analysis.xlsx" label="Download analysis table" /></>}
      {tab === "Stock Increase Analysis" && <><h2>Stock review candidates</h2><p className="notice">A product is a candidate when quantity growth is positive, activity is recent and consistent, and current quantity is at least the location median. Review candidates; do not treat this as an automatic purchase instruction.</p><DataTable rows={candidates} /></>}
      {tab === "Vendor Analysis" && <><h2>Vendor purchase activity</h2><DataTable rows={Object.values(filtered.reduce((all, r) => { const item = all[r.Vendor] ?? { vendor: r.Vendor, totalQuantity: 0, purchaseAmount: 0, transactions: 0 }; item.totalQuantity += r.QTY; item.purchaseAmount += r.Amount; item.transactions += 1; all[r.Vendor] = item; return all; }, {}))} /></>}
      {tab === "Purchase Cost Analysis" && <><h2>Purchase Amount by product</h2><Chart><BarChart data={analysis.metrics.slice(0, 20)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="particular" /><YAxis /><Tooltip /><Bar dataKey="purchaseAmount" fill="#f59e0b" /></BarChart></Chart><DataTable rows={analysis.metrics} /></>}
      {tab === "Data Quality" && <><h2>Data quality</h2><DataTable rows={Object.entries(quality).map(([metric, count]) => ({ metric, count }))} /><p className="notice">Invalid and duplicate records are reported. They are not silently deleted.</p></>}
      </section></div>}
  </main>;
}

function DataTable({ rows }) { const columns = Object.keys(rows[0] ?? {}); return <div className="table-wrap"><table><thead><tr>{columns.map((c) => <th key={c}>{c.replaceAll(/([A-Z])/g, " $1")}</th>)}</tr></thead><tbody>{rows.slice(0, 200).map((row, i) => <tr key={i}>{columns.map((c) => <td key={c}>{typeof row[c] === "number" ? number(row[c]) : String(row[c] ?? "—")}</td>)}</tr>)}</tbody></table>{rows.length > 200 && <p>Showing the first 200 rows.</p>}</div>; }
