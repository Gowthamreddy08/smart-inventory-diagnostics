-- ============================================================================
-- Smart Inventory Diagnostics - Phase 3: Fact Table Modeling (DuckDB SQL)
-- Builds factual analytical entities: fct_daily_sales, fct_daily_inventory_snapshot, fct_purchase_orders
-- ============================================================================

-- 1. Daily Sales Fact
-- Grain: One row per customer transaction
CREATE OR REPLACE TABLE fct_daily_sales AS
SELECT
    s.transaction_id,
    s.sku_id,
    s.store_id,
    s.transaction_date,
    s.units_demanded,
    s.units_fulfilled,
    (s.units_demanded - s.units_fulfilled) AS unfulfilled_units,
    ROUND(s.units_fulfilled * p.unit_selling_price, 2) AS gross_revenue,
    ROUND(s.units_fulfilled * p.unit_cost, 2) AS cogs,
    ROUND(s.units_fulfilled * p.contribution_margin, 2) AS gross_contribution_margin,
    CASE WHEN s.units_fulfilled = s.units_demanded THEN 1 ELSE 0 END AS is_fully_fulfilled
FROM stg_sales_transactions s
INNER JOIN dim_product p ON s.sku_id = p.sku_id;

-- 2. Daily Inventory Snapshot Fact
-- Grain: One row per snapshot_date × sku_id × store_id
CREATE OR REPLACE TABLE fct_daily_inventory_snapshot AS
SELECT
    i.snapshot_date,
    i.sku_id,
    i.store_id,
    i.stock_on_hand,
    i.stock_in_transit,
    (i.stock_on_hand + i.stock_in_transit) AS inventory_position,
    ROUND(i.stock_on_hand * p.unit_cost, 2) AS inventory_value,
    i.is_stockout_flag
FROM stg_inventory_snapshots i
INNER JOIN dim_product p ON i.sku_id = p.sku_id;

-- 3. Supplier Purchase Orders Fact
-- Grain: One row per purchase order
CREATE OR REPLACE TABLE fct_purchase_orders AS
SELECT
    o.po_id,
    o.sku_id,
    o.supplier_id,
    o.destination_store_id,
    o.order_placed_date,
    o.order_delivered_date,
    o.order_quantity,
    o.delivered_quantity,
    o.actual_lead_time_days,
    sup.contracted_lead_time_days,
    (o.actual_lead_time_days - sup.contracted_lead_time_days) AS lead_time_variance_days,
    CASE WHEN o.actual_lead_time_days <= sup.contracted_lead_time_days THEN 1 ELSE 0 END AS is_on_time,
    o.is_lead_time_outlier
FROM stg_supplier_orders o
INNER JOIN dim_supplier sup ON o.supplier_id = sup.supplier_id;
