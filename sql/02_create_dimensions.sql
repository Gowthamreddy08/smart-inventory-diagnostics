-- ============================================================================
-- Smart Inventory Diagnostics - Phase 3: Dimensional Modeling (DuckDB SQL)
-- Builds dimensional entities: dim_product, dim_store, dim_supplier, dim_date
-- ============================================================================

-- 1. Product Dimension
CREATE OR REPLACE TABLE dim_product AS
SELECT
    sku_id,
    product_name,
    category,
    unit_cost,
    unit_selling_price,
    contribution_margin,
    ROUND((contribution_margin / unit_selling_price) * 100, 2) AS margin_percentage,
    CASE
        WHEN unit_selling_price < 10.0 THEN 'Budget (< $10)'
        WHEN unit_selling_price BETWEEN 10.0 AND 30.0 THEN 'Mid-Range ($10-$30)'
        ELSE 'Premium (> $30)'
    END AS price_tier,
    primary_supplier_id,
    shelf_life_days,
    is_perishable
FROM stg_products;

-- 2. Store Dimension
CREATE OR REPLACE TABLE dim_store AS
SELECT
    store_id,
    store_name,
    region,
    store_tier,
    is_open_flag
FROM stg_stores;

-- 3. Supplier Dimension
CREATE OR REPLACE TABLE dim_supplier AS
SELECT
    supplier_id,
    supplier_name,
    contracted_lead_time_days,
    on_time_sla_target
FROM stg_suppliers;

-- 4. Calendar Date Dimension
-- Generates full 365 calendar days for the 2025 operating year
CREATE OR REPLACE TABLE dim_date AS
SELECT
    d::DATE AS date_key,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(QUARTER FROM d)::INTEGER AS quarter,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    STRFTIME(d, '%B') AS month_name,
    STRFTIME(d, '%b') AS month_short_name,
    EXTRACT(DAY FROM d)::INTEGER AS day,
    EXTRACT(DOW FROM d)::INTEGER AS day_of_week, -- 0=Sunday, 6=Saturday in DuckDB
    STRFTIME(d, '%A') AS day_name,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
    CASE WHEN d = LAST_DAY(d) THEN 1 ELSE 0 END AS is_month_end
FROM generate_series(DATE '2025-01-01', DATE '2025-12-31', INTERVAL 1 DAY) AS t(d);
