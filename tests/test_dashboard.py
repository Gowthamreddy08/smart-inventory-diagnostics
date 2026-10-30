"""
Tests for Phase 6: Streamlit Interactive Dashboard
Validates script compilation, data loading queries, filter logic, and simulator math.
"""

import os
import py_compile
import duckdb
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "inventory_analytics.duckdb")
APP_PATH = os.path.join(BASE_DIR, "dashboard", "app.py")


class TestDashboard:
    """Test suite validating the Phase 6 Streamlit dashboard components."""

    def test_app_script_exists_and_compiles(self):
        """Assert dashboard/app.py exists and compiles cleanly without syntax errors."""
        assert os.path.exists(APP_PATH), "dashboard/app.py not found"
        assert os.path.getsize(APP_PATH) > 0, "dashboard/app.py is empty"
        # Test python compilation
        py_compile.compile(APP_PATH, doraise=True)

    def test_dashboard_database_queries(self):
        """Verify that all DuckDB queries executed by the dashboard succeed and return expected schemas."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            # 1. Policies mart query
            policies_df = con.execute("SELECT * FROM mart_sku_store_policies;").df()
            assert len(policies_df) == 750
            assert "priority_alert" in policies_df.columns
            assert "segment_9box" in policies_df.columns

            # 2. Lost sales monthly aggregation query
            lost_sales = con.execute("""
                SELECT 
                    DATE_TRUNC('month', snapshot_date) as month,
                    store_id,
                    sku_id,
                    SUM(units_fulfilled) as units_fulfilled,
                    SUM(estimated_lost_units) as lost_units,
                    SUM(estimated_lost_revenue) as lost_revenue,
                    SUM(estimated_lost_contribution_margin) as lost_margin,
                    SUM(is_stockout_flag) as stockout_days,
                    COUNT(*) as total_days
                FROM fct_lost_sales_daily
                GROUP BY 1, 2, 3
                ORDER BY 1;
            """).df()
            assert len(lost_sales) > 0
            assert lost_sales["lost_units"].sum() == 217026

            # 3. Supplier aggregation query
            supp_df = con.execute("""
                SELECT 
                    po.supplier_id,
                    s.supplier_name,
                    COUNT(po.po_id) as total_pos,
                    SUM(po.order_quantity) as total_units_ordered,
                    ROUND(AVG(po.actual_lead_time_days), 2) as avg_actual_lead_time,
                    ROUND(AVG(po.contracted_lead_time_days), 2) as contracted_lead_time,
                    ROUND(VAR_SAMP(po.actual_lead_time_days), 3) as lead_time_variance,
                    ROUND(STDDEV_SAMP(po.actual_lead_time_days), 2) as lead_time_std_dev,
                    ROUND(100.0 * SUM(po.is_on_time) / COUNT(po.po_id), 2) as on_time_rate_pct
                FROM fct_purchase_orders po
                JOIN dim_supplier s ON po.supplier_id = s.supplier_id
                GROUP BY po.supplier_id, s.supplier_name
                ORDER BY po.supplier_id;
            """).df()
            assert len(supp_df) == 10
            assert supp_df["total_pos"].sum() == 37519

        finally:
            con.close()

    def test_simulator_gaussian_math(self):
        """Verify dynamic simulator Gaussian calculations across service levels."""
        from scipy.stats import norm
        import math

        z_90 = norm.ppf(0.90)
        z_95 = norm.ppf(0.95)
        z_99 = norm.ppf(0.99)

        assert abs(z_90 - 1.282) < 0.01
        assert abs(z_95 - 1.645) < 0.01
        assert abs(z_99 - 2.326) < 0.01

        # Test safety stock scaling
        std = 10.0
        ss_90 = math.ceil(z_90 * std)
        ss_95 = math.ceil(z_95 * std)
        ss_99 = math.ceil(z_99 * std)

        assert ss_90 < ss_95 < ss_99

    def test_procurement_action_filtering_logic(self):
        """Verify that filtering for CRITICAL and HIGH alerts extracts the expected counts."""
        con = duckdb.connect(DB_PATH, read_only=True)
        try:
            df = con.execute("SELECT priority_alert, count(*) as cnt FROM mart_sku_store_policies GROUP BY 1;").df()
            counts = dict(zip(df["priority_alert"], df["cnt"]))
            assert counts.get("CRITICAL", 0) == 40
            assert counts.get("HIGH", 0) == 255
            assert counts.get("MEDIUM", 0) == 72
            assert counts.get("HEALTHY", 0) == 383
        finally:
            con.close()
