-- ============================================================================
-- Smart Inventory Diagnostics - Phase 3: Staging Layer (DuckDB SQL)
-- Ingests raw CSVs, applies strict data typing, parses dates,
-- and filters out quarantined records identified in Phase 2.
-- ============================================================================

-- 1. Staging Products (Master Data)
CREATE OR REPLACE TABLE stg_products AS
SELECT
    TRIM(sku_id) AS sku_id,
    TRIM(product_name) AS product_name,
    TRIM(category) AS category,
    CAST(unit_cost AS DOUBLE) AS unit_cost,
    CAST(unit_selling_price AS DOUBLE) AS unit_selling_price,
    CAST(contribution_margin AS DOUBLE) AS contribution_margin,
    TRIM(primary_supplier_id) AS primary_supplier_id,
    CAST(shelf_life_days AS INTEGER) AS shelf_life_days,
    CAST(is_perishable AS BOOLEAN) AS is_perishable
FROM read_csv_auto('data/raw/products.csv', header=True);

-- 2. Staging Stores (Master Data)
CREATE OR REPLACE TABLE stg_stores AS
SELECT
    TRIM(store_id) AS store_id,
    TRIM(store_name) AS store_name,
    TRIM(region) AS region,
    TRIM(store_tier) AS store_tier,
    CAST(is_open_flag AS INTEGER) AS is_open_flag
FROM read_csv_auto('data/raw/stores.csv', header=True);

-- 3. Staging Suppliers (Master Data)
CREATE OR REPLACE TABLE stg_suppliers AS
SELECT
    TRIM(supplier_id) AS supplier_id,
    TRIM(supplier_name) AS supplier_name,
    CAST(contracted_lead_time_days AS INTEGER) AS contracted_lead_time_days,
    CAST(on_time_sla_target AS DOUBLE) AS on_time_sla_target
FROM read_csv_auto('data/raw/suppliers.csv', header=True);

-- 4. Staging Sales Transactions
-- Excludes quarantined ghost sales records identified in Phase 2
CREATE OR REPLACE TABLE stg_sales_transactions AS
SELECT
    TRIM(s.transaction_id) AS transaction_id,
    TRIM(s.sku_id) AS sku_id,
    TRIM(s.store_id) AS store_id,
    CAST(s.transaction_date AS DATE) AS transaction_date,
    CAST(s.units_demanded AS INTEGER) AS units_demanded,
    CAST(s.units_fulfilled AS INTEGER) AS units_fulfilled
FROM read_csv_auto('data/raw/sales_transactions.csv', header=True) s
WHERE TRIM(s.transaction_id) NOT IN (
    SELECT TRIM(transaction_id)
    FROM read_csv_auto('data/quarantine/quarantined_sales_transactions.csv', header=True)
);

-- 5. Staging Inventory Snapshots
-- Excludes quarantined negative inventory records identified in Phase 2
CREATE OR REPLACE TABLE stg_inventory_snapshots AS
SELECT
    CAST(i.snapshot_date AS DATE) AS snapshot_date,
    TRIM(i.sku_id) AS sku_id,
    TRIM(i.store_id) AS store_id,
    CAST(i.stock_on_hand AS INTEGER) AS stock_on_hand,
    CAST(i.stock_in_transit AS INTEGER) AS stock_in_transit,
    CAST(i.is_stockout_flag AS INTEGER) AS is_stockout_flag
FROM read_csv_auto('data/raw/inventory_snapshots.csv', header=True) i
WHERE NOT EXISTS (
    SELECT 1
    FROM read_csv_auto('data/quarantine/quarantined_inventory_snapshots.csv', header=True) q
    WHERE CAST(i.snapshot_date AS DATE) = CAST(q.snapshot_date AS DATE)
      AND TRIM(i.sku_id) = TRIM(q.sku_id)
      AND TRIM(i.store_id) = TRIM(q.store_id)
);

-- 6. Staging Supplier Orders (Purchase Orders)
-- Excludes quarantined invalid date sequence POs and flags extreme lead time outliers
CREATE OR REPLACE TABLE stg_supplier_orders AS
SELECT
    TRIM(p.po_id) AS po_id,
    TRIM(p.sku_id) AS sku_id,
    TRIM(p.supplier_id) AS supplier_id,
    TRIM(p.destination_store_id) AS destination_store_id,
    CAST(p.order_placed_date AS DATE) AS order_placed_date,
    CAST(p.order_delivered_date AS DATE) AS order_delivered_date,
    CAST(p.order_quantity AS INTEGER) AS order_quantity,
    CAST(p.delivered_quantity AS INTEGER) AS delivered_quantity,
    CAST(p.actual_lead_time_days AS INTEGER) AS actual_lead_time_days,
    CASE WHEN CAST(p.actual_lead_time_days AS INTEGER) > 60 THEN 1 ELSE 0 END AS is_lead_time_outlier
FROM read_csv_auto('data/raw/supplier_orders.csv', header=True) p
WHERE TRIM(p.po_id) NOT IN (
    SELECT TRIM(po_id)
    FROM read_csv_auto('data/quarantine/quarantined_supplier_orders.csv', header=True)
);
