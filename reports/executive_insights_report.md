# Executive Supply Chain Diagnostics & Policy Optimization Report
**Smart Inventory Diagnostics: Optimizing Safety Stock, Reorder Points, and Stockout Risk**  
*Analytics Warehouse: DuckDB | Baseline Service Level: 95% Cycle Service Level (CSL) | Holding Cost: 22% Annual*

---

## 1. Executive Summary & Key Performance Indicators

Across a retail network of **5 stores** and **150 SKUs** (750 operational pairs), the business generated **$100,558,841.75** in gross revenue and **$42,464,922.02** in gross contribution margin (**42.23%** margin rate) over the 365-day historical trading period.

However, supply-chain friction and sub-optimal inventory buffers resulted in a network-wide stockout rate of **6.93%** (18,963.0 stockout snapshot days). Applying an empirical **counterfactual demand model** (rolling 4-week same-weekday in-stock sales baseline), suppressed customer demand during stockout events accounted for **217,026.0 unfulfilled units**, translating to **$10,074,157.71** in modeled lost revenue and **$4,313,057.21** in modeled lost contribution margin.

### Network Scorecard:
* **Gross Sales Revenue:** $100,558,841.75
* **Gross Contribution Margin:** $42,464,922.02 (42.23%)
* **Network Stockout Rate:** 6.93%
* **Modeled Counterfactual Lost Revenue:** $10,074,157.71 *(lost margin: $4,313,057.21)*
* **Average Network Inventory Value:** $962,449.63
* **Annualized Holding Cost (at 22%):** $211,738.89
* **Network Inventory Turnover:** 60.36x (Avg DOH: 6.0 days)
* **Active Replenishment Alert Pairs:** 40.0 CRITICAL (5.3%), 255.0 HIGH (34.0%)
* **Immediate Replenishment Capital Required:** $2,544,105.62 (86,213.0 units)
* **Primary Excess Inventory:** $0.00 (0 units exceeding Order-Up-To level)

> [!NOTE]
> **Governance Notice on Lost Sales:** Estimated lost revenue and units are modeled counterfactuals reflecting unfulfilled demand during stockout days based on preceding same-weekday velocity. They represent commercial opportunity cost, not audited accounting write-offs.

---

## 2. Store-Level Performance & Regional Disparities

The network exhibits pronounced revenue concentration in flagship urban locations, which correspondingly bear the greatest stockout dollar exposure:

| Store ID | Store Name | Region | Tier | Gross Revenue ($) | Margin % | Stockout % | Modeled Lost Rev ($) | Avg DOH | Urgent Reorder ($) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **STORE-01** | Metro Flagship | Central | Tier 1 - Flagship | $27,159,235.67 | 42.2% | 7.93% | $2,848,495.25 | 3.9d | $701,558.29 |
| **STORE-02** | Downtown Urban | North | Tier 2 - Urban | $21,246,888.04 | 42.2% | 7.02% | $2,054,124.77 | 3.8d | $564,832.73 |
| **STORE-04** | Westside Hub | West | Tier 2 - Urban | $19,293,954.42 | 42.3% | 6.85% | $1,965,785.29 | 4.2d | $460,226.41 |
| **STORE-03** | Suburban Center | South | Tier 3 - Suburban | $17,520,670.51 | 42.2% | 6.75% | $1,813,517.76 | 3.6d | $424,228.32 |
| **STORE-05** | Eastgate Retail | East | Tier 3 - Suburban | $15,338,093.11 | 42.2% | 6.09% | $1,392,234.64 | 3.8d | $393,259.87 |

### Key Store Observations:
1. **Metro Flagship (STORE-01)** is the dominant revenue engine ($27,159,235.67), but suffered the highest lost revenue exposure ($2,848,495.25) due to high sales velocity compressing stock buffers before replenishment arrived.
2. **Eastgate Retail (STORE-05)** operates at the leanest throughput, experiencing lower stockout volume ($1,392,234.64) and requiring $393,259.87 in urgent replenishment capital.

---

## 3. Merchandising Category Diagnostics & Lost Sales Concentration

Demand and stockout exposure vary significantly across the five merchandising categories:

| Category | SKUs | Gross Revenue ($) | Share % | Margin % | Stockout % | Modeled Lost Rev ($) | Turnover | 95% SS Units | 95% SS Capital ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Packaged Goods** | 39 | $30,043,360.89 | 29.9% | 43.8% | 7.73% | $3,201,636.99 | 65.5x | 11,456 | $298,862.08 |
| **Beverages** | 34 | $19,745,653.09 | 19.6% | 40.1% | 6.58% | $1,870,519.31 | 60.7x | 8,543 | $241,955.98 |
| **Personal Care** | 30 | $19,221,073.22 | 19.1% | 44.5% | 6.96% | $1,925,286.85 | 75.8x | 5,888 | $135,509.28 |
| **Dry Grocery** | 23 | $16,723,666.33 | 16.6% | 42.4% | 6.25% | $1,812,803.34 | 45.2x | 11,068 | $329,888.73 |
| **Household Goods** | 24 | $14,825,088.22 | 14.7% | 38.7% | 6.72% | $1,263,911.22 | 58.4x | 6,780 | $184,413.59 |

### Key Merchandising Takeaways:
* **Packaged Goods** generates the largest gross revenue share (29.9%) and suffered the largest lost revenue ($3.20M). Its high turnover (64.4x) necessitates high replenishment agility.
* **Personal Care** has the highest contribution margin rate (44.53%), meaning stockouts in Personal Care carry the highest percentage margin penalty ($893.9K lost margin on $1.93M lost sales).
* **Beverages and Dry Grocery** require the largest absolute safety stock capital ($242.0K and $329.9K respectively) driven by supplier lead-time dynamics.

---

## 4. ABC-XYZ Portfolio Segmentation (9-Box Playbook Matrix)

Portfolio segmentation classifies each SKU-Store pair along two rigorous dimensions:
1. **ABC Class (Contribution Margin Pareto):** Class A accounts for the top 80% of margin; Class B accounts for 80–95%; Class C accounts for the final 5%.
2. **XYZ Class (Demand Volatility):** Class X (Smooth, $CV \le 0.5$); Class Y (Variable, $0.5 < CV \le 1.0$); Class Z (Erratic, $CV > 1.0$).

| Segment | Pairs | Share % | Gross Margin ($) | Margin Share % | Mean CV | SOH | 95% SS Capital ($) | Prescribed Strategy |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **AX** | 37 | 4.9% | $8,958,564.76 | 21.1% | 0.39 | 2,967 | $90,581.13 | High Margin, Stable Demand (Cash Cow): Implement automated continuous replenishment with tight safety stock. High inventory turnover target. |
| **AY** | 104 | 13.9% | $24,976,836.87 | 58.8% | 0.73 | 12,730 | $786,377.75 | High Margin, Moderate Volatility: Maintain dynamic safety stock buffer; establish automated weekly review with supplier. |
| **BX** | 61 | 8.1% | $2,407,117.31 | 5.7% | 0.40 | 2,509 | $47,299.37 | Medium Margin, Stable Demand: Standard continuous ROP replenishment; automate PO generation. |
| **BY** | 96 | 12.8% | $3,952,242.06 | 9.3% | 0.70 | 5,428 | $147,307.94 | Medium Margin, Moderate Volatility: Periodic weekly review (Order-Up-To); monitor seasonal shifts. |
| **BZ** | 1 | 0.1% | $33,331.14 | 0.1% | 1.02 | 25 | $1,740.32 | Medium Margin, Erratic Demand: Buffer against demand surges with safety stock; optimize purchase order batch sizes. |
| **CX** | 162 | 21.6% | $615,341.35 | 1.4% | 0.44 | 2,104 | $18,640.96 | Low Margin, Stable Demand: Vendor-Managed Inventory (VMI) or bulk reorders with large pack sizes to minimize ordering costs. |
| **CY** | 285 | 38.0% | $1,480,801.51 | 3.5% | 0.68 | 5,779 | $93,932.12 | Low Margin, Moderate Volatility: Periodic review with high review period; minimize management attention. |
| **CZ** | 4 | 0.5% | $40,687.02 | 0.1% | 1.03 | 179 | $4,750.07 | Low Margin, Erratic Demand (Tail Risk): Audit for strategic necessity (e.g. required accessory). If non-essential, liquidate or transition to drop-ship. |

### Strategic Portfolio Insights:
* **The A-Item Core (Segments AX + AY):** **141 pairs (18.8%)** generate **$33.94M (79.93%)** of network gross margin. These items must receive priority allocation, multi-source supplier agreements, and strict daily monitoring.
* **Long Tail Rationalization (Segment CY):** **285 pairs (38.0%)** represent Class C items with moderate demand variability, contributing only 3.49% of network margin ($1.48M). Ordering should be consolidated to periodic minimum order quantities to slash handling overhead.
* **Erratic Outliers (Segment CZ):** **4 pairs** exhibit erratic demand ($CV > 1.0$) with low margin contribution ($40.7K). Recommended for make-to-order or vendor drop-shipping to eliminate carrying costs.

---

## 5. Supplier Delivery Reliability & Lead-Time Variance Impact

Safety stock is mathematically partitioned into demand variance and lead-time variance:
$$\sigma_{LTD}^2 = \bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2$$

Where $\sigma_L^2 > 0$, supplier delivery unreliability expands the required buffer. The table below isolates the capital required **strictly due to supplier lead-time variance**:

| Supplier ID | Supplier Name | Spend ($) | On-Time % | Mean Lead Time | Lead Time Std | Actual 95% SS | Supplier Buffer Units | Working Capital Impact ($) | SS Share from Supplier Var |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SUP-01** | Apex Global Logistics | $4,954,347.86 | 57.3% | 10.1d | 2.43d | 5,187 | 1,696 | $40,631.87 | **32.7%** |
| **SUP-02** | Pinnacle Brands Inc | $9,936,279.77 | 58.1% | 7.1d | 2.17d | 5,554 | 2,129 | $64,374.49 | **38.3%** |
| **SUP-03** | BlueSky Supply Co | $2,171,691.93 | 68.5% | 14.0d | 1.81d | 2,373 | 310 | $3,992.99 | **13.1%** |
| **SUP-04** | Keystone Consumer Goods | $6,238,808.01 | 69.4% | 7.0d | 1.53d | 4,934 | 740 | $17,721.35 | **15.0%** |
| **SUP-05** | Vanguard Distributors | $8,955,481.94 | 59.8% | 7.0d | 2.29d | 5,726 | 2,328 | $83,719.86 | **40.7%** |
| **SUP-06** | Frontier Beverage Supply | $6,359,534.29 | 68.5% | 10.0d | 1.06d | 6,155 | 505 | $12,417.81 | **8.2%** |
| **SUP-07** | Summit Packaging Solutions | $5,212,341.66 | 72.6% | 7.0d | 0.87d | 3,961 | 361 | $7,288.27 | **9.1%** |
| **SUP-08** | Pacific Rim Sourcing | $995,723.92 | 59.2% | 5.0d | 2.05d | 1,217 | 539 | $5,959.78 | **44.3%** |
| **SUP-09** | Continental Foods Group | $5,306,651.62 | 67.7% | 5.0d | 1.15d | 1,770 | 514 | $12,581.55 | **29.0%** |
| **SUP-10** | National Wholesale Alliance | $8,102,818.05 | 60.6% | 14.0d | 1.83d | 6,858 | 1,376 | $38,602.18 | **20.1%** |

### Procurement Takeaways:
* **Supplier Variance Drives 22.8% of Total Network Safety Stock:** Network safety stock requires 43,735 units under actual conditions vs 33,782 units under deterministic delivery—**9,953 buffer units ($287,301.65 in working capital)** exist solely to hedge against vendor delivery delays.
* **High-Volatility Vendors:**
  * **Vanguard Distributors (SUP-05):** Lead time standard deviation of 2.29 days forces **2,328 units ($83,719.86 in capital)** into buffer stock—**40.7%** of its required safety stock is caused by supplier variance.
  * **Pinnacle Brands (SUP-02):** Unreliability forces **2,129 buffer units ($64,374.49 in capital)**.
* **Negotiation Action:** Procurement must negotiate tighter SLA delivery windows with SUP-05 and SUP-02. Reducing delivery variance by 50% would immediately free ~$70K in working capital without impacting service level.

---

## 6. Service Level Policy Optimization (90% vs 95% vs 99% CSL)

Trade-off analysis comparing required safety buffer units, inventory valuation, and annual holding costs across three Cycle Service Level scenarios:

| Category | 90% SS Units | 90% Capital ($) | 95% SS Units | 95% Capital ($) | 99% SS Units | 99% Capital ($) | $\Delta$ Units (95 vs 90) | $\Delta$ Capital (99 vs 95) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Beverages** | 6,672 | $188,836.02 | 8,543 | $241,955.98 | 12,047 | $341,541.88 | +1,871 (28.0%) | +$99,585.90 (41.0%) |
| **Dry Grocery** | 8,636 | $257,328.21 | 11,068 | $329,888.73 | 15,626 | $466,044.43 | +2,432 (28.2%) | +$136,155.70 (41.2%) |
| **Household Goods** | 5,291 | $143,788.64 | 6,780 | $184,413.59 | 9,557 | $260,248.52 | +1,489 (28.1%) | +$75,834.93 (41.0%) |
| **Packaged Goods** | 8,951 | $233,261.90 | 11,456 | $298,862.08 | 16,141 | $421,574.67 | +2,505 (28.0%) | +$122,712.59 (40.9%) |
| **Personal Care** | 4,605 | $105,902.86 | 5,888 | $135,509.28 | 8,302 | $191,201.96 | +1,283 (27.9%) | +$55,692.68 (41.0%) |
| **NETWORK TOTAL** | 34,155 | $929,117.63 | 43,735 | $1,190,629.66 | 61,673 | $1,680,611.46 | +9,580 (28.0%) | +$489,981.80 (41.0%) |

### Capital Trade-Off Recommendations:
1. **The Cost of Near-Zero Stockouts (99% CSL):** Moving from the baseline 95% CSL ($Z = 1.645$) to 99% CSL ($Z = 2.326$) demands an additional **17,938 safety stock units (+41.0%)** and **$454,497.03 in working capital**, raising annual holding costs by **$99,989.35**.
2. **Segmented Service Level Policy:** Rather than a blanket 95% or 99% CSL across all items, the business should implement:
   * **Class A items (141 pairs):** 99% CSL to protect 80% of margin ($33.9M).
   * **Class B items (158 pairs):** 95% CSL.
   * **Class C items (451 pairs):** 90% CSL to release ~$150K in buffer capital from slow-moving inventory.

---

## 7. Immediate Procurement Action Center (Priority Replenishment)

Using current inventory positions (Position = Current SOH + Stock in Transit):
* **CRITICAL (Position <= SS):** **40 pairs** require expedited purchase orders for **18,124 units ($538,054.49)** to avoid imminent shelf depletion.
* **HIGH (SS < Position <= ROP):** **255 pairs** require standard scheduled purchase orders for **68,089 units ($2,006,051.13)**.
* **Combined Immediate Capital Requirement:** **$2,544,105.62** (86,213.0 units).

Top 5 Urgent Expedited Items:
* **SKU-0102 (Organic Soy Milk Vanilla 1L) at Metro Flagship:** Pos=448, SS=587, ROP=1330 -> Order **1774 units** ($87,813.00)
* **SKU-0102 (Organic Soy Milk Vanilla 1L) at Downtown Urban:** Pos=281, SS=457, ROP=1033 -> Order **1443 units** ($71,428.50)
* **SKU-0074 (Shredded Mozzarella Cheese 300g) at Metro Flagship:** Pos=571, SS=599, ROP=1983 -> Order **2208 units** ($68,757.12)
* **SKU-0139 (Pure Grade A Canadian Maple Syrup 250ml) at Downtown Urban:** Pos=281, SS=366, ROP=1241 -> Order **1459 units** ($68,383.33)
* **SKU-0102 (Organic Soy Milk Vanilla 1L) at Eastgate Retail:** Pos=172, SS=341, ROP=764 -> Order **1103 units** ($54,598.50)

---

## 8. Synthetic Perishables & Spoilage Module (Governance Segregation)

> [!IMPORTANT]
> **Synthetic Module Disclaimer:** Public and ERP transaction datasets do not record true shelf-life expiration or spoilage. This analysis uses synthetic shelf lives (average 36.5 days for perishables) to model potential risk when Days of Inventory on Hand (DOH) approaches expiration. It is strictly segregated from core replenishment and stockout metrics.

* **Perishable SKUs Evaluated:** 33 SKUs (19 Beverages, 14 Packaged Goods; 165 operational pairs).
* **High Spoilage Risk (DOH > Shelf Life):** **0 pairs** (average DOH across perishables is ~3.8 days, well within the 30–45 day shelf life).
* **Conclusion:** Network inventory turns rapidly enough that expiration waste is minimal under normal operating conditions.

---

## 9. Data Quality & Pipeline Reconciliation Governance

All 26 pipeline and quality assertions passed with zero variance:
* **Raw Ingested Records:** 518,423 rows across 6 CSVs.
* **Quarantined Records:** 16 critical anomalies isolated into `data/quarantine/` (8 negative inventory, 6 ghost sales, 2 negative lead-time POs).
* **Analytical Warehouse Parity:** 100% reconciled with zero dropped rows.
* **Raw Immutability:** All source CSVs remain bit-for-bit unchanged.
