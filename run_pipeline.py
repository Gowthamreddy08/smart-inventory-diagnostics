#!/usr/bin/env python
"""
Smart Inventory Diagnostics: Retail Supply Chain Analytics
Master End-to-End Pipeline Orchestrator (run_pipeline.py)

Reproducibly executes the full supply-chain analytics pipeline from raw data
auditing to dimensional modeling, counterfactual metrics, policy calibration,
reporting, and optional dashboard launching.
"""

import os
import sys
import time
import argparse
import subprocess

# Ensure base directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "processed", "inventory_analytics.duckdb")
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
QUARANTINE_DIR = os.path.join(BASE_DIR, "data", "quarantine")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def print_banner():
    banner = """
================================================================================
       SMART INVENTORY DIAGNOSTICS & POLICY OPTIMIZATION PIPELINE
         Retail Supply Chain Analytics & Multi-Echelon Replenishment
================================================================================
"""
    print(banner)


def run_stage_audit():
    """Stage 1: Automated Data Profiling, Quality Audit & Quarantine Isolation."""
    print("\n" + "=" * 80)
    print(">>> STAGE 1: DATA PROFILING, QUALITY AUDIT & QUARANTINE ISOLATION")
    print("=" * 80)
    start_t = time.perf_counter()
    from src.run_quality_audit import run_full_quality_audit
    run_full_quality_audit()
    elapsed = time.perf_counter() - start_t
    print(f"\n[STAGE 1 COMPLETE] Data Quality Audit finished in {elapsed:.2f} seconds.")
    return elapsed


def run_stage_database():
    """Stage 2: DuckDB Staging, Dimensional Modeling & Analytics Views."""
    print("\n" + "=" * 80)
    print(">>> STAGE 2: DUCKDB ANALYTICS WAREHOUSE & SQL MODELING")
    print("=" * 80)
    start_t = time.perf_counter()
    from src.build_database import build_analytics_database
    con = build_analytics_database(DB_PATH)
    con.close()
    elapsed = time.perf_counter() - start_t
    print(f"\n[STAGE 2 COMPLETE] DuckDB SQL Warehouse built in {elapsed:.2f} seconds.")
    return elapsed


def run_stage_metrics():
    """Stage 3: Rolling Counterfactual Demand, ABC-XYZ Segmentation & Policies."""
    print("\n" + "=" * 80)
    print(">>> STAGE 3: CORE RETAIL & INVENTORY METRICS ENGINE")
    print("=" * 80)
    start_t = time.perf_counter()
    from src.run_phase_4_metrics import run_phase_4_pipeline
    run_phase_4_pipeline(DB_PATH)
    elapsed = time.perf_counter() - start_t
    print(f"\n[STAGE 3 COMPLETE] Core Metrics & Policies calibrated in {elapsed:.2f} seconds.")
    return elapsed


def run_stage_reporting():
    """Stage 4: Business Insights, CSV Export & Executive Narrative Report."""
    print("\n" + "=" * 80)
    print(">>> STAGE 4: BUSINESS INSIGHTS & EXECUTIVE REPORTING")
    print("=" * 80)
    start_t = time.perf_counter()
    from src.analytics_reporting import AnalyticsReporter
    reporter = AnalyticsReporter(DB_PATH, REPORTS_DIR)
    reporter.generate_all_reports()
    elapsed = time.perf_counter() - start_t
    print(f"\n[STAGE 4 COMPLETE] Analytics Reports generated in {elapsed:.2f} seconds.")
    return elapsed


def run_tests():
    """Executes the comprehensive pytest suite."""
    print("\n" + "=" * 80)
    print(">>> RUNNING FULL REGRESSION TEST SUITE (PYTEST)")
    print("=" * 80)
    start_t = time.perf_counter()
    import pytest
    tests_dir = os.path.join(BASE_DIR, "tests")
    exit_code = pytest.main([tests_dir, "-v"])
    elapsed = time.perf_counter() - start_t
    print(f"\n[TESTS COMPLETE] Pytest suite finished in {elapsed:.2f} seconds with exit code {exit_code}.")
    return exit_code, elapsed


def launch_dashboard():
    """Launches the interactive Streamlit dashboard."""
    print("\n" + "=" * 80)
    print(">>> LAUNCHING INTERACTIVE STREAMLIT DASHBOARD")
    print("=" * 80)
    app_path = os.path.join(BASE_DIR, "dashboard", "app.py")
    streamlit_exe = os.path.join(BASE_DIR, ".venv", "Scripts", "streamlit.exe")
    if not os.path.exists(streamlit_exe):
        streamlit_exe = "streamlit"

    print(f"Starting Streamlit app: {app_path}")
    print("Open your browser at: http://localhost:8501\n")
    try:
        subprocess.run([streamlit_exe, "run", app_path], check=True)
    except KeyboardInterrupt:
        print("\nStreamlit server stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Inventory Diagnostics - Master Supply Chain Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --all                # Run entire pipeline from audit to reporting
  python run_pipeline.py --audit-only         # Run only data quality profiling & quarantine
  python run_pipeline.py --build-db-only      # Build DuckDB SQL warehouse
  python run_pipeline.py --metrics-only       # Calibrate lost sales and inventory policies
  python run_pipeline.py --reports-only       # Generate executive and operational CSV reports
  python run_pipeline.py --run-tests          # Run full 47-test pytest suite
  python run_pipeline.py --launch-dashboard   # Launch Streamlit interactive web app
        """
    )
    parser.add_argument("--all", action="store_true", help="Execute the complete end-to-end analytics pipeline")
    parser.add_argument("--audit-only", action="store_true", help="Run data quality audit and quarantine isolation only")
    parser.add_argument("--build-db-only", action="store_true", help="Build DuckDB staging, dimensions, facts and views")
    parser.add_argument("--metrics-only", action="store_true", help="Calculate demand counterfactuals, ABC-XYZ, and policies")
    parser.add_argument("--reports-only", action="store_true", help="Generate all business insights CSV and Markdown reports")
    parser.add_argument("--run-tests", action="store_true", help="Run the comprehensive pytest suite")
    parser.add_argument("--launch-dashboard", action="store_true", help="Launch the interactive Streamlit web dashboard")

    args = parser.parse_args()

    # Default to --all if no specific stage flag is provided
    if not any([args.all, args.audit_only, args.build_db_only, args.metrics_only, args.reports_only, args.run_tests, args.launch_dashboard]):
        args.all = True

    print_banner()
    total_start = time.perf_counter()
    timings = {}

    try:
        if args.audit_only:
            timings["Data Quality Audit"] = run_stage_audit()

        elif args.build_db_only:
            timings["DuckDB Warehouse Build"] = run_stage_database()

        elif args.metrics_only:
            timings["Metrics & Policies Engine"] = run_stage_metrics()

        elif args.reports_only:
            timings["Analytics Reporting"] = run_stage_reporting()

        elif args.all:
            timings["Stage 1: Quality Audit"] = run_stage_audit()
            timings["Stage 2: DuckDB Warehouse"] = run_stage_database()
            timings["Stage 3: Metrics & Policies"] = run_stage_metrics()
            timings["Stage 4: Analytics Reporting"] = run_stage_reporting()

        if args.run_tests:
            exit_code, t_test = run_tests()
            timings["Pytest Suite"] = t_test
            if exit_code != 0:
                print(f"\n[PIPELINE WARNING] Test suite completed with non-zero exit code: {exit_code}")
                sys.exit(exit_code)

        if args.launch_dashboard:
            launch_dashboard()

        total_elapsed = time.perf_counter() - total_start

        # Final Summary
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        for stage, duration in timings.items():
            print(f"  • {stage:<35} : {duration:>6.2f} seconds")
        print("-" * 80)
        print(f"  • Total Pipeline Elapsed Time         : {total_elapsed:>6.2f} seconds")
        print("=" * 80)
        print(">> ALL STAGES COMPLETED SUCCESSFULLY WITH ZERO ERRORS.\n")
        sys.exit(0)

    except Exception as e:
        print("\n" + "!" * 80)
        print(f"[PIPELINE FATAL ERROR] {e}")
        print("!" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
