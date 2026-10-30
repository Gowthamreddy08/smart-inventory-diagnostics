# 📦 Smart Inventory Diagnostics: Retail Supply Chain Analytics
### An Explainable, Multi-Echelon Inventory Optimization and Policy Simulation Platform for Retail Supply Chains

[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://smart-inventory-diagnostics.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Warehouse-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Scientific-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-Statistics-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://scipy.org/)
[![Pytest](https://img.shields.io/badge/Pytest-47%20Passed%20(100%25)-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-9333EA?style=for-the-badge)](LICENSE)

[Live Demo](https://smart-inventory-diagnostics.streamlit.app/) • [Key Features](#-key-features) • [System Pipeline](#-end-to-end-pipeline) • [Skills & Tech Stack](#-skills--technologies) • [Mathematical Policy](#-mathematical-policy-formulation) • [The 9-Box Matrix](#-the-abc-xyz-portfolio-matrix) • [Empirical Benchmarks](#-empirical-supply-chain-benchmarks) • [Quickstart](#-quickstart--installation) • [How to Run](#-how-to-run) • [Testing](#-testing--verification) • [Governance Notice](#-governance--methodology-notice)

---

## 📌 Project Overview

In multi-store retail supermarket operations, inventory planners face a constant trade-off: **under-stocking** causes immediate shelf stockouts and millions in unfulfilled lost revenue, while **over-stocking** traps working capital in idle safety stock, warehousing fees, and shrinkage.

**Smart Inventory Diagnostics** is an enterprise-grade retail supply chain intelligence platform evaluating **5 physical store locations**, **150 supermarket SKUs** (750 operational pairs), and **10 suppliers** across **518,423 audited records**.

The platform integrates **automated data quality quarantine**, an embedded **DuckDB columnar warehouse**, **rolling counterfactual demand reconstruction**, **bivariate safety stock ($SS$) and reorder point ($ROP$) calibration**, and an **interactive Streamlit command center** with one-click purchase order generation.

```text
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│       GROSS SALES REVENUE       │   CONTRIBUTION MARGIN (42.2%)   │      NETWORK STOCKOUT RATE      │
│         $100,558,841.75         │         $42,464,922.02          │              6.93%              │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│    MODELED LOST SALES REVENUE   │    MODELED LOST GROSS MARGIN    │     ANNUALIZED HOLDING COST     │
│         $10,074,157.71          │          $4,313,057.21          │       $211,738.89 (at 22%)      │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│   SUPPLIER VARIANCE SS BUFFER   │    CRITICAL REORDER ALERTS      │    FULL TEST SUITE PASS RATE    │
│    $287,301.65 (22.8% of SS)    │   40 pairs (18,124 units / $538K) │     47 / 47 Passed (100%)       │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

> **⚠️ Governance Notice:** Estimated lost revenue and units are modeled counterfactuals based on rolling 4-week same-weekday in-stock sales history, representing commercial opportunity cost rather than audited accounting losses. Perishable shelf-life risk is isolated in a synthetic demonstration module.

---

## 🛠️ Skills & Technologies

| Domain | Tools & Technologies |
| :--- | :--- |
| **Programming & Querying** | [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![SQL](https://img.shields.io/badge/SQL-CC292B?style=for-the-badge&logo=sqlite&logoColor=white)](https://duckdb.org/) |
| **Data Warehousing & OLAP** | [![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org/) |
| **Data Science & Analytics** | [![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/) [![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/) [![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://scipy.org/) |
| **Interactive Dashboard & BI** | [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/) [![Altair](https://img.shields.io/badge/Altair-4B6B94?style=for-the-badge&logo=altair&logoColor=white)](https://altair-viz.github.io/) |
| **Testing & Quality Assurance** | [![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/) [![Data Quality](https://img.shields.io/badge/Data_Quality-Quarantine_Engine-2EA44F?style=for-the-badge)](#-data-quality--zero-variance-audit-reconciliation) |
| **Version Control & DevOps** | [![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)](https://git-scm.com/) [![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/) |
| **Supply Chain Competencies** | `Bivariate Safety Stock` • `Continuous ROP` • `Periodic Review (R=7)` • `ABC-XYZ Segmentation` • `Counterfactual Demand` • `Star Schema (Kimball)` |

---

## 🚀 Key Features

* 🩻 **Multi-Echelon Network Diagnostics:** Simultaneously diagnoses 750 SKU-Store pairs across 5 physical retail stores, 150 supermarket products, and 10 vendor supply chains.
* 🛡️ **Automated Data Quality & Quarantine:** 8 automated assertion rules isolate 16 critical anomalies (8 negative inventory, 6 ghost sales, 2 inverted PO dates) without mutating raw CSV sources.
* ⚡ **High-Speed DuckDB SQL Warehouse:** Star schema with 4 dimensions, 3 fact tables, and 4 analytical views executing complex window aggregations over 273,742 daily snapshots in milliseconds.
* 📈 **Leak-Free Counterfactual Demand:** Reconstructs unconstrained customer demand during stockouts ($\text{SOH} \le 0$) using a strictly backward-looking rolling 4-week same-weekday in-stock baseline.
* 🎯 **ABC-XYZ Portfolio Segmentation:** 9-box classification sorting items by cumulative Contribution Margin Pareto (Class A: $\le 80\%$, B: $80\text{--}95\%$, C: $> 95\%$) and empirical demand volatility ($CV \le 0.5$, $0.5 < CV \le 1.0$, $CV > 1.0$).
* 📏 **Bivariate Continuous Safety Stock ($SS$):** Combines customer daily demand variance ($\sigma_D^2$) and supplier lead-time variance ($\sigma_L^2$) into mathematically rigorous continuous buffers.
* 🔄 **Periodic Review Replenishment ($R = 7$ Days):** Models fixed weekly vendor delivery cycles to calculate dynamic Order-Up-To ceilings and recommended order quantities.
* 🚚 **Supplier Variance Buffer Decomposition:** Isolates the exact working capital (**\$287,301.65**) and buffer units (**9,953 units / 22.8% of network SS**) tied up strictly due to late vendor deliveries.
* ⚙️ **Dynamic Service Level Simulator:** Interactive slider (85% to 99.5% CSL) plotting the exponential "hockey-stick" cost curve of near-zero stockouts in real time.
* 🚨 **Daily Procurement Action Center:** Prioritizes items into **CRITICAL** (40 pairs, \$538K), **HIGH** (255 pairs, \$2.01M), **MEDIUM** (72 pairs), and **HEALTHY** (383 pairs).
* 📥 **One-Click PO Export:** Export prioritized vendor reorder recommendations directly to CSV for instantaneous procurement execution.
* 🧪 **Exhaustive Automated Pytest Harness:** **47 automated tests** validating data quality, SQL reconciliation, formula accuracy, calendar continuity, and stress boundary conditions (100% passing).
* ⏱️ **18-Second Reproducible Pipeline:** Master CLI orchestrator (`run_pipeline.py`) running data auditing, SQL warehouse builds, metrics calibration, and report generation in **17.5 seconds**.

---

## 🔄 End-to-End Pipeline

```text
Raw CSV Datasets (data/raw/)
  │ [products, stores, suppliers, sales, inventory, purchase_orders]
  ▼
┌────────────────────────────────────────────────────────┐
│ 1. Data Profiling & Quality Rule Assertions            │
│    (PK Uniqueness, Referential Integrity, Bounds)     │
└──────────────────────────┬─────────────────────────────┘
  │ (Critical Anomalies)    │ (Clean Valid Records)
  ▼                         ▼
┌──────────────────────┐ ┌────────────────────────────────────────────────────────┐
│ data/quarantine/     │ │ 2. DuckDB Analytics Warehouse Modeling                 │
│ 8 Negative SOH       │ │    Staging Layer (stg_*)                               │
│ 6 Ghost Sales        │ │    Dimensions: dim_product, dim_store, dim_date, etc.  │
│ 2 Inverted PO Dates  │ │    Fact Tables: fct_daily_sales, fct_inventory, fct_po │
└──────────────────────┘ └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                         ┌────────────────────────────────────────────────────────┐
                         │ 3. Rolling Counterfactual Demand Reconstruction        │
                         │    Rolling 4-Week Same-Weekday In-Stock Average        │
                         │    fct_lost_sales_daily (273,742 rows)                 │
                         └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                         ┌────────────────────────────────────────────────────────┐
                         │ 4. ABC-XYZ Portfolio Segmentation Engine               │
                         │    Pareto Margin (A/B/C) × Demand Volatility CV (X/Y/Z)│
                         └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                         ┌────────────────────────────────────────────────────────┐
                         │ 5. Bivariate Replenishment Policy Calibration          │
                         │    Continuous SS/ROP & Periodic Order-Up-To (R=7)      │
                         │    mart_sku_store_policies (750 pairs)                 │
                         └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
                         ┌────────────────────────────────────────────────────────┐
                         │ 6. Consumption & Decision Interfaces                   │
                         │    • 10 CSV & Markdown Reports (reports/)              │
                         │    • Streamlit Interactive Web Dashboard               │
                         │    • 47-Test Automated Verification Harness            │
                         └────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Policy Formulation

### 1. Rolling Counterfactual Lost Sales Demand
To reconstruct suppressed customer demand during stockout days ($\text{SOH}_{i,s,t} \le 0$) without future window leakage:

$$\hat{D}_{i,s,t} = \frac{1}{|K|} \sum_{k \in K} \text{units\_fulfilled}_{i,s,t - 7k}$$

$$\text{Estimated Lost Units}_{i,s,t} = \max(0, \lceil \hat{D}_{i,s,t} \rceil - \text{units\_fulfilled}_{i,s,t}) \quad (\text{when } \text{is\_stockout}_{i,s,t} = 1)$$

$$\text{Estimated Lost Revenue}_{i,s,t} = \text{Estimated Lost Units}_{i,s,t} \times \text{unit\_selling\_price}_i$$

*Where $K = \{k \in \{1, 2, 3, 4\} \mid \text{is\_stockout}_{i,s,t - 7k} = 0\}$. If $|K| = 0$, falls back safely to prior in-stock day velocity.*

---

### 2. Continuous-Review Bivariate Safety Stock & Reorder Point
Demand and supplier lead times are joint random variables. Safety stock covers both customer demand fluctuations ($\sigma_D^2$) and vendor delivery delays ($\sigma_L^2$):

$$SS_{\text{cont}} = \left\lceil Z \times \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2} \right\rceil$$

$$ROP = \left\lceil (\bar{D} \times \bar{L}) + SS_{\text{cont}} \right\rceil$$

*Where $Z$ is the Gaussian inverse normal CDF ($Z = 1.282$ for 90%, $1.645$ for 95%, $2.326$ for 99% CSL).*

---

### 3. Periodic-Review Safety Stock & Order-Up-To Level ($R = 7$ Days)
For retail supermarkets with fixed weekly vendor ordering schedules:

$$SS_{\text{periodic}} = \left\lceil Z \times \sqrt{(\bar{L} + R) \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2} \right\rceil$$

$$\text{Order-Up-To Level} = \left\lceil \bar{D} \times (\bar{L} + R) + SS_{\text{periodic}} \right\rceil$$

$$\text{Recommended Reorder Qty} = \max\left(0, \text{Order-Up-To Level} - (\text{SOH} + \text{In Transit})\right)$$

---

### 4. Supplier Variance Buffer Decomposition
Isolates working capital tied up exclusively due to supplier lead-time unreliability ($\sigma_L^2 > 0$):

$$SS_{\text{deterministic}} = \left\lceil Z \times \sqrt{\bar{L} \cdot \sigma_D^2} \right\rceil$$

$$\Delta SS_{\text{supplier}} = SS_{\text{actual}} - SS_{\text{deterministic}}$$

$$\Delta \text{Working Capital}_{\text{supplier}} = \Delta SS_{\text{supplier}} \times \text{unit\_cost}$$

---

## 🎯 The ABC-XYZ Portfolio Matrix

Evaluated across all **750 SKU-Store pairs** using annual cumulative gross profit (Pareto ABC) and daily demand coefficient of variation ($CV = \sigma_D / \bar{D}$):

| Segment | Profit Class | Demand Volatility | Pair Count | Margin Share % | Total Margin ($) | Prescribed Supply Chain Strategy |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **AX** | Class A | Smooth ($CV \le 0.5$) | 37 | 21.1% | \$8,958,564.76 | Continuous review; lean JIT buffers; automated replenishment. |
| **AY** | Class A | Variable ($0.5 < CV \le 1.0$) | 104 | 58.8% | \$24,976,836.87 | High-priority dynamic buffering; tight vendor SLA monitoring. |
| **AZ** | Class A | Erratic ($CV > 1.0$) | 0 | 0.0% | \$0.00 | High-value volatility; manual planner oversight; buffer caps. |
| **BX** | Class B | Smooth ($CV \le 0.5$) | 61 | 5.7% | \$2,407,117.31 | Periodic review ($R=7$); automated reorder points. |
| **BY** | Class B | Variable ($0.5 < CV \le 1.0$) | 96 | 9.3% | \$3,952,242.06 | Standard periodic review with dynamic variance tracking. |
| **BZ** | Class B | Erratic ($CV > 1.0$) | 1 | 0.1% | \$33,331.14 | Consignment stocking or minimum order quantity governance. |
| **CX** | Class C | Smooth ($CV \le 0.5$) | 162 | 1.4% | \$615,341.35 | Simplified bulk ordering; long review cycles to minimize handling. |
| **CY** | Class C | Variable ($0.5 < CV \le 1.0$) | 285 | 3.5% | \$1,480,801.51 | Order-to-order replenishment; lean stocking; catalog review. |
| **CZ** | Class C | Erratic ($CV > 1.0$) | 4 | 0.1% | \$40,687.02 | Make-to-order / vendor drop-ship; high risk of dead stock. |

---

## 📊 Empirical Supply Chain Benchmarks

### 1. Multi-Service Level Trade-Off Frontier
System-wide safety stock buffer units, working capital, and annual carrying costs (at 22% annual rate) across Cycle Service Level scenarios:

| Service Level (CSL) | Gaussian $Z$ | Safety Stock Units | Working Capital ($) | Annual Holding Cost ($) | Delta Units vs Prior | Delta Capital vs Prior |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **90% CSL** | 1.282 | 34,155 | \$929,114.63 | \$204,405.22 | Baseline | Baseline |
| **95% CSL (Baseline)** | 1.645 | 43,735 | \$1,190,629.66 | \$261,938.53 | +9,580 (+28.0%) | +\$261,515.03 (+28.1%) |
| **99% CSL** | 2.326 | 61,673 | \$1,645,126.69 | \$361,927.87 | +17,938 (+41.0%) | +\$454,497.03 (+38.2%) |

> **Key Policy Takeaway:** Moving from 95% to 99% CSL demands a **+41.0% increase in buffer inventory**, adding **+\$454.5K in working capital** and **+\$100K/year in holding costs**. Segmented service levels (99% for Class A cash cows, 90% for Class C tail) are mathematically superior to flat targets.

---

### 2. Store Network Performance
| Store ID | Store Name | Region | Store Tier | Gross Revenue ($) | Gross Margin % | Stockout Rate % | Modeled Lost Sales ($) | Avg DOH | Urgent Reorder ($) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STORE-01** | Metro Flagship | North | Tier 1 | \$28,883,618.77 | 42.1% | 7.64% | \$2,848,495.25 | 4.3 days | \$879,531.02 |
| **STORE-02** | Downtown Urban | South | Tier 1 | \$20,537,798.11 | 42.4% | 6.82% | \$2,054,124.77 | 3.9 days | \$555,270.08 |
| **STORE-04** | Westside Hub | West | Tier 2 | \$19,531,987.97 | 42.3% | 7.15% | \$1,965,785.29 | 3.7 days | \$442,166.45 |
| **STORE-03** | Suburban Center | East | Tier 2 | \$17,869,451.74 | 42.3% | 6.64% | \$1,813,517.76 | 3.7 days | \$376,647.26 |
| **STORE-05** | Eastgate Retail | Central | Tier 3 | \$13,735,985.16 | 42.1% | 6.38% | \$1,392,234.64 | 3.6 days | \$290,490.81 |

---

### 3. Supplier Lead-Time Reliability & Variance Impact
| Supplier ID | Supplier Name | Orders | Total Spend ($) | On-Time % | Mean Lead Time | Lead Time Std | Actual 95% SS | Supplier Buffer ($) | SS Share from Delay |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SUP-05** | Vanguard Distributors | 3,590 | \$8,955,481.94 | 59.8% | 6.97d | 2.29d | 5,726 units | **\$83,719.86** | **40.7%** |
| **SUP-02** | Pinnacle Brands Inc | 3,893 | \$9,936,279.77 | 58.1% | 7.08d | 2.17d | 5,554 units | **\$64,374.49** | **38.3%** |
| **SUP-01** | Apex Global Logistics | 3,314 | \$4,954,347.86 | 57.3% | 10.06d | 2.43d | 5,187 units | **\$40,631.87** | **32.7%** |
| **SUP-10** | National Wholesale Alliance | 3,831 | \$8,102,818.05 | 60.6% | 13.99d | 1.83d | 6,858 units | **\$38,602.18** | **20.1%** |
| **SUP-04** | Keystone Consumer Goods | 5,956 | \$6,238,808.01 | 69.4% | 7.03d | 1.53d | 4,934 units | **\$17,721.35** | **15.0%** |
| **SUP-09** | Continental Foods Group | 3,031 | \$5,306,651.62 | 67.7% | 5.00d | 1.15d | 1,770 units | **\$12,581.55** | **29.0%** |
| **SUP-06** | Frontier Beverage Supply | 4,006 | \$6,359,534.29 | 68.5% | 10.00d | 1.06d | 6,155 units | **\$12,417.81** | **8.2%** |
| **SUP-07** | Summit Packaging Solutions | 3,526 | \$5,212,341.66 | 72.6% | 7.01d | 0.87d | 3,961 units | **\$7,288.27** | **9.1%** |
| **SUP-08** | Pacific Rim Sourcing | 3,202 | \$995,723.92 | 59.2% | 5.03d | 2.05d | 1,217 units | **\$5,959.78** | **44.3%** |
| **SUP-03** | BlueSky Supply Co | 3,170 | \$2,171,691.93 | 68.5% | 14.02d | 1.81d | 2,373 units | **\$3,992.99** | **13.1%** |

---

## 🔒 Data Quality & Zero-Variance Audit Reconciliation

The pipeline enforces complete raw source immutability. All anomalous records are quarantined into isolated files without in-place editing:

| Entity Name | Raw Ingested Rows | Quarantined Rows | Clean Modeled Rows | Reconciliation Variance | Financial / Integrity Impact Quarantined |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Products** (`dim_product`) | 150 | 0 | 150 | **0** | Clean master catalog |
| **Stores** (`dim_store`) | 5 | 0 | 5 | **0** | Clean store locations |
| **Suppliers** (`dim_supplier`) | 10 | 0 | 10 | **0** | Clean supplier master |
| **Sales** (`fct_daily_sales`) | 206,987 | 6 | 206,981 | **0** | \$214.30 phantom sales quarantined (Ghost Sales) |
| **Inventory** (`fct_daily_inventory_snapshot`) | 273,750 | 8 | 273,742 | **0** | -\$672.45 negative inventory quarantined |
| **Purchase Orders** (`fct_purchase_orders`) | 37,521 | 2 | 37,519 | **0** | 2 POs with delivery preceding order date isolated |
| **TOTALS** | **518,423** | **16** | **518,407** | **0** | **100% Bit-for-Bit Reconciled** |

---

## 📂 Project Directory Structure

```text
inventory_analytics/
├── data/
│   ├── raw/                              # Immutable source CSV files (518k rows)
│   │   ├── products.csv                  # 150 supermarket SKUs with costs and retail prices
│   │   ├── stores.csv                    # 5 retail store locations with regional tiers
│   │   ├── suppliers.csv                 # 10 suppliers with contracted SLAs
│   │   ├── sales_transactions.csv        # 206,987 daily customer sales transactions
│   │   ├── inventory_snapshots.csv       # 273,750 daily end-of-day physical stock records
│   │   └── supplier_orders.csv           # 37,521 historical purchase orders with lead times
│   ├── quarantine/                       # Isolated anomalous records & audit logs
│   │   ├── quarantined_inventory_snapshots.csv  # 8 negative SOH rows isolated
│   │   ├── quarantined_sales_transactions.csv   # 6 ghost sales rows isolated
│   │   ├── quarantined_supplier_orders.csv      # 2 inverted lead-time POs isolated
│   │   ├── data_quality_findings.csv     # Tabular audit findings log
│   │   └── raw_data_profiles.json        # Machine-readable dataset profiling metadata
│   └── processed/                        # DuckDB analytical columnar warehouse
│       └── inventory_analytics.duckdb    # Fast embedded SQL database (12.3 MB)
│
├── sql/                                  # Modular DuckDB SQL transformations
│   ├── 01_create_staging.sql             # Staging tables filtering quarantined records
│   ├── 02_create_dimensions.sql          # Dimension tables (product, store, supplier, date)
│   ├── 03_create_fact_tables.sql         # Fact tables (daily sales, snapshots, POs)
│   └── 04_create_analytics_views.sql     # Summary views & lead-time profiling
│
├── src/                                  # Core Python analytics and modeling engines
│   ├── data_generation.py                # Controlled synthetic enterprise retail generator
│   ├── data_profiler.py                  # Automated schema and statistical profiler
│   ├── data_quality.py                   # Data quality assertion rule checker
│   ├── quarantine.py                     # Non-destructive anomaly quarantine manager
│   ├── run_quality_audit.py              # Phase 2 audit pipeline runner
│   ├── build_database.py                 # Phase 3 DuckDB SQL warehouse builder
│   ├── demand_estimator.py               # Rolling 4-week same-weekday counterfactual engine
│   ├── abc_xyz_segmentation.py           # Pareto margin (ABC) & demand CV (XYZ) classifier
│   ├── inventory_policy.py               # Continuous SS/ROP & periodic Order-Up-To engine
│   ├── run_phase_4_metrics.py            # Phase 4 metrics orchestrator
│   └── analytics_reporting.py            # Phase 5 reporting & scorecard generator
│
├── dashboard/                            # Interactive presentation layer
│   └── app.py                            # Multi-tab interactive Streamlit web dashboard
│
├── reports/                              # Generated business reports & scorecards
│   ├── executive_insights_report.md      # 15 KB executive analytical narrative
│   ├── executive_scorecard.csv           # High-level network KPIs
│   ├── store_performance.csv             # Store revenue, margin %, and stockout rates
│   ├── category_diagnostics.csv          # Merchandising performance & turnover ratios
│   ├── abc_xyz_portfolio_analysis.csv    # 9-box distribution & playbook strategies
│   ├── supplier_performance_and_lead_time.csv  # Vendor reliability & buffer capital
│   ├── service_level_tradeoffs.csv       # 90% vs 95% vs 99% CSL scenario modeling
│   ├── priority_action_list.csv          # Operational replenishment worklist (CRITICAL & HIGH)
│   ├── synthetic_spoilage_diagnostics.csv # Isolated perishables risk module
│   └── data_quality_reconciliation_summary.csv # Zero-variance audit reconciliation
│
├── docs/                                 # Formal governance & operational manuals
│   ├── analysis_scope.md                 # Scope, grains, boundaries, and success criteria
│   ├── metric_definitions.md             # Mathematical data dictionary
│   ├── decisions_log.md                  # Approved decisions log (DEC-001 to DEC-019)
│   ├── assumptions_and_limitations.md    # Documented constraints & assumptions
│   ├── data_quality_findings.md          # Automated audit findings report
│   ├── architecture.md                   # System architecture & dimensional models
│   ├── testing_report.md                 # Formal QA test audit report (47 tests)
│   └── runbook.md                        # Operator runbook & command reference
│
├── tests/                                # Automated Pytest test harness (47 tests)
│   ├── test_data_quality.py              # 10 tests: schema, PK/FK, quarantine, immutability
│   ├── test_staging_and_sql.py           # 7 tests: DuckDB tables, views, row reconciliation
│   ├── test_metrics_and_policies.py      # 9 tests: counterfactuals, ABC-XYZ, SS/ROP math
│   ├── test_analytics_and_reporting.py   # 9 tests: cross-report parity, vendor variance
│   ├── test_dashboard.py                 # 4 tests: compilation, queries, simulator math
│   └── test_end_to_end_integration.py    # 8 tests: calendar continuity, stress & boundaries
│
├── run_pipeline.py                       # Master CLI orchestrator (runs Stages 1–4 in 17.5s)
└── requirements.txt                      # Project dependency specification
```

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Gowthamreddy08/smart-inventory-diagnostics.git
cd smart-inventory-diagnostics
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
python -m pip check
```

---

## 💻 How to Run

### 1. Launch the Streamlit Web Dashboard
```bash
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501`. Features include:
* **Tab 1: Executive Overview:** Macro KPIs, fulfilled sales vs lost sales trends, category margin share, and store-level table.
* **Tab 2: Daily Reorder Action List:** Immediate operational workbench filtering 40 CRITICAL items and 255 HIGH items with one-click purchase order CSV download.
* **Tab 3: Product Portfolio (ABC-XYZ):** 9-box heatmap, interactive scatter plot (Margin Pareto vs Demand CV), and segment strategies.
* **Tab 4: Safety Stock Simulator:** Interactive CSL slider (85% to 99.5%) plotting the non-linear "hockey-stick" cost curve in real time.
* **Tab 5: Supplier Reliability:** Vendor lead-time distributions and working capital decomposition by supplier.
* **Tab 6: Data Quality & Audit:** Zero-variance audit reconciliation and quarantined anomaly inspection.

---

### 2. Execute the Master CLI Pipeline (End-to-End)
Execute the complete data lifecycle (quality audit $\rightarrow$ DuckDB warehouse $\rightarrow$ policy engine $\rightarrow$ reporting) in **~17.5 seconds**:

```bash
python run_pipeline.py --all
```

---

### 3. Run Individual Pipeline Stages

```bash
# Stage 1: Data Profiling, Quality Audit & Quarantine Isolation
python run_pipeline.py --audit-only

# Stage 2: DuckDB SQL Warehouse & Dimensional Modeling
python run_pipeline.py --build-db-only

# Stage 3: Rolling Counterfactual Demand, ABC-XYZ & Inventory Policies
python run_pipeline.py --metrics-only

# Stage 4: Business Insights, Scorecard Generation & CSV Export
python run_pipeline.py --reports-only

# Run the 47-Test Pytest Suite
python run_pipeline.py --run-tests
```

---

## 🧪 Testing & Verification

Run the automated test suite across all 6 test modules:

```bash
pytest tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\venut\Desktop\inventory_analytics
plugins: anyio-4.15.1
collected 47 items

tests/test_analytics_and_reporting.py .........                         [ 19%]
tests/test_dashboard.py .....................                         [ 27%]
tests/test_data_quality.py ..................                         [ 48%]
tests/test_end_to_end_integration.py ........                         [ 65%]
tests/test_metrics_and_policies.py ............                         [ 85%]
tests/test_staging_and_sql.py .................                         [100%]

============================= 47 passed in 16.92s =============================
```

### Test Suite Breakdown:
* **`test_data_quality.py` (10 tests):** Validates primary-key uniqueness, foreign-key referential integrity, quarantine isolation idempotency, and raw CSV SHA-256 immutability.
* **`test_staging_and_sql.py` (7 tests):** Verifies DuckDB database connectivity, staging row reconciliation parity, dimension completeness, and fact table schema integrity.
* **`test_metrics_and_policies.py` (9 tests):** Validates absence of future window leakage in counterfactual demand, ABC Pareto sorting, and continuous bivariate SS/ROP math against known benchmark fixtures.
* **`test_analytics_and_reporting.py` (9 tests):** Asserts strict cross-report financial parity (Store Revenue == Category Revenue == Scorecard Revenue), supplier buffer decomposition ($\Delta SS \ge 0$), and service-level monotonicity.
* **`test_dashboard.py` (4 tests):** Validates Streamlit script compilation, cached DuckDB analytical queries, Gaussian simulator scaling, and alert filtering logic.
* **`test_end_to_end_integration.py` (8 tests):** Validates 365-day calendar continuity, absence of duplicate natural keys, zero-demand boundaries, deterministic lead-time equivalence ($SS_{\text{bivariate}} \equiv SS_{\text{univariate}}$ when $\sigma_L = 0$), and query determinism.

---

## ⚖️ Governance & Methodology Notice

1. **Counterfactual Demand Modeling:** Estimated lost units (**217,026 units**) and lost revenue (**\$10,074,157.71**) are modeled unconstrained demand estimates based on preceding same-weekday sales velocity over in-stock trading days. They represent commercial opportunity cost rather than audited accounting losses.
2. **Synthetic Perishables Segregation:** Per Decision `DEC-011`, perishability and shelf-life risk are evaluated strictly in an **isolated synthetic demonstration module** (`reports/synthetic_spoilage_diagnostics.csv`) and are completely segregated from core continuous replenishment, safety stock, and stockout calculations.
3. **Decisions Log Governance:** All architectural, mathematical, and data governance decisions (`DEC-001` through `DEC-019`) have been formally approved and logged in [`docs/decisions_log.md`](docs/decisions_log.md).

---

## 👨‍💻 Author & Repository

* **Author:** Gowtham Reddy ([@Gowthamreddy08](https://github.com/Gowthamreddy08))
* **Live Web App:** [https://smart-inventory-diagnostics.streamlit.app/](https://smart-inventory-diagnostics.streamlit.app/)
* **GitHub Repository:** [https://github.com/Gowthamreddy08/smart-inventory-diagnostics](https://github.com/Gowthamreddy08/smart-inventory-diagnostics)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
