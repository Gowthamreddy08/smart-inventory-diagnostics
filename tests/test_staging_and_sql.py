"""
Smart Inventory Diagnostics - Phase 3 Test Suite
Validates DuckDB staging tables, dimensional models, facts, and analytical SQL views.
"""

import os
import sys
import duckdb
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.build_database import build_analytics_database, DB_PATH


@pytest.fixture(scope="module")
def duckdb_conn():
    """Builds and yields a shared connection to the DuckDB analytics database."""
    con = build_analytics_database(DB_PATH)
    yield con
    con.close()


class TestStagingAndSQL:
    """Test suite for Phase 3 DuckDB staging and dimensional warehouse layer."""

    def test_database_exists_and_connects(self, duckdb_conn):
        """Verify the DuckDB database exists and accepts queries."""
        assert os.path.exists(DB_PATH)
        assert os.path.getsize(DB_PATH) > 0
        res = duckdb_conn.execute("SELECT 1").fetchone()
        assert res[0] == 1

    def test_staging_row_counts_and_reconciliation(self, duckdb_conn):
        """Assert exact row counts matching Phase 2 reconciliation bridge."""
        rec_df = duckdb_conn.execute("SELECT * FROM v_pipeline_reconciliation").df()
        
        expected = {
            "products": (150, 0, 150, 150),
            "stores": (5, 0, 5, 5),
            "suppliers": (10, 0, 10, 10),
            "sales_transactions": (206987, 6, 206981, 206981),
            "inventory_snapshots": (273750, 8, 273742, 273742),
            "supplier_orders": (37521, 2, 37519, 37519),
        }

        for _, row in rec_df.iterrows():
            entity = row["entity_name"]
            assert entity in expected
            exp_raw, exp_q, exp_stg, exp_mod = expected[entity]
            assert row["raw_row_count"] == exp_raw
            assert row["quarantined_row_count"] == exp_q
            assert row["staging_row_count"] == exp_stg
            assert row["modeled_row_count"] == exp_mod

    def test_dimensions_completeness(self, duckdb_conn):
        """Assert dimensional tables have expected completeness and keys."""
        # dim_product
        prod_cnt = duckdb_conn.execute("SELECT COUNT(DISTINCT sku_id) FROM dim_product").fetchone()[0]
        assert prod_cnt == 150
        bad_cost = duckdb_conn.execute("SELECT COUNT(*) FROM dim_product WHERE unit_cost <= 0 OR unit_selling_price < unit_cost").fetchone()[0]
        assert bad_cost == 0

        # dim_store
        store_cnt = duckdb_conn.execute("SELECT COUNT(DISTINCT store_id) FROM dim_store").fetchone()[0]
        assert store_cnt == 5

        # dim_supplier
        sup_cnt = duckdb_conn.execute("SELECT COUNT(DISTINCT supplier_id) FROM dim_supplier").fetchone()[0]
        assert sup_cnt == 10

        # dim_date
        date_cnt = duckdb_conn.execute("SELECT COUNT(DISTINCT date_key) FROM dim_date").fetchone()[0]
        assert date_cnt == 365
        date_min_max = duckdb_conn.execute("SELECT MIN(date_key), MAX(date_key) FROM dim_date").fetchone()
        assert str(date_min_max[0]) == "2025-01-01"
        assert str(date_min_max[1]) == "2025-12-31"

    def test_fact_sales_integrity(self, duckdb_conn):
        """Assert fct_daily_sales has no ghost sales and valid revenues."""
        sales_cnt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_daily_sales").fetchone()[0]
        assert sales_cnt == 206981

        # Assert no ghost sales remained in fact table
        ghost_cnt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_daily_sales WHERE transaction_id LIKE '%GHOST%'").fetchone()[0]
        assert ghost_cnt == 0

        # Check positive revenue for fulfilled transactions and non-negative overall
        min_rev_all = duckdb_conn.execute("SELECT MIN(gross_revenue), MIN(cogs), MIN(gross_contribution_margin) FROM fct_daily_sales").fetchone()
        assert min_rev_all[0] >= 0.0
        assert min_rev_all[1] >= 0.0
        assert min_rev_all[2] >= 0.0

        rev_stats_fulfilled = duckdb_conn.execute("""
            SELECT MIN(gross_revenue), MIN(cogs), MIN(gross_contribution_margin)
            FROM fct_daily_sales
            WHERE units_fulfilled > 0
        """).fetchone()
        assert rev_stats_fulfilled[0] > 0.0
        assert rev_stats_fulfilled[1] > 0.0
        assert rev_stats_fulfilled[2] > 0.0

    def test_fact_inventory_snapshot_integrity(self, duckdb_conn):
        """Assert fct_daily_inventory_snapshot has zero negative inventory and valid calculations."""
        snap_cnt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_daily_inventory_snapshot").fetchone()[0]
        assert snap_cnt == 273742

        # Assert zero negative inventory values
        neg_cnt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_daily_inventory_snapshot WHERE stock_on_hand < 0").fetchone()[0]
        assert neg_cnt == 0

        # Assert inventory position math holds: position == SOH + SIT
        math_err = duckdb_conn.execute("""
            SELECT COUNT(*) FROM fct_daily_inventory_snapshot
            WHERE inventory_position != (stock_on_hand + stock_in_transit)
        """).fetchone()[0]
        assert math_err == 0

    def test_fact_purchase_orders_integrity(self, duckdb_conn):
        """Assert fct_purchase_orders has zero negative lead times and flags outliers."""
        po_cnt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_purchase_orders").fetchone()[0]
        assert po_cnt == 37519

        # Assert zero negative lead times
        neg_lt = duckdb_conn.execute("SELECT COUNT(*) FROM fct_purchase_orders WHERE actual_lead_time_days < 0").fetchone()[0]
        assert neg_lt == 0

        # Assert exactly 2 outlier warnings flagged
        outliers = duckdb_conn.execute("SELECT COUNT(*) FROM fct_purchase_orders WHERE is_lead_time_outlier = 1").fetchone()[0]
        assert outliers == 2

    def test_analytical_views_execution(self, duckdb_conn):
        """Assert all analytical views execute cleanly and return valid aggregations."""
        # 1. v_daily_demand_velocity
        vel_sample = duckdb_conn.execute("SELECT COUNT(*) FROM v_daily_demand_velocity").fetchone()[0]
        assert vel_sample == 273750 # full 150 SKUs x 5 Stores x 365 Days grid

        # 2. v_supplier_lead_time_profile
        sup_prof = duckdb_conn.execute("SELECT COUNT(*) FROM v_supplier_lead_time_profile").fetchone()[0]
        assert sup_prof == 150 # 150 SKUs evaluated against suppliers

        # 3. v_sku_store_annual_summary
        annual_sum = duckdb_conn.execute("SELECT COUNT(*) FROM v_sku_store_annual_summary").fetchone()[0]
        assert annual_sum == 750 # exactly 150 SKUs x 5 Stores

        # Verify annual holding cost is strictly 22% of avg inventory value
        holding_check = duckdb_conn.execute("""
            SELECT COUNT(*) FROM v_sku_store_annual_summary
            WHERE ABS(annual_holding_cost - ROUND(avg_inventory_value * 0.22, 2)) > 0.05
        """).fetchone()[0]
        assert holding_check == 0
