# 🏛️ System Architecture & Data Engineering Design
**Smart Inventory Diagnostics: Retail Supply Chain Analytics**

This document details the end-to-end data engineering architecture, relational modeling, mathematical policy engine, and technical design governing the project.

---

## 1. High-Level Data Flow Architecture

The data pipeline enforces a strict four-layer architecture (**Raw $\rightarrow$ Quarantine $\rightarrow$ Warehouse $\rightarrow$ Analytics & Consumption**), ensuring source immutability, data quality governance, and reproducible calculations:

```mermaid
flowchart TD
    subgraph Raw_Layer["1. Immutable Raw Layer (data/raw/)"]
        R1["products.csv (150 rows)"]
        R2["stores.csv (5 rows)"]
        R3["suppliers.csv (10 rows)"]
        R4["sales_transactions.csv (206,987 rows)"]
        R5["inventory_snapshots.csv (273,750 rows)"]
        R6["supplier_orders.csv (37,521 rows)"]
    end

    subgraph Quality_Audit["2. Quality Engine & Quarantine (data/quarantine/)"]
        QA["Automated Profiling & Assertion Engine (src/data_quality.py)"]
        Q1["quarantined_inventory_snapshots.csv (8 negative SOH rows)"]
        Q2["quarantined_sales_transactions.csv (6 ghost sales rows)"]
        Q3["quarantined_supplier_orders.csv (2 inverted lead-time POs)"]
    end

    subgraph Warehouse_Layer["3. DuckDB Analytics Warehouse (data/processed/inventory_analytics.duckdb)"]
        STG["Staging Views / Tables (stg_*)"]
        DIM["Dimensional Models (dim_product, dim_store, dim_supplier, dim_date)"]
        FCT["Fact Tables (fct_daily_sales, fct_daily_inventory_snapshot, fct_purchase_orders)"]
        VIEWS["Analytical Aggregation Views (v_sku_store_annual_summary, v_supplier_lead_time_profile)"]
    end

    subgraph Metrics_Engine["4. Core Retail Metrics & Policy Marts"]
        DE["Demand Counterfactual Estimator (Rolling 4-Week Same-Weekday)"]
        LS["fct_lost_sales_daily (273,742 rows)"]
        ABC["ABC-XYZ 9-Box Classifier (Pareto Margin × Demand CV)"]
        POL["Inventory Policy Engine (Continuous SS/ROP & Periodic Order-Up-To)"]
        MART["mart_sku_store_policies (750 operational pairs)"]
    end

    subgraph Consumption_Layer["5. Consumption & Operational Interfaces"]
        REP["Business Insights & CSV Scorecards (reports/)"]
        MD["Executive Narrative Report (reports/executive_insights_report.md)"]
        DASH["Streamlit Interactive Web Dashboard (dashboard/app.py)"]
        TEST["Comprehensive Pytest Harness (47 automated tests)"]
    end

    Raw_Layer --> QA
    QA -->|Quarantined Anomalies| Quality_Audit
    QA -->|Clean Records Only| STG
    STG --> DIM
    STG --> FCT
    DIM --> VIEWS
    FCT --> VIEWS
    VIEWS --> DE --> LS
    VIEWS --> ABC
    VIEWS --> POL
    ABC --> MART
    POL --> MART
    MART --> REP
    MART --> MD
    MART --> DASH
    REP --> TEST
    MART --> TEST
```

---

## 2. Relational Star Schema Data Model

The DuckDB analytical warehouse models retail operations using an enterprise star schema optimized for fast analytical aggregations and window operations:

```mermaid
erDiagram
    dim_date ||--o{ fct_daily_sales : "transaction_date"
    dim_date ||--o{ fct_daily_inventory_snapshot : "snapshot_date"
    dim_date ||--o{ fct_purchase_orders : "order_placed_date"
    dim_date ||--o{ fct_lost_sales_daily : "snapshot_date"

    dim_product ||--o{ fct_daily_sales : "sku_id"
    dim_product ||--o{ fct_daily_inventory_snapshot : "sku_id"
    dim_product ||--o{ fct_purchase_orders : "sku_id"
    dim_product ||--o{ fct_lost_sales_daily : "sku_id"
    dim_product ||--o{ mart_sku_store_policies : "sku_id"

    dim_store ||--o{ fct_daily_sales : "store_id"
    dim_store ||--o{ fct_daily_inventory_snapshot : "store_id"
    dim_store ||--o{ fct_purchase_orders : "destination_store_id"
    dim_store ||--o{ fct_lost_sales_daily : "store_id"
    dim_store ||--o{ mart_sku_store_policies : "store_id"

    dim_supplier ||--o{ fct_purchase_orders : "supplier_id"
    dim_supplier ||--o{ dim_product : "primary_supplier_id"

    dim_date {
        date date_key PK
        int year
        int quarter
        int month
        varchar month_name
        int day
        int day_of_week
        varchar day_name
        int is_weekend
    }

    dim_product {
        varchar sku_id PK
        varchar product_name
        varchar category
        double unit_cost
        double unit_selling_price
        double contribution_margin
        double margin_percentage
        varchar primary_supplier_id FK
        int shelf_life_days
        boolean is_perishable
    }

    dim_store {
        varchar store_id PK
        varchar store_name
        varchar region
        varchar store_tier
        int is_open_flag
    }

    dim_supplier {
        varchar supplier_id PK
        varchar supplier_name
        int contracted_lead_time_days
        double on_time_sla_target
    }

    fct_daily_sales {
        date transaction_date FK
        varchar store_id FK
        varchar sku_id FK
        int units_requested
        int units_fulfilled
        int units_unfulfilled
        double gross_revenue
        double cogs
        double contribution_margin
    }

    fct_daily_inventory_snapshot {
        date snapshot_date FK
        varchar store_id FK
        varchar sku_id FK
        int stock_on_hand
        int stock_in_transit
        int inventory_position
        int is_stockout
        double inventory_value
    }

    fct_purchase_orders {
        varchar po_id PK
        varchar sku_id FK
        varchar supplier_id FK
        varchar destination_store_id FK
        date order_placed_date FK
        date order_delivered_date
        int order_quantity
        int delivered_quantity
        int actual_lead_time_days
        int contracted_lead_time_days
        int is_on_time
    }

    mart_sku_store_policies {
        varchar sku_id PK, FK
        varchar store_id PK, FK
        varchar abc_class
        varchar xyz_class
        varchar segment_9box
        double annual_gross_revenue
        double annual_contribution_margin
        double stockout_rate_pct
        int safety_stock_cont_95
        int reorder_point_95
        int order_up_to_level_95
        int recommended_reorder_qty
        varchar priority_alert
    }
```

---

## 3. Mathematical Policy Formulations

### A. Rolling 4-Week Same-Weekday Counterfactual Demand
To model true unconstrained customer demand during stockouts ($\text{SOH} \le 0$) without future data leakage, the counterfactual demand $\hat{D}_{i,s,t}$ is calculated as the average fulfilled demand during in-stock trading days on the identical day-of-week over the preceding 4 weeks:

$$\hat{D}_{i,s,t} = \frac{1}{|K|} \sum_{k \in K} \text{units\_fulfilled}_{i,s,t - 7k}$$

Where:
* $K = \{k \in \{1, 2, 3, 4\} \mid \text{is\_stockout}_{i,s,t - 7k} = 0\}$
* If $|K| = 0$ (sustained multi-week stockout), the model safely falls back to the prior in-stock trading day velocity.

$$\text{Estimated Lost Units}_{i,s,t} = \begin{cases} \max(0, \lceil \hat{D}_{i,s,t} \rceil - \text{units\_fulfilled}_{i,s,t}), & \text{if } \text{is\_stockout}_{i,s,t} = 1 \\ 0, & \text{otherwise} \end{cases}$$

$$\text{Estimated Lost Revenue}_{i,s,t} = \text{Estimated Lost Units}_{i,s,t} \times \text{unit\_selling\_price}_i$$

$$\text{Estimated Lost Margin}_{i,s,t} = \text{Estimated Lost Units}_{i,s,t} \times \text{contribution\_margin}_i$$

---

### B. Continuous-Review Bivariate Safety Stock & Reorder Point
Demand and supplier lead times are both treated as random variables. Safety stock ($SS$) accounts for both customer demand volatility ($\sigma_D^2$) and supplier lead-time variance ($\sigma_L^2$):

$$SS_{\text{cont}} = \left\lceil Z \times \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2} \right\rceil$$

$$ROP = \left\lceil (\bar{D} \times \bar{L}) + SS_{\text{cont}} \right\rceil$$

Where:
* $Z$: Gaussian standard normal inverse CDF corresponding to the target Cycle Service Level ($Z = 1.282$ for 90%, $1.645$ for 95%, $2.326$ for 99%).
* $\bar{D}$: Empirical mean daily demand over in-stock trading days.
* $\sigma_D^2$: Sample variance of daily demand over in-stock trading days.
* $\bar{L}$: Empirical mean lead time (days) for the assigned supplier.
* $\sigma_L^2$: Sample variance of supplier delivery lead time ($\text{days}^2$).

---

### C. Periodic-Review Safety Stock & Order-Up-To Level ($R = 7$ Days)
For retail environments with fixed weekly replenishment delivery windows ($R = 7$ days), inventory exposure extends over the entire lead-time plus review cycle ($\bar{L} + R$):

$$SS_{\text{periodic}} = \left\lceil Z \times \sqrt{(\bar{L} + R) \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2} \right\rceil$$

$$\text{Order-Up-To Level} = \left\lceil \bar{D} \times (\bar{L} + R) + SS_{\text{periodic}} \right\rceil$$

$$\text{Recommended Reorder Qty} = \max\left(0, \text{Order-Up-To Level} - \text{Current Inventory Position}\right)$$

Where $\text{Current Inventory Position} = \text{Stock on Hand} + \text{Stock in Transit}$.

---

### D. Supplier Variance Buffer Decomposition
The incremental safety stock units ($\Delta SS$) and working capital ($\Delta C$) necessitated strictly by vendor delivery unreliability ($\sigma_L^2 > 0$) is isolated by:

$$SS_{\text{deterministic}} = \left\lceil Z \times \sqrt{\bar{L} \cdot \sigma_D^2} \right\rceil$$

$$\Delta SS_{\text{supplier}} = SS_{\text{actual}} - SS_{\text{deterministic}}$$

$$\Delta C_{\text{supplier}} = \Delta SS_{\text{supplier}} \times \text{unit\_cost}$$

---

### E. Operational Alert Classification Boundaries

Current inventory positions are evaluated against policy boundaries:

$$\text{Priority Alert} = \begin{cases} 
\textbf{CRITICAL}, & \text{if } \text{Position} \le SS_{\text{primary}} \\ 
\textbf{HIGH}, & \text{if } SS_{\text{primary}} < \text{Position} \le ROP_{\text{primary}} \\ 
\textbf{MEDIUM}, & \text{if } ROP_{\text{primary}} < \text{Position} \le 1.10 \times ROP_{\text{primary}} \\ 
\textbf{HEALTHY}, & \text{if } \text{Position} > 1.10 \times ROP_{\text{primary}} 
\end{cases}$$

---

## 4. Technology Stack & Design Principles

* **Database Engine:** Embedded **DuckDB** for vectorized, high-performance in-process SQL execution.
* **Core Languages & Libraries:** Python 3.14, pandas, NumPy, SciPy, pytest.
* **Visualization & Presentation:** Streamlit (wide layout) with declarative Altair graphics.
* **Strict Raw Immutability:** Source CSV files in `data/raw/` are read-only and never modified in place.
* **Idempotent Pipelines:** Every pipeline stage produces deterministic, identical outputs when rerun with identical inputs.
