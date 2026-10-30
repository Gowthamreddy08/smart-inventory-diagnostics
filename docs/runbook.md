# 📖 Operations Runbook & User Manual
**Smart Inventory Diagnostics: Retail Supply Chain Analytics**

This runbook provides step-by-step instructions for running, testing, troubleshooting, and operating the supply chain analytics pipeline.

---

## 1. Environment & Prerequisites

### A. Python Environment
The project runs within a dedicated Python virtual environment located at `.venv`:
* **Python Version:** Python 3.14+
* **Virtual Environment Path:** `C:\Users\venut\Desktop\inventory_analytics\.venv`

### B. Activating the Environment on Windows PowerShell

```powershell
# Open PowerShell and navigate to the project root
cd C:\Users\venut\Desktop\inventory_analytics

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, activate via `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or directly invoke the interpreter `.\.venv\Scripts\python.exe`)*.

### C. Verify Dependency Integrity
Confirm all required packages are properly installed and conflict-free:

```powershell
python -m pip check
```
*Expected Output:* `No broken requirements found.`

---

## 2. Running the Analytical Pipeline

The project features a master orchestrator (`run_pipeline.py`) that executes the workflow with automatic stage timing and error handling:

### A. Full End-to-End Pipeline (Recommended)
Executes data quality profiling, quarantine isolation, DuckDB warehouse build, counterfactual demand calculations, policy calibrations, and all 10 CSV/Markdown reports in ~17.5 seconds:

```powershell
python run_pipeline.py --all
```

### B. Granular Stage Execution Flags

| Flag | Purpose | Typical Runtime | Outputs |
| :--- | :--- | :---: | :--- |
| `python run_pipeline.py --audit-only` | Runs automated profiling and anomaly quarantine | ~1.2s | `data/quarantine/*`, `docs/data_quality_findings.md` |
| `python run_pipeline.py --build-db-only` | Executes DuckDB staging, dimensions, facts & views | ~1.2s | `data/processed/inventory_analytics.duckdb` |
| `python run_pipeline.py --metrics-only` | Computes rolling counterfactuals, ABC-XYZ & policies | ~14.8s | `fct_lost_sales_daily`, `mart_sku_store_policies` |
| `python run_pipeline.py --reports-only` | Generates executive scorecards and CSV exports | ~0.2s | `reports/*.csv`, `reports/*.md` |
| `python run_pipeline.py --run-tests` | Executes the complete 47-test pytest suite | ~24.0s | Terminal test execution logs |
| `python run_pipeline.py --launch-dashboard` | Starts the interactive Streamlit web application | Long-running | Launches local web server on port 8501 |

---

## 3. Running Automated Tests

To run the complete test suite across all 47 unit, SQL, policy, reporting, and integration tests:

```powershell
python -m pytest tests -v
```

To run a specific test module:

```powershell
# Data Quality & Quarantine tests (10 tests)
python -m pytest tests/test_data_quality.py -v

# DuckDB SQL Staging & Warehouse tests (7 tests)
python -m pytest tests/test_staging_and_sql.py -v

# Core Metrics & Replenishment Policy tests (9 tests)
python -m pytest tests/test_metrics_and_policies.py -v

# Business Analytics & Reporting tests (9 tests)
python -m pytest tests/test_analytics_and_reporting.py -v

# Streamlit Dashboard tests (4 tests)
python -m pytest tests/test_dashboard.py -v

# End-to-End Integration & Boundary tests (8 tests)
python -m pytest tests/test_end_to_end_integration.py -v
```

---

## 4. Launching the Interactive Web Dashboard

To launch the interactive dashboard in your browser:

```powershell
streamlit run dashboard/app.py
```

* Browser URL: `http://localhost:8501`
* Features:
  * Executive Scorecard with live revenue, margin, and counterfactual lost sales.
  * Interactive ABC-XYZ 9-box scatter plot and heatmap.
  * Dynamic Service Level Simulator (interactive CSL slider from 85% to 99.5%).
  * Daily Procurement Action Center with one-click CSV export of purchase orders.
  * Supplier reliability scorecard and lead-time variance decomposition.
  * Transparent data governance and anomaly quarantine audit logs.

---

## 5. Daily Procurement Operator Workflow

Inventory planners and procurement specialists should follow this standard daily operational sequence:

1. **Step 1: Check System Priority Alerts**
   * Open the dashboard tab **🚨 Procurement Action Center** or inspect [`reports/priority_action_list.csv`](file:///C:/Users/venut/Desktop/inventory_analytics/reports/priority_action_list.csv).
2. **Step 2: Expedite CRITICAL Items**
   * Filter for `priority_alert = 'CRITICAL'`.
   * These 40 items have current inventory positions below safety stock ($Pos \le SS$).
   * Expedite purchase orders for the indicated `recommended_reorder_qty` (totaling 18,124 units / \$538K capital).
3. **Step 3: Issue Standard Purchase Orders for HIGH Items**
   * Filter for `priority_alert = 'HIGH'`.
   * These 255 items have broken their reorder boundary ($Pos \le ROP$).
   * Generate scheduled purchase orders to bring inventory back to Order-Up-To levels (totaling 68,089 units / \$2.01M capital).
4. **Step 4: Export Reorder List**
   * Click **📥 Export Filtered Purchase Orders to CSV** in the dashboard to generate the clean vendor ordering manifest.

---

## 6. Troubleshooting & FAQs

### A. DuckDB File Lock Error (`IOException: Could not set lock on file`)
* **Cause:** DuckDB enforces single-writer / multi-reader file locks. This occurs if an active Streamlit dashboard or another Python script is writing to `inventory_analytics.duckdb`.
* **Fix:** Ensure any running writer process has closed its connection. Use `read_only=True` in analytical query scripts that only read data.

### B. Streamlit Fails to Start with `ModuleNotFoundError`
* **Cause:** The virtual environment is not active or Streamlit was executed with the system Python interpreter.
* **Fix:** Use the explicit virtual environment executable:
  ```powershell
  & "C:\Users\venut\Desktop\inventory_analytics\.venv\Scripts\streamlit.exe" run dashboard/app.py
  ```

### C. Quarantine Log Verification
* If data anomalies are suspected, inspect `data/quarantine/data_quality_findings.csv` and `docs/data_quality_findings.md`. Raw CSVs in `data/raw/` are **never modified in place**.
