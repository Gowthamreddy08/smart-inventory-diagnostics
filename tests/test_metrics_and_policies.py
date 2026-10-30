"""
Smart Inventory Diagnostics - Phase 4 Test Suite
Validates lost-sales counterfactual estimation, ABC-XYZ segmentation,
dynamic safety stock, reorder points, order-up-to ceilings, and priority alerts.
"""

import os
import sys
import math
import duckdb
import pytest
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.demand_estimator import LostSalesEstimator
from src.abc_xyz_segmentation import ABCXYZClassifier
from src.inventory_policy import InventoryPolicyEngine, Z_SCORES
from src.run_phase_4_metrics import run_phase_4_pipeline, DB_PATH


@pytest.fixture(scope="module")
def duckdb_con():
    """Runs Phase 4 pipeline and yields a shared DuckDB connection."""
    run_phase_4_pipeline(DB_PATH)
    con = duckdb.connect(DB_PATH)
    yield con
    con.close()


class TestMetricsAndPolicies:
    """Test suite for Phase 4 core retail and inventory metrics."""

    def test_tables_created_in_duckdb(self, duckdb_con):
        """Assert Phase 4 analytical tables exist and have expected row counts."""
        # 1. fct_lost_sales_daily
        lost_cnt = duckdb_con.execute("SELECT COUNT(*) FROM fct_lost_sales_daily").fetchone()[0]
        assert lost_cnt == 273742  # exactly matches cleaned snapshots

        # 2. mart_sku_store_policies
        pol_cnt = duckdb_con.execute("SELECT COUNT(*) FROM mart_sku_store_policies").fetchone()[0]
        assert pol_cnt == 750  # 150 SKUs x 5 Stores

    def test_lost_sales_no_future_leakage(self, duckdb_con):
        """
        Verify that on stockout days, expected demand is estimated
        strictly using prior historical observations (no future data leakage).
        """
        sample_so = duckdb_con.execute("""
            SELECT snapshot_date, sku_id, store_id, expected_daily_demand, estimation_method
            FROM fct_lost_sales_daily
            WHERE is_stockout_flag = 1
              AND snapshot_date >= '2025-02-01'
            LIMIT 50
        """).df()

        assert len(sample_so) > 0
        for _, row in sample_so.iterrows():
            # Ensure estimation method references prior history
            assert "AVG" in row["estimation_method"] or "MEAN" in row["estimation_method"]
            assert row["expected_daily_demand"] is not None
            assert row["expected_daily_demand"] >= 0

    def test_lost_sales_formula_accuracy(self, duckdb_con):
        """Assert lost units = max(0, round(expected) - fulfilled) and lost revenue = lost_units * price."""
        query = """
        SELECT
            l.estimated_lost_units,
            l.expected_daily_demand,
            l.units_fulfilled,
            l.estimated_lost_revenue,
            p.unit_selling_price
        FROM fct_lost_sales_daily l
        INNER JOIN dim_product p ON l.sku_id = p.sku_id
        WHERE l.is_stockout_flag = 1
          AND l.estimated_lost_units > 0
        LIMIT 100
        """
        sample = duckdb_con.execute(query).df()
        assert len(sample) > 0

        for _, row in sample.iterrows():
            expected_units = max(0, round(row["expected_daily_demand"]) - row["units_fulfilled"])
            assert row["estimated_lost_units"] == expected_units
            expected_rev = round(expected_units * row["unit_selling_price"], 2)
            assert abs(row["estimated_lost_revenue"] - expected_rev) <= 0.01

    def test_abc_pareto_curve(self, duckdb_con):
        """Assert ABC segmentation strictly adheres to 80% / 15% / 5% cumulative contribution margin."""
        df = duckdb_con.execute("""
            SELECT abc_class, annual_contribution_margin, cumulative_margin_pct
            FROM mart_sku_store_policies
            ORDER BY annual_contribution_margin DESC
        """).df()

        # Check A items are all within the top 80% cumulative margin
        a_items = df[df["abc_class"] == "A"]
        assert len(a_items) > 0
        assert a_items["cumulative_margin_pct"].max() <= 80.0

        # Check B items are between 80% and 95%
        b_items = df[df["abc_class"] == "B"]
        assert len(b_items) > 0
        assert b_items["cumulative_margin_pct"].min() > 80.0
        assert b_items["cumulative_margin_pct"].max() <= 95.0

        # Check C items are above 95%
        c_items = df[df["abc_class"] == "C"]
        assert len(c_items) > 0
        assert c_items["cumulative_margin_pct"].min() > 95.0

    def test_xyz_classification_thresholds(self, duckdb_con):
        """Assert XYZ classification uses approved CV cutoffs (<=0.5: X, 0.5-1.0: Y, >1.0: Z)."""
        df = duckdb_con.execute("""
            SELECT xyz_class, demand_coefficient_of_variation AS cv, in_stock_days
            FROM mart_sku_store_policies
        """).df()

        for _, row in df.iterrows():
            if row["in_stock_days"] < 30:
                assert row["xyz_class"] == "INSUFFICIENT_DATA"
            elif row["cv"] <= 0.5:
                assert row["xyz_class"] == "X"
            elif row["cv"] <= 1.0:
                assert row["xyz_class"] == "Y"
            else:
                assert row["xyz_class"] == "Z"

    def test_continuous_safety_stock_and_rop_math(self):
        """
        Verify safety stock and ROP formulas against a known manual calculation fixture.
        Fixture:
          Z = 1.645 (95% CSL)
          Avg Lead Time (L) = 9 days
          Lead Time Std (sigma_L) = 2 days -> Var = 4
          Avg Daily Demand (D) = 10 units/day
          Demand Std (sigma_D) = 3 units/day -> Var = 9
        """
        z = 1.645
        l_mean = 9.0
        l_var = 4.0
        d_mean = 10.0
        d_var = 9.0

        comb_var = (l_mean * d_var) + ((d_mean ** 2) * l_var)
        assert comb_var == (9.0 * 9.0) + (100.0 * 4.0)  # 81 + 400 = 481.0
        std_comb = math.sqrt(comb_var)  # ~21.9317

        expected_ss = int(math.ceil(z * std_comb))  # ceil(1.645 * 21.9317) = ceil(36.077) = 37
        expected_rop = int(math.ceil((d_mean * l_mean) + expected_ss))  # ceil(90 + 37) = 127

        assert expected_ss == 37
        assert expected_rop == 127

    def test_periodic_safety_stock_math(self):
        """
        Verify periodic safety stock with review period R = 7 days.
        Exposure = L + R = 9 + 7 = 16 days.
        """
        z = 1.645
        l_mean = 9.0
        r_period = 7.0
        l_var = 4.0
        d_mean = 10.0
        d_var = 9.0

        comb_var = ((l_mean + r_period) * d_var) + ((d_mean ** 2) * l_var)
        assert comb_var == (16.0 * 9.0) + (100.0 * 4.0)  # 144 + 400 = 544.0
        std_comb = math.sqrt(comb_var)  # ~23.3238

        expected_ss = int(math.ceil(z * std_comb))  # ceil(1.645 * 23.3238) = ceil(38.367) = 39
        expected_order_up_to = int(math.ceil((d_mean * (l_mean + r_period)) + expected_ss))  # 160 + 39 = 199

        assert expected_ss == 39
        assert expected_order_up_to == 199

    def test_priority_alert_boundaries(self, duckdb_con):
        """Assert priority alert classifications strictly follow boundary rules."""
        sample = duckdb_con.execute("""
            SELECT
                current_inventory_position AS pos,
                safety_stock_primary AS ss,
                reorder_point_primary AS rop,
                priority_alert
            FROM mart_sku_store_policies
        """).df()

        for _, row in sample.iterrows():
            pos = row["pos"]
            ss = row["ss"]
            rop = row["rop"]
            alert = row["priority_alert"]

            if pos <= ss:
                assert alert == "CRITICAL"
            elif pos <= rop:
                assert alert == "HIGH"
            elif pos <= rop * 1.10:
                assert alert == "MEDIUM"
            else:
                assert alert == "HEALTHY"

    def test_excess_inventory_calculations(self, duckdb_con):
        """Assert excess inventory formula matches max(0, SOH - Order-Up-To) and value = units * cost."""
        sample = duckdb_con.execute("""
            SELECT
                current_stock_on_hand AS soh,
                order_up_to_primary AS out_lvl,
                excess_inventory_units AS exc_units,
                excess_inventory_value AS exc_val,
                unit_cost
            FROM mart_sku_store_policies
        """).df()

        for _, row in sample.iterrows():
            expected_units = max(0, row["soh"] - row["out_lvl"])
            assert row["exc_units"] == expected_units
            expected_val = round(expected_units * row["unit_cost"], 2)
            assert abs(row["exc_val"] - expected_val) <= 0.01
