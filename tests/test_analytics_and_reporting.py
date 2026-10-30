"""
Unit and Integration Tests for Phase 5: Analytics, Business Insights & Reporting
Validates financial cross-reconciliation, file generation, supplier variance decomposition,
and service level monotonicity.
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


class TestAnalyticsAndReporting:
    """Test suite validating Phase 5 analytical reports and metrics consistency."""

    REQUIRED_FILES = [
        "executive_scorecard.csv",
        "store_performance.csv",
        "category_diagnostics.csv",
        "abc_xyz_portfolio_analysis.csv",
        "supplier_performance_and_lead_time.csv",
        "service_level_tradeoffs.csv",
        "priority_action_list.csv",
        "synthetic_spoilage_diagnostics.csv",
        "data_quality_reconciliation_summary.csv",
        "executive_insights_report.md"
    ]

    def test_all_report_files_exist_and_non_empty(self):
        """Assert that all 10 Phase 5 report artifacts exist and are not empty."""
        for filename in self.REQUIRED_FILES:
            file_path = os.path.join(REPORTS_DIR, filename)
            assert os.path.exists(file_path), f"Report file missing: {filename}"
            assert os.path.getsize(file_path) > 0, f"Report file is empty: {filename}"

    def test_executive_scorecard_metrics(self):
        """Verify executive scorecard financial and operational sanity checks."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "executive_scorecard.csv"))
        assert len(df) == 1
        row = df.iloc[0]

        assert row["total_skus"] == 150
        assert row["total_stores"] == 5
        assert row["total_sku_store_pairs"] == 750
        assert row["total_gross_revenue"] > 50_000_000.0
        assert row["total_contribution_margin"] > 20_000_000.0
        assert 30.0 <= row["gross_margin_pct"] <= 55.0
        assert 4.0 <= row["network_stockout_rate_pct"] <= 12.0
        assert row["modeled_lost_revenue"] > 1_000_000.0
        assert row["modeled_lost_margin"] > 500_000.0
        assert row["network_inventory_turnover"] > 0
        assert row["network_days_inventory_on_hand"] > 0
        assert row["critical_alert_pairs"] + row["high_alert_pairs"] + row["medium_alert_pairs"] + row["healthy_pairs"] == 750

    def test_financial_reconciliation_cross_reports(self):
        """Assert strict financial cross-reconciliation between Executive, Store, and Category reports."""
        df_exec = pd.read_csv(os.path.join(REPORTS_DIR, "executive_scorecard.csv")).iloc[0]
        df_store = pd.read_csv(os.path.join(REPORTS_DIR, "store_performance.csv"))
        df_cat = pd.read_csv(os.path.join(REPORTS_DIR, "category_diagnostics.csv"))

        # Gross Revenue Reconciliations
        store_rev_total = round(df_store["annual_gross_revenue"].sum(), 2)
        cat_rev_total = round(df_cat["annual_gross_revenue"].sum(), 2)
        exec_rev = round(df_exec["total_gross_revenue"], 2)

        assert abs(store_rev_total - exec_rev) <= 0.05, f"Store revenue {store_rev_total} != Exec {exec_rev}"
        assert abs(cat_rev_total - exec_rev) <= 0.05, f"Category revenue {cat_rev_total} != Exec {exec_rev}"

        # Contribution Margin Reconciliations
        store_margin_total = round(df_store["annual_contribution_margin"].sum(), 2)
        cat_margin_total = round(df_cat["annual_contribution_margin"].sum(), 2)
        exec_margin = round(df_exec["total_contribution_margin"], 2)

        assert abs(store_margin_total - exec_margin) <= 0.05
        assert abs(cat_margin_total - exec_margin) <= 0.05

        # Modeled Lost Revenue Reconciliations
        store_lost_rev = round(df_store["modeled_lost_revenue"].sum(), 2)
        cat_lost_rev = round(df_cat["modeled_lost_revenue"].sum(), 2)
        exec_lost_rev = round(df_exec["modeled_lost_revenue"], 2)

        assert abs(store_lost_rev - exec_lost_rev) <= 0.05
        assert abs(cat_lost_rev - exec_lost_rev) <= 0.05

    def test_abc_xyz_portfolio_coverage(self):
        """Verify ABC-XYZ segmentation covers all 750 pairs with valid margins and playbook recommendations."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "abc_xyz_portfolio_analysis.csv"))
        assert df["pair_count"].sum() == 750
        assert abs(df["pair_share_pct"].sum() - 100.0) <= 0.1
        assert abs(df["margin_share_pct"].sum() - 100.0) <= 0.1

        # Check playbook strategies are non-empty
        for _, row in df.iterrows():
            assert isinstance(row["playbook_strategy"], str) and len(row["playbook_strategy"]) > 5

    def test_supplier_variance_decomposition(self):
        """Verify that lead time variance strictly increases or maintains safety stock across all suppliers."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "supplier_performance_and_lead_time.csv"))
        assert len(df) == 10

        for _, row in df.iterrows():
            # Actual SS with lead time variance must be >= deterministic SS without variance
            assert row["total_ss_actual"] >= row["total_ss_deterministic"]
            assert row["supplier_buffer_units"] >= 0
            assert row["supplier_buffer_capital"] >= 0.0
            assert 0.0 <= row["supplier_variance_ss_share_pct"] <= 100.0
            assert row["reliability_tier"] in [
                "Tier 1 - High Reliability",
                "Tier 2 - Moderate Risk",
                "Tier 3 - High Volatility / Escalation"
            ]

    def test_priority_action_list_filtering(self):
        """Verify the priority action list contains only CRITICAL and HIGH items with positive reorder quantities."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "priority_action_list.csv"))
        assert len(df) > 0
        assert set(df["priority_alert"].unique()).issubset({"CRITICAL", "HIGH"})

        # Every action item must have positive reorder requirements
        assert (df["recommended_reorder_qty"] > 0).all()
        assert (df["order_capital_required"] > 0).all()
        assert (df["priority_rank"].isin([1, 2])).all()

    def test_service_level_monotonicity(self):
        """Verify strict monotonicity of safety stock requirements across 90%, 95%, and 99% CSL."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "service_level_tradeoffs.csv"))

        for _, row in df.iterrows():
            # Units must strictly increase with higher service levels
            assert row["ss_units_90"] < row["ss_units_95"] < row["ss_units_99"]
            assert row["ss_capital_90"] < row["ss_capital_95"] < row["ss_capital_99"]
            assert row["holding_cost_90"] < row["holding_cost_95"] < row["holding_cost_99"]
            assert row["delta_units_95_vs_90"] > 0
            assert row["delta_units_99_vs_95"] > 0

    def test_data_quality_reconciliation_zero_variance(self):
        """Verify audit report shows 0 variance across all database entities."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "data_quality_reconciliation_summary.csv"))
        assert len(df) == 6
        assert (df["reconciliation_variance"] == 0).all()
        assert (df["raw_ingested_rows"] == df["quarantined_rows"] + df["warehouse_clean_rows"]).all()

    def test_synthetic_spoilage_isolation(self):
        """Verify that the synthetic spoilage report strictly contains perishable items."""
        df = pd.read_csv(os.path.join(REPORTS_DIR, "synthetic_spoilage_diagnostics.csv"))
        assert len(df) > 0
        assert (df["is_perishable"] == True).all()
        assert (df["shelf_life_days"] > 0).all()
        assert df["synthetic_spoilage_risk_category"].isin([
            "LOW_RISK", "MODERATE_SPOILAGE_RISK", "HIGH_SPOILAGE_RISK"
        ]).all()
