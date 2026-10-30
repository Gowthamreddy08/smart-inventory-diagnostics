"""
Smart Inventory Diagnostics - Phase 4: ABC-XYZ Segmentation Engine
Classifies products using Contribution Margin Pareto (ABC) and Demand Volatility CV (XYZ).
"""

import os
import sys
from typing import Dict, Any, Tuple
import duckdb
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "inventory_analytics.duckdb")

# Strategic Action Guidance Dictionary
ACTION_PLAYBOOK = {
    "AX": "High Margin, Stable Demand (Cash Cow): Implement automated continuous replenishment with tight safety stock. High inventory turnover target.",
    "AY": "High Margin, Moderate Volatility: Maintain dynamic safety stock buffer; establish automated weekly review with supplier.",
    "AZ": "High Margin, Erratic Demand: Centralize safety buffer pooling; collaborate closely with procurement; evaluate make-to-order or vendor consignment.",
    "BX": "Medium Margin, Stable Demand: Standard continuous ROP replenishment; automate PO generation.",
    "BY": "Medium Margin, Moderate Volatility: Periodic weekly review (Order-Up-To); monitor seasonal shifts.",
    "BZ": "Medium Margin, Erratic Demand: Buffer against demand surges with safety stock; optimize purchase order batch sizes.",
    "CX": "Low Margin, Stable Demand: Vendor-Managed Inventory (VMI) or bulk reorders with large pack sizes to minimize ordering costs.",
    "CY": "Low Margin, Moderate Volatility: Periodic review with high review period; minimize management attention.",
    "CZ": "Low Margin, Erratic Demand (Tail Risk): Audit for strategic necessity (e.g. required accessory). If non-essential, liquidate or transition to drop-ship."
}


class ABCXYZClassifier:
    """
    Executes empirical ABC Pareto segmentation on Contribution Margin
    and XYZ demand volatility classification on Coefficient of Variation.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)

    def calculate_segmentation(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Calculates ABC and XYZ segments at the primary SKU-Store planning grain.
        Returns the classified DataFrame and empirical distribution diagnostics.
        """
        con = duckdb.connect(self.db_path)
        try:
            query = """
            SELECT
                sku_id,
                product_name,
                category,
                store_id,
                store_name,
                region,
                unit_cost,
                unit_selling_price,
                contribution_margin,
                margin_percentage,
                primary_supplier_id,
                annual_units_fulfilled,
                annual_gross_revenue,
                annual_cogs,
                annual_contribution_margin,
                total_snapshot_days,
                in_stock_days,
                stockout_days,
                stockout_rate_pct,
                avg_stock_on_hand,
                avg_inventory_value,
                current_stock_on_hand,
                current_inventory_value,
                current_inventory_position,
                annual_holding_cost,
                mean_daily_demand,
                demand_variance,
                demand_std_dev,
                demand_coefficient_of_variation,
                demand_coefficient_of_variation AS cv,
                doh_units,
                doh_value,
                inventory_turnover_ratio
            FROM v_sku_store_annual_summary
            ORDER BY annual_contribution_margin DESC
            """
            df = con.execute(query).df()
        finally:
            con.close()

        # 1. ABC Segmentation on Contribution Margin
        total_margin = df["annual_contribution_margin"].sum()
        df["margin_share"] = df["annual_contribution_margin"] / total_margin
        df["cumulative_margin_pct"] = df["margin_share"].cumsum() * 100.0

        def assign_abc(cum_pct: float) -> str:
            if cum_pct <= 80.0:
                return "A"
            elif cum_pct <= 95.0:
                return "B"
            else:
                return "C"

        df["abc_class"] = df["cumulative_margin_pct"].apply(assign_abc)

        # 2. XYZ Segmentation on Coefficient of Variation
        # Minimum observation rule: in_stock_days >= 30
        cv_values = df[df["in_stock_days"] >= 30]["cv"].dropna()
        percentiles = {
            "p25": float(np.percentile(cv_values, 25)),
            "p50_median": float(np.percentile(cv_values, 50)),
            "p75": float(np.percentile(cv_values, 75)),
            "p90": float(np.percentile(cv_values, 90)),
            "mean_cv": float(np.mean(cv_values)),
            "min_cv": float(np.min(cv_values)),
            "max_cv": float(np.max(cv_values)),
        }

        def assign_xyz(row) -> str:
            if row["in_stock_days"] < 30:
                return "INSUFFICIENT_DATA"
            cv = row["cv"]
            if cv <= 0.5:
                return "X"
            elif cv <= 1.0:
                return "Y"
            else:
                return "Z"

        df["xyz_class"] = df.apply(assign_xyz, axis=1)

        # 3. 9-Box Combined Segment & Playbook Recommendation
        df["segment_9box"] = df["abc_class"] + df["xyz_class"]
        df["action_recommendation"] = df["segment_9box"].map(
            lambda s: ACTION_PLAYBOOK.get(s, "Review data quality and replenish manually.")
        )

        diagnostics = {
            "total_pairs": len(df),
            "total_portfolio_margin": float(total_margin),
            "abc_distribution": df["abc_class"].value_counts().to_dict(),
            "xyz_distribution": df["xyz_class"].value_counts().to_dict(),
            "segment_9box_distribution": df["segment_9box"].value_counts().to_dict(),
            "empirical_cv_percentiles": percentiles,
        }

        return df, diagnostics

    def save_to_duckdb(self, segmented_df: pd.DataFrame) -> None:
        """Saves segmented items to DuckDB as stg_segmented_portfolio."""
        con = duckdb.connect(self.db_path)
        try:
            con.register("df_seg_temp", segmented_df)
            con.execute("CREATE OR REPLACE TABLE stg_segmented_portfolio AS SELECT * FROM df_seg_temp;")
            con.unregister("df_seg_temp")
        finally:
            con.close()
