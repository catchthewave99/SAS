"""
Unit tests for test data generation functionality.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sas_clinical.data_processing.test_data_generator import TestDataGenerator, create_test_data


class TestTestDataGenerator:
    """Test suite for TestDataGenerator class."""

    @pytest.fixture
    def sample_dataset(self):
        """Create sample dataset for testing."""
        return pd.DataFrame(
            {
                "usubjid": ["001", "002", "003", "004", "005", "006"],
                "age": [25, 30, 35, 40, 45, 50],
                "sex": ["M", "F", "M", "F", "M", "F"],
                "race": ["WHITE", "BLACK", "ASIAN", "WHITE", "BLACK", "ASIAN"],
                "saffl": ["Y", "Y", "Y", "Y", "Y", "Y"],
                "aval": [10.5, 20.3, 30.1, 40.8, 50.2, 60.7],
            }
        )

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary base and modified directories."""
        base_dir = tempfile.mkdtemp()
        mod_dir = tempfile.mkdtemp()
        yield Path(base_dir), Path(mod_dir)
        shutil.rmtree(base_dir)
        shutil.rmtree(mod_dir)

    def test_initialization(self, temp_dirs):
        """Test TestDataGenerator initialization."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        assert generator.base_path == base_dir
        assert generator.mod_path == mod_dir
        assert mod_dir.exists()

    def test_drop_variables(self, sample_dataset, temp_dirs):
        """Test dropping variables from dataset."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(sample_dataset, "test_dataset", drop_vars=["saffl", "aval"])

        assert "saffl" not in df_mod.columns
        assert "aval" not in df_mod.columns
        assert "usubjid" in df_mod.columns
        assert len(df_mod) == len(sample_dataset)

    def test_add_variables(self, sample_dataset, temp_dirs):
        """Test adding variables to dataset."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(sample_dataset, "test_dataset", add_vars=["newvar1", "newvar2"])

        assert "newvar1" in df_mod.columns
        assert "newvar2" in df_mod.columns
        assert df_mod["newvar1"].isna().all()
        assert df_mod["newvar2"].isna().all()
        assert len(df_mod) == len(sample_dataset)

    def test_delete_every_nth_observation(self, sample_dataset, temp_dirs):
        """Test deleting every Nth observation."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        # Delete every 2nd observation
        df_mod = generator.create_modified_dataset(sample_dataset, "test_dataset", delete_every_nth=2)

        # Should have 3 rows remaining (indices 0, 2, 4)
        assert len(df_mod) == 3
        assert list(df_mod["usubjid"]) == ["001", "003", "005"]

    def test_delete_every_17th_observation(self, temp_dirs):
        """Test deleting every 17th observation (matching SAS behavior)."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        # Create dataset with 50 rows
        df = pd.DataFrame({"id": range(1, 51), "value": range(100, 150)})

        df_mod = generator.create_modified_dataset(df, "test_dataset", delete_every_nth=17)

        # Should delete rows at indices 16, 33 (0-indexed)
        # Original: 50 rows, delete 2 rows = 48 rows
        assert len(df_mod) == 48
        assert 17 not in df_mod["id"].values  # Row 17 (index 16) deleted
        assert 34 not in df_mod["id"].values  # Row 34 (index 33) deleted

    def test_modify_specific_row(self, sample_dataset, temp_dirs):
        """Test modifying specific row values."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(
            sample_dataset, "test_dataset", modify_row=1, modify_values={"race": "OTHER", "age": 99}
        )

        assert df_mod.loc[1, "race"] == "OTHER"
        assert df_mod.loc[1, "age"] == 99
        assert df_mod.loc[0, "race"] == "WHITE"  # Other rows unchanged

    def test_duplicate_row(self, sample_dataset, temp_dirs):
        """Test duplicating a specific row."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(sample_dataset, "test_dataset", duplicate_row=2)

        # Should have 7 rows (6 original + 1 duplicate)
        assert len(df_mod) == 7

        # Last row should be duplicate of row 2
        assert df_mod.iloc[-1]["age"] == df_mod.iloc[2]["age"]

    def test_duplicate_row_with_key_value(self, sample_dataset, temp_dirs):
        """Test duplicating row with modified key value."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(
            sample_dataset, "test_dataset", duplicate_row=2, duplicate_key_value="999"
        )

        # Should have 7 rows
        assert len(df_mod) == 7

        # Last row should have modified usubjid
        assert df_mod.iloc[-1]["usubjid"] == "999"
        assert df_mod.iloc[-1]["age"] == df_mod.iloc[2]["age"]

    def test_multiple_modifications(self, sample_dataset, temp_dirs):
        """Test applying multiple modifications together."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_mod = generator.create_modified_dataset(
            sample_dataset,
            "test_dataset",
            drop_vars=["saffl"],
            add_vars=["newvar"],
            delete_every_nth=3,
            modify_row=0,
            modify_values={"race": "WHITE"},
            duplicate_row=1,
            duplicate_key_value="999",
        )

        # Check all modifications applied
        assert "saffl" not in df_mod.columns
        assert "newvar" in df_mod.columns
        assert len(df_mod) < len(sample_dataset) + 1  # Some deleted, one added
        assert df_mod.iloc[0]["race"] == "WHITE"

    def test_create_compare_test_data_with_csv(self, temp_dirs):
        """Test creating complete test data structure with CSV files."""
        base_dir, mod_dir = temp_dirs

        # Create sample CSV files in base directory
        adsl = pd.DataFrame({"usubjid": ["001", "002", "003"], "age": [25, 30, 35], "saffl": ["Y", "Y", "Y"]})
        adsl.to_csv(base_dir / "adsl.csv", index=False)

        adae = pd.DataFrame({"usubjid": ["001", "002"], "aeterm": ["Headache", "Nausea"]})
        adae.to_csv(base_dir / "adae.csv", index=False)

        adtte = pd.DataFrame({"usubjid": ["001", "002", "003"], "aval": [10.5, 20.3, 30.1], "saffl": ["Y", "Y", "Y"]})
        adtte.to_csv(base_dir / "adtte.csv", index=False)

        # Create test data
        generator = TestDataGenerator(base_dir, mod_dir)
        generator.create_compare_test_data(datasets_to_copy=["adsl", "adae"], dataset_to_modify="adtte")

        # Check copied datasets exist
        assert (mod_dir / "adsl.csv").exists()
        assert (mod_dir / "adae.csv").exists()

        # Check modified dataset exists
        assert (mod_dir / "adtte.csv").exists()

        # Check new dataset created
        assert (mod_dir / "new.csv").exists()

        # Verify modifications in adtte
        adtte_mod = pd.read_csv(mod_dir / "adtte.csv")
        assert "saffl" not in adtte_mod.columns  # Dropped
        assert "newvar" in adtte_mod.columns  # Added
        # Note: With only 3 rows and delete_every_nth=17, no rows are deleted
        # (only deletes at indices 16, 33, etc.)

    def test_convenience_function(self, temp_dirs):
        """Test convenience function for creating test data."""
        base_dir, mod_dir = temp_dirs

        # Create sample CSV file
        adsl = pd.DataFrame({"usubjid": ["001", "002"], "age": [25, 30]})
        adsl.to_csv(base_dir / "adsl.csv", index=False)

        adtte = pd.DataFrame({"usubjid": ["001", "002"], "aval": [10.5, 20.3], "saffl": ["Y", "Y"]})
        adtte.to_csv(base_dir / "adtte.csv", index=False)

        # Use convenience function
        create_test_data(base_dir, mod_dir)

        # Check files were created
        assert (mod_dir / "new.csv").exists()


class TestEdgeCases:
    """Test edge cases for test data generation."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary base and modified directories."""
        base_dir = tempfile.mkdtemp()
        mod_dir = tempfile.mkdtemp()
        yield Path(base_dir), Path(mod_dir)
        shutil.rmtree(base_dir)
        shutil.rmtree(mod_dir)

    def test_empty_dataset(self, temp_dirs):
        """Test with empty dataset."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df_empty = pd.DataFrame()
        df_mod = generator.create_modified_dataset(df_empty, "empty_dataset", add_vars=["newvar"])

        assert "newvar" in df_mod.columns
        assert len(df_mod) == 0

    def test_drop_nonexistent_variable(self, temp_dirs):
        """Test dropping variable that doesn't exist."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df = pd.DataFrame({"a": [1, 2, 3]})
        df_mod = generator.create_modified_dataset(df, "test_dataset", drop_vars=["nonexistent"])

        # Should not crash, just skip nonexistent variable
        assert "a" in df_mod.columns
        assert len(df_mod) == 3

    def test_modify_row_out_of_bounds(self, temp_dirs):
        """Test modifying row index that doesn't exist."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df = pd.DataFrame({"a": [1, 2, 3]})
        df_mod = generator.create_modified_dataset(df, "test_dataset", modify_row=999, modify_values={"a": 999})

        # Should not crash, just skip modification
        assert len(df_mod) == 3
        assert 999 not in df_mod["a"].values

    def test_duplicate_row_out_of_bounds(self, temp_dirs):
        """Test duplicating row index that doesn't exist."""
        base_dir, mod_dir = temp_dirs
        generator = TestDataGenerator(base_dir, mod_dir)

        df = pd.DataFrame({"a": [1, 2, 3]})
        df_mod = generator.create_modified_dataset(df, "test_dataset", duplicate_row=999)

        # Should not crash, just skip duplication
        assert len(df_mod) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
