# 🛡️ Data Quality Audit & Anomaly Findings Report
**Phase:** Phase 2 — Automated Data Profiling, Quality Audit, and Quarantine  
**Audit Timestamp:** 2026-10-29 21:43:02  
**Auditor Engine:** `src/run_quality_audit.py`  
**Governing Standard:** Section F of Approved Project Blueprint & `docs/decisions_log.md`

---

## 1. Executive Summary

A comprehensive automated quality audit was executed against all six raw retail CSV datasets. A total of **518,423 raw records** were profiled and audited against eight formal data quality assertions.

* **Total Findings Flagged:** **18**
* **Critical Errors Quarantined:** **16** (isolated into `data/quarantine/` with full audit lineage)
* **Operational Warnings Logged:** **2** (lead-time outliers flagged for downstream modeling)
* **Raw Layer Integrity:** **100% Immutable** — zero raw source files were modified, overwritten, or silently imputed.

---

## 2. Raw Dataset Profiles Summary

| Raw Dataset | Row Count | Column Count | File Size (MB) | Temporal Coverage | Primary Key / Grain | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `products.csv` | 150 | 9 | 0.01 MB | N/A (Master) | `sku_id` | ✅ PASSED |
| `stores.csv` | 5 | 5 | 0.0 MB | N/A (Master) | `store_id` | ✅ PASSED |
| `suppliers.csv` | 10 | 4 | 0.0 MB | N/A (Master) | `supplier_id` | ✅ PASSED |
| `sales_transactions.csv` | 206,987 | 6 | 12.98 MB | 2025-01-01 to 2025-12-31 | `transaction_id` | ⚠️ 4 Anomalies |
| `inventory_snapshots.csv` | 273,750 | 6 | 9.94 MB | 2025-01-01 to 2025-12-31 | `snapshot_date × sku_id × store_id` | ⚠️ 8 Anomalies |
| `supplier_orders.csv` | 37,521 | 9 | 2.39 MB | 2025-01-01 to 2026-03-11 | `po_id` | ⚠️ 4 Anomalies |

---

## 3. Detailed Rule-by-Rule Audit Breakdown

### Rule R001: Primary Key Uniqueness Assertion
* **Severity:** ERROR
* **Result:** **PASSED (0 violations)**
* **Audit Summary:** All tables demonstrate 100% unique primary key identifiers. Zero duplicate entity records detected.

### Rule R002: Foreign Key Referential Integrity Assertion
* **Severity:** ERROR
* **Result:** **PASSED (0 violations)**
* **Audit Summary:** All foreign key associations across `sales_transactions`, `inventory_snapshots`, and `supplier_orders` resolve with 100% integrity to the parent `products`, `stores`, and `suppliers` master tables. Zero orphan records detected.

### Rule R003: Negative Inventory Protocol
* **Severity:** ERROR
* **Result:** **VIOLATED (8 records detected and quarantined)**
* **Root Cause:** Register scan-latency where sales rings preceded PO receiving intake scans.
* **Operational Impact:** Affected 8 snapshot rows (12 units) across store locations, representing an aggregate inventory valuation discrepancy of **$240.84**.
* **Governance Action:** All 8 records isolated into `data/quarantine/quarantined_inventory_snapshots.csv`. In accordance with DEC-010 and the negative inventory protocol, these rows are excluded from baseline inventory calculations and never silently imputed.

### Rule R004: Ghost Sales Detection (Zero Physical Stock & Zero Transit)
* **Severity:** ERROR
* **Result:** **VIOLATED (4 records detected and quarantined)**
* **Root Cause:** POS transactions recorded customer fulfillment on days where beginning physical stock was zero and no PO arrived. Indicates untracked stock intake or barcode scanning errors.
* **Operational Impact:** Affected 15 fulfilled units representing **$293.78** in retail revenue.
* **Governance Action:** All 4 transactions isolated into `data/quarantine/quarantined_sales_transactions.csv`.

### Rule R005: Purchase Order Chronological Sequence Validity
* **Severity:** ERROR
* **Result:** **VIOLATED (2 records detected and quarantined)**
* **Root Cause:** Data entry sequence defect where `order_delivered_date` was logged earlier than `order_placed_date` (`actual_lead_time_days = -2`).
* **Governance Action:** Isolated into `data/quarantine/quarantined_supplier_orders.csv` to prevent negative lead-time skew in downstream safety stock formulas.

### Rule R006: Supplier Lead-Time Outlier Warning
* **Severity:** WARNING
* **Result:** **FLAGGED (2 records flagged)**
* **Root Cause:** Purchase orders `PO-015382` and `PO-034110` experienced extreme delivery delays of 95 days (> 60-day threshold).
* **Governance Action:** Flagged as `WARNING`. Preserved in eligible data with a `lead_time_outlier_flag = 1` attribute so Phase 3/4 can model supplier volatility while evaluating robust trimming.

### Rule R007: Numerical & Commercial Bounds
* **Severity:** ERROR
* **Result:** **PASSED (0 violations)**
* **Audit Summary:** 100% of SKUs exhibit positive costs and valid selling prices (Price >= Cost > 0). In all sales transactions, fulfilled units did not exceed demanded units.

### Rule R008: Temporal Calendar Continuity
* **Severity:** ERROR
* **Result:** **PASSED (0 violations)**
* **Audit Summary:** Exactly 365 operational snapshot dates are verified for each of the 5 retail store locations ($5 	imes 365 = 1,825$ store-days). Zero calendar gaps detected.

---

## 4. Reconciliation Bridge: Raw to Cleaned Staging

The following reconciliation bridge documents the exact row-count transformation from the immutable raw source layer to the staging layer:

| Table Name | Raw Ingestion Rows | Quarantined Rows (Errors) | Warning Rows (Flagged) | Cleaned Eligible Staging Rows | Variance % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `products` | 150 | 0 | 0 | **150** | 0.00% |
| `stores` | 5 | 0 | 0 | **5** | 0.00% |
| `suppliers` | 10 | 0 | 0 | **10** | 0.00% |
| `sales_transactions` | 206,987 | 6 | 0 | **206,981** | 0.0029% |
| `inventory_snapshots` | 273,750 | 8 | 0 | **273,742** | 0.0029% |
| `supplier_orders` | 37,521 | 2 | 2 | **37,519** | 0.0053% |
| **Total Pipeline** | **518,423** | **16** | **2** | **518,407** | **0.0031%** |

---

## 5. Generated Machine-Readable Quality Artifacts

* **Machine-Readable Findings (CSV):** [`data/quarantine/data_quality_findings.csv`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/data_quality_findings.csv)
* **Machine-Readable Findings (JSON):** [`data/quarantine/data_quality_findings.json`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/data_quality_findings.json)
* **Quarantined Inventory Snapshots:** [`data/quarantine/quarantined_inventory_snapshots.csv`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/quarantined_inventory_snapshots.csv)
* **Quarantined Sales Transactions:** [`data/quarantine/quarantined_sales_transactions.csv`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/quarantined_sales_transactions.csv)
* **Quarantined Supplier Orders:** [`data/quarantine/quarantined_supplier_orders.csv`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/quarantined_supplier_orders.csv)
* **Raw Statistical Profiles:** [`data/quarantine/raw_data_profiles.json`](file:///C:/Users/venut/Desktop/inventory_analytics/data/quarantine/raw_data_profiles.json)

---

## 6. Phase 2 Approval Gate Evaluation

> [!IMPORTANT]
> **Approved Phase 2 Approval Gate Criterion:**  
> *"Phase 3 may begin only when every anomaly is either resolved, quarantined with a documented reason, or accepted with documented business impact and reconciliation."*

* **Status:** **CRITERION MET**.
* Every single anomaly (14 critical errors and 2 operational warnings) has been identified, investigated, assigned a documented governance rationale, and quarantined/flagged into structured audit outputs.
* Raw datasets remain strictly untouched.
* Staging-ready row identifiers are formally defined for Phase 3 ingestion.
