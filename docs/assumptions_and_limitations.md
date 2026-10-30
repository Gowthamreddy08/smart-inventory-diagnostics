# ⚠️ Assumptions and Methodological Limitations
## Smart Inventory Diagnostics: Retail Supply Chain Analytics

This document details the core analytical assumptions, statistical boundary conditions, operational trade-offs, and data limitations governing the Smart Inventory Diagnostics framework.

---

### 1. Demand and Lead-Time Independence Assumption
* **Assumption:** Daily customer demand ($D$) and supplier order delivery lead time ($L$) are statistically independent random variables ($\text{Cov}(D, L) = 0$).
* **Mathematical Implication:** Enables the standard bivariate variance decomposition for continuous safety stock:
  $$\sigma_{DL} = \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
* **Limitation in Practice:** In real-world supply chain crises (e.g., severe regional blizzards, pandemics, or port strikes), demand for emergency items spikes at the exact moment supplier transportation networks freeze. Under such correlated systemic shocks, this formula underestimates the required safety buffer.

---

### 2. Normal-Distribution Assumption for Non-Intermittent SKUs
* **Assumption:** For medium-to-high velocity products (where daily demand $> 2$ units and zero-demand days $< 30\%$), aggregate lead-time demand is approximated by a Gaussian normal distribution via the Central Limit Theorem.
* **Mathematical Implication:** Allows the use of standard inverse normal cumulative distribution functions ($Z$-scores: $1.282$ for $90\%$, $1.645$ for $95\%$, $2.326$ for $99\%$).
* **Limitation in Practice:** Retail sales distributions are frequently right-skewed (long tail of rare large purchases). In extreme right-tail cases, the normal approximation may slightly under-buffer relative to empirical demand distributions.

---

### 3. Intermittent-Demand Boundary & Croston/Poisson Extension
* **Assumption:** Standard continuous-review ROP and Gaussian safety stock calculations apply only to SKUs with regular, non-intermittent transactions.
* **Limitation in Practice:** Long-tail products (often found in quadrant $CZ$) where zero-demand days exceed $70\%$ violate Gaussian assumptions. For these items, calculating $\sigma_D$ yields extreme variance and inflated safety stock.
* **Analytical Treatment:** In Phase 4, SKUs with $> 70\%$ zero-demand days are flagged as "Intermittent" and segregated. Future production extensions should apply **Croston’s Method** (separating demand size from inter-arrival intervals) or negative binomial / Poisson modeling rather than standard Gaussian ROP.

---

### 4. Lost-Sales Counterfactual Estimation Limitation
* **Assumption:** Customer purchasing intent during out-of-stock periods can be counterfactually approximated by evaluating average sales on the 4 preceding in-stock same weekdays.
* **Limitation in Practice:**
  * **Unobservable Ground Truth:** Realized customer walk-aways are unrecorded by POS scanners. The counterfactual is a modeled proxy, not confirmed accounting loss.
  * **Macro & Promotional Distortions:** If a competitor ran a major ad campaign or local weather kept shoppers home, historical in-stock averages will over-estimate what sales would have been.
* **Governance Rule:** Estimated lost revenue must always be reported with an explicit counterfactual disclosure.

---

### 5. Absence of Customer Substitution Modeling
* **Assumption:** Customers who encounter an out-of-stock item leave without making an alternative purchase (the "walk-away" assumption).
* **Limitation in Practice:** In retail, customers frequently substitute within category (e.g., buying a 1-liter bottle of Brand B if Brand A is out of stock, or buying two 500ml cartons). Assuming $100\%$ lost sales represents an upper-bound estimate of revenue loss. True basket salvage effects are excluded from the current scope.

---

### 6. Exclusion of Price-Elasticity & Promotional Dynamics
* **Assumption:** Unit selling prices and supplier unit costs are held constant across the analysis period.
* **Limitation in Practice:** Retail inventory velocity is heavily influenced by temporary price reductions (TPR), clearance markdowns, and volume discounts. The current framework isolates structural replenishment from marketing promotional elasticity.

---

### 7. Exclusion of Multi-Echelon & Inter-Store Transfer Dynamics
* **Assumption:** Each retail store location operates as an independent inventory node supplied directly by vendors.
* **Limitation in Practice:** Enterprise retailers frequently execute lateral inventory rebalancing (trucking excess stock from Store 01 to cover an impending stockout at Store 04) or buffer stock at a central Distribution Center (DC). Multi-echelon pooling effects and transfer transportation costs are excluded from this project scope.

---

### 8. Explicit Spoilage & Perishables Disclosure
> [!IMPORTANT]
> **Mandatory Governance Disclosure:**  
> Spoilage is not observed in the source data. It is simulated using shelf-life and waste-rate assumptions to demonstrate how perishable inventory policy could be extended.
* **Methodological Boundary:** Spoilage is strictly an **isolated, optional synthetic module** and is **completely excluded from the core stockout, safety stock, and replenishment engine**. Core project metrics focus purely on empirical non-perishable stockouts, holding costs, lead-time variance, and working capital.

---

### 9. Excess Inventory: Primary Boundary vs. Secondary Flag
* **Primary Mathematical Boundary:** Excess units are defined strictly against the operational replenishment ceiling:
  $$\text{Excess Units} = \max(0, \text{Stock-on-Hand} - \text{Order-Up-To Level})$$
* **Secondary Diagnostic Flag:** Inventory exceeding $60$ days of forward demand ($\text{DOH} > 60\text{ days}$) serves as a secondary operational diagnostic flag for identifying slow-moving items, not as the primary excess inventory formula.

---

### 10. Empirical Validation Requirement for XYZ Thresholds
* **Initial Cutoffs:** The baseline thresholds for demand Coefficient of Variation are set to $X \le 0.5$, $0.5 < Y \le 1.0$, and $Z > 1.0$.
* **Mandatory Validation Gate:** These thresholds will be empirically evaluated and calibrated against the actual distribution percentiles during Phase 4 exploratory data analysis to ensure they produce meaningful, balanced operational segments rather than arbitrary groupings.

---

### 11. Simulation & Policy Backtest Limitations
* **Assumption:** Historical replay simulation provides an objective mechanism to evaluate alternative replenishment policies under identical historical conditions.
* **Limitation in Practice:** Backtesting against historical demand does not guarantee future performance. Supplier lead times may structurally shift due to geopolitical or macro-economic disruptions, and customer demand patterns may permanently migrate.

---

### 12. Data-Quality & Operational Integrity Limitations
* **Assumption:** Inventory snapshot anomalies (e.g., negative stock-on-hand, ghost sales during zero recorded stock) indicate operational scan-latency or data pipeline defects rather than valid physical states.
* **Mandatory Protocol:** Under no circumstances should negative inventory values be silently forward-filled or auto-imputed. All anomalies must be quarantined, investigated against intake logs, and documented in `docs/data_quality_findings.md` prior to SQL modeling.
