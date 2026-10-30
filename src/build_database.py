"""
Smart Inventory Diagnostics - Phase 3: DuckDB Analytics Database Builder
Executes SQL staging, dimensional modeling, fact building, and analytical views.
"""

import os
import sys
import duckdb
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SQL_DIR = os.path.join(BASE_DIR, "sql")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "inventory_analytics.duckdb")

os.makedirs(PROCESSED_DIR, exist_ok=True)


def build_analytics_database(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    """
    Builds the complete analytical DuckDB database executing Phase 3 SQL scripts.
    """
    print("=" * 75)
    print("STARTING PHASE 3: STAGING & DUCKDB SQL ANALYTICS FOUNDATION")
    print("=" * 75)
    print(f"Target DuckDB database: {db_path}")

    # Set working directory to project root so relative paths in SQL scripts resolve correctly
    orig_cwd = os.getcwd()
    os.chdir(BASE_DIR)

    try:
        con = duckdb.connect(db_path)

        scripts = [
            ("Step 1/4: Staging Tables", "01_create_staging.sql"),
            ("Step 2/4: Dimensional Modeling", "02_create_dimensions.sql"),
            ("Step 3/4: Fact Table Modeling", "03_create_fact_tables.sql"),
            ("Step 4/4: Analytical Views", "04_create_analytics_views.sql"),
        ]

        for step_label, script_name in scripts:
            script_path = os.path.join(SQL_DIR, script_name)
            print(f"\n[{step_label}] Executing {script_name}...")
            with open(script_path, "r", encoding="utf-8") as f:
                sql_content = f.read()
            con.execute(sql_content)
            print(f"  --> {script_name} executed successfully.")

        # Print Pipeline Reconciliation Table
        print("\n" + "-" * 75)
        print("PIPELINE RECONCILIATION AUDIT (Raw -> Quarantined -> Staging -> Modeled)")
        print("-" * 75)
        rec_df = con.execute("SELECT * FROM v_pipeline_reconciliation").df()
        print(rec_df.to_string(index=False))

        # Check Table Counts
        tables = [
            "stg_products", "stg_stores", "stg_suppliers",
            "stg_sales_transactions", "stg_inventory_snapshots", "stg_supplier_orders",
            "dim_product", "dim_store", "dim_supplier", "dim_date",
            "fct_daily_sales", "fct_daily_inventory_snapshot", "fct_purchase_orders"
        ]

        print("\n" + "-" * 75)
        print("MODEL ROW-COUNT SUMMARY")
        print("-" * 75)
        for tbl in tables:
            cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  • {tbl:<32} : {cnt:>8,} rows")

        # Summary Metrics Test from Analytical Views
        print("\n" + "-" * 75)
        print("ANALYTICAL VIEWS SANITY TEST")
        print("-" * 75)
        annual_summary = con.execute("""
            SELECT
                COUNT(*) AS total_sku_store_pairs,
                SUM(annual_gross_revenue) AS total_revenue,
                SUM(annual_contribution_margin) AS total_contribution_margin,
                ROUND(AVG(stockout_rate_pct), 2) AS avg_stockout_rate_pct,
                ROUND(AVG(doh_units), 1) AS avg_doh_units,
                ROUND(AVG(doh_value), 1) AS avg_doh_value,
                ROUND(SUM(annual_holding_cost), 2) AS total_annual_holding_cost
            FROM v_sku_store_annual_summary
        """).df()
        print(annual_summary.to_string(index=False))

        db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        print(f"\nDatabase build complete. Database file size: {db_size_mb} MB")
        print("=" * 75)
        return con

    finally:
        os.chdir(orig_cwd)


if __name__ == "__main__":
    con = build_analytics_database()
    con.close()
