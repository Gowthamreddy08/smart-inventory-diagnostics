# 📋 Project Analysis Scope: Smart Inventory Diagnostics
## Optimizing Safety Stock, Reorder Points, and Stockout Risk in Retail Supply Chains

---

## 1. Business Problem Statement
Retail supply chain networks are caught between two opposing financial pressures:
* **The Stockout Trap:** Inadequate safety buffering and late vendor deliveries cause high-velocity items to run out of stock. This results in direct revenue loss, reduced customer lifetime value, and missed service levels.
* **The Overstock Trap:** Ordering based on static rules of thumb or inflated batch sizes ties up working capital in slow-moving inventory, elevating warehousing holding costs and risking obsolescence.

This project delivers an end-to-end analytical framework to replace manual, rule-of-thumb replenishment with mathematically sound, data-driven inventory policies calibrated at the SKU-store level.

---

## 2. Primary Business Question
> **How can retail supply chain leadership systematically balance inventory carrying costs against stockout risk by calibrating dynamic safety stock, continuous reorder points (ROP), and periodic review thresholds at the individual SKU-store level?**

---

## 3. Secondary Analytical Questions
1. **Portfolio Segmentation:** Which SKUs contribute to the top 80% of cumulative contribution margin (ABC), and how volatile is their daily customer demand (XYZ)?
2. **Stockout Diagnostics & Lost Sales:** What is the historical frequency of stockout events by store and product category, and what is the modeled counterfactual dollar impact of unfulfilled customer demand?
3. **Supplier Reliability:** How does lead-time volatility ($\sigma_L$) across vendors amplify the required safety buffer compared to demand volatility ($\sigma_D$) alone?
4. **Policy Backtesting & Service-Level Trade-offs:** When evaluated under identical historical demand, what is the measurable trade-off in holding costs versus lost margin across $90\%$, $95\%$, and $99\%$ Cycle Service Levels (CSL)?
5. **Operational Prioritization:** Which SKUs currently breach their reorder point and represent an immediate high-severity risk to store fulfillment?

---

## 4. Target Stakeholder Audiences

| Stakeholder Group | Primary Operational & Strategic Needs | Core Dashboard & Reporting Focus |
| :--- | :--- | :--- |
| **Procurement & Sourcing** | Vendor SLA compliance, lead-time variance tracking, purchase order sizing. | Operational Reorder Action Center: recommended order quantities, lead-time buffers. |
| **Inventory Planners** | Parameter maintenance, review period settings ($R$), safety stock calibration. | Continuous ROP vs. Periodic Order-Up-To level recommendations, ABC-XYZ migration. |
| **Store Operations** | Shelf replenishment urgency, physical capacity constraints, out-of-stock mitigation. | Unit-based Days of Inventory on Hand (DOH), daily stockout alerts. |
| **Finance & Executive Leadership** | Working capital velocity, inventory carrying cost reduction, gross margin recovery. | Executive Summary: Total inventory value, value-based DOH, estimated lost revenue. |

---

## 5. Analysis Grains & Scope Boundaries

### Analysis Grains
* **Primary Planning Grain:** `SKU × Store × Date` (Daily store-level inventory positions and sales velocity).
* **Supplier Lead-Time Grain:** `SKU × Supplier × Purchase Order` (Lead-time distribution, receipt quantities, delivery timeliness).
* **Portfolio Segmentation Grain:** `SKU × Store` (Annualized baseline for contribution margin Pareto and demand coefficient of variation).

### Scope Boundaries
* **Store & Network Scope:** Multi-store regional retail network (5 operational physical store locations).
* **Product Scope:** 150 active SKUs across 5 core retail merchandise categories (Beverages, Dry Grocery, Household Goods, Personal Care, and Packaged Goods).
* **Temporal Scope:** 365 consecutive calendar days (1 full operating year) of daily transaction and snapshot history.

---

## 6. Systems Boundary: Inclusions vs. Exclusions

### Included in Analysis Scope
* Store-level point-of-sale (POS) daily fulfilled transaction volume.
* Daily end-of-day stock-on-hand ($SOH$) and stock-in-transit ($SIT$) snapshot logs.
* Supplier purchase orders, PO placement timestamps, and actual receiving timestamps.
* Product master hierarchy, cost of goods sold ($COGS$), and retail selling prices.
* Modeling of unconstrained demand during stockout periods using in-stock baseline counterfactuals.

### Excluded from Analysis Scope
* **Intra-Store Transfers:** Lateral stock transfers between store locations are excluded; all stores replenish independently from vendors.
* **Multi-Echelon DC Buffering:** Central regional distribution center (DC) cross-docking dynamics are excluded.
* **Promotional Markdown Optimization:** Elasticity modeling around temporary promotional discounting is excluded.
* **Customer Brand Substitution:** Cross-elasticity behavior (e.g., customer buying Brand B when Brand A is out of stock) is not modeled.

---

## 7. Project Success Criteria
1. **Data Governance & Integrity:** Documented row-level reconciliation from raw source rows to cleaned staging and modeled aggregates, with zero unhandled anomalies.
2. **Methodological Defensibility:** Safety stock and reorder point formulas strictly incorporate both demand variance and supplier lead-time variance.
3. **Operational Utility:** Delivery of a 3-page interactive Power BI dashboard featuring clear visual hierarchy and real-time replenishment queues.
4. **Simulation Rigor:** Clear policy backtest demonstrating holding cost versus service-level trade-offs across $90\%$, $95\%$, and $99\%$ CSL without data leakage.

---

## 8. Explicit Spoilage Module Disclosure
> [!IMPORTANT]
> **Synthetic Perishable Module Disclosure:**  
> Spoilage is an optional synthetic module and is **not** an observed source-data metric. Spoilage is not observed in the source data. It is simulated using shelf-life and waste-rate assumptions to demonstrate how perishable inventory policy could be extended.
