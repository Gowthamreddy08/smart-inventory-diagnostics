"""
Smart Inventory Diagnostics - Phase 4: Lost-Sales Counterfactual Estimator
Estimates unconstrained customer demand during out-of-stock periods using
strictly prior in-stock same-weekday observations (no future data leakage).
"""

import os
import sys
import duckdb
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "inventory_analytics.duckdb")


class LostSalesEstimator:
    """
    Estimates unconstrained customer demand and lost revenue on stockout days
    using the approved rolling 4-week same-weekday historical in-stock baseline.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)

    def compute_lost_sales(self) -> pd.DataFrame:
        """
        Executes the counterfactual lost-sales estimation algorithm.
        Ensures strict temporal causality: only prior observations are used.
        """
        con = duckdb.connect(self.db_path)
        try:
            # Query the complete daily grid of sales and stock status
            query = """
            SELECT
                i.snapshot_date,
                EXTRACT(DOW FROM i.snapshot_date)::INTEGER AS day_of_week,
                i.sku_id,
                i.store_id,
                p.product_name,
                p.category,
                p.unit_cost,
                p.unit_selling_price,
                p.contribution_margin,
                i.stock_on_hand,
                i.is_stockout_flag,
                COALESCE(s.units_demanded, 0) AS units_demanded,
                COALESCE(s.units_fulfilled, 0) AS units_fulfilled
            FROM fct_daily_inventory_snapshot i
            INNER JOIN dim_product p ON i.sku_id = p.sku_id
            LEFT JOIN fct_daily_sales s
                ON i.snapshot_date = s.transaction_date
               AND i.sku_id = s.sku_id
               AND i.store_id = s.store_id
            ORDER BY i.sku_id, i.store_id, i.snapshot_date
            """
            df = con.execute(query).df()
        finally:
            con.close()

        records = []
        # Group by SKU-Store pair to compute historical rolling baselines chronologically
        grouped = df.groupby(["sku_id", "store_id"], sort=False)

        for (sku_id, store_id), group in grouped:
            group = group.sort_values("snapshot_date").reset_index(drop=True)
            
            # History buffer: maps day_of_week (0-6) -> list of prior in-stock fulfilled sales
            dow_history = {dow: [] for dow in range(7)}
            all_instock_history = []

            for idx, row in group.iterrows():
                snap_date = row["snapshot_date"]
                dow = int(row["day_of_week"])
                soh = row["stock_on_hand"]
                is_stockout = row["is_stockout_flag"]
                fulfilled = row["units_fulfilled"]
                price = row["unit_selling_price"]
                margin = row["contribution_margin"]

                expected_demand = None
                lost_units = 0
                lost_revenue = 0.0
                lost_margin = 0.0
                estimation_method = "IN_STOCK"

                if is_stockout == 1 or soh <= 0:
                    # Stockout condition: calculate expected demand from prior in-stock history
                    prior_dow_sales = dow_history[dow]
                    
                    if len(prior_dow_sales) >= 4:
                        # Standard approved baseline: average of previous 4 in-stock same-weekdays
                        expected_demand = float(np.mean(prior_dow_sales[-4:]))
                        estimation_method = "SAME_WEEKDAY_4WK_AVG"
                    elif len(prior_dow_sales) > 0:
                        # Fewer than 4 available (e.g. early January): average available same-weekdays
                        expected_demand = float(np.mean(prior_dow_sales))
                        estimation_method = f"SAME_WEEKDAY_{len(prior_dow_sales)}WK_AVG"
                    elif len(all_instock_history) > 0:
                        # Fallback: overall prior in-stock daily mean
                        expected_demand = float(np.mean(all_instock_history))
                        estimation_method = "PRIOR_INSTOCK_OVERALL_MEAN"
                    else:
                        # Day 1 stockout with zero prior history: conservative estimate
                        expected_demand = float(row["units_demanded"]) if row["units_demanded"] > 0 else 1.0
                        estimation_method = "DAY1_INITIAL_ESTIMATE"

                    # Formula: max(0, expected_demand - fulfilled_units)
                    lost_units = int(max(0, round(expected_demand) - fulfilled))
                    lost_revenue = round(lost_units * price, 2)
                    lost_margin = round(lost_units * margin, 2)
                else:
                    # In-stock condition: customer demand was fully fulfilled or unconstrained
                    expected_demand = float(fulfilled)
                    # Add to in-stock historical buffer for future counterfactual calculations
                    dow_history[dow].append(fulfilled)
                    all_instock_history.append(fulfilled)

                records.append({
                    "snapshot_date": snap_date,
                    "sku_id": sku_id,
                    "store_id": store_id,
                    "day_of_week": dow,
                    "stock_on_hand": soh,
                    "is_stockout_flag": is_stockout,
                    "units_demanded": row["units_demanded"],
                    "units_fulfilled": fulfilled,
                    "expected_daily_demand": round(expected_demand, 2) if expected_demand is not None else None,
                    "estimated_lost_units": lost_units,
                    "estimated_lost_revenue": lost_revenue,
                    "estimated_lost_contribution_margin": lost_margin,
                    "estimation_method": estimation_method,
                    "is_counterfactual_estimate": 1 if is_stockout == 1 else 0
                })

        return pd.DataFrame(records)

    def save_to_duckdb(self, lost_sales_df: pd.DataFrame) -> None:
        """Saves the daily lost sales table to the DuckDB warehouse."""
        con = duckdb.connect(self.db_path)
        try:
            con.register("df_lost_sales_temp", lost_sales_df)
            con.execute("""
            CREATE OR REPLACE TABLE fct_lost_sales_daily AS
            SELECT
                snapshot_date::DATE AS snapshot_date,
                sku_id,
                store_id,
                day_of_week,
                stock_on_hand,
                is_stockout_flag,
                units_demanded,
                units_fulfilled,
                expected_daily_demand,
                estimated_lost_units,
                estimated_lost_revenue,
                estimated_lost_contribution_margin,
                estimation_method,
                is_counterfactual_estimate
            FROM df_lost_sales_temp;
            """)
            con.unregister("df_lost_sales_temp")
        finally:
            con.close()
