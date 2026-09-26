# Vercel Stock Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit runtime with a browser-based Next.js dashboard Vercel can build and deploy.

**Architecture:** A client-side Next.js page accepts the Excel/CSV upload, uses SheetJS to parse it, and derives quality, filter, monthly comparison, and stock-review data in TypeScript. Charts and tables render from the filtered data without API routes or a database.

**Tech Stack:** Next.js, React, TypeScript, SheetJS, Recharts, Vitest.

**Spec:** `docs/superpowers/specs/2026-09-26-vercel-stock-dashboard-design.md`

## Global Constraints

- No purchase data is committed to Git.
- The Vercel build must use `next build`; no Python Vercel entrypoint remains.
- Product growth is calculated after Month + Location + Particular aggregation.
- Purchase Amount is never labelled as profit.

## Review Focus

- Excel workbooks with no eligible sheet must show a clear error.
- Previous-month zero quantity must never produce infinity or a divide-by-zero error.
- Reset must clear all dimension filters and restore the full date range.
- Duplicate chart labels must not create duplicate React/visualization keys.
- Invalid or incomplete records must be reported and excluded only where calculations require valid fields.

---

### Task 1: Vercel-ready project shell

**Files:** Create `package.json`, `next.config.mjs`, `tsconfig.json`, `app/layout.tsx`, `app/globals.css`; remove `app.py`.

- [ ] Write a failing build test for the required Next.js scripts and absence of `app.py`.
- [ ] Add the minimal Next.js configuration and root layout.
- [ ] Run `npm run build` successfully.

### Task 2: Purchase-data analysis module

**Files:** Create `lib/purchase-data.ts`, `lib/purchase-data.test.ts`.

- [ ] Write failing tests for monthly aggregation, zero previous quantity, filters, and the stock-review signal.
- [ ] Implement parsing-ready normalization and pure data analysis functions.
- [ ] Run `npm test` successfully.

### Task 3: Dashboard interface

**Files:** Create `app/page.tsx`, `components/dashboard.tsx`.

- [ ] Write a failing component test for the upload-empty state.
- [ ] Build upload, filters, KPI cards, analysis tabs, download actions, and stock-review tables/charts.
- [ ] Run tests and `npm run build` successfully.

### Task 4: Publish and verify

**Files:** Modify `README.md`, `.gitignore`.

- [ ] Document Vercel deployment.
- [ ] Run the full tests and production build.
- [ ] Commit and push the completed conversion to `main`.
