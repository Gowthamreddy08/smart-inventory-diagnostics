"""
Smart Inventory Diagnostics - Phase 1: Data Generation & Ingestion Engine
Generates enterprise retail datasets with controlled operational dynamics
and intentional anomalies for Phase 2 data quality audit.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Set deterministic random seed
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

START_DATE = datetime(2025, 1, 1)
NUM_DAYS = 365
DATE_RANGE = [START_DATE + timedelta(days=i) for i in range(NUM_DAYS)]

NUM_SKUS = 150
NUM_STORES = 5
NUM_SUPPLIERS = 10

CATEGORIES = [
    "Beverages",
    "Dry Grocery",
    "Household Goods",
    "Personal Care",
    "Packaged Goods"
]

def generate_stores():
    print("Generating Store master data...")
    stores = [
        {"store_id": "STORE-01", "store_name": "Metro Flagship", "region": "Central", "store_tier": "Tier 1 - Flagship", "demand_multiplier": 1.4, "is_open_flag": 1},
        {"store_id": "STORE-02", "store_name": "Downtown Urban", "region": "North", "store_tier": "Tier 2 - Urban", "demand_multiplier": 1.1, "is_open_flag": 1},
        {"store_id": "STORE-03", "store_name": "Suburban Center", "region": "South", "store_tier": "Tier 3 - Suburban", "demand_multiplier": 0.9, "is_open_flag": 1},
        {"store_id": "STORE-04", "store_name": "Westside Hub", "region": "West", "store_tier": "Tier 2 - Urban", "demand_multiplier": 1.0, "is_open_flag": 1},
        {"store_id": "STORE-05", "store_name": "Eastgate Retail", "region": "East", "store_tier": "Tier 3 - Suburban", "demand_multiplier": 0.8, "is_open_flag": 1},
    ]
    df = pd.DataFrame(stores)
    return df

def generate_suppliers():
    print("Generating Supplier master data...")
    suppliers = []
    names = [
        "Apex Global Logistics", "Pinnacle Brands Inc", "BlueSky Supply Co",
        "Keystone Consumer Goods", "Vanguard Distributors", "Frontier Beverage Supply",
        "Summit Packaging Solutions", "Pacific Rim Sourcing", "Continental Foods Group",
        "National Wholesale Alliance"
    ]
    for i in range(NUM_SUPPLIERS):
        suppliers.append({
            "supplier_id": f"SUP-{i+1:02d}",
            "supplier_name": names[i],
            "contracted_lead_time_days": int(np.random.choice([3, 5, 7, 10, 14])),
            "lead_time_std_days": round(float(np.random.uniform(0.8, 2.5)), 2),
            "on_time_sla_target": 0.95
        })
    return pd.DataFrame(suppliers)

def generate_products(suppliers_df):
    print("Generating Product master data...")
    products = []
    
    # 20% A items (high volume/margin), 30% B items, 50% C items
    tier_assignment = ["A"] * 30 + ["B"] * 45 + ["C"] * 75
    random.shuffle(tier_assignment)
    
    # Volatility assignment: 40% X (low CV), 35% Y (medium CV), 25% Z (high CV / intermittent)
    volatility_assignment = ["X"] * 60 + ["Y"] * 53 + ["Z"] * 37
    random.shuffle(volatility_assignment)
    
    for i in range(1, NUM_SKUS + 1):
        sku_id = f"SKU-{i:04d}"
        category = random.choice(CATEGORIES)
        tier = tier_assignment[i - 1]
        volatility = volatility_assignment[i - 1]
        
        # Unit Cost & Price
        if tier == "A":
            unit_cost = round(float(np.random.uniform(12.0, 60.0)), 2)
            margin_pct = round(float(np.random.uniform(0.35, 0.55)), 2)
            base_daily_demand = round(float(np.random.uniform(15.0, 35.0)), 2)
        elif tier == "B":
            unit_cost = round(float(np.random.uniform(6.0, 30.0)), 2)
            margin_pct = round(float(np.random.uniform(0.25, 0.40)), 2)
            base_daily_demand = round(float(np.random.uniform(5.0, 15.0)), 2)
        else: # C
            unit_cost = round(float(np.random.uniform(2.0, 20.0)), 2)
            margin_pct = round(float(np.random.uniform(0.15, 0.35)), 2)
            base_daily_demand = round(float(np.random.uniform(0.5, 5.0)), 2)
            
        unit_price = round(unit_cost / (1.0 - margin_pct), 2)
        contribution_margin = round(unit_price - unit_cost, 2)
        
        # CV target
        if volatility == "X":
            cv_target = round(float(np.random.uniform(0.15, 0.45)), 2)
        elif volatility == "Y":
            cv_target = round(float(np.random.uniform(0.55, 0.95)), 2)
        else: # Z
            cv_target = round(float(np.random.uniform(1.05, 2.20)), 2)
            
        supplier_id = random.choice(suppliers_df["supplier_id"].tolist())
        
        # Synthetic Perishable Module Fields (clearly designated)
        is_perishable = bool(category in ["Beverages", "Packaged Goods"] and random.random() < 0.35)
        shelf_life_days = int(random.choice([14, 21, 30, 45, 60])) if is_perishable else 365
        
        products.append({
            "sku_id": sku_id,
            "product_name": f"{category[:-1]} Product {i}",
            "category": category,
            "unit_cost": unit_cost,
            "unit_selling_price": unit_price,
            "contribution_margin": contribution_margin,
            "primary_supplier_id": supplier_id,
            "shelf_life_days": shelf_life_days,
            "is_perishable": is_perishable,
            "_base_demand": base_daily_demand,
            "_cv_target": cv_target,
            "_planned_tier": tier,
            "_planned_volatility": volatility
        })
    return pd.DataFrame(products)

def simulate_daily_operations(products_df, stores_df, suppliers_df):
    print("Simulating 365 days of retail operations across 5 stores and 150 SKUs...")
    
    supplier_lookup = suppliers_df.set_index("supplier_id").to_dict(orient="index")
    
    # Tables to collect
    all_sales = []
    all_snapshots = []
    all_pos = []
    
    po_counter = 1000
    
    # Pre-calculate store-SKU parameters
    sku_dict = products_df.set_index("sku_id").to_dict(orient="index")
    
    for store in stores_df.to_dict(orient="records"):
        store_id = store["store_id"]
        store_mult = store["demand_multiplier"]
        print(f"  Simulating {store['store_name']} ({store_id})...")
        
        for sku_id, sku in sku_dict.items():
            base_mean = sku["_base_demand"] * store_mult
            cv = sku["_cv_target"]
            supplier = supplier_lookup[sku["primary_supplier_id"]]
            lead_time_mean = supplier["contracted_lead_time_days"]
            lead_time_std = supplier["lead_time_std_days"]
            
            # Initial opening stock (typically 1.5 to 2.5 weeks of demand)
            stock_on_hand = int(max(10, base_mean * (lead_time_mean + 5)))
            stock_in_transit = 0
            
            # Tracking active pipeline deliveries: list of dicts {arrival_date, qty}
            open_deliveries = []
            
            # Status Quo rule-of-thumb replenishment:
            # Order weekly or when stock drops below 7 days of demand
            review_period = 7
            last_review_day = 0
            
            for day_idx, current_date in enumerate(DATE_RANGE):
                # 1. Process Deliveries Arriving Today
                arriving_qty = sum(d["qty"] for d in open_deliveries if d["arrival_date"] == current_date)
                open_deliveries = [d for d in open_deliveries if d["arrival_date"] > current_date]
                stock_on_hand += arriving_qty
                stock_in_transit = sum(d["qty"] for d in open_deliveries)
                
                # 2. Customer Demand Generation
                # Weekend effect (Fri/Sat lift)
                weekday = current_date.weekday()
                day_factor = 1.25 if weekday in [4, 5] else (0.85 if weekday == 6 else 1.0)
                
                # Seasonal December holiday lift
                seasonal_factor = 1.30 if current_date.month == 12 else 1.0
                adjusted_mean = base_mean * day_factor * seasonal_factor
                
                # Demand distribution based on CV
                if sku["_planned_volatility"] == "Z":
                    # Intermittent / Zero-inflated Poisson or Gamma
                    if random.random() < 0.65:
                        demand = 0
                    else:
                        demand = int(np.random.gamma(shape=2.0, scale=(adjusted_mean * 2.5) / 2.0))
                else:
                    std_dev = max(1.0, adjusted_mean * cv)
                    demand = int(max(0, np.random.normal(loc=adjusted_mean, scale=std_dev)))
                
                # 3. Fulfillment & Stockout Tracking
                if stock_on_hand >= demand:
                    fulfilled = demand
                    stock_on_hand -= demand
                    is_stockout = False
                elif stock_on_hand > 0:
                    fulfilled = stock_on_hand
                    stock_on_hand = 0
                    is_stockout = True
                else:
                    fulfilled = 0
                    stock_on_hand = 0
                    is_stockout = True
                
                # Append Sales Transaction if demand was present
                if demand > 0:
                    all_sales.append({
                        "transaction_id": f"TXN-{store_id}-{sku_id}-{current_date.strftime('%Y%m%d')}",
                        "sku_id": sku_id,
                        "store_id": store_id,
                        "transaction_date": current_date.strftime("%Y-%m-%d"),
                        "units_demanded": demand,
                        "units_fulfilled": fulfilled
                    })
                
                # 4. Status Quo Replenishment Trigger (Rule of Thumb Baseline)
                # Evaluates weekly or if stock is very low (< 3 days demand)
                if (day_idx - last_review_day >= review_period) or (stock_on_hand <= base_mean * 3 and stock_in_transit == 0):
                    inventory_position = stock_on_hand + stock_in_transit
                    target_stock = int(base_mean * (lead_time_mean + review_period))
                    
                    if inventory_position < target_stock:
                        order_qty = max(10, target_stock - inventory_position)
                        # Supplier delivery lead time draw
                        actual_lt = int(max(1, round(np.random.normal(loc=lead_time_mean, scale=lead_time_std))))
                        delivery_date = current_date + timedelta(days=actual_lt)
                        
                        po_counter += 1
                        po_id = f"PO-{po_counter:06d}"
                        
                        all_pos.append({
                            "po_id": po_id,
                            "sku_id": sku_id,
                            "supplier_id": sku["primary_supplier_id"],
                            "destination_store_id": store_id,
                            "order_placed_date": current_date.strftime("%Y-%m-%d"),
                            "order_delivered_date": delivery_date.strftime("%Y-%m-%d"),
                            "order_quantity": order_qty,
                            "delivered_quantity": order_qty, # standard fulfillment
                            "actual_lead_time_days": actual_lt
                        })
                        
                        open_deliveries.append({"arrival_date": delivery_date, "qty": order_qty})
                        stock_in_transit += order_qty
                        last_review_day = day_idx
                
                # 5. Record Daily Inventory Snapshot
                all_snapshots.append({
                    "snapshot_date": current_date.strftime("%Y-%m-%d"),
                    "sku_id": sku_id,
                    "store_id": store_id,
                    "stock_on_hand": stock_on_hand,
                    "stock_in_transit": stock_in_transit,
                    "is_stockout_flag": 1 if is_stockout else 0
                })
                
    return pd.DataFrame(all_sales), pd.DataFrame(all_snapshots), pd.DataFrame(all_pos)

def inject_controlled_anomalies(sales_df, snapshots_df, pos_df, products_df):
    print("Injecting controlled anomalies for Phase 2 data quality audit...")
    anomalies_manifest = []
    
    # 1. Negative Inventory Values (e.g. scan latency / intake timing delay) - 8 instances
    print("  Injecting 8 negative inventory scan-latency records...")
    zero_stock_indices = snapshots_df[snapshots_df["stock_on_hand"] == 0].index.tolist()
    if len(zero_stock_indices) >= 8:
        neg_indices = np.random.choice(zero_stock_indices, size=8, replace=False)
    else:
        neg_indices = np.random.choice(snapshots_df.index, size=8, replace=False)

    for idx in neg_indices:
        val = int(np.random.choice([-1, -2, -3]))
        row = snapshots_df.loc[idx]
        snapshots_df.at[idx, "stock_on_hand"] = val
        snapshots_df.at[idx, "is_stockout_flag"] = 1
        anomalies_manifest.append({
            "table": "inventory_snapshots",
            "anomaly_type": "NEGATIVE_INVENTORY",
            "identifier": f"{row['sku_id']} | {row['store_id']} | {row['snapshot_date']}",
            "details": f"Stock-on-hand recorded as {val} units due to scan latency.",
            "planned_phase_2_treatment": "Investigate against intake timestamps. Quarantine if unexplainable; never silently impute."
        })
        
    # 2. Ghost Sales (Units sold when stock-on-hand is 0 and stock-in-transit is 0) - 4 instances
    print("  Injecting 4 ghost sales anomalies...")
    remaining_zero_indices = [i for i in zero_stock_indices if i not in neg_indices]
    if len(remaining_zero_indices) >= 4:
        ghost_indices = np.random.choice(remaining_zero_indices, size=4, replace=False)
    else:
        ghost_indices = np.random.choice([i for i in snapshots_df.index if i not in neg_indices], size=4, replace=False)

    for idx in ghost_indices:
        snapshots_df.at[idx, "stock_on_hand"] = 0
        snapshots_df.at[idx, "stock_in_transit"] = 0
        snapshots_df.at[idx, "is_stockout_flag"] = 1
        snap_row = snapshots_df.loc[idx]
        
        ghost_txn_id = f"TXN-GHOST-{snap_row['store_id']}-{snap_row['sku_id']}-{snap_row['snapshot_date'].replace('-', '')}"
        ghost_sale_row = pd.DataFrame([{
            "transaction_id": ghost_txn_id,
            "sku_id": snap_row["sku_id"],
            "store_id": snap_row["store_id"],
            "transaction_date": snap_row["snapshot_date"],
            "units_demanded": 3,
            "units_fulfilled": 3
        }])
        sales_df = pd.concat([sales_df, ghost_sale_row], ignore_index=True)
        anomalies_manifest.append({
            "table": "sales_transactions",
            "anomaly_type": "GHOST_SALE_ZERO_STOCK",
            "identifier": ghost_txn_id,
            "details": "3 units fulfilled despite 0 stock-on-hand and 0 stock-in-transit.",
            "planned_phase_2_treatment": "Audit against unrecorded deliveries or quarantine transaction."
        })
        
    # 3. Supplier Order Date Bounds Anomaly (Delivery date earlier than placed date / negative lead time) - 2 instances
    print("  Injecting 2 supplier order date sequence anomalies...")
    po_anom_indices = np.random.choice(pos_df.index, size=2, replace=False)
    for idx in po_anom_indices:
        po_row = pos_df.loc[idx]
        placed = datetime.strptime(po_row["order_placed_date"], "%Y-%m-%d")
        bad_delivered = placed - timedelta(days=2)
        pos_df.at[idx, "order_delivered_date"] = bad_delivered.strftime("%Y-%m-%d")
        pos_df.at[idx, "actual_lead_time_days"] = -2
        anomalies_manifest.append({
            "table": "supplier_orders",
            "anomaly_type": "INVALID_LEAD_TIME_DATE_SEQUENCE",
            "identifier": po_row["po_id"],
            "details": f"Delivery date ({bad_delivered.strftime('%Y-%m-%d')}) precedes placed date ({po_row['order_placed_date']}).",
            "planned_phase_2_treatment": "Quarantine PO from lead-time variance calculation."
        })
        
    # 4. Lead Time Outlier (Extreme vendor delay > 90 days) - 2 instances
    print("  Injecting 2 extreme supplier lead-time outliers...")
    po_outlier_indices = np.random.choice(pos_df.drop(po_anom_indices).index, size=2, replace=False)
    for idx in po_outlier_indices:
        po_row = pos_df.loc[idx]
        placed = datetime.strptime(po_row["order_placed_date"], "%Y-%m-%d")
        extreme_delivered = placed + timedelta(days=95)
        pos_df.at[idx, "order_delivered_date"] = extreme_delivered.strftime("%Y-%m-%d")
        pos_df.at[idx, "actual_lead_time_days"] = 95
        anomalies_manifest.append({
            "table": "supplier_orders",
            "anomaly_type": "LEAD_TIME_OUTLIER",
            "identifier": po_row["po_id"],
            "details": "Lead time of 95 days represents an extreme vendor supply chain shock.",
            "planned_phase_2_treatment": "Flag as vendor disruption; evaluate impact on variance calculations."
        })
        
    return sales_df, snapshots_df, pos_df, pd.DataFrame(anomalies_manifest)

def main():
    print("=" * 70)
    print("STARTING PHASE 1: DATASET GENERATION & RAW INGESTION")
    print("=" * 70)
    
    stores_df = generate_stores()
    suppliers_df = generate_suppliers()
    products_df = generate_products(suppliers_df)
    
    sales_df, snapshots_df, pos_df = simulate_daily_operations(products_df, stores_df, suppliers_df)
    
    # Inject deliberate anomalies
    sales_df, snapshots_df, pos_df, manifest_df = inject_controlled_anomalies(
        sales_df, snapshots_df, pos_df, products_df
    )
    
    # Clean internal helper columns from product master before saving
    products_clean_df = products_df.drop(columns=["_base_demand", "_cv_target", "_planned_tier", "_planned_volatility"])
    stores_clean_df = stores_df.drop(columns=["demand_multiplier"])
    suppliers_clean_df = suppliers_df.drop(columns=["lead_time_std_days"])
    
    # Save Raw Datasets
    print("\nSaving raw CSV datasets to data/raw/...")
    products_clean_df.to_csv(os.path.join(RAW_DATA_DIR, "products.csv"), index=False)
    stores_clean_df.to_csv(os.path.join(RAW_DATA_DIR, "stores.csv"), index=False)
    suppliers_clean_df.to_csv(os.path.join(RAW_DATA_DIR, "suppliers.csv"), index=False)
    sales_df.to_csv(os.path.join(RAW_DATA_DIR, "sales_transactions.csv"), index=False)
    snapshots_df.to_csv(os.path.join(RAW_DATA_DIR, "inventory_snapshots.csv"), index=False)
    pos_df.to_csv(os.path.join(RAW_DATA_DIR, "supplier_orders.csv"), index=False)
    
    # Write Ingestion & Anomaly Manifest Log
    print("Writing docs/data_ingestion_log.md...")
    log_content = f"""# 📦 Phase 1 Data Ingestion & Raw Lineage Log
**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Deterministic Seed:** {SEED}  
**Time Range:** {START_DATE.strftime('%Y-%m-%d')} to {(START_DATE + timedelta(days=NUM_DAYS-1)).strftime('%Y-%m-%d')} ({NUM_DAYS} Days)

---

## 1. Raw Datasets Created

| File Name | File Path | Row Count | Column Count | Primary Grain |
| :--- | :--- | :--- | :--- | :--- |
| `products.csv` | `data/raw/products.csv` | {len(products_clean_df):,} | {len(products_clean_df.columns)} | `sku_id` |
| `stores.csv` | `data/raw/stores.csv` | {len(stores_clean_df):,} | {len(stores_clean_df.columns)} | `store_id` |
| `suppliers.csv` | `data/raw/suppliers.csv` | {len(suppliers_clean_df):,} | {len(suppliers_clean_df.columns)} | `supplier_id` |
| `sales_transactions.csv` | `data/raw/sales_transactions.csv` | {len(sales_df):,} | {len(sales_df.columns)} | `transaction_id` (`sku_id × store_id × date`) |
| `inventory_snapshots.csv` | `data/raw/inventory_snapshots.csv` | {len(snapshots_df):,} | {len(snapshots_df.columns)} | `snapshot_date × sku_id × store_id` |
| `supplier_orders.csv` | `data/raw/supplier_orders.csv` | {len(pos_df):,} | {len(pos_df.columns)} | `po_id` (`sku_id × supplier_id × destination_store`) |

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
"""
    for _, row in manifest_df.iterrows():
        log_content += f"| `{row['table']}` | `{row['anomaly_type']}` | `{row['identifier']}` | {row['details']} | {row['planned_phase_2_treatment']} |\n"

    log_content += """
---

## 4. Phase 1 Data Lineage & Integrity Certification

* **Preservation of Raw Data:** All raw CSV files have been generated directly into `data/raw/` and represent the untouched raw layer.
* **Zero Silent Imputation:** All anomalies exist in their raw, natural state.
* **Phase 1 Completion Status:** **SUCCESSFUL**. Ready for Phase 2 Data Profiling & Audit Gate.
"""

    with open(os.path.join(DOCS_DIR, "data_ingestion_log.md"), "w", encoding="utf-8") as f:
        f.write(log_content)
        
    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETE: All 6 raw CSV files generated successfully.")
    print(f"Products: {len(products_clean_df):,} rows")
    print(f"Stores: {len(stores_clean_df):,} rows")
    print(f"Suppliers: {len(suppliers_clean_df):,} rows")
    print(f"Sales Transactions: {len(sales_df):,} rows")
    print(f"Inventory Snapshots: {len(snapshots_df):,} rows")
    print(f"Supplier Orders: {len(pos_df):,} rows")
    print(f"Controlled Anomalies Injected: {len(manifest_df)} records")
    print("=" * 70)

if __name__ == "__main__":
    main()
