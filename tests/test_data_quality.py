"""
Smart Inventory Diagnostics - Phase 2 Quality Test Suite
Validates profiling, assertion rules, quarantine isolation, and raw data immutability.
"""

import os
import hashlib
import pandas as pd
import pytest
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_profiler import DataProfiler
from src.data_quality import DataQualityAuditor
from src.quarantine import QuarantineManager

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
QUARANTINE_DIR = os.path.join(BASE_DIR, "data", "quarantine")


def _calculate_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestDataQualityAudit:
    """Test suite for Phase 2 data quality audit and quarantine engine."""

    @pytest.fixture(autouse=True)
    def setup_auditor(self):
        self.profiler = DataProfiler(RAW_DATA_DIR)
        self.auditor = DataQualityAuditor(RAW_DATA_DIR)
        self.quarantine_mgr = QuarantineManager(RAW_DATA_DIR, QUARANTINE_DIR)

    def test_raw_files_exist_and_non_empty(self):
        """Verify all 6 raw files exist and have expected non-zero sizes."""
        expected_files = [
            "products.csv", "stores.csv", "suppliers.csv",
            "sales_transactions.csv", "inventory_snapshots.csv", "supplier_orders.csv"
        ]
        for fname in expected_files:
            fpath = os.path.join(RAW_DATA_DIR, fname)
            assert os.path.exists(fpath), f"Missing raw file: {fname}"
            assert os.path.getsize(fpath) > 0, f"Raw file is empty: {fname}"

    def test_profiler_schema_accuracy(self):
        """Test that data profiler produces correct column counts and rows."""
        profiles = self.profiler.profile_all()
        assert "products.csv" in profiles
        assert profiles["products.csv"]["row_count"] == 150
        assert profiles["stores.csv"]["row_count"] == 5
        assert profiles["suppliers.csv"]["row_count"] == 10
        assert profiles["sales_transactions.csv"]["row_count"] == 206987
        assert profiles["inventory_snapshots.csv"]["row_count"] == 273750
        assert profiles["supplier_orders.csv"]["row_count"] == 37521

    def test_pk_uniqueness(self):
        """Test that master tables have 0 duplicate primary keys."""
        self.auditor.check_pk_uniqueness()
        pk_errors = [f for f in self.auditor.findings if f.rule_id == "R001_PK_UNIQUENESS"]
        assert len(pk_errors) == 0, f"Unexpected PK duplicates: {pk_errors}"

    def test_fk_referential_integrity(self):
        """Test that all foreign keys resolve with 0 orphan records."""
        self.auditor.check_referential_integrity()
        fk_errors = [f for f in self.auditor.findings if f.rule_id == "R002_FK_INTEGRITY"]
        assert len(fk_errors) == 0, f"Unexpected orphan FKs: {fk_errors}"

    def test_negative_inventory_detection(self):
        """Test that exactly 8 negative inventory records are detected."""
        self.auditor.check_negative_inventory()
        neg_findings = [f for f in self.auditor.findings if f.rule_id == "R003_NEGATIVE_INVENTORY"]
        assert len(neg_findings) == 8, f"Expected 8 negative inventory records, found {len(neg_findings)}"
        for f in neg_findings:
            assert f.value < 0
            assert f.severity == "ERROR"

    def test_ghost_sales_detection(self):
        """Test that ghost sales records (injected + organic zero-stock transactions) are detected."""
        self.auditor.check_ghost_sales()
        ghost_findings = [f for f in self.auditor.findings if f.rule_id == "R004_GHOST_SALES"]
        assert len(ghost_findings) == 6, f"Expected 6 ghost sales, found {len(ghost_findings)}"
        for f in ghost_findings:
            assert f.value > 0
            assert f.severity == "ERROR"

    def test_po_date_sequence_detection(self):
        """Test that exactly 2 PO date sequence anomalies are detected."""
        self.auditor.check_po_date_sequence()
        seq_findings = [f for f in self.auditor.findings if f.rule_id == "R005_PO_DATE_SEQUENCE"]
        assert len(seq_findings) == 2, f"Expected 2 invalid PO date sequences, found {len(seq_findings)}"
        for f in seq_findings:
            assert f.value < 0
            assert f.severity == "ERROR"

    def test_po_lead_time_outliers(self):
        """Test that exactly 2 lead time outliers are flagged as WARNING."""
        self.auditor.check_lead_time_outliers()
        outlier_findings = [f for f in self.auditor.findings if f.rule_id == "R006_LEAD_TIME_OUTLIER"]
        assert len(outlier_findings) == 2, f"Expected 2 lead-time outliers, found {len(outlier_findings)}"
        for f in outlier_findings:
            assert f.value > 60
            assert f.severity == "WARNING"

    def test_quarantine_isolation_and_idempotency(self):
        """Test that quarantine manager isolates records and is idempotent."""
        findings = self.auditor.run_all_checks()
        q_res1 = self.quarantine_mgr.process_quarantine(findings)
        
        # Verify quarantine files exist and have exact counts
        assert os.path.exists(q_res1["findings_csv"])
        assert os.path.exists(q_res1["findings_json"])
        assert q_res1["quarantined_files"]["inventory_snapshots"]["count"] == 8
        assert q_res1["quarantined_files"]["sales_transactions"]["count"] == 6
        assert q_res1["quarantined_files"]["supplier_orders"]["count"] == 2

        # Re-run quarantine to assert idempotency
        q_res2 = self.quarantine_mgr.process_quarantine(findings)
        assert q_res2["quarantined_files"]["inventory_snapshots"]["count"] == 8
        assert q_res2["quarantined_files"]["sales_transactions"]["count"] == 6
        assert q_res2["quarantined_files"]["supplier_orders"]["count"] == 2

    def test_raw_data_immutability(self):
        """Verify that running the entire audit and quarantine leaves raw files 100% untouched."""
        raw_files = [os.path.join(RAW_DATA_DIR, f) for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]
        hashes_before = {f: _calculate_file_hash(f) for f in raw_files}
        
        # Execute audit and quarantine
        findings = self.auditor.run_all_checks()
        self.quarantine_mgr.process_quarantine(findings)
        
        hashes_after = {f: _calculate_file_hash(f) for f in raw_files}
        for f in raw_files:
            assert hashes_before[f] == hashes_after[f], f"Raw file was mutated: {f}"
