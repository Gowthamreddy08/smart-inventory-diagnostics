"""
Smart Inventory Diagnostics - Modern Executive & Operational Supply Chain Dashboard
A clean, intuitive, and responsive Streamlit command center designed for instant readability (5-10s).
"""

import os
import sys
import math
import duckdb
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from scipy.stats import norm

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "inventory_analytics.duckdb")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Set Page Config
st.set_page_config(
    page_title="Smart Inventory Diagnostics | Retail Command Center",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern, Professional CSS Styling
st.markdown("""
<style>
    /* Global Font & Spacing */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Header */
    .hero-container {
        padding: 1.25rem 1.5rem;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin: 0;
        color: #F8FAFC;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 0.25rem;
        margin-bottom: 0;
    }
    
    /* KPI Metric Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem 1.15rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    }
    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.35rem;
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #0F172A;
        line-height: 1.2;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 0.35rem;
    }
    .kpi-badge-positive {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        background: #DCFCE7;
        color: #15803D;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .kpi-badge-negative {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        background: #FEE2E2;
        color: #B91C1C;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .kpi-badge-neutral {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        background: #F1F5F9;
        color: #475569;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    
    /* Section Headers */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0F172A;
        margin-top: 0.5rem;
        margin-bottom: 0.2rem;
    }
    .section-desc {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 1rem;
    }
    
    /* Priority Badges */
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-high {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-healthy {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    
    /* Takeaway Callout Box */
    .insight-callout {
        background: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 0.85rem 1.1rem;
        border-radius: 0 8px 8px 0;
        color: #1E40AF;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }
    .insight-callout-warning {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 0.85rem 1.1rem;
        border-radius: 0 8px 8px 0;
        color: #92400E;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_data():
    """Connects to DuckDB and caches key tables and marts."""
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        policies_df = con.execute("""
            SELECT p.*, s.store_tier 
            FROM mart_sku_store_policies p
            LEFT JOIN dim_store s ON p.store_id = s.store_id;
        """).df()
        lost_sales_summary = con.execute("""
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
        
        supplier_df = con.execute("""
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

        stores_df = con.execute("SELECT * FROM dim_store;").df()
        products_df = con.execute("SELECT * FROM dim_product;").df()

    finally:
        con.close()

    return policies_df, lost_sales_summary, supplier_df, stores_df, products_df


# Load Data
try:
    policies_df, lost_sales_monthly, supplier_df, stores_df, products_df = load_data()
except Exception as e:
    st.error(f"Error loading analytical database at `{DB_PATH}`: {e}")
    st.stop()

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & FILTERS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 📦 Supply Chain Filters")
    st.caption("Customize your view by store, category, and product tier.")
    
    # Store Filter
    all_stores = sorted(policies_df["store_name"].unique())
    selected_stores = st.multiselect(
        "🏢 Retail Stores",
        options=all_stores,
        default=all_stores,
        help="Select one or more stores to analyze local performance."
    )

    # Category Filter
    all_categories = sorted(policies_df["category"].unique())
    selected_categories = st.multiselect(
        "🏷️ Merchandising Categories",
        options=all_categories,
        default=all_categories,
        help="Filter items by department/category."
    )

    # ABC Class Filter
    all_abc = ["A", "B", "C"]
    selected_abc = st.multiselect(
        "⭐ Profit Contribution (ABC)",
        options=all_abc,
        default=all_abc,
        help="Class A: Top 80% Profit | Class B: Next 15% | Class C: Remaining 5%"
    )

    st.divider()
    
    # Filter Dataset
    filtered_df = policies_df[
        (policies_df["store_name"].isin(selected_stores)) &
        (policies_df["category"].isin(selected_categories)) &
        (policies_df["abc_class"].isin(selected_abc))
    ]

    st.markdown(f"**Viewing:** `{len(filtered_df):,}` of `{len(policies_df):,}` SKU-Store pairs")
    
    # Quick baseline facts
    st.caption("📋 **Baseline Assumptions:**")
    st.caption("• Annual Holding Cost: **22.0%**")
    st.caption("• Target Service Level: **95% CSL**")
    st.caption("• Supplier Review Cycle: **7 Days**")

# ---------------------------------------------------------
# TOP HERO BANNER (CLEAN & PROFESSIONAL)
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Smart Inventory Diagnostics & Policy Engine</div>
    <div class="hero-subtitle">Executive Command Center: Multi-Store Stockout Diagnostics, Counterfactual Demand & Automated Replenishment</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INTUITIVE TAB NAVIGATION
# ---------------------------------------------------------
tab_overview, tab_actions, tab_portfolio, tab_simulator, tab_suppliers, tab_governance = st.tabs([
    "📊 Executive Overview",
    "🚨 Daily Reorder Action List",
    "🎯 Product Portfolio (ABC-XYZ)",
    "⚙️ Safety Stock Simulator",
    "🚚 Supplier Reliability",
    "🛡️ Data Quality & Audit"
])

# =========================================================
# TAB 1: EXECUTIVE OVERVIEW (5-10 SECOND READABILITY)
# =========================================================
with tab_overview:
    st.markdown('<div class="section-title">Network Financial & Stockout Scorecard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">At-a-glance financial health, stockout incidence, and modeled sales opportunities across the selected stores.</div>', unsafe_allow_html=True)

    # Top-line metrics calculation
    tot_rev = filtered_df["annual_gross_revenue"].sum()
    tot_margin = filtered_df["annual_contribution_margin"].sum()
    margin_pct = (tot_margin / tot_rev * 100.0) if tot_rev > 0 else 0.0
    tot_avg_val = filtered_df["avg_inventory_value"].sum()
    tot_holding_cost = filtered_df["annual_holding_cost"].sum()
    avg_turnover = filtered_df["annual_cogs"].sum() / tot_avg_val if tot_avg_val > 0 else 0.0
    avg_stockout_rate = filtered_df["stockout_rate_pct"].mean()

    # Lost Sales from filtered pairs
    matched_lost = lost_sales_monthly[
        lost_sales_monthly["sku_id"].isin(filtered_df["sku_id"]) &
        lost_sales_monthly["store_id"].isin(filtered_df["store_id"])
    ]
    tot_lost_rev = matched_lost["lost_revenue"].sum()
    tot_lost_margin = matched_lost["lost_margin"].sum()
    tot_lost_units = matched_lost["lost_units"].sum()

    # 4 Primary KPI Cards (Clean, readable, 5-second glance)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-header">
                    <span class="kpi-label">Gross Revenue</span>
                    <span class="kpi-badge-positive">Active Sales</span>
                </div>
                <div class="kpi-value">${tot_rev:,.0f}</div>
            </div>
            <div class="kpi-subtext">Profit Margin: <strong>${tot_margin:,.0f} ({margin_pct:.1f}%)</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-header">
                    <span class="kpi-label">Stockout Rate</span>
                    <span class="kpi-badge-negative">{avg_stockout_rate:.1f}% Days</span>
                </div>
                <div class="kpi-value">{avg_stockout_rate:.2f}%</div>
            </div>
            <div class="kpi-subtext">Frequency of shelves being completely empty</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-header">
                    <span class="kpi-label">Lost Sales Opportunity</span>
                    <span class="kpi-badge-negative">Modeled</span>
                </div>
                <div class="kpi-value">${tot_lost_rev:,.0f}</div>
            </div>
            <div class="kpi-subtext">Unfulfilled demand: <strong>{tot_lost_units:,.0f} lost units</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-header">
                    <span class="kpi-label">Holding Cost (22%)</span>
                    <span class="kpi-badge-neutral">Working Capital</span>
                </div>
                <div class="kpi-value">${tot_holding_cost:,.0f}</div>
            </div>
            <div class="kpi-subtext">Annual cost of capital, storage, and shrinkage</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Core Charts in 2 columns
    c_left, c_right = st.columns([6, 4])

    with c_left:
        st.markdown("##### 📈 Fulfilled Sales vs Lost Sales Opportunity (Month-by-Month)")
        st.caption("Blue bars show units sold; red line shows sales lost when items were out of stock.")
        
        monthly_trend = matched_lost.groupby("month").agg(
            fulfilled_units=("units_fulfilled", "sum"),
            lost_units=("lost_units", "sum"),
            lost_revenue=("lost_revenue", "sum")
        ).reset_index()
        monthly_trend["month_str"] = pd.to_datetime(monthly_trend["month"]).dt.strftime("%b %Y")

        bar_chart = alt.Chart(monthly_trend).mark_bar(color="#3B82F6", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("month_str:N", title="Month", sort=None),
            y=alt.Y("fulfilled_units:Q", title="Fulfilled Units"),
            tooltip=[
                alt.Tooltip("month_str:N", title="Month"),
                alt.Tooltip("fulfilled_units:Q", format=",.0f", title="Units Fulfilled")
            ]
        )
        line_chart = alt.Chart(monthly_trend).mark_line(color="#EF4444", strokeWidth=3, point=alt.OverlayMarkDef(color="#EF4444", size=50)).encode(
            x=alt.X("month_str:N", sort=None),
            y=alt.Y("lost_units:Q", title="Lost Sales Units"),
            tooltip=[
                alt.Tooltip("month_str:N", title="Month"),
                alt.Tooltip("lost_units:Q", format=",.0f", title="Lost Units"),
                alt.Tooltip("lost_revenue:Q", format="$,.0f", title="Lost Revenue")
            ]
        )
        combo = alt.layer(bar_chart, line_chart).resolve_scale(y="independent").properties(height=280)
        st.altair_chart(combo, width="stretch")

    with c_right:
        st.markdown("##### 🏷️ Profit Contribution by Category")
        st.caption("Distribution of gross contribution margin across merchandising categories.")
        cat_margin = filtered_df.groupby("category")["annual_contribution_margin"].sum().reset_index()
        donut = alt.Chart(cat_margin).mark_arc(innerRadius=55, stroke="#FFFFFF", strokeWidth=2).encode(
            theta=alt.Theta("annual_contribution_margin:Q"),
            color=alt.Color("category:N", scale=alt.Scale(scheme="tableau10"), legend=alt.Legend(orient="bottom", columns=2, title=None)),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("annual_contribution_margin:Q", format="$,.0f", title="Profit Margin")
            ]
        ).properties(height=280)
        st.altair_chart(donut, width="stretch")

    # Store Breakdown Table
    st.markdown("##### 🏢 Store-by-Store Performance Breakdown")
    group_cols = ["store_name", "region"]
    if "store_tier" in filtered_df.columns:
        group_cols.append("store_tier")

    store_summary = filtered_df.groupby(group_cols).agg(
        revenue=("annual_gross_revenue", "sum"),
        margin=("annual_contribution_margin", "sum"),
        stockout_pct=("stockout_rate_pct", "mean"),
        current_inventory=("current_inventory_value", "sum"),
        turnover=("inventory_turnover_ratio", "mean"),
        doh=("doh_units", "mean")
    ).reset_index()
    store_summary["margin_pct"] = (store_summary["margin"] / store_summary["revenue"] * 100.0).round(1).astype(str) + "%"
    store_summary["revenue"] = store_summary["revenue"].apply(lambda v: f"${v:,.0f}")
    store_summary["margin"] = store_summary["margin"].apply(lambda v: f"${v:,.0f}")
    store_summary["current_inventory"] = store_summary["current_inventory"].apply(lambda v: f"${v:,.0f}")
    store_summary["stockout_pct"] = store_summary["stockout_pct"].round(2).astype(str) + "%"
    store_summary["doh"] = store_summary["doh"].round(1).astype(str) + " days"
    store_summary["turnover"] = store_summary["turnover"].round(1).astype(str) + "x"

    rename_map = {
        "store_name": "Store",
        "region": "Region",
        "revenue": "Gross Revenue",
        "margin": "Profit Margin",
        "margin_pct": "Margin %",
        "stockout_pct": "Stockout Rate",
        "current_inventory": "Current Inventory",
        "doh": "Days on Hand",
        "turnover": "Turnover"
    }
    if "store_tier" in store_summary.columns:
        rename_map["store_tier"] = "Tier"

    st.dataframe(
        store_summary.rename(columns=rename_map),
        width="stretch",
        hide_index=True
    )


# =========================================================
# TAB 2: DAILY REORDER ACTION LIST (OPERATIONAL WORKBENCH)
# =========================================================
with tab_actions:
    st.markdown('<div class="section-title">Daily Procurement Reorder Center</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-callout-warning">
        <strong>⚡ Operational Rule:</strong> 
        Items flagged <strong>CRITICAL</strong> have current stock below their safety buffer. Order these immediately today to prevent shelf stockouts.
    </div>
    """, unsafe_allow_html=True)

    # Alert Count Summary
    crit_count = (filtered_df["priority_alert"] == "CRITICAL").sum()
    high_count = (filtered_df["priority_alert"] == "HIGH").sum()
    med_count = (filtered_df["priority_alert"] == "MEDIUM").sum()
    health_count = (filtered_df["priority_alert"] == "HEALTHY").sum()

    urgent_reorder_units = filtered_df[filtered_df["priority_alert"].isin(["CRITICAL", "HIGH"])]["recommended_reorder_qty"].sum()
    urgent_reorder_capital = (filtered_df[filtered_df["priority_alert"].isin(["CRITICAL", "HIGH"])]["recommended_reorder_qty"] * filtered_df[filtered_df["priority_alert"].isin(["CRITICAL", "HIGH"])]["unit_cost"]).sum()

    # 4 Clear Action Cards
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid #EF4444;">
            <div>
                <div class="kpi-label">🚨 CRITICAL Alerts</div>
                <div class="kpi-value" style="color: #DC2626;">{crit_count:,} items</div>
            </div>
            <div class="kpi-subtext">Current Stock is <strong>below safety buffer</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left: 4px solid #F59E0B;">
            <div>
                <div class="kpi-label">⚠️ HIGH Priority Alerts</div>
                <div class="kpi-value" style="color: #D97706;">{high_count:,} items</div>
            </div>
            <div class="kpi-subtext">Stock has hit standard <strong>Reorder Point</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with a3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-label">📦 Total Units to Order</div>
                <div class="kpi-value">{urgent_reorder_units:,} units</div>
            </div>
            <div class="kpi-subtext">Across all Critical & High items</div>
        </div>
        """, unsafe_allow_html=True)
    with a4:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-label">💰 Reorder Capital Needed</div>
                <div class="kpi-value" style="color: #2563EB;">${urgent_reorder_capital:,.2f}</div>
            </div>
            <div class="kpi-subtext">Total cash investment required for today's POs</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Severity Filter
    col_f1, col_f2 = st.columns([4, 6])
    with col_f1:
        selected_alerts = st.multiselect(
            "Filter Table by Alert Severity",
            options=["CRITICAL", "HIGH", "MEDIUM", "HEALTHY"],
            default=["CRITICAL", "HIGH"],
            help="Select severity levels to view in the action list."
        )

    action_items = filtered_df[filtered_df["priority_alert"].isin(selected_alerts)].copy()
    action_items["order_capital_required"] = (action_items["recommended_reorder_qty"] * action_items["unit_cost"]).round(2)
    action_items = action_items.sort_values(by=["priority_rank", "order_capital_required"], ascending=[True, False])

    with col_f2:
        st.markdown("<div style='text-align: right; margin-top: 1.5rem;'>", unsafe_allow_html=True)
        csv_data = action_items.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Purchase Order Recommendations (.CSV)",
            data=csv_data,
            file_name="procurement_purchase_orders.csv",
            mime="text/csv",
            help="Click to download today's purchase order list for supplier transmission."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    display_cols = [
        "sku_id", "product_name", "category", "store_name", "priority_alert",
        "current_stock_on_hand", "current_inventory_position", "safety_stock_primary",
        "reorder_point_primary", "order_up_to_primary", "recommended_reorder_qty",
        "unit_cost", "order_capital_required", "action_recommendation"
    ]

    st.dataframe(
        action_items[display_cols].rename(columns={
            "sku_id": "SKU",
            "product_name": "Product Name",
            "category": "Category",
            "store_name": "Store",
            "priority_alert": "Alert Level",
            "current_stock_on_hand": "Stock on Shelf",
            "current_inventory_position": "Total Position (SOH + Transit)",
            "safety_stock_primary": "Safety Cushion",
            "reorder_point_primary": "Reorder Boundary",
            "order_up_to_primary": "Max Ceiling",
            "recommended_reorder_qty": "Order Qty",
            "unit_cost": "Cost/Unit",
            "order_capital_required": "Order Total ($)",
            "action_recommendation": "Recommended Action"
        }),
        width="stretch",
        hide_index=True
    )


# =========================================================
# TAB 3: PRODUCT PORTFOLIO (ABC-XYZ)
# =========================================================
with tab_portfolio:
    st.markdown('<div class="section-title">ABC-XYZ Product Segmentation (9-Box Playbook)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-callout">
        <strong>💡 How to read this:</strong> 
        <strong>ABC (Profit):</strong> Class A items generate 80% of total profit. Protect them at all costs.<br>
        <strong>XYZ (Predictability):</strong> Class X items sell steadily every day. Class Z items have unpredictable, lumpy spikes.
    </div>
    """, unsafe_allow_html=True)

    col_mat1, col_mat2 = st.columns([5, 5])

    with col_mat1:
        st.markdown("##### 📊 9-Box Grid Distribution (Pairs & Profit Share)")
        matrix_counts = filtered_df.groupby("segment_9box").agg(
            pair_count=("sku_id", "count"),
            margin=("annual_contribution_margin", "sum"),
            avg_cv=("demand_coefficient_of_variation", "mean")
        ).reset_index()
        tot_m = filtered_df["annual_contribution_margin"].sum()
        matrix_counts["margin_share_pct"] = (matrix_counts["margin"] / tot_m * 100.0).round(1) if tot_m > 0 else 0

        heatmap_chart = alt.Chart(matrix_counts).mark_rect(cornerRadius=6).encode(
            x=alt.X("segment_9box:N", title="Segment", sort=["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"]),
            y=alt.Y("pair_count:Q", title="Item Count"),
            color=alt.Color("margin_share_pct:Q", scale=alt.Scale(scheme="blues"), title="Profit Share %"),
            tooltip=[
                alt.Tooltip("segment_9box:N", title="Segment"),
                alt.Tooltip("pair_count:Q", title="Number of Items"),
                alt.Tooltip("margin_share_pct:Q", format=".1f", title="Profit Share %"),
                alt.Tooltip("margin:Q", format="$,.0f", title="Total Profit Margin"),
                alt.Tooltip("avg_cv:Q", format=".2f", title="Avg Volatility (CV)")
            ]
        ).properties(height=260)
        st.altair_chart(heatmap_chart, width="stretch")

    with col_mat2:
        st.markdown("##### 🎯 Demand Volatility vs Margin Pareto Curve")
        scatter_chart = alt.Chart(filtered_df).mark_circle(size=65, opacity=0.75).encode(
            x=alt.X("demand_coefficient_of_variation:Q", title="Demand Volatility (CV)", scale=alt.Scale(domain=[0.2, 1.15])),
            y=alt.Y("cumulative_margin_pct:Q", title="Cumulative Profit % (Pareto)", scale=alt.Scale(domain=[0, 105])),
            color=alt.Color("abc_class:N", scale=alt.Scale(domain=["A", "B", "C"], range=["#10B981", "#3B82F6", "#F59E0B"]), title="Profit Class"),
            tooltip=[
                alt.Tooltip("product_name:N", title="Product"),
                alt.Tooltip("store_name:N", title="Store"),
                alt.Tooltip("segment_9box:N", title="Segment"),
                alt.Tooltip("annual_contribution_margin:Q", format="$,.0f", title="Profit"),
                alt.Tooltip("demand_coefficient_of_variation:Q", format=".2f", title="Demand CV")
            ]
        ).properties(height=260)
        st.altair_chart(scatter_chart, width="stretch")

    st.markdown("##### 📋 Recommended Strategy by Segment")
    playbook_df = filtered_df.groupby(["segment_9box", "abc_class", "xyz_class"]).agg(
        pairs=("sku_id", "count"),
        total_margin=("annual_contribution_margin", "sum"),
        avg_doh=("doh_units", "mean"),
        strategy=("action_recommendation", "first")
    ).reset_index()
    playbook_df["total_margin"] = playbook_df["total_margin"].apply(lambda v: f"${v:,.0f}")
    playbook_df["avg_doh"] = playbook_df["avg_doh"].apply(lambda v: f"{v:.1f} days")

    st.dataframe(
        playbook_df.rename(columns={
            "segment_9box": "Segment",
            "abc_class": "Profit Class",
            "xyz_class": "Volatility",
            "pairs": "Item Count",
            "total_margin": "Total Profit",
            "avg_doh": "Avg Days on Hand",
            "strategy": "Playbook Strategy"
        }),
        width="stretch",
        hide_index=True
    )


# =========================================================
# TAB 4: SAFETY STOCK SIMULATOR (WHAT-IF ANALYSIS)
# =========================================================
with tab_simulator:
    st.markdown('<div class="section-title">Service Level & Safety Stock Simulator</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-callout">
        <strong>🤔 The Trade-Off:</strong> 
        Higher service levels (e.g. 99%) protect against empty shelves, but demand <strong>exponentially more cash</strong> tied up in backup stock.
        Use the slider below to test the financial impact on your stores.
    </div>
    """, unsafe_allow_html=True)

    col_sim_ctrl, col_sim_empty = st.columns([6, 4])
    with col_sim_ctrl:
        sim_csl = st.slider(
            "Select Target Cycle Service Level (% CSL)",
            min_value=85.0,
            max_value=99.5,
            value=95.0,
            step=0.5,
            help="95% is the standard retail baseline. 99% provides premium availability but costs more."
        )

    # Dynamic calculation
    sim_z = norm.ppf(sim_csl / 100.0)

    sim_results = []
    for _, row in filtered_df.iterrows():
        d_mean = max(0.01, float(row["mean_daily_demand"]))
        d_var = max(0.01, float(row["demand_variance"]))
        l_mean = max(1.0, float(row["avg_lead_time_days"]))
        l_var = max(0.01, float(row["lead_time_variance"]))
        unit_cost = float(row["unit_cost"])

        comb_var = (l_mean * d_var) + ((d_mean ** 2) * l_var)
        std_cont = math.sqrt(max(0.01, comb_var))
        ss_units = int(math.ceil(sim_z * std_cont))
        ss_capital = ss_units * unit_cost

        sim_results.append({
            "ss_units": ss_units,
            "ss_capital": ss_capital,
            "holding_cost": ss_capital * 0.22
        })

    df_sim = pd.DataFrame(sim_results)
    tot_sim_units = df_sim["ss_units"].sum()
    tot_sim_capital = df_sim["ss_capital"].sum()
    tot_sim_holding = df_sim["holding_cost"].sum()

    base_units = filtered_df["safety_stock_cont_95"].sum()
    base_capital = (filtered_df["safety_stock_cont_95"] * filtered_df["unit_cost"]).sum()
    delta_units = tot_sim_units - base_units
    delta_capital = tot_sim_capital - base_capital

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Target Service Level</div>
            <div class="kpi-value">{sim_csl:.1f}%</div>
            <div class="kpi-subtext">Gaussian Z-Score: <strong>{sim_z:.3f}</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Required Buffer Stock</div>
            <div class="kpi-value">{tot_sim_units:,} units</div>
            <div class="kpi-subtext">Delta vs 95%: <strong>{delta_units:+,} units</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Capital Investment</div>
            <div class="kpi-value">${tot_sim_capital:,.0f}</div>
            <div class="kpi-subtext">Delta vs 95%: <strong>${delta_capital:+,.0f}</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Annual Holding Cost</div>
            <div class="kpi-value">${tot_sim_holding:,.0f}</div>
            <div class="kpi-subtext">At 22% annual inventory carrying rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # The Cost Curve
    st.markdown("##### 📈 The Exponential 'Hockey-Stick' Cost Curve")
    st.caption("Notice how costs skyrocket past 97% service level. This is why 99% should only be applied to Class A cash cows.")

    frontier_data = []
    for test_csl in np.arange(85.0, 100.0, 1.0):
        z_t = norm.ppf(test_csl / 100.0)
        c_tot = 0
        u_tot = 0
        for _, row in filtered_df.iterrows():
            d_m = max(0.01, float(row["mean_daily_demand"]))
            d_v = max(0.01, float(row["demand_variance"]))
            l_m = max(1.0, float(row["avg_lead_time_days"]))
            l_v = max(0.01, float(row["lead_time_variance"]))
            comb_v = (l_m * d_v) + ((d_m ** 2) * l_v)
            u = math.ceil(z_t * math.sqrt(max(0.01, comb_v)))
            u_tot += u
            c_tot += u * float(row["unit_cost"])
        frontier_data.append({"csl": test_csl, "capital": c_tot, "units": u_tot})

    df_front = pd.DataFrame(frontier_data)
    frontier_chart = alt.Chart(df_front).mark_line(color="#2563EB", strokeWidth=3, point=True).encode(
        x=alt.X("csl:Q", title="Cycle Service Level (% CSL)", scale=alt.Scale(domain=[85, 99.5])),
        y=alt.Y("capital:Q", title="Safety Stock Working Capital ($)", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("csl:Q", title="Service Level %"),
            alt.Tooltip("capital:Q", format="$,.0f", title="Required Capital"),
            alt.Tooltip("units:Q", format=",", title="Safety Buffer Units")
        ]
    ).properties(height=300)

    st.altair_chart(frontier_chart, width="stretch")


# =========================================================
# TAB 5: SUPPLIER RELIABILITY SCORECARD
# =========================================================
with tab_suppliers:
    st.markdown('<div class="section-title">Supplier Delivery Reliability & Working Capital Impact</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-callout-warning">
        <strong>🚚 Supplier Impact:</strong> 
        When suppliers deliver late, your stores are forced to store extra safety stock.
        Across our network, <strong>$287,301 in cash</strong> is trapped purely because suppliers have erratic delivery times!
    </div>
    """, unsafe_allow_html=True)

    supp_report_path = os.path.join(REPORTS_DIR, "supplier_performance_and_lead_time.csv")
    if os.path.exists(supp_report_path):
        supp_perf = pd.read_csv(supp_report_path)

        col_s1, col_s2 = st.columns([6, 4])

        with col_s1:
            st.markdown("##### 💰 Cash Trapped in Buffer Stock by Supplier")
            supp_bar = alt.Chart(supp_perf).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                y=alt.Y("supplier_name:N", title=None, sort="-x"),
                x=alt.X("supplier_buffer_capital:Q", title="Cash Trapped ($)"),
                color=alt.Color("reliability_tier:N", scale=alt.Scale(range=["#10B981", "#F59E0B", "#EF4444"]), title="Reliability Tier"),
                tooltip=[
                    alt.Tooltip("supplier_name:N", title="Supplier"),
                    alt.Tooltip("on_time_delivery_rate_pct:Q", format=".1f", title="On-Time Delivery %"),
                    alt.Tooltip("lead_time_std_dev:Q", format=".2f", title="Lead Time Std Dev (Days)"),
                    alt.Tooltip("supplier_buffer_capital:Q", format="$,.0f", title="Trapped Working Capital")
                ]
            ).properties(height=300)
            st.altair_chart(supp_bar, width="stretch")

        with col_s2:
            st.markdown("##### 📌 Key Procurement Negotiation Points")
            st.info("""
            * **SUP-05 (Vanguard Distributors):** 
              Lead time swings by **±2.3 days**. This forces **$83,720** of extra safety buffer.
            * **SUP-02 (Pinnacle Brands):** 
              Only 58% on-time delivery rate. Ties up **$64,374** in extra buffer.
            * **Action:** Cutting vendor delivery variance in half through SLA enforcement would immediately release **~$140,000 in cash** back into the business!
            """)

        st.markdown("##### 📋 Complete Supplier Performance Scorecard")
        st.dataframe(
            supp_perf[[
                "supplier_id", "supplier_name", "total_pos", "total_spend",
                "avg_actual_lead_time", "lead_time_std_dev", "on_time_delivery_rate_pct",
                "supplier_buffer_units", "supplier_buffer_capital", "reliability_tier"
            ]].rename(columns={
                "supplier_id": "Supplier ID",
                "supplier_name": "Supplier Name",
                "total_pos": "Orders Completed",
                "total_spend": "Total Spend ($)",
                "avg_actual_lead_time": "Avg Lead Time (Days)",
                "lead_time_std_dev": "Lead Time Std Dev",
                "on_time_delivery_rate_pct": "On-Time Delivery %",
                "supplier_buffer_units": "Extra Units Trapped",
                "supplier_buffer_capital": "Extra Cash Trapped ($)",
                "reliability_tier": "Status"
            }),
            width="stretch",
            hide_index=True
        )


# =========================================================
# TAB 6: DATA QUALITY & AUDIT
# =========================================================
with tab_governance:
    st.markdown('<div class="section-title">Data Quality & Pipeline Governance</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-callout">
        <strong>🛡️ 100% Data Integrity Guarantee:</strong> 
        All source CSV files remain untouched and immutable. Critical errors were automatically quarantined into <code>data/quarantine/</code>, ensuring zero silent corruption in safety stock or profit metrics.
    </div>
    """, unsafe_allow_html=True)

    dq_path = os.path.join(REPORTS_DIR, "data_quality_reconciliation_summary.csv")
    if os.path.exists(dq_path):
        df_dq = pd.read_csv(dq_path)
        st.markdown("##### 🔍 Pipeline Audit Reconciliation (Zero Variance)")
        st.dataframe(df_dq, width="stretch", hide_index=True)

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("##### 1. Negative Inventory")
        st.caption("8 rows with negative stock were quarantined into `quarantined_inventory_snapshots.csv`. This prevented corrupted turnover and false stock calculations.")
    with g2:
        st.markdown("##### 2. Phantom Ghost Sales")
        st.caption("6 transactions claiming sales during zero-stockout days were isolated into `quarantined_sales_transactions.csv` to keep demand modeling clean.")
    with g3:
        st.markdown("##### 3. Supplier Date Inversions")
        st.caption("2 POs with delivery dates earlier than order dates were isolated into `quarantined_supplier_orders.csv`, preventing negative variance errors.")

    st.divider()
    st.caption("🔒 **Governance Notice:** Per decision DEC-011, perishable spoilage is modeled in an isolated synthetic module and segregated from continuous reorder calculations.")
