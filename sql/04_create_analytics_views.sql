-- ============================================================================
-- Smart Inventory Diagnostics - Phase 3: Analytical SQL Views (DuckDB SQL)
-- Provides foundational analytics: demand velocity, supplier lead-time profiling,
-- and SKU-store annualized performance metrics.
-- ============================================================================

-- 1. Daily Demand Velocity View
-- Computes rolling demand averages across 7-day, 14-day, and 30-day windows per SKU-Store
CREATE OR REPLACE VIEW v_daily_demand_velocity AS
WITH daily_sku_store_demand AS (
    SELECT
        d.date_key AS calendar_date,
        p.sku_id,
        st.store_id,
        COALESCE(s.units_demanded, 0) AS units_demanded,
        COALESCE(s.units_fulfilled, 0) AS units_fulfilled,
        COALESCE(i.stock_on_hand, 0) AS stock_on_hand,
        COALESCE(i.is_stockout_flag, 0) AS is_stockout_flag
    FROM dim_date d
    CROSS JOIN dim_product p
    CROSS JOIN dim_store st
    LEFT JOIN fct_daily_sales s
        ON d.date_key = s.transaction_date
       AND p.sku_id = s.sku_id
       AND st.store_id = s.store_id
    LEFT JOIN fct_daily_inventory_snapshot i
        ON d.date_key = i.snapshot_date
       AND p.sku_id = i.sku_id
       AND st.store_id = i.store_id
)
SELECT
    calendar_date,
    sku_id,
    store_id,
    units_demanded,
    units_fulfilled,
    stock_on_hand,
    is_stockout_flag,
    ROUND(AVG(units_fulfilled) OVER (
        PARTITION BY sku_id, store_id
        ORDER BY calendar_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_avg_demand_7d,
    ROUND(AVG(units_fulfilled) OVER (
        PARTITION BY sku_id, store_id
        ORDER BY calendar_date
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_avg_demand_14d,
    ROUND(AVG(units_fulfilled) OVER (
        PARTITION BY sku_id, store_id
        ORDER BY calendar_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_avg_demand_30d
FROM daily_sku_store_demand;

-- 2. Supplier Lead-Time Performance Profile View
-- Aggregates delivery performance, average lead time (L), lead time variance (σL²), and SLA compliance
CREATE OR REPLACE VIEW v_supplier_lead_time_profile AS
SELECT
    o.supplier_id,
    sup.supplier_name,
    o.sku_id,
    p.product_name,
    p.category,
    COUNT(o.po_id) AS total_orders_placed,
    SUM(o.order_quantity) AS total_units_ordered,
    SUM(o.delivered_quantity) AS total_units_delivered,
    sup.contracted_lead_time_days,
    ROUND(AVG(o.actual_lead_time_days), 2) AS avg_lead_time_days,
    ROUND(VAR_SAMP(o.actual_lead_time_days), 4) AS lead_time_variance,
    ROUND(STDDEV_SAMP(o.actual_lead_time_days), 4) AS lead_time_std_dev,
    ROUND(MIN(o.actual_lead_time_days), 2) AS min_lead_time_days,
    ROUND(MAX(o.actual_lead_time_days), 2) AS max_lead_time_days,
    ROUND(AVG(o.is_on_time) * 100, 2) AS on_time_delivery_rate_pct,
    sup.on_time_sla_target * 100 AS on_time_sla_target_pct,
    SUM(o.is_lead_time_outlier) AS lead_time_outlier_count
FROM fct_purchase_orders o
INNER JOIN dim_supplier sup ON o.supplier_id = sup.supplier_id
INNER JOIN dim_product p ON o.sku_id = p.sku_id
GROUP BY
    o.supplier_id,
    sup.supplier_name,
    o.sku_id,
    p.product_name,
    p.category,
    sup.contracted_lead_time_days,
    sup.on_time_sla_target;

-- 3. SKU-Store Annual Performance Summary View
-- Computes annual volume, financial contribution, in-stock statistics, and demand variance over in-stock days
CREATE OR REPLACE VIEW v_sku_store_annual_summary AS
WITH in_stock_sales_stats AS (
    SELECT
        s.sku_id,
        s.store_id,
        COUNT(s.transaction_id) AS total_transactions,
        SUM(s.units_demanded) AS annual_units_demanded,
        SUM(s.units_fulfilled) AS annual_units_fulfilled,
        SUM(s.gross_revenue) AS annual_gross_revenue,
        SUM(s.cogs) AS annual_cogs,
        SUM(s.gross_contribution_margin) AS annual_contribution_margin,
        ROUND(AVG(s.units_fulfilled), 4) AS mean_in_stock_daily_demand,
        ROUND(VAR_SAMP(s.units_fulfilled), 4) AS demand_variance_in_stock,
        ROUND(STDDEV_SAMP(s.units_fulfilled), 4) AS demand_std_dev_in_stock
    FROM fct_daily_sales s
    GROUP BY s.sku_id, s.store_id
),
inventory_snapshot_stats AS (
    SELECT
        i.sku_id,
        i.store_id,
        COUNT(i.snapshot_date) AS total_snapshot_days,
        SUM(CASE WHEN i.is_stockout_flag = 0 THEN 1 ELSE 0 END) AS in_stock_days,
        SUM(i.is_stockout_flag) AS stockout_days,
        ROUND(AVG(i.stock_on_hand), 2) AS avg_stock_on_hand,
        ROUND(AVG(i.inventory_value), 2) AS avg_inventory_value,
        -- Ending stock on latest snapshot date
        ARG_MAX(i.stock_on_hand, i.snapshot_date) AS current_stock_on_hand,
        ARG_MAX(i.inventory_value, i.snapshot_date) AS current_inventory_value,
        ARG_MAX(i.inventory_position, i.snapshot_date) AS current_inventory_position
    FROM fct_daily_inventory_snapshot i
    GROUP BY i.sku_id, i.store_id
)
SELECT
    p.sku_id,
    p.product_name,
    p.category,
    st.store_id,
    st.store_name,
    st.region,
    p.unit_cost,
    p.unit_selling_price,
    p.contribution_margin,
    p.margin_percentage,
    p.primary_supplier_id,
    -- Inventory Snapshot Performance
    inv.total_snapshot_days,
    inv.in_stock_days,
    inv.stockout_days,
    ROUND((inv.stockout_days::DOUBLE / inv.total_snapshot_days::DOUBLE) * 100, 2) AS stockout_rate_pct,
    inv.avg_stock_on_hand,
    inv.avg_inventory_value,
    inv.current_stock_on_hand,
    inv.current_inventory_value,
    inv.current_inventory_position,
    -- Holding Cost (22% annual rate)
    ROUND(inv.avg_inventory_value * 0.22, 2) AS annual_holding_cost,
    -- Sales & Demand Statistics
    COALESCE(s.annual_units_demanded, 0) AS annual_units_demanded,
    COALESCE(s.annual_units_fulfilled, 0) AS annual_units_fulfilled,
    COALESCE(s.annual_gross_revenue, 0.0) AS annual_gross_revenue,
    COALESCE(s.annual_cogs, 0.0) AS annual_cogs,
    COALESCE(s.annual_contribution_margin, 0.0) AS annual_contribution_margin,
    COALESCE(s.mean_in_stock_daily_demand, 0.0) AS mean_daily_demand,
    COALESCE(s.demand_variance_in_stock, 0.0) AS demand_variance,
    COALESCE(s.demand_std_dev_in_stock, 0.0) AS demand_std_dev,
    -- Coefficient of Variation (CV = σ / μ)
    CASE
        WHEN COALESCE(s.mean_in_stock_daily_demand, 0.0) > 0 THEN
            ROUND(s.demand_std_dev_in_stock / s.mean_in_stock_daily_demand, 4)
        ELSE 0.0
    END AS demand_coefficient_of_variation,
    -- Operational Unit-Based Days of Inventory on Hand (Current SOH / Daily Demand)
    CASE
        WHEN COALESCE(s.mean_in_stock_daily_demand, 0.0) > 0 THEN
            ROUND(inv.current_stock_on_hand / s.mean_in_stock_daily_demand, 2)
        ELSE 0.0
    END AS doh_units,
    -- Financial Value-Based Days of Inventory on Hand (Current Value / Daily COGS)
    CASE
        WHEN COALESCE(s.annual_cogs, 0.0) > 0 THEN
            ROUND(inv.current_inventory_value / (s.annual_cogs / 365.0), 2)
        ELSE 0.0
    END AS doh_value,
    -- Inventory Turnover Ratio (Annual COGS / Avg Inventory Value)
    CASE
        WHEN inv.avg_inventory_value > 0 THEN
            ROUND(s.annual_cogs / inv.avg_inventory_value, 2)
        ELSE 0.0
    END AS inventory_turnover_ratio
FROM dim_product p
CROSS JOIN dim_store st
LEFT JOIN inventory_snapshot_stats inv ON p.sku_id = inv.sku_id AND st.store_id = inv.store_id
LEFT JOIN in_stock_sales_stats s ON p.sku_id = s.sku_id AND st.store_id = s.store_id;

-- 4. Pipeline Row-Count Reconciliation View
-- Validates row reconciliation across raw, quarantine, and staging layers
CREATE OR REPLACE VIEW v_pipeline_reconciliation AS
SELECT
    'products' AS entity_name,
    150 AS raw_row_count,
    0 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_products) AS staging_row_count,
    (SELECT COUNT(*) FROM dim_product) AS modeled_row_count
UNION ALL
SELECT
    'stores' AS entity_name,
    5 AS raw_row_count,
    0 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_stores) AS staging_row_count,
    (SELECT COUNT(*) FROM dim_store) AS modeled_row_count
UNION ALL
SELECT
    'suppliers' AS entity_name,
    10 AS raw_row_count,
    0 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_suppliers) AS staging_row_count,
    (SELECT COUNT(*) FROM dim_supplier) AS modeled_row_count
UNION ALL
SELECT
    'sales_transactions' AS entity_name,
    206987 AS raw_row_count,
    6 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_sales_transactions) AS staging_row_count,
    (SELECT COUNT(*) FROM fct_daily_sales) AS modeled_row_count
UNION ALL
SELECT
    'inventory_snapshots' AS entity_name,
    273750 AS raw_row_count,
    8 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_inventory_snapshots) AS staging_row_count,
    (SELECT COUNT(*) FROM fct_daily_inventory_snapshot) AS modeled_row_count
UNION ALL
SELECT
    'supplier_orders' AS entity_name,
    37521 AS raw_row_count,
    2 AS quarantined_row_count,
    (SELECT COUNT(*) FROM stg_supplier_orders) AS staging_row_count,
    (SELECT COUNT(*) FROM fct_purchase_orders) AS modeled_row_count;
