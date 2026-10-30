"""
Smart Inventory Diagnostics - Phase 2: Quarantine Manager
Isolates anomalous and invalid records into structured quarantine datasets
with full audit metadata, preserving raw data immutability.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Set
import pandas as pd
from src.data_quality import QualityFinding


class QuarantineManager:
    """Manages the quarantine of data quality rule violations."""

    def __init__(self, raw_data_dir: str, quarantine_dir: str):
        self.raw_data_dir = os.path.abspath(raw_data_dir)
        self.quarantine_dir = os.path.abspath(quarantine_dir)
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def process_quarantine(self, findings: List[QualityFinding]) -> Dict[str, Any]:
        """
        Isolates records violating critical data quality rules (ERROR severity)
        into dedicated quarantine tables, adding governance audit metadata.
        """
        now_ts = datetime.now().isoformat()
        
        # Group findings by table and severity
        error_findings = [f for f in findings if f.severity == "ERROR"]
        warning_findings = [f for f in findings if f.severity == "WARNING"]
        
        # 1. Save all findings to CSV and JSON
        findings_records = []
        for idx, f in enumerate(findings, start=1):
            findings_records.append({
                "finding_id": f"FND-{idx:04d}",
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "table": f.table,
                "record_id": f.record_id,
                "column": f.column,
                "value": str(f.value),
                "severity": f.severity,
                "reason": f.reason,
                "audited_at": now_ts,
            })
        
        findings_df = pd.DataFrame(findings_records)
        findings_csv_path = os.path.join(self.quarantine_dir, "data_quality_findings.csv")
        findings_json_path = os.path.join(self.quarantine_dir, "data_quality_findings.json")
        findings_df.to_csv(findings_csv_path, index=False)
        
        with open(findings_json_path, "w", encoding="utf-8") as jf:
            json.dump(findings_records, jf, indent=2)

        # 2. Extract and save quarantined rows per table
        quarantined_files = {}
        
        # Table A: inventory_snapshots (Negative Inventory)
        neg_inv_findings = [f for f in error_findings if f.rule_id == "R003_NEGATIVE_INVENTORY"]
        if neg_inv_findings:
            rows = []
            for idx, f in enumerate(neg_inv_findings, start=1):
                rec = dict(f.raw_record)
                rec["quarantine_id"] = f"Q-SNAP-{idx:04d}"
                rec["rule_id"] = f.rule_id
                rec["quarantine_reason"] = f.reason
                rec["quarantine_timestamp"] = now_ts
                rows.append(rec)
            q_df = pd.DataFrame(rows)
            q_path = os.path.join(self.quarantine_dir, "quarantined_inventory_snapshots.csv")
            q_df.to_csv(q_path, index=False)
            quarantined_files["inventory_snapshots"] = {"path": q_path, "count": len(q_df)}

        # Table B: sales_transactions (Ghost Sales)
        ghost_findings = [f for f in error_findings if f.rule_id == "R004_GHOST_SALES"]
        if ghost_findings:
            rows = []
            for idx, f in enumerate(ghost_findings, start=1):
                rec = dict(f.raw_record)
                rec["quarantine_id"] = f"Q-SALE-{idx:04d}"
                rec["rule_id"] = f.rule_id
                rec["quarantine_reason"] = f.reason
                rec["quarantine_timestamp"] = now_ts
                rows.append(rec)
            q_df = pd.DataFrame(rows)
            q_path = os.path.join(self.quarantine_dir, "quarantined_sales_transactions.csv")
            q_df.to_csv(q_path, index=False)
            quarantined_files["sales_transactions"] = {"path": q_path, "count": len(q_df)}

        # Table C: supplier_orders (Invalid Date Sequences)
        seq_findings = [f for f in error_findings if f.rule_id == "R005_PO_DATE_SEQUENCE"]
        if seq_findings:
            rows = []
            for idx, f in enumerate(seq_findings, start=1):
                rec = dict(f.raw_record)
                rec["quarantine_id"] = f"Q-PO-{idx:04d}"
                rec["rule_id"] = f.rule_id
                rec["quarantine_reason"] = f.reason
                rec["quarantine_timestamp"] = now_ts
                rows.append(rec)
            q_df = pd.DataFrame(rows)
            q_path = os.path.join(self.quarantine_dir, "quarantined_supplier_orders.csv")
            q_df.to_csv(q_path, index=False)
            quarantined_files["supplier_orders"] = {"path": q_path, "count": len(q_df)}

        return {
            "total_findings": len(findings),
            "errors_quarantined": len(error_findings),
            "warnings_flagged": len(warning_findings),
            "quarantined_files": quarantined_files,
            "findings_csv": findings_csv_path,
            "findings_json": findings_json_path,
        }

    def get_quarantined_keys(self) -> Dict[str, Set[str]]:
        """
        Returns sets of quarantined record identifiers to allow downstream staging
        to exclude quarantined rows cleanly without mutating raw data.
        """
        keys = {
            "inventory_snapshots": set(),
            "sales_transactions": set(),
            "supplier_orders": set()
        }
        
        snap_q = os.path.join(self.quarantine_dir, "quarantined_inventory_snapshots.csv")
        if os.path.exists(snap_q):
            df = pd.read_csv(snap_q)
            for _, r in df.iterrows():
                keys["inventory_snapshots"].add(f"{r['snapshot_date']}|{r['sku_id']}|{r['store_id']}")
                
        sales_q = os.path.join(self.quarantine_dir, "quarantined_sales_transactions.csv")
        if os.path.exists(sales_q):
            df = pd.read_csv(sales_q)
            keys["sales_transactions"] = set(df["transaction_id"].astype(str))
            
        po_q = os.path.join(self.quarantine_dir, "quarantined_supplier_orders.csv")
        if os.path.exists(po_q):
            df = pd.read_csv(po_q)
            keys["supplier_orders"] = set(df["po_id"].astype(str))
            
        return keys
