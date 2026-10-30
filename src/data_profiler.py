"""
Smart Inventory Diagnostics - Phase 2: Data Profiler
Generates statistical profiles and schema summaries for raw datasets.
"""

import os
import json
from typing import Dict, Any
import numpy as np
import pandas as pd


class DataProfiler:
    """Automated statistical profiler for raw CSV datasets."""

    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = os.path.abspath(raw_data_dir)

    def profile_file(self, filename: str) -> Dict[str, Any]:
        """Profiles a single CSV dataset."""
        file_path = os.path.join(self.raw_data_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_csv(file_path)
        file_size = os.path.getsize(file_path)

        columns_profile = {}
        for col in df.columns:
            col_data = df[col]
            col_type = str(col_data.dtype)
            null_count = int(col_data.isnull().sum())
            unique_count = int(col_data.nunique(dropna=True))

            profile_entry = {
                "dtype": col_type,
                "null_count": null_count,
                "null_pct": round(null_count / max(1, len(df)) * 100, 2),
                "unique_count": unique_count,
            }

            if pd.api.types.is_numeric_dtype(col_data) and not pd.api.types.is_bool_dtype(col_data):
                valid_num = col_data.dropna()
                if len(valid_num) > 0:
                    profile_entry.update({
                        "min": float(valid_num.min()),
                        "max": float(valid_num.max()),
                        "mean": round(float(valid_num.mean()), 2),
                        "std": round(float(valid_num.std()), 2) if len(valid_num) > 1 else 0.0,
                    })
            elif "date" in col.lower() or "snapshot" in col.lower():
                valid_dates = col_data.dropna()
                if len(valid_dates) > 0:
                    profile_entry.update({
                        "min_date": str(valid_dates.min()),
                        "max_date": str(valid_dates.max()),
                    })

            columns_profile[col] = profile_entry

        return {
            "filename": filename,
            "row_count": len(df),
            "col_count": len(df.columns),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "columns": columns_profile,
        }

    def profile_all(self) -> Dict[str, Any]:
        """Profiles all raw CSV files in raw_data_dir."""
        profiles = {}
        for fname in sorted(os.listdir(self.raw_data_dir)):
            if fname.endswith(".csv"):
                profiles[fname] = self.profile_file(fname)
        return profiles

    def save_profile_json(self, output_path: str) -> None:
        """Saves machine-readable profile JSON."""
        profiles = self.profile_all()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2)
