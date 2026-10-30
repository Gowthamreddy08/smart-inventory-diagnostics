"""
Smart Inventory Diagnostics - Phase 4: Metrics & Policies Orchestrator
Executes lost sales counterfactual estimation, ABC-XYZ segmentation,
and multi-scenario inventory policy calibration.
"""

import os
import sys
import duckdb
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.demand_estimator import LostSalesEstimator
from src.abc_xyz_segmentation import ABCXYZClassifier
from src.inventory_policy import InventoryPolicyEngine

DB_PATH = os.path.join(BASE_DIR, "data", "processed", "inventory_analytics.duckdb")


def run_phase_4_pipeline(db_path: str = DB_PATH):
    print("=" * 75)
    print("STARTING PHASE 4: CORE RETAIL & INVENTORY METRICS ENGINE")
    print("=" * 75)
    print(f"Target DuckDB Warehouse: {db_path}")

    # 1. Lost Sales Counterfactual Estimation
    print("\n[Step 1/3] Computing counterfactual lost-sales demand (Rolling 4-Week Same-Weekday)...")
    estimator = LostSalesEstimator(db_path)
    lost_sales_df = estimator.compute_lost_sales()
    estimator.save_to_duckdb(lost_sales_df)
    
    total_lost_units = lost_sales_df["estimated_lost_units"].sum()
    total_lost_rev = lost_sales_df["estimated_lost_revenue"].sum()
    total_lost_margin = lost_sales_df["estimated_lost_contribution_margin"].sum()
    stockout_instances = lost_sales_df["is_stockout_flag"].sum()
    
    print(f"  --> Saved fct_lost_sales_daily: {len(lost_sales_df):,} daily snapshot rows.")
    print(f"      • Total Stockout Days Identified: {stockout_instances:,}")
    print(f"      • Total Estimated Lost Units: {total_lost_units:,} units")
    print(f"      • Total Estimated Lost Revenue: ${total_lost_rev:,.2f} (modeled counterfactual)")
    print(f"      • Total Estimated Lost Margin: ${total_lost_margin:,.2f}")

    # 2. ABC-XYZ Portfolio Segmentation
    print("\n[Step 2/3] Performing ABC (Contribution Margin) & XYZ (Demand CV) Segmentation...")
    classifier = ABCXYZClassifier(db_path)
    segmented_df, diag = classifier.calculate_segmentation()
    classifier.save_to_duckdb(segmented_df)
    
    print(f"  --> Segmented {len(segmented_df):,} SKU-Store operational pairs.")
    print("      • ABC Distribution (Contribution Margin Pareto):")
    for k, v in diag["abc_distribution"].items():
        print(f"        - Class {k}: {v:>3} pairs ({v/len(segmented_df)*100:.1f}%)")
    print("      • XYZ Distribution (Demand Volatility):")
    for k, v in diag["xyz_distribution"].items():
        print(f"        - Class {k}: {v:>3} pairs ({v/len(segmented_df)*100:.1f}%)")
    print("      • Empirical CV Distribution Percentiles:")
    for k, v in diag["empirical_cv_percentiles"].items():
        print(f"        - {k:<12}: {v:.4f}")

    # 3. Dynamic Inventory Policies & Alerts
    print("\n[Step 3/3] Calibrating Dynamic Continuous ROP & Periodic Order-Up-To Policies...")
    policy_engine = InventoryPolicyEngine(db_path)
    policies_df = policy_engine.calculate_policies(review_period_days=7)
    policy_engine.save_to_duckdb(policies_df)
    
    print(f"  --> Saved mart_sku_store_policies: {len(policies_df):,} SKU-Store policy rows.")
    
    # Priority Alert breakdown
    alert_counts = policies_df["priority_alert"].value_counts().to_dict()
    print("      • Current Operational Priority Alerts (at 95% CSL):")
    for k in ["CRITICAL", "HIGH", "MEDIUM", "HEALTHY"]:
        cnt = alert_counts.get(k, 0)
        print(f"        - {k:<10}: {cnt:>3} pairs ({cnt/len(policies_df)*100:.1f}%)")
        
    total_excess_units = policies_df["excess_inventory_units"].sum()
    total_excess_val = policies_df["excess_inventory_value"].sum()
    slow_moving_count = policies_df["is_slow_moving_flag"].sum()
    print(f"      • Primary Excess Inventory: {total_excess_units:,} units (${total_excess_val:,.2f})")
    print(f"      • Secondary Slow-Moving Flag (>60 Days DOH): {slow_moving_count} pairs")

    # Multi-Service Level Safety Stock Comparison
    print("\n" + "-" * 75)
    print("MULTI-SERVICE LEVEL SAFETY STOCK SCENARIO COMPARISON (System-wide)")
    print("-" * 75)
    ss_90 = policies_df["safety_stock_cont_90"].sum()
    ss_95 = policies_df["safety_stock_cont_95"].sum()
    ss_99 = policies_df["safety_stock_cont_99"].sum()
    print(f"  • 90% CSL (Z=1.282) Required Safety Stock: {ss_90:>8,} units")
    print(f"  • 95% CSL (Z=1.645) Required Safety Stock: {ss_95:>8,} units (+{((ss_95-ss_90)/ss_90)*100:.1f}% vs 90%)")
    print(f"  • 99% CSL (Z=2.326) Required Safety Stock: {ss_99:>8,} units (+{((ss_99-ss_95)/ss_95)*100:.1f}% vs 95%)")
    print("=" * 75)
    print("PHASE 4 METRICS CALCULATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    run_phase_4_pipeline()
