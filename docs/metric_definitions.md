# 📐 Metric Definitions & Mathematical Framework
## Smart Inventory Diagnostics: Retail Supply Chain Analytics

This document establishes the official definitions, computational formulas, execution grains, business interpretations, required schema fields, edge-case limitations, and worked numerical examples for all 32 metrics used in the Smart Inventory Diagnostics project.

> [!NOTE]
> **Core Counterfactual Disclaimer:**  
> Estimated lost revenue is a modeled counterfactual based on expected unconstrained demand during stockout periods. It is not confirmed realized revenue loss.

---

### 1. Daily Fulfilled Demand
* **Definition:** The quantity of units successfully sold and rung up through the point-of-sale register (or fulfilled and dispatched) on a specific trading date.
* **Formula:**  
  $$\text{Fulfilled Demand}_{i, s, t} = \sum \text{units\_sold}$$
* **Calculation Grain:** `sku_id` ($i$) × `store_id` ($s$) × `date` ($t$)
* **Business Interpretation:** Historical realized sales volume. Reflects sales constrained by available physical stock.
* **Data Fields Required:** `sales_transactions.units_fulfilled`, `sales_transactions.transaction_date`, `sales_transactions.sku_id`, `sales_transactions.store_id`
* **Known Limitations:** In stockout conditions, fulfilled demand drops to zero regardless of customer purchase intent.
* **Example:** 12 cartons of milk sold at Store 01 on March 15. $\text{Fulfilled Demand} = 12\text{ units}$.

---

### 2. Daily Requested Demand
* **Definition:** The total quantity of units that customers attempted to purchase on a given trading date (fulfilled units plus immediate unfulfilled requests recorded by digital orders or store rainchecks).
* **Formula:**  
  $$\text{Requested Demand}_{i, s, t} = \text{Fulfilled Units}_{i, s, t} + \text{Immediate Unfulfilled Requests}_{i, s, t}$$
* **Calculation Grain:** `sku_id` ($i$) × `store_id` ($s$) × `date` ($t$)
* **Business Interpretation:** True customer demand before supply-side inventory constraints occur.
* **Data Fields Required:** `sales_transactions.units_demanded`
* **Known Limitations:** In physical brick-and-mortar retail, unfulfilled demand is rarely recorded directly at the register because customers simply leave empty-handed.
* **Example:** 10 customers bought 1 unit each; 2 customers asked for out-of-stock units and were turned away. $\text{Requested Demand} = 10 + 2 = 12\text{ units}$.

---

### 3. Stock-on-Hand (SOH)
* **Definition:** The physical, sellable quantity of units present on store shelves and backroom storage at the end of the trading day.
* **Formula:**  
  $$\text{SOH}_{i, s, t} = \text{Closing Physical Unit Balance}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Current physical inventory available for customer fulfillment.
* **Data Fields Required:** `inventory_snapshots.stock_on_hand`
* **Known Limitations:** Scan-latency, shrinkage, misplacement, and theft can cause phantom inventory where recorded SOH differs from physical reality.
* **Example:** End-of-day count shows 45 cereal boxes in Store 04. $\text{SOH} = 45\text{ units}$.

---

### 4. Stock-in-Transit (SIT)
* **Definition:** The quantity of units ordered from a supplier that has been shipped or confirmed on an active purchase order but has not yet arrived and been received into store inventory.
* **Formula:**  
  $$\text{SIT}_{i, s, t} = \sum_{\text{open POs}} \text{ordered\_quantity}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Replenishment pipeline volume committed to arriving in future days.
* **Data Fields Required:** `supplier_orders.order_quantity`, `supplier_orders.status`
* **Known Limitations:** Does not account for supplier short-shipments until goods are physically intake-scanned.
* **Example:** A purchase order of 100 shampoo bottles was dispatched on Tuesday and is due Thursday. $\text{SIT} = 100\text{ units}$.

---

### 5. Inventory Position
* **Definition:** The total effective inventory available to the planning system, encompassing physical stock plus pipeline orders minus unfulfilled customer backorders.
* **Formula:**  
  $$\text{Inventory Position} = \text{Stock-on-Hand} + \text{Stock-in-Transit} - \text{Backorders}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** The true number evaluated against the Reorder Point (ROP) to decide whether to issue a new replenishment order.
* **Data Fields Required:** `stock_on_hand`, `stock_in_transit`, `backorders` (assumed 0 in retail walk-away environments)
* **Known Limitations:** If transit times are erratic, a high inventory position can mask imminent shelf stockouts.
* **Example:** $\text{SOH} = 15$, $\text{SIT} = 50$, $\text{Backorders} = 0$. $\text{Inventory Position} = 15 + 50 - 0 = 65\text{ units}$.

---

### 6. Active Trading Day
* **Definition:** A boolean operational flag indicating whether a specific store location was open for retail business and customer transactions on a given calendar date.
* **Formula:**  
  $$\text{Active Trading Day}_{s, t} = \begin{cases} 1 & \text{if store is open for trade} \\ 0 & \text{if store is closed (holiday, weather, closure)} \end{cases}$$
* **Calculation Grain:** `store_id` × `date`
* **Business Interpretation:** Isolates operational retail days from planned closures, preventing false stockout or zero-demand flags.
* **Data Fields Required:** `stores.is_open_flag`, `calendar.is_holiday`
* **Known Limitations:** Emergency mid-day closures require intra-day store operating logs.
* **Example:** Store 02 is closed on Christmas Day. $\text{Active Trading Day} = 0$.

---

### 7. Stockout Day
* **Definition:** A condition on an active trading day where beginning or intra-day stock-on-hand drops to zero or below, preventing customer fulfillment.
* **Formula:**  
  $$\text{Stockout Day}_{i, s, t} = \begin{cases} 1 & \text{if } \text{SOH}_{i, s, t} \le 0 \text{ AND } \text{Active Trading Day}_{s, t} = 1 \\ 0 & \text{otherwise} \end{cases}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Out-of-stock event on the retail shelf.
* **Data Fields Required:** `inventory_snapshots.stock_on_hand`, `stores.is_open_flag`
* **Known Limitations:** A stockout occurring at 7:00 PM will still show daily sales from earlier in the afternoon.
* **Example:** Store 03 has $0$ units of pasta on a trading Saturday. $\text{Stockout Day} = 1$.

---

### 8. Expected Daily Demand ($\widehat{D}_t$)
* **Definition:** A modeled counterfactual estimate of unconstrained customer purchasing intent during periods when the item was out of stock.
* **Formula:**  
  $$\widehat{D}_{i, s, t} = \frac{1}{4} \sum_{k=1}^{4} \text{Fulfilled Demand}_{i, s, t - 7k} \quad (\text{evaluated over preceding in-stock same weekdays})$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Answers the counterfactual question: *"How many units would customers have bought today if the shelf were fully stocked?"*
* **Data Fields Required:** `sales_transactions.units_fulfilled`, `inventory_snapshots.is_stockout_flag`
* **Known Limitations:** Does not account for broader promotional spikes, holiday anomalies, or intra-store brand substitution.
* **Example:** For a stockout on Friday, the sales on the previous 4 in-stock Fridays were 18, 22, 20, and 20. $\widehat{D} = \frac{18 + 22 + 20 + 20}{4} = 20\text{ units}$.

---

### 9. Estimated Lost Units
* **Definition:** The estimated quantity of customer demand that went unfulfilled specifically due to an out-of-stock condition.
* **Formula:**  
  $$\text{Estimated Lost Units}_{i, s, t} = \begin{cases} \max(0, \widehat{D}_{i, s, t} - \text{Fulfilled Units}_{i, s, t}) & \text{if } \text{Stockout Day} = 1 \\ 0 & \text{otherwise} \end{cases}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Physical volume of unserved customer demand caused by supply chain replenishment failure.
* **Data Fields Required:** `Expected Daily Demand`, `units_fulfilled`, `is_stockout_flag`
* **Known Limitations:** Represents an unobservable estimate; cannot be verified by register receipts.
* **Example:** On a stockout day, expected demand $\widehat{D} = 20$ units, but only $3$ units were sold before stock hit zero. $\text{Lost Units} = 20 - 3 = 17\text{ units}$.

---

### 10. Estimated Lost Revenue
* **Definition:** The modeled top-line monetary loss resulting from unfulfilled customer demand on stockout days.
* **Formula:**  
  $$\text{Estimated Lost Revenue}_{i, s, t} = \text{Estimated Lost Units}_{i, s, t} \times \text{Unit Selling Price}_{i}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Top-line revenue leakage estimate (*modeled counterfactual*).
* **Data Fields Required:** `Estimated Lost Units`, `products.unit_selling_price`
* **Known Limitations:** Assumes customer walked away rather than substituting an alternative brand or buying later.
* **Example:** 17 estimated lost units at a selling price of $\$5.00$. $\text{Lost Revenue} = 17 \times \$5.00 = \$85.00$.

---

### 11. Inventory Value
* **Definition:** The total balance-sheet monetary value of inventory currently held in physical stock, valued at acquisition cost.
* **Formula:**  
  $$\text{Inventory Value}_{i, s, t} = \text{Stock-on-Hand}_{i, s, t} \times \text{Unit Cost}_{i}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Working capital committed to inventory on the balance sheet.
* **Data Fields Required:** `inventory_snapshots.stock_on_hand`, `products.unit_cost`
* **Known Limitations:** Assumes FIFO/standard replacement cost; does not reflect inventory write-downs.
* **Example:** 100 units on hand with a unit cost of $\$8.00$. $\text{Inventory Value} = 100 \times \$8.00 = \$800.00$.

---

### 12. Unit-Based Days of Inventory on Hand (DOH - Units)
* **Definition:** The number of days the current physical stock balance will last at the current average daily unit sales burn rate.
* **Formula:**  
  $$\text{DOH}_{\text{units}} = \frac{\text{Current Stock-on-Hand (Units)}}{\text{Average Daily Demand (Units/Day)}}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** **Primary Operational Metric:** Measures shelf capacity and days until physical stockout under normal demand.
* **Data Fields Required:** `stock_on_hand`, `average_daily_demand`
* **Known Limitations:** Distorted if daily demand is intermittent or zero; does not permit meaningful aggregation across products of differing unit sizes (e.g., TVs vs. packs of gum).
* **Example:** 60 units in stock with an average demand of 3 units/day. $\text{DOH}_{\text{units}} = \frac{60}{3} = 20\text{ days}$.

---

### 13. Value-Based Days of Inventory on Hand (DOH - Value)
* **Definition:** The financial velocity metric measuring how many days of inventory investment are tied up relative to the daily Cost of Goods Sold.
* **Formula:**  
  $$\text{DOH}_{\text{value}} = \frac{\text{Current Inventory Value (\$)}}{\text{Average Daily COGS (\$)}} = \frac{\text{SOH} \times \text{Unit Cost}}{\text{Daily Demand Units} \times \text{Unit Cost}}$$
* **Calculation Grain:** `sku_id` × `store_id` or Store / Category / Total Company
* **Business Interpretation:** **Primary Financial Metric:** Allows valid portfolio working capital comparison across diverse categories and price tiers. *(Never mix units and currency).*
* **Data Fields Required:** `Inventory Value`, `Average Daily COGS`
* **Known Limitations:** Highly sensitive to recent COGS swings or supplier price renegotiations.
* **Example:** Store inventory value is $\$120,000$ and average daily COGS is $\$4,000$. $\text{DOH}_{\text{value}} = \frac{\$120,000}{\$4,000} = 30\text{ days}$.

---

### 14. Inventory Turnover Ratio
* **Definition:** The number of times a company's average inventory is sold and replaced over a full operating year.
* **Formula:**  
  $$\text{Inventory Turnover} = \frac{\text{Annual Cost of Goods Sold (COGS)}}{\text{Average Inventory Value across Year}}$$
* **Calculation Grain:** `sku_id` × `store_id` or Store / Total Company
* **Business Interpretation:** Primary balance-sheet efficiency measure. High turnover indicates agile stock management; low turnover signals overstocking.
* **Data Fields Required:** `Annual COGS`, `Average Inventory Value`
* **Known Limitations:** Can appear artificially high if stockouts are frequent (low average inventory).
* **Example:** Annual COGS is $\$500,000$ and average inventory value is $\$100,000$. $\text{Turnover} = \frac{\$500,000}{\$100,000} = 5.0\times\text{ per year}$.

---

### 15. Average Inventory Value
* **Definition:** The arithmetic mean of the closing daily inventory value over a defined evaluation period (e.g., 365 days).
* **Formula:**  
  $$\text{Average Inventory Value} = \frac{1}{T} \sum_{t=1}^{T} (\text{SOH}_{t} \times \text{Unit Cost})$$
* **Calculation Grain:** `sku_id` × `store_id` (over time period $T$)
* **Business Interpretation:** Baseline capital tied up in inventory across the annual operating cycle.
* **Data Fields Required:** Daily `Inventory Value`
* **Known Limitations:** Can mask severe cyclical swings (e.g., massive holiday surge followed by summer trough).
* **Example:** Sum of daily inventory values across 365 days is $\$36,500,000$. $\text{Avg Inventory Value} = \frac{\$36,500,000}{365} = \$100,000$.

---

### 16. Annual COGS (Cost of Goods Sold)
* **Definition:** The direct acquisition cost of all inventory units sold during a 365-day operating period.
* **Formula:**  
  $$\text{Annual COGS} = \sum_{t=1}^{365} (\text{Fulfilled Units}_{t} \times \text{Unit Cost})$$
* **Calculation Grain:** `sku_id` × `store_id` or Store / Total Company
* **Business Interpretation:** Baseline cost of product movement, used to evaluate capital velocity and turnover.
* **Data Fields Required:** `sales_transactions.units_fulfilled`, `products.unit_cost`
* **Known Limitations:** Excludes operational freight, scrap, and shrinkage unless explicitly integrated.
* **Example:** 50,000 units sold over the year with a unit cost of $\$10.00$. $\text{Annual COGS} = 50,000 \times \$10.00 = \$500,000$.

---

### 17. Holding-Cost Rate ($h$)
* **Definition:** The annual cost of holding inventory expressed as a percentage of the total unit cost.
* **Component Breakdown:**
  * **Cost of Capital:** $10.0\%$ (opportunity cost of tied-up working capital)
  * **Storage & Warehousing:** $4.0\%$ (rent, utilities, handling labor)
  * **Insurance & Taxes:** $2.0\%$ (property taxes and casualty insurance)
  * **Obsolescence & Shrinkage:** $6.0\%$ (damage, theft, product aging)
  * **Total Annual Holding-Cost Rate ($h$):** $\mathbf{22.0\% \text{ per year}}$ ($\approx 0.0603\%$ daily)
* **Calculation Grain:** Company-wide financial parameter
* **Business Interpretation:** Financial carrying penalty for holding excess inventory.
* **Data Fields Required:** Executive financial assumption
* **Known Limitations:** Fixed rate may underestimate holding costs for refrigeration or hazardous storage.
* **Example:** Standard retail annual carrying rate $h = 0.22$. Daily holding cost per $\$100$ of inventory is $\$100 \times \frac{0.22}{365} \approx \$0.0603$.

---

### 18. Holding Cost (Carrying Cost)
* **Definition:** The total monetary expense incurred by the business to store, insure, finance, and maintain inventory over an evaluation period.
* **Formula:**  
  $$\text{Holding Cost} = \text{Average Inventory Value} \times h$$
* **Calculation Grain:** `sku_id` × `store_id` (Annualized)
* **Business Interpretation:** Direct balance-sheet drag of idle working capital.
* **Data Fields Required:** `Average Inventory Value`, `Holding-Cost Rate (h)`
* **Known Limitations:** Does not account for discrete warehouse step-costs.
* **Example:** Average inventory value is $\$100,000$ and $h = 0.22$. $\text{Holding Cost} = \$100,000 \times 0.22 = \$22,000\text{/year}$.

---

### 19. Contribution Margin
* **Definition:** The absolute dollar amount each sold unit contributes toward covering fixed operational costs and generating corporate profit.
* **Formula:**  
  $$\text{Contribution Margin} = \text{Unit Selling Price} - \text{Unit Cost}$$
  $$\text{Margin \%} = \frac{\text{Unit Selling Price} - \text{Unit Cost}}{\text{Unit Selling Price}}$$
* **Calculation Grain:** `sku_id`
* **Business Interpretation:** **Confirmed Core Metric for Prioritization:** Used instead of gross revenue for ABC classification because high-revenue zero-margin products tie up working capital without delivering corporate net profit.
* **Data Fields Required:** `products.unit_selling_price`, `products.unit_cost`
* **Known Limitations:** Excludes variable packaging and transaction processing fees.
* **Example:** Selling price is $\$15.00$, unit cost is $\$9.00$. $\text{Contribution Margin} = \$15.00 - \$9.00 = \$6.00$ ($40\%$).

---

### 20. ABC Classification
* **Definition:** Pareto segmentation classifying products by their total annual cumulative **Contribution Margin**.
* **Rationale for Basis:** Contribution margin is explicitly chosen over gross revenue because items with high revenue but near-zero margin tie up significant warehouse space and working capital without generating profit.
* **Formula:**  
  $$\text{Cumulative Margin \%} = \frac{\sum_{j=1}^{k} \text{Annual Contribution Margin}_j}{\text{Total Portfolio Contribution Margin}}$$
  $$\text{Class} = \begin{cases} A & \text{Top 80\% of cumulative contribution margin} \\ B & \text{Next 15\% of cumulative contribution margin (80\% to 95\%)} \\ C & \text{Bottom 5\% of cumulative contribution margin (95\% to 100\%)} \end{cases}$$
* **Calculation Grain:** `sku_id` × `store_id` (Annualized)
* **Business Interpretation:** Identifies profit drivers ($A$) requiring highest replenishment focus versus long-tail items ($C$).
* **Data Fields Required:** `Annual Fulfilled Demand`, `Contribution Margin`
* **Known Limitations:** New products with limited sales history may be initially categorized as $C$.
* **Example:** Top 20 SKUs generate $\$800,000$ of $\$1,000,000$ total margin $\rightarrow$ Classified as **A**.

---

### 21. Coefficient of Variation ($CV$)
* **Definition:** A normalized statistical measure of demand volatility, calculated as the ratio of standard deviation to the mean.
* **Formula:**  
  $$CV = \frac{\sigma_D}{\bar{D}} = \frac{\sqrt{\frac{1}{N-1} \sum_{t=1}^{N} (D_t - \bar{D})^2}}{\frac{1}{N} \sum_{t=1}^{N} D_t} \quad (\text{calculated across in-stock trading days})$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Standardizes demand predictability independent of sales volume.
* **Data Fields Required:** Daily in-stock `Fulfilled Demand`
* **Known Limitations:** Explodes toward infinity as mean demand ($\bar{D}$) approaches zero (intermittent items).
* **Example:** $\bar{D} = 10\text{ units/day}$, $\sigma_D = 3\text{ units/day}$. $CV = \frac{3}{10} = 0.30$.

---

### 22. XYZ Classification
* **Definition:** Demand stability segmentation grouping SKUs by their demand predictability ($CV$).
* **Initial Thresholds:**  
  $$\text{Class} = \begin{cases} X & \text{if } CV \le 0.5 \quad (\text{Stable, highly predictable demand}) \\ Y & \text{if } 0.5 < CV \le 1.0 \quad (\text{Moderate, fluctuating demand}) \\ Z & \text{if } CV > 1.0 \quad (\text{Volatile, erratic, or intermittent demand}) \end{cases}$$
* **Mandatory Empirical Validation:** In Phase 4, these initial cutoffs ($0.5$ and $1.0$) **must and will be validated against the empirical demand distribution percentiles** of the actual dataset to ensure balanced, operationally sound segment boundaries.
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Determines whether replenishment should be automated ($X$) or buffered with high safety stock ($Z$).
* **Data Fields Required:** `Coefficient of Variation (CV)`
* **Example:** $CV = 0.30 \rightarrow \mathbf{X}$; $CV = 0.75 \rightarrow \mathbf{Y}$; $CV = 1.45 \rightarrow \mathbf{Z}$.

---

### 23. Cycle Service Level (CSL)
* **Definition:** The target statistical probability that customer demand will not exceed available stock during a replenishment cycle.
* **Formula:**  
  $$\text{CSL} = P(\text{Demand during lead time} \le \text{Reorder Point})$$
* **Calculation Grain:** Policy parameter per SKU segment
* **Business Interpretation:** Management's service commitment (e.g., $95\%$ CSL means a $5\%$ stockout risk per replenishment cycle).
* **Data Fields Required:** Policy selection ($90\%$, $95\%$, $99\%$)
* **Example:** Management selects a $95\%$ service level target. $\text{CSL} = 0.95$.

---

### 24. Z-Score (Service Factor)
* **Definition:** The number of standard deviations from the mean corresponding to a specified Cycle Service Level under a standard normal distribution.
* **Formula:**  
  $$Z = \Phi^{-1}(\text{CSL})$$
* **Standard Values:**  
  * $\text{CSL} = 90\% \rightarrow Z = 1.282$  
  * $\text{CSL} = 95\% \rightarrow Z = 1.645$  
  * $\text{CSL} = 98\% \rightarrow Z = 2.054$  
  * $\text{CSL} = 99\% \rightarrow Z = 2.326$

---

### 25. Continuous-Review Safety Stock ($SS_{\text{continuous}}$)
* **Definition:** Buffer inventory held under continuous real-time inventory monitoring to absorb both daily customer demand variance and supplier lead-time variance.
* **Formula:**  
  $$SS_{\text{continuous}} = Z \times \sqrt{(\bar{L} \times \sigma_D^2) + (\bar{D}^2 \times \sigma_L^2)}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Buffer inventory protecting against stockouts during supplier lead time $\bar{L}$.
* **Data Fields Required:** $Z$ (Service Factor), $\bar{L}$ (Avg Lead Time in Days), $\sigma_D^2$ (Demand Variance), $\bar{D}$ (Avg Daily Demand), $\sigma_L^2$ (Lead-Time Variance)
* **Example:**  
  $Z = 1.645$ ($95\%$), $\bar{L} = 9$, $\sigma_L = 2$ ($\sigma_L^2 = 4$), $\bar{D} = 10$, $\sigma_D = 3$ ($\sigma_D^2 = 9$).  
  $$\text{Variance} = (9 \times 9) + (100 \times 4) = 81 + 400 = 481 \implies \sqrt{481} \approx 21.93$$  
  $$SS_{\text{continuous}} = 1.645 \times 21.93 \approx 36.07 \rightarrow \mathbf{36\text{ units}}.$$

---

### 26. Continuous-Review Reorder Point (ROP)
* **Definition:** The inventory position threshold that triggers a purchase order under continuous real-time tracking.
* **Formula:**  
  $$\text{ROP} = (\bar{D} \times \bar{L}) + SS_{\text{continuous}}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** When physical stock plus pipeline orders drops to or below ROP, procurement must place an order.
* **Data Fields Required:** $\bar{D}$, $\bar{L}$, $SS_{\text{continuous}}$
* **Example:** $\bar{D} = 10$, $\bar{L} = 9$, $SS = 36$. $\text{ROP} = (10 \times 9) + 36 = 90 + 36 = \mathbf{126\text{ units}}$.

---

### 27. Periodic-Review Safety Stock ($SS_{\text{periodic}}$)
* **Definition:** Buffer inventory required when inventory is reviewed only at fixed intervals ($R$), buffering uncertainty across lead time plus review period.
* **Formula:**  
  $$SS_{\text{periodic}} = Z \times \sqrt{((\bar{L} + R) \times \sigma_D^2) + (\bar{D}^2 \times \sigma_L^2)}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Buffer inventory covering exposure over the longer window $\bar{L} + R$ because orders cannot be placed between review dates.
* **Data Fields Required:** $Z$, $\bar{L}$, $R$ (Review Period in Days), $\sigma_D^2$, $\bar{D}$, $\sigma_L^2$
* **Example:**  
  $Z = 1.645$, $\bar{L} = 9$, $R = 7$ ($\bar{L} + R = 16$), $\bar{D} = 10$, $\sigma_D^2 = 9$, $\sigma_L^2 = 4$.  
  $$\text{Variance} = (16 \times 9) + (100 \times 4) = 144 + 400 = 544 \implies \sqrt{544} \approx 23.32$$  
  $$SS_{\text{periodic}} = 1.645 \times 23.32 \approx 38.36 \rightarrow \mathbf{38\text{ units}}.$$

---

### 28. Periodic-Review Order-Up-To Level ($S$)
* **Definition:** The target maximum inventory ceiling for periodic review replenishment policies.
* **Formula:**  
  $$\text{Order-Up-To Level} = (\bar{D} \times (\bar{L} + R)) + SS_{\text{periodic}}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Target inventory ceiling that stock is topped up to at each review date.
* **Data Fields Required:** $\bar{D}$, $\bar{L}$, $R$, $SS_{\text{periodic}}$
* **Example:** $\bar{D} = 10$, $\bar{L} = 9$, $R = 7$, $SS_{\text{periodic}} = 38$.  
  $$\text{Order-Up-To Level} = (10 \times (9 + 7)) + 38 = 160 + 38 = \mathbf{198\text{ units}}.$$

---

### 29. Recommended Reorder Quantity ($Q_{\text{reorder}}$)
* **Definition:** The exact purchase order quantity that procurement should issue to the vendor.
* **Formula:**  
  $$Q_{\text{reorder}} = \max(0, \text{Order-Up-To Level} - (\text{Stock-on-Hand} + \text{Stock-in-Transit}))$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Purchase order size recommended to procurement on today's review schedule.
* **Data Fields Required:** `Order-Up-To Level`, `stock_on_hand`, `stock_in_transit`
* **Example:** $\text{Order-Up-To} = 198$, $\text{SOH} = 40$, $\text{SIT} = 50$.  
  $$Q_{\text{reorder}} = \max(0, 198 - (40 + 50)) = 198 - 90 = \mathbf{108\text{ units}}.$$

---

### 30. Excess Inventory Units (Primary & Secondary Definitions)
* **Primary Definition:** Physical stock-on-hand held in excess of the operational target ceiling (Order-Up-To level).
* **Primary Formula:**  
  $$\mathbf{\text{Excess Units}_{i, s, t} = \max(0, \text{Stock-on-Hand}_{i, s, t} - \text{Order-Up-To Level}_{i, s})}$$
* **Secondary Slow-Moving Flag:**  
  $$\text{Slow-Moving Flag}_{i, s, t} = \begin{cases} 1 & \text{if } \text{DOH}_{\text{units}} > 60\text{ days} \\ 0 & \text{otherwise} \end{cases}$$
* **Clarification:** Stock exceeding 60 days of forward demand is strictly a **secondary diagnostic flag** for slow-moving stock identification, **not** the primary mathematical excess definition.
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Quantifies unneeded inventory tying up warehouse capacity.
* **Data Fields Required:** `stock_on_hand`, `Order-Up-To Level`, `DOH_units`
* **Example:** $\text{SOH} = 250\text{ units}$, $\text{Order-Up-To Level} = 198\text{ units}$.  
  $$\text{Excess Units} = \max(0, 250 - 198) = \mathbf{52\text{ units}}.$$

---

### 31. Excess Inventory Value
* **Definition:** The balance-sheet dollar capital locked in excess inventory.
* **Formula:**  
  $$\text{Excess Inventory Value}_{i, s, t} = \text{Excess Units}_{i, s, t} \times \text{Unit Cost}_{i}$$
* **Calculation Grain:** `sku_id` × `store_id` × `date`
* **Business Interpretation:** Trapped working capital that could be redeployed or liquidated.
* **Data Fields Required:** `Excess Inventory Units`, `products.unit_cost`
* **Example:** 52 excess units at a unit cost of $\$10.00$. $\text{Excess Value} = 52 \times \$10.00 = \mathbf{\$520.00}$.

---

### 32. Priority Alert Levels (Procurement Queue)
* **Definition:** Categorical urgency rating assigned to SKUs in the procurement action center based on how severely current inventory breaches the safety buffer.
* **Exact Rules:**  
  $$\text{Priority} = \begin{cases} 
  \mathbf{CRITICAL\text{ (RED)}} & \text{if } \text{Inventory Position} \le SS_{\text{continuous}} \\ 
  & \quad (\text{Safety stock is breached; stockout is active or imminent}) \\ 
  \mathbf{HIGH\text{ (ORANGE)}} & \text{if } SS_{\text{continuous}} < \text{Inventory Position} \le \text{ROP} \\ 
  & \quad (\text{Reorder point breached; replenishment order must be placed today}) \\ 
  \mathbf{MEDIUM\text{ (YELLOW)}} & \text{if } \text{ROP} < \text{Inventory Position} \le \text{ROP} \times 1.10 \\ 
  & \quad (\text{Approaching reorder point within 10\%; prepare PO}) \\ 
  \mathbf{HEALTHY\text{ (GREEN)}} & \text{if } \text{Inventory Position} > \text{ROP} \times 1.10 
  \end{cases}$$
* **Calculation Grain:** `sku_id` × `store_id`
* **Business Interpretation:** Triages daily replenishment tasks for buyers and inventory planners.
* **Data Fields Required:** `Inventory Position`, `Safety Stock`, `Reorder Point`
* **Example:** $SS = 36$, $\text{ROP} = 126$.  
  * If $\text{Inventory Position} = 20 \rightarrow \mathbf{CRITICAL}$.  
  * If $\text{Inventory Position} = 85 \rightarrow \mathbf{HIGH}$.  
  * If $\text{Inventory Position} = 130 \rightarrow \mathbf{MEDIUM}$.  
  * If $\text{Inventory Position} = 150 \rightarrow \mathbf{HEALTHY}$.
