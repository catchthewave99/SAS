"""
Unit tests for data utility functions.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sas_clinical.utils.data_utils import (
    get_variable_list,
    check_unique_values,
    count_unique_values,
    get_labels_from_var,
    filter_analysis_population,
    get_var_min_max,
    format_value,
    merge_datasets,
    transpose_dataset,
)


class TestDataUtils:
    """Test suite for data utility functions."""

    @pytest.fixture
    def sample_df(self):
        """Create sample dataset."""
        return pd.DataFrame(
            {
                "usubjid": ["001", "002", "003", "004"],
                "age": [25, 30, 35, 40],
                "weight": [70.5, 80.2, 65.8, 75.3],
                "sex": ["M", "F", "M", "F"],
                "race": ["WHITE", "BLACK", "ASIAN", "WHITE"],
                "saffl": ["Y", "Y", "Y", "N"],
                "anl01fl": ["Y", "Y", "N", "Y"],
            }
        )

    def test_get_variable_list_all(self, sample_df):
        """Test getting all variables."""
        vars_list = get_variable_list(sample_df)
        assert len(vars_list) == 7
        assert "usubjid" in vars_list
        assert "age" in vars_list

    def test_get_variable_list_numeric(self, sample_df):
        """Test getting numeric variables only."""
        vars_list = get_variable_list(sample_df, var_type="numeric")
        assert len(vars_list) == 2
        assert "age" in vars_list
        assert "weight" in vars_list
        assert "sex" not in vars_list

    def test_get_variable_list_character(self, sample_df):
        """Test getting character variables only."""
        vars_list = get_variable_list(sample_df, var_type="character")
        assert "usubjid" in vars_list
        assert "sex" in vars_list
        assert "age" not in vars_list

    def test_check_unique_values_no_duplicates(self, sample_df):
        """Test checking unique values with no duplicates."""
        result = check_unique_values(sample_df, "usubjid")
        assert result["has_duplicates"] is False
        assert result["num_duplicates"] == 0

    def test_check_unique_values_with_duplicates(self):
        """Test checking unique values with duplicates."""
        df = pd.DataFrame({"id": [1, 2, 2, 3], "value": [10, 20, 20, 30]})
        result = check_unique_values(df, "id")
        assert result["has_duplicates"] is True
        assert result["num_duplicates"] == 2

    def test_count_unique_values(self, sample_df):
        """Test counting unique values."""
        count = count_unique_values(sample_df, "race")
        assert count == 3  # WHITE, BLACK, ASIAN

    def test_get_labels_from_var(self):
        """Test getting label mapping from variables."""
        df = pd.DataFrame({"paramcd": ["ALB", "GLUC", "HGB"], "param": ["Albumin", "Glucose", "Hemoglobin"]})
        mapping = get_labels_from_var(df, "paramcd", "param")
        assert mapping["ALB"] == "Albumin"
        assert mapping["GLUC"] == "Glucose"
        assert len(mapping) == 3

    def test_filter_analysis_population(self, sample_df):
        """Test filtering to analysis population."""
        filtered = filter_analysis_population(sample_df, "saffl", "anl01fl")
        assert len(filtered) == 2  # Only rows with both flags = 'Y'
        assert all(filtered["saffl"] == "Y")
        assert all(filtered["anl01fl"] == "Y")

    def test_get_var_min_max(self, sample_df):
        """Test getting variable min/max."""
        min_val, max_val = get_var_min_max(sample_df, "age")
        assert min_val == 25
        assert max_val == 40

    def test_get_var_min_max_with_extra_values(self, sample_df):
        """Test getting variable min/max with extra values."""
        min_val, max_val = get_var_min_max(sample_df, "age", extra_values=[20, 50])
        assert min_val == 20
        assert max_val == 50

    def test_format_value(self):
        """Test value formatting."""
        assert format_value(3.14159, 2) == "3.14"
        assert format_value(3.14159, 4) == "3.1416"
        assert format_value(np.nan, 2) == ""

    def test_merge_datasets(self):
        """Test merging datasets."""
        df1 = pd.DataFrame({"id": [1, 2, 3], "val1": [10, 20, 30]})
        df2 = pd.DataFrame({"id": [1, 2, 3], "val2": [100, 200, 300]})

        merged = merge_datasets(df1, df2, on="id")
        assert len(merged) == 3
        assert "val1" in merged.columns
        assert "val2" in merged.columns

    def test_transpose_dataset(self):
        """Test dataset transposition."""
        df = pd.DataFrame({"id": [1, 2], "var1": [10, 20], "var2": [100, 200]})

        transposed = transpose_dataset(df, id_vars="id")
        assert len(transposed) == 4  # 2 rows * 2 variables
        assert "variable" in transposed.columns
        assert "value" in transposed.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
