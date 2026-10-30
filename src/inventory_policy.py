"""
Smart Inventory Diagnostics - Phase 4: Inventory Policy Engine
Calculates dynamic continuous (ROP) and periodic (Order-Up-To) replenishment parameters,
excess inventory, holding costs, and procurement priority alert tiers.
"""

import os
import sys
import math
import duckdb
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "inventory_analytics.duckdb")

# Standard Gaussian Z-scores for Cycle Service Levels
Z_SCORES = {
    0.90: 1.282,
    0.95: 1.645,
    0.99: 2.326
}


class InventoryPolicyEngine:
    """
    Computes mathematically rigorous safety stock, reorder points, order-up-to ceilings,
    excess stock exposure, and daily procurement alerts.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)

    def calculate_policies(self, review_period_days: int = 7) -> pd.DataFrame:
        """
        Calculates inventory policies across 90%, 95%, and 99% Cycle Service Levels.
        Uses 95% CSL as the operational baseline for priority alerts and ceilings.
        """
        con = duckdb.connect(self.db_path)
        try:
            # Query segmented items along with supplier lead-time parameters
            query = """
            SELECT
                s.*,
                COALESCE(sup.avg_lead_time_days, 7.0) AS avg_lead_time_days,
                COALESCE(sup.lead_time_variance, 2.0) AS lead_time_variance,
                COALESCE(sup.lead_time_std_dev, 1.41) AS lead_time_std_dev,
                COALESCE(sup.on_time_delivery_rate_pct, 95.0) AS on_time_delivery_rate_pct
            FROM stg_segmented_portfolio s
            LEFT JOIN v_supplier_lead_time_profile sup
                ON s.sku_id = sup.sku_id
               AND s.primary_supplier_id = sup.supplier_id
            """
            df = con.execute(query).df()
        finally:
            con.close()

        records = []

        for _, row in df.iterrows():
            d_mean = max(0.01, float(row["mean_daily_demand"]))
            d_var = max(0.01, float(row["demand_variance"]))
            l_mean = max(1.0, float(row["avg_lead_time_days"]))
            l_var = max(0.01, float(row["lead_time_variance"]))
            r_period = float(review_period_days)
            
            soh = int(row["current_stock_on_hand"])
            pos = int(row["current_inventory_position"])
            sit = pos - soh
            cost = float(row["unit_cost"])
            doh_units = float(row["doh_units"])

            # 1. Bivariate Combined Variance Terms
            # Continuous: L * sigma_D^2 + D^2 * sigma_L^2
            comb_var_cont = (l_mean * d_var) + ((d_mean ** 2) * l_var)
            std_cont = math.sqrt(max(0.01, comb_var_cont))

            # Periodic: (L + R) * sigma_D^2 + D^2 * sigma_L^2
            comb_var_periodic = ((l_mean + r_period) * d_var) + ((d_mean ** 2) * l_var)
            std_periodic = math.sqrt(max(0.01, comb_var_periodic))

            # Lead time demand baseline: D * L
            ltd_baseline = d_mean * l_mean
            exposure_baseline = d_mean * (l_mean + r_period)

            # 2. Multi-Service Level Parameter Calculation
            policy_row = dict(row)
            policy_row["review_period_days"] = review_period_days

            for csl, z in Z_SCORES.items():
                pct_label = int(csl * 100)
                # Continuous SS & ROP
                ss_cont = int(math.ceil(z * std_cont))
                rop = int(math.ceil(ltd_baseline + ss_cont))

                # Periodic SS & Order-Up-To
                ss_periodic = int(math.ceil(z * std_periodic))
                order_up_to = int(math.ceil(exposure_baseline + ss_periodic))

                policy_row[f"safety_stock_cont_{pct_label}"] = ss_cont
                policy_row[f"reorder_point_{pct_label}"] = rop
                policy_row[f"safety_stock_periodic_{pct_label}"] = ss_periodic
                policy_row[f"order_up_to_level_{pct_label}"] = order_up_to

            # Primary operational policies (at 95% CSL)
            ss_primary = policy_row["safety_stock_cont_95"]
            rop_primary = policy_row["reorder_point_95"]
            out_primary = policy_row["order_up_to_level_95"]

            policy_row["safety_stock_primary"] = ss_primary
            policy_row["reorder_point_primary"] = rop_primary
            policy_row["order_up_to_primary"] = out_primary

            # 3. Recommended Reorder Quantity (Periodic Review)
            # max(0, Order-Up-To Level - (Stock on Hand + Stock in Transit))
            recom_order_qty = max(0, out_primary - pos)
            policy_row["recommended_reorder_qty"] = recom_order_qty

            # 4. Excess Inventory (Primary Definition)
            # max(0, Stock on Hand - Order-Up-To Level)
            excess_units = max(0, soh - out_primary)
            excess_value = round(excess_units * cost, 2)
            policy_row["excess_inventory_units"] = excess_units
            policy_row["excess_inventory_value"] = excess_value

            # 5. Secondary Slow-Moving Flag
            # DOH_units > 60 days
            policy_row["is_slow_moving_flag"] = 1 if doh_units > 60.0 else 0

            # 6. Priority Alert Level
            # Critical: Position <= SS; High: SS < Position <= ROP; Medium: ROP < Position <= 1.10*ROP; Healthy: > 1.10*ROP
            if pos <= ss_primary:
                priority = "CRITICAL"
                priority_rank = 1
            elif pos <= rop_primary:
                priority = "HIGH"
                priority_rank = 2
            elif pos <= rop_primary * 1.10:
                priority = "MEDIUM"
                priority_rank = 3
            else:
                priority = "HEALTHY"
                priority_rank = 4

            policy_row["priority_alert"] = priority
            policy_row["priority_rank"] = priority_rank

            records.append(policy_row)

        return pd.DataFrame(records)

    def save_to_duckdb(self, policies_df: pd.DataFrame) -> None:
        """Saves the comprehensive policies mart to DuckDB."""
        con = duckdb.connect(self.db_path)
        try:
            con.register("df_policies_temp", policies_df)
            con.execute("""
            CREATE OR REPLACE TABLE mart_sku_store_policies AS
            SELECT * FROM df_policies_temp;
            """)
            con.unregister("df_policies_temp")
        finally:
            con.close()
