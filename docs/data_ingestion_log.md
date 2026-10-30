# 📦 Phase 1 Data Ingestion & Raw Lineage Log
**Generated At:** 2026-10-28 21:30:13  
**Deterministic Seed:** 42  
**Time Range:** 2025-01-01 to 2025-12-31 (365 Days)

---

## 1. Raw Datasets Created

| File Name | File Path | Row Count | Column Count | Primary Grain |
| :--- | :--- | :--- | :--- | :--- |
| `products.csv` | `data/raw/products.csv` | 150 | 9 | `sku_id` |
| `stores.csv` | `data/raw/stores.csv` | 5 | 5 | `store_id` |
| `suppliers.csv` | `data/raw/suppliers.csv` | 10 | 4 | `supplier_id` |
| `sales_transactions.csv` | `data/raw/sales_transactions.csv` | 206,987 | 6 | `transaction_id` (`sku_id × store_id × date`) |
| `inventory_snapshots.csv` | `data/raw/inventory_snapshots.csv` | 273,750 | 6 | `snapshot_date × sku_id × store_id` |
| `supplier_orders.csv` | `data/raw/supplier_orders.csv` | 37,521 | 9 | `po_id` (`sku_id × supplier_id × destination_store`) |

---

## 2. Dataset Schemas & Column Types

### `products.csv`
```text
sku_id: object (string, PK)
product_name: object (string)
category: object (string)
unit_cost: float64
unit_selling_price: float64
contribution_margin: float64
primary_supplier_id: object (string, FK)
shelf_life_days: int64 (Synthetic Module)
is_perishable: bool (Synthetic Module)
```

### `stores.csv`
```text
store_id: object (string, PK)
store_name: object (string)
region: object (string)
store_tier: object (string)
is_open_flag: int64 (boolean flag)
```

### `suppliers.csv`
```text
supplier_id: object (string, PK)
supplier_name: object (string)
contracted_lead_time_days: int64
on_time_sla_target: float64
```

### `sales_transactions.csv`
```text
transaction_id: object (string, PK)
sku_id: object (string, FK)
store_id: object (string, FK)
transaction_date: object (YYYY-MM-DD)
units_demanded: int64
units_fulfilled: int64
```

### `inventory_snapshots.csv`
```text
snapshot_date: object (YYYY-MM-DD, PK part)
sku_id: object (string, PK part, FK)
store_id: object (string, PK part, FK)
stock_on_hand: int64
stock_in_transit: int64
is_stockout_flag: int64 (boolean flag)
```

### `supplier_orders.csv`
```text
po_id: object (string, PK)
sku_id: object (string, FK)
supplier_id: object (string, FK)
destination_store_id: object (string, FK)
order_placed_date: object (YYYY-MM-DD)
order_delivered_date: object (YYYY-MM-DD)
order_quantity: int64
delivered_quantity: int64
actual_lead_time_days: int64
```

---

## 3. Deliberate Injected Anomalies Manifest (For Phase 2 Audit)

The following controlled anomalies were intentionally injected into the raw source data according to DEC-012 to test Phase 2 automated auditing and quarantine protocols. **No raw rows were silently cleaned or deleted.**

| Table | Anomaly Type | Record Identifier | Description / Root Cause | Planned Phase 2 Governance Treatment |
| :--- | :--- | :--- | :--- | :--- |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0020 | STORE-02 | 2025-06-09` | Stock-on-hand recorded as -2 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0116 | STORE-03 | 2025-04-13` | Stock-on-hand recorded as -1 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0005 | STORE-04 | 2025-01-10` | Stock-on-hand recorded as -1 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0128 | STORE-01 | 2025-01-29` | Stock-on-hand recorded as -2 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0071 | STORE-01 | 2025-10-12` | Stock-on-hand recorded as -2 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0125 | STORE-04 | 2025-08-23` | Stock-on-hand recorded as -1 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0016 | STORE-03 | 2025-10-12` | Stock-on-hand recorded as -2 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `inventory_snapshots` | `NEGATIVE_INVENTORY` | `SKU-0136 | STORE-01 | 2025-07-04` | Stock-on-hand recorded as -1 units due to scan latency. | Investigate against intake timestamps. Quarantine if unexplainable; never silently impute. |
| `sales_transactions` | `GHOST_SALE_ZERO_STOCK` | `TXN-GHOST-STORE-01-SKU-0109-20251003` | 3 units fulfilled despite 0 stock-on-hand and 0 stock-in-transit. | Audit against unrecorded deliveries or quarantine transaction. |
| `sales_transactions` | `GHOST_SALE_ZERO_STOCK` | `TXN-GHOST-STORE-02-SKU-0122-20250901` | 3 units fulfilled despite 0 stock-on-hand and 0 stock-in-transit. | Audit against unrecorded deliveries or quarantine transaction. |
| `sales_transactions` | `GHOST_SALE_ZERO_STOCK` | `TXN-GHOST-STORE-02-SKU-0111-20251230` | 3 units fulfilled despite 0 stock-on-hand and 0 stock-in-transit. | Audit against unrecorded deliveries or quarantine transaction. |
| `sales_transactions` | `GHOST_SALE_ZERO_STOCK` | `TXN-GHOST-STORE-01-SKU-0094-20251209` | 3 units fulfilled despite 0 stock-on-hand and 0 stock-in-transit. | Audit against unrecorded deliveries or quarantine transaction. |
| `supplier_orders` | `INVALID_LEAD_TIME_DATE_SEQUENCE` | `PO-002978` | Delivery date (2025-12-22) precedes placed date (2025-12-24). | Quarantine PO from lead-time variance calculation. |
| `supplier_orders` | `INVALID_LEAD_TIME_DATE_SEQUENCE` | `PO-005985` | Delivery date (2025-05-28) precedes placed date (2025-05-30). | Quarantine PO from lead-time variance calculation. |
| `supplier_orders` | `LEAD_TIME_OUTLIER` | `PO-009319` | Lead time of 95 days represents an extreme vendor supply chain shock. | Flag as vendor disruption; evaluate impact on variance calculations. |
| `supplier_orders` | `LEAD_TIME_OUTLIER` | `PO-021323` | Lead time of 95 days represents an extreme vendor supply chain shock. | Flag as vendor disruption; evaluate impact on variance calculations. |

---

## 4. Phase 1 Data Lineage & Integrity Certification

* **Preservation of Raw Data:** All raw CSV files have been generated directly into `data/raw/` and represent the untouched raw layer.
* **Zero Silent Imputation:** All anomalies exist in their raw, natural state.
* **Phase 1 Completion Status:** **SUCCESSFUL**. Ready for Phase 2 Data Profiling & Audit Gate.
