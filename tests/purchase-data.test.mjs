import assert from "node:assert/strict";
import test from "node:test";
import { buildMetrics, filterRows } from "../lib/purchase-data.js";

const rows = [
  { Date: "2026-07-01", Location: "Rinas", Particular: "Tomato", QTY: 10, Rate: 10, Amount: 100, Vendor: "Cash" },
  { Date: "2026-07-02", Location: "Rinas", Particular: "Tomato", QTY: 15, Rate: 10, Amount: 150, Vendor: "Cash" },
  { Date: "2026-08-03", Location: "Rinas", Particular: "Tomato", QTY: 40, Rate: 11, Amount: 440, Vendor: "Cash" },
];

test("buildMetrics aggregates transactions before monthly growth and flags a review candidate", () => {
  const { metrics, currentMonth } = buildMetrics(rows);
  assert.equal(currentMonth, "2026-08");
  assert.equal(metrics[0].previousQuantity, 25);
  assert.equal(metrics[0].currentQuantity, 40);
  assert.equal(metrics[0].quantityChange, 15);
  assert.equal(metrics[0].growthPercent, 60);
  assert.equal(metrics[0].increaseSignal, "Candidate for stock review");
});

test("buildMetrics avoids percentage division by zero", () => {
  const { metrics } = buildMetrics([{ ...rows[2], Date: "2026-08-03" }]);
  assert.equal(metrics[0].previousQuantity, 0);
  assert.equal(metrics[0].growthPercent, null);
  assert.equal(metrics[0].growthStatus, "New activity");
});

test("filterRows applies date and dimension filters", () => {
  const result = filterRows(rows, { startDate: "2026-08-01", endDate: "2026-08-31", locations: ["Rinas"], products: ["Tomato"], vendors: ["Cash"] });
  assert.equal(result.length, 1);
  assert.equal(result[0].QTY, 40);
});
