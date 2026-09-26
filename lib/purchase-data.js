export const REQUIRED_COLUMNS = ["Date", "Particular", "QTY", "Rate", "Amount", "Vendor", "Location"];

export function normalizeRows(rows) {
  return rows.filter((row) => Object.values(row).some((value) => value !== null && value !== undefined && value !== "")).map((row) => ({
    Date: row.Date ? new Date(row.Date).toISOString().slice(0, 10) : null,
    Particular: String(row.Particular ?? "").trim() || null,
    QTY: Number(row.QTY), Rate: Number(row.Rate), Amount: Number(row.Amount),
    Vendor: String(row.Vendor ?? "").trim() || null,
    Location: String(row.Location ?? "").trim() || null,
  }));
}

export function filterRows(rows, filters) {
  return rows.filter((row) => (!filters.startDate || row.Date >= filters.startDate)
    && (!filters.endDate || row.Date <= filters.endDate)
    && (!filters.locations?.length || filters.locations.includes(row.Location))
    && (!filters.products?.length || filters.products.includes(row.Particular))
    && (!filters.vendors?.length || filters.vendors.includes(row.Vendor)));
}

export function qualityProfile(rows) {
  return {
    "Missing dates": rows.filter((r) => !r.Date).length,
    "Missing products": rows.filter((r) => !r.Particular).length,
    "Missing quantities": rows.filter((r) => !Number.isFinite(r.QTY)).length,
    "Negative quantities": rows.filter((r) => r.QTY < 0).length,
    "Zero quantities": rows.filter((r) => r.QTY === 0).length,
    "Non-positive rates": rows.filter((r) => !Number.isFinite(r.Rate) || r.Rate <= 0).length,
    "Negative amounts": rows.filter((r) => r.Amount < 0).length,
    "Duplicate rows": rows.length - new Set(rows.map((r) => JSON.stringify(r))).size,
  };
}

export function buildMetrics(rows) {
  const valid = rows.filter((r) => r.Date && r.Location && r.Particular && Number.isFinite(r.QTY) && Number.isFinite(r.Amount));
  const months = [...new Set(valid.map((r) => r.Date.slice(0, 7)))].sort();
  const currentMonth = months.at(-1) ?? null;
  const previousMonth = currentMonth ? new Date(`${currentMonth}-01T00:00:00Z`).toISOString().slice(0, 7).replace(/-(\d{2})$/, (_, month) => month === "01" ? "-12" : `-${String(Number(month) - 1).padStart(2, "0")}`) : null;
  if (currentMonth?.endsWith("-01")) {
    const year = Number(currentMonth.slice(0, 4)) - 1;
    return buildMetricsWithMonths(valid, currentMonth, `${year}-12`);
  }
  return buildMetricsWithMonths(valid, currentMonth, previousMonth);
}

function buildMetricsWithMonths(rows, currentMonth, previousMonth) {
  const keyOf = (row) => `${row.Location}|||${row.Particular}`;
  const records = new Map();
  const monthly = new Map();
  rows.forEach((row) => {
    const key = keyOf(row); const month = row.Date.slice(0, 7);
    if (!records.has(key)) records.set(key, { location: row.Location, particular: row.Particular, purchaseAmount: 0, totalQuantity: 0, purchaseFrequency: 0, activeMonths: new Set(), lastPurchaseDate: row.Date, rateAmount: 0, rateQuantity: 0 });
    const aggregate = records.get(key);
    aggregate.purchaseAmount += row.Amount; aggregate.totalQuantity += row.QTY; aggregate.purchaseFrequency += 1; aggregate.activeMonths.add(month); aggregate.lastPurchaseDate = aggregate.lastPurchaseDate > row.Date ? aggregate.lastPurchaseDate : row.Date;
    if (row.Rate > 0 && row.QTY > 0) { aggregate.rateAmount += row.Amount; aggregate.rateQuantity += row.QTY; }
    monthly.set(`${month}|||${key}`, (monthly.get(`${month}|||${key}`) ?? 0) + row.QTY);
  });
  const raw = [...records.entries()].map(([key, value]) => ({ ...value, currentQuantity: monthly.get(`${currentMonth}|||${key}`) ?? 0, previousQuantity: monthly.get(`${previousMonth}|||${key}`) ?? 0 }));
  const medians = Object.fromEntries([...new Set(raw.map((r) => r.location))].map((location) => {
    const values = raw.filter((r) => r.location === location).map((r) => r.currentQuantity).sort((a, b) => a - b);
    const mid = Math.floor(values.length / 2); return [location, values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2];
  }));
  const metrics = raw.map((r) => {
    const quantityChange = r.currentQuantity - r.previousQuantity;
    const growthPercent = r.previousQuantity ? Number((quantityChange / r.previousQuantity * 100).toFixed(2)) : null;
    const growthStatus = quantityChange > 0 ? (r.previousQuantity === 0 ? "New activity" : "Increasing") : quantityChange < 0 ? "Decreasing" : "No change";
    const candidate = quantityChange > 0 && r.activeMonths.size >= 2 && r.lastPurchaseDate.slice(0, 7) === currentMonth && r.currentQuantity >= medians[r.location];
    return { ...r, activeMonths: r.activeMonths.size, quantityChange, growthPercent, growthStatus, averageRate: r.rateQuantity ? Number((r.rateAmount / r.rateQuantity).toFixed(2)) : null, increaseSignal: candidate ? "Candidate for stock review" : "Monitor" };
  });
  return { metrics: metrics.sort((a, b) => b.quantityChange - a.quantityChange), currentMonth, previousMonth };
}

export function locationSummary(rows) {
  const summary = new Map();
  rows.forEach((r) => { const value = summary.get(r.Location) ?? { location: r.Location, totalQuantity: 0, purchaseAmount: 0, products: new Set() }; value.totalQuantity += r.QTY; value.purchaseAmount += r.Amount; value.products.add(r.Particular); summary.set(r.Location, value); });
  return [...summary.values()].map((r) => ({ ...r, products: r.products.size }));
}
