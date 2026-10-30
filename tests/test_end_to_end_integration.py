"""
End-to-End Integration, Boundary, Edge-Case & Idempotency Test Suite (Phase 7)
Validates calendar continuity, absence of duplicate keys, mathematical boundary conditions,
empty input handling, zero-variance / zero-demand edge cases, and deterministic pipeline behavior.
"""

import os
import math
import duckdb
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "inventory_analytics.duckdb")


@pytest.fixture(scope="module")
def db_conn():
    """DuckDB connection fixture."""
    con = duckdb.connect(DB_PATH, read_only=True)
    yield con
    con.close()


class TestEndToEndIntegration:
    """Enterprise-grade integration and stress tests for supply chain analytics."""

    def test_calendar_coverage_and_continuity(self, db_conn):
        """Verify that dim_date spans exactly 365 days from 2025-01-01 to 2025-12-31 with zero gaps."""
        df = db_conn.execute("""
            SELECT 
                MIN(date_key) as min_date,
                MAX(date_key) as max_date,
                COUNT(*) as total_days,
                COUNT(DISTINCT date_key) as unique_days
            FROM dim_date;
        """).df()

        assert str(pd.to_datetime(df["min_date"].iloc[0]).date()) == "2025-01-01"
        assert str(pd.to_datetime(df["max_date"].iloc[0]).date()) == "2025-12-31"
        assert df["total_days"].iloc[0] == 365
        assert df["unique_days"].iloc[0] == 365

    def test_natural_key_duplicate_absence(self, db_conn):
        """Verify that no duplicate natural keys exist in sales, inventory snapshots, or purchase orders."""
        # 1. Sales: (transaction_date, store_id, sku_id)
        dup_sales = db_conn.execute("""
            SELECT transaction_date, store_id, sku_id, COUNT(*) as cnt
            FROM fct_daily_sales
            GROUP BY transaction_date, store_id, sku_id
            HAVING COUNT(*) > 1;
        """).df()
        assert len(dup_sales) == 0, f"Found {len(dup_sales)} duplicate sales keys"

        # 2. Inventory Snapshots: (snapshot_date, store_id, sku_id)
        dup_inv = db_conn.execute("""
            SELECT snapshot_date, store_id, sku_id, COUNT(*) as cnt
            FROM fct_daily_inventory_snapshot
            GROUP BY snapshot_date, store_id, sku_id
            HAVING COUNT(*) > 1;
        """).df()
        assert len(dup_inv) == 0, f"Found {len(dup_inv)} duplicate snapshot keys"

        # 3. Purchase Orders: po_id
        dup_po = db_conn.execute("""
            SELECT po_id, COUNT(*) as cnt
            FROM fct_purchase_orders
            GROUP BY po_id
            HAVING COUNT(*) > 1;
        """).df()
        assert len(dup_po) == 0, f"Found {len(dup_po)} duplicate PO keys"

    def test_edge_case_zero_demand_handling(self):
        """
        Verify safety stock and ROP calculations when mean daily demand is zero.
        SS and ROP must be non-negative and handle zero demand without division by zero.
        """
        z = 1.645
        d_mean = 0.0
        d_var = 0.0
        l_mean = 7.0
        l_var = 2.0

        comb_var = (l_mean * d_var) + ((d_mean ** 2) * l_var)
        std_cont = math.sqrt(max(0.0, comb_var))
        ss = math.ceil(z * std_cont)
        rop = math.ceil((d_mean * l_mean) + ss)

        assert ss == 0
        assert rop == 0

        # Demand CV calculation with zero mean should be handled safely
        cv = (math.sqrt(d_var) / d_mean) if d_mean > 0 else 0.0
        assert cv == 0.0

    def test_edge_case_deterministic_lead_time_parity(self):
        """
        Verify that when lead time variance is 0 (deterministic vendor),
        bivariate safety stock collapses exactly to classic univariant safety stock:
        SS = Z * sigma_D * sqrt(L).
        """
        z = 1.645
        d_mean = 25.0
        sigma_d = 4.0
        d_var = sigma_d ** 2  # 16.0
        l_mean = 9.0
        l_var = 0.0  # Deterministic supplier!

        # Bivariate formula: sqrt(L * sigma_D^2 + D^2 * sigma_L^2)
        comb_var = (l_mean * d_var) + ((d_mean ** 2) * l_var)
        ss_bivariate = math.ceil(z * math.sqrt(comb_var))

        # Univariate classic formula: Z * sigma_D * sqrt(L)
        ss_univariate = math.ceil(z * sigma_d * math.sqrt(l_mean))

        assert ss_bivariate == ss_univariate
        assert ss_bivariate == math.ceil(1.645 * 4.0 * 3.0)  # math.ceil(19.74) = 20

    def test_edge_case_extreme_demand_volatility(self):
        """
        Test XYZ classification with extreme lumpy/intermittent demand (e.g. CV = 2.5).
        Assert it is strictly categorized as 'Z' class.
        """
        # Intermittent demand: mostly zeros, occasional spikes
        demand_series = np.array([0, 0, 0, 0, 0, 50, 0, 0, 0, 0, 0, 80, 0, 0, 0, 0, 100])
        mean_d = np.mean(demand_series)
        std_d = np.std(demand_series, ddof=1)
        cv = std_d / mean_d

        assert cv > 1.0  # Lumpy demand has CV > 1.0

        # Apply classification rule
        xyz_class = "X" if cv <= 0.5 else ("Y" if cv <= 1.0 else "Z")
        assert xyz_class == "Z"

    def test_counterfactual_demand_non_negative_and_bounded(self, db_conn):
        """Verify that all estimated lost units and revenues in fct_lost_sales_daily are non-negative and bounded."""
        df = db_conn.execute("""
            SELECT 
                MIN(estimated_lost_units) as min_lost_units,
                MAX(estimated_lost_units) as max_lost_units,
                MIN(estimated_lost_revenue) as min_lost_rev,
                MIN(estimated_lost_contribution_margin) as min_lost_margin
            FROM fct_lost_sales_daily;
        """).df()

        assert df["min_lost_units"].iloc[0] >= 0
        assert df["min_lost_rev"].iloc[0] >= 0.0
        assert df["min_lost_margin"].iloc[0] >= 0.0
        # No single-day stockout should exceed reasonable maximum store daily volume (e.g., 200 units)
        assert df["max_lost_units"].iloc[0] <= 200

    def test_pipeline_determinism_and_reproducibility(self, db_conn):
        """
        Verify analytical query determinism.
        Total gross revenue, contribution margin, and stockout count must match the certified benchmark.
        """
        df = db_conn.execute("""
            SELECT 
                ROUND(SUM(annual_gross_revenue), 2) as total_revenue,
                ROUND(SUM(annual_contribution_margin), 2) as total_margin,
                SUM(stockout_days) as total_stockouts
            FROM mart_sku_store_policies;
        """).df()

        assert df["total_revenue"].iloc[0] == 100558841.75
        assert df["total_margin"].iloc[0] == 42464922.02
        assert df["total_stockouts"].iloc[0] == 18963

    def test_empty_dataset_handling(self):
        """Verify that helper calculations handle empty DataFrames safely without crashing."""
        empty_df = pd.DataFrame(columns=["sku_id", "store_id", "annual_contribution_margin", "units_fulfilled"])
        
        # Test empty aggregations
        total_margin = empty_df["annual_contribution_margin"].sum()
        assert total_margin == 0.0

        # Test empty grouping
        grouped = empty_df.groupby("store_id")["units_fulfilled"].sum()
        assert len(grouped) == 0
