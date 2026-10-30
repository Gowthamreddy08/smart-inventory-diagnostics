"""
Smart Inventory Diagnostics - Phase 2: Data Quality Auditor
Executes automated data quality rules, schema assertions, and anomaly detection.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class QualityFinding:
    """Represents a single data quality rule failure or anomaly."""
    rule_id: str
    rule_name: str
    table: str
    record_id: str
    column: str
    value: Any
    severity: str  # ERROR, WARNING, INFO
    reason: str
    raw_record: Dict[str, Any]


class DataQualityAuditor:
    """Enterprise Data Quality Auditor for Retail Supply Chain Analytics."""

    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = os.path.abspath(raw_data_dir)
        self.findings: List[QualityFinding] = []
        self._load_datasets()

    def _load_datasets(self):
        """Loads all raw datasets into memory for auditing."""
        self.products = pd.read_csv(os.path.join(self.raw_data_dir, "products.csv"))
        self.stores = pd.read_csv(os.path.join(self.raw_data_dir, "stores.csv"))
        self.suppliers = pd.read_csv(os.path.join(self.raw_data_dir, "suppliers.csv"))
        self.sales = pd.read_csv(os.path.join(self.raw_data_dir, "sales_transactions.csv"))
        self.snapshots = pd.read_csv(os.path.join(self.raw_data_dir, "inventory_snapshots.csv"))
        self.pos = pd.read_csv(os.path.join(self.raw_data_dir, "supplier_orders.csv"))

    def check_pk_uniqueness(self) -> None:
        """Rule R001: Assert primary key uniqueness across all tables."""
        tables_pks = [
            ("products", self.products, ["sku_id"]),
            ("stores", self.stores, ["store_id"]),
            ("suppliers", self.suppliers, ["supplier_id"]),
            ("sales_transactions", self.sales, ["transaction_id"]),
            ("inventory_snapshots", self.snapshots, ["snapshot_date", "sku_id", "store_id"]),
            ("supplier_orders", self.pos, ["po_id"]),
        ]
        for tbl_name, df, pk_cols in tables_pks:
            dups = df[df.duplicated(subset=pk_cols, keep=False)]
            if len(dups) > 0:
                for _, row in dups.iterrows():
                    rec_id = " | ".join(str(row[c]) for c in pk_cols)
                    self.findings.append(QualityFinding(
                        rule_id="R001_PK_UNIQUENESS",
                        rule_name="Primary Key Uniqueness Assertion",
                        table=tbl_name,
                        record_id=rec_id,
                        column="; ".join(pk_cols),
                        value=rec_id,
                        severity="ERROR",
                        reason=f"Duplicate primary key record in table '{tbl_name}'.",
                        raw_record=row.to_dict()
                    ))

    def check_referential_integrity(self) -> None:
        """Rule R002: Assert foreign key referential integrity."""
        valid_skus = set(self.products["sku_id"])
        valid_stores = set(self.stores["store_id"])
        valid_suppliers = set(self.suppliers["supplier_id"])

        fk_checks = [
            ("sales_transactions", self.sales, "sku_id", valid_skus, "products.sku_id"),
            ("sales_transactions", self.sales, "store_id", valid_stores, "stores.store_id"),
            ("inventory_snapshots", self.snapshots, "sku_id", valid_skus, "products.sku_id"),
            ("inventory_snapshots", self.snapshots, "store_id", valid_stores, "stores.store_id"),
            ("supplier_orders", self.pos, "sku_id", valid_skus, "products.sku_id"),
            ("supplier_orders", self.pos, "supplier_id", valid_suppliers, "suppliers.supplier_id"),
            ("supplier_orders", self.pos, "destination_store_id", valid_stores, "stores.store_id"),
        ]

        for tbl_name, df, fk_col, valid_set, ref_name in fk_checks:
            orphans = df[~df[fk_col].isin(valid_set)]
            if len(orphans) > 0:
                for _, row in orphans.iterrows():
                    rec_id = str(row.get("transaction_id") or row.get("po_id") or f"{row.get('sku_id')}|{row.get('store_id')}")
                    self.findings.append(QualityFinding(
                        rule_id="R002_FK_INTEGRITY",
                        rule_name="Foreign Key Referential Integrity",
                        table=tbl_name,
                        record_id=rec_id,
                        column=fk_col,
                        value=row[fk_col],
                        severity="ERROR",
                        reason=f"Orphan foreign key value '{row[fk_col]}' does not exist in '{ref_name}'.",
                        raw_record=row.to_dict()
                    ))

    def check_negative_inventory(self) -> None:
        """Rule R003: Detect negative inventory values in snapshots."""
        neg_rows = self.snapshots[self.snapshots["stock_on_hand"] < 0]
        for _, row in neg_rows.iterrows():
            rec_id = f"{row['sku_id']} | {row['store_id']} | {row['snapshot_date']}"
            self.findings.append(QualityFinding(
                rule_id="R003_NEGATIVE_INVENTORY",
                rule_name="Negative Inventory Protocol",
                table="inventory_snapshots",
                record_id=rec_id,
                column="stock_on_hand",
                value=int(row["stock_on_hand"]),
                severity="ERROR",
                reason=f"Negative stock-on-hand ({row['stock_on_hand']} units) recorded. Indicates register scan-latency or unposted intake.",
                raw_record=row.to_dict()
            ))

    def check_ghost_sales(self) -> None:
        """Rule R004: Detect sales fulfilled when stock-on-hand is 0 and stock-in-transit is 0."""
        # Merge sales with inventory snapshots on sku, store, and date
        merged = pd.merge(
            self.sales,
            self.snapshots[["snapshot_date", "sku_id", "store_id", "stock_on_hand", "stock_in_transit"]],
            left_on=["transaction_date", "sku_id", "store_id"],
            right_on=["snapshot_date", "sku_id", "store_id"],
            how="inner"
        )
        ghosts = merged[
            (merged["units_fulfilled"] > 0) &
            (merged["stock_on_hand"] == 0) &
            (merged["stock_in_transit"] == 0)
        ]
        for _, row in ghosts.iterrows():
            self.findings.append(QualityFinding(
                rule_id="R004_GHOST_SALES",
                rule_name="Ghost Sales Detection",
                table="sales_transactions",
                record_id=str(row["transaction_id"]),
                column="units_fulfilled",
                value=int(row["units_fulfilled"]),
                severity="ERROR",
                reason=f"Sales fulfilled ({row['units_fulfilled']} units) on {row['transaction_date']} despite zero physical stock and zero transit.",
                raw_record=row.to_dict()
            ))

    def check_po_date_sequence(self) -> None:
        """Rule R005: Detect purchase orders where delivered date precedes placed date."""
        invalid_pos = self.pos[self.pos["actual_lead_time_days"] < 0]
        for _, row in invalid_pos.iterrows():
            self.findings.append(QualityFinding(
                rule_id="R005_PO_DATE_SEQUENCE",
                rule_name="PO Chronological Sequence Validity",
                table="supplier_orders",
                record_id=str(row["po_id"]),
                column="actual_lead_time_days",
                value=int(row["actual_lead_time_days"]),
                severity="ERROR",
                reason=f"Delivered date ({row['order_delivered_date']}) precedes placed date ({row['order_placed_date']}). Lead time: {row['actual_lead_time_days']} days.",
                raw_record=row.to_dict()
            ))

    def check_lead_time_outliers(self) -> None:
        """Rule R006: Flag extreme lead-time outliers (> 60 days) as WARNING."""
        outlier_pos = self.pos[self.pos["actual_lead_time_days"] > 60]
        for _, row in outlier_pos.iterrows():
            self.findings.append(QualityFinding(
                rule_id="R006_LEAD_TIME_OUTLIER",
                rule_name="Supplier Lead-Time Outlier Warning",
                table="supplier_orders",
                record_id=str(row["po_id"]),
                column="actual_lead_time_days",
                value=int(row["actual_lead_time_days"]),
                severity="WARNING",
                reason=f"Extreme lead time of {row['actual_lead_time_days']} days observed. Represents major vendor disruption.",
                raw_record=row.to_dict()
            ))

    def check_numerical_bounds(self) -> None:
        """Rule R007: Assert positive prices, costs, and logical margins."""
        # Price and cost bounds
        bad_products = self.products[
            (self.products["unit_cost"] <= 0) |
            (self.products["unit_selling_price"] < self.products["unit_cost"])
        ]
        for _, row in bad_products.iterrows():
            self.findings.append(QualityFinding(
                rule_id="R007_NUMERICAL_BOUNDS",
                rule_name="Product Price & Cost Bounds",
                table="products",
                record_id=str(row["sku_id"]),
                column="unit_selling_price",
                value=float(row["unit_selling_price"]),
                severity="ERROR",
                reason=f"Selling price (${row['unit_selling_price']}) is less than cost (${row['unit_cost']}) or cost is non-positive.",
                raw_record=row.to_dict()
            ))

        # Sales fulfilment bounds: fulfilled cannot exceed demanded
        bad_sales = self.sales[self.sales["units_fulfilled"] > self.sales["units_demanded"]]
        for _, row in bad_sales.iterrows():
            self.findings.append(QualityFinding(
                rule_id="R007_NUMERICAL_BOUNDS",
                rule_name="Sales Fulfillment Bounds",
                table="sales_transactions",
                record_id=str(row["transaction_id"]),
                column="units_fulfilled",
                value=int(row["units_fulfilled"]),
                severity="ERROR",
                reason=f"Fulfilled units ({row['units_fulfilled']}) exceeds demanded units ({row['units_demanded']}).",
                raw_record=row.to_dict()
            ))

    def check_calendar_continuity(self) -> None:
        """Rule R008: Assert all 365 calendar dates are present for each store."""
        expected_days = 365
        for store_id in self.stores["store_id"]:
            store_snaps = self.snapshots[self.snapshots["store_id"] == store_id]
            unique_dates = store_snaps["snapshot_date"].nunique()
            if unique_dates != expected_days:
                self.findings.append(QualityFinding(
                    rule_id="R008_CALENDAR_CONTINUITY",
                    rule_name="Temporal Calendar Continuity",
                    table="inventory_snapshots",
                    record_id=store_id,
                    column="snapshot_date",
                    value=unique_dates,
                    severity="ERROR",
                    reason=f"Store '{store_id}' has {unique_dates} snapshot dates, expected {expected_days}.",
                    raw_record={"store_id": store_id, "observed_dates": unique_dates}
                ))

    def run_all_checks(self) -> List[QualityFinding]:
        """Executes all data quality assertions and returns findings."""
        self.findings = []
        self.check_pk_uniqueness()
        self.check_referential_integrity()
        self.check_negative_inventory()
        self.check_ghost_sales()
        self.check_po_date_sequence()
        self.check_lead_time_outliers()
        self.check_numerical_bounds()
        self.check_calendar_continuity()
        return self.findings

    def get_findings_dataframe(self) -> pd.DataFrame:
        """Converts findings into a standardized Pandas DataFrame."""
        if not self.findings:
            self.run_all_checks()
        records = [
            {
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "table": f.table,
                "record_id": f.record_id,
                "column": f.column,
                "value": str(f.value),
                "severity": f.severity,
                "reason": f.reason,
            }
            for f in self.findings
        ]
        return pd.DataFrame(records)
