"""
Unit tests for library comparison functionality.
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

from sas_clinical.comparison.dataset_compare import DatasetComparison, compare_libraries


class TestCompareLibraries:
    """Test suite for library comparison functionality."""

    @pytest.fixture
    def temp_library_dirs(self):
        """Create temporary library directories with CSV files."""
        lib1_dir = tempfile.mkdtemp()
        lib2_dir = tempfile.mkdtemp()

        lib1_path = Path(lib1_dir)
        lib2_path = Path(lib2_dir)

        # Create datasets in lib1
        adsl1 = pd.DataFrame({"usubjid": ["001", "002", "003"], "age": [25, 30, 35], "sex": ["M", "F", "M"]})
        adsl1.to_csv(lib1_path / "adsl.csv", index=False)

        adae1 = pd.DataFrame(
            {"usubjid": ["001", "002"], "aeterm": ["Headache", "Nausea"], "aesev": ["MILD", "MODERATE"]}
        )
        adae1.to_csv(lib1_path / "adae.csv", index=False)

        adtte1 = pd.DataFrame({"usubjid": ["001", "002", "003"], "aval": [10.5, 20.3, 30.1]})
        adtte1.to_csv(lib1_path / "adtte.csv", index=False)

        # Create datasets in lib2 (with some differences)
        adsl2 = pd.DataFrame({"usubjid": ["001", "002", "003"], "age": [25, 30, 35], "sex": ["M", "F", "M"]})
        adsl2.to_csv(lib2_path / "adsl.csv", index=False)

        adae2 = pd.DataFrame(
            {
                "usubjid": ["001", "002"],
                "aeterm": ["Headache", "Nausea"],
                "aesev": ["MILD", "SEVERE"],  # Different value
            }
        )
        adae2.to_csv(lib2_path / "adae.csv", index=False)

        # adtte not in lib2 (only in lib1)

        # advs only in lib2
        advs2 = pd.DataFrame({"usubjid": ["001", "002"], "vstestcd": ["SYSBP", "DIABP"], "vsorres": [120, 80]})
        advs2.to_csv(lib2_path / "advs.csv", index=False)

        yield lib1_path, lib2_path

        shutil.rmtree(lib1_dir)
        shutil.rmtree(lib2_dir)

    def test_compare_libraries_identifies_common_datasets(self, temp_library_dirs):
        """Test that compare_libraries identifies common datasets."""
        lib1_path, lib2_path = temp_library_dirs

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        # Should identify adsl and adae as common
        assert "adsl" in result["common_datasets"]
        assert "adae" in result["common_datasets"]
        assert len(result["common_datasets"]) == 2

    def test_compare_libraries_identifies_only_lib1(self, temp_library_dirs):
        """Test that compare_libraries identifies datasets only in lib1."""
        lib1_path, lib2_path = temp_library_dirs

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        # adtte is only in lib1
        assert "adtte" in result["only_lib1"]
        assert len(result["only_lib1"]) == 1

    def test_compare_libraries_identifies_only_lib2(self, temp_library_dirs):
        """Test that compare_libraries identifies datasets only in lib2."""
        lib1_path, lib2_path = temp_library_dirs

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        # advs is only in lib2
        assert "advs" in result["only_lib2"]
        assert len(result["only_lib2"]) == 1

    def test_compare_libraries_compares_common_datasets(self, temp_library_dirs):
        """Test that compare_libraries compares common datasets."""
        lib1_path, lib2_path = temp_library_dirs

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        # Should have comparison results for common datasets
        assert "adsl" in result["dataset_comparisons"]
        assert "adae" in result["dataset_comparisons"]

        # adsl should be identical
        assert result["dataset_comparisons"]["adsl"]["summary"]["status"] == "IDENTICAL"

        # adae should have differences
        assert result["dataset_comparisons"]["adae"]["summary"]["status"] == "DIFFERENCES_FOUND"
        assert result["dataset_comparisons"]["adae"]["summary"]["has_value_diffs"] == True

    def test_compare_libraries_with_by_variable(self, temp_library_dirs):
        """Test library comparison with BY variable."""
        lib1_path, lib2_path = temp_library_dirs

        result = compare_libraries(lib1_path, lib2_path, by="usubjid", file_pattern="*.csv")

        # Should still work with BY variable
        assert "adsl" in result["common_datasets"]
        assert "adae" in result["common_datasets"]

    def test_compare_libraries_empty_lib1(self):
        """Test with empty lib1 directory."""
        lib1_dir = tempfile.mkdtemp()
        lib2_dir = tempfile.mkdtemp()

        lib1_path = Path(lib1_dir)
        lib2_path = Path(lib2_dir)

        # Create dataset only in lib2
        df = pd.DataFrame({"a": [1, 2, 3]})
        df.to_csv(lib2_path / "test.csv", index=False)

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        assert len(result["only_lib1"]) == 0
        assert len(result["only_lib2"]) == 1
        assert len(result["common_datasets"]) == 0

        shutil.rmtree(lib1_dir)
        shutil.rmtree(lib2_dir)

    def test_compare_libraries_empty_lib2(self):
        """Test with empty lib2 directory."""
        lib1_dir = tempfile.mkdtemp()
        lib2_dir = tempfile.mkdtemp()

        lib1_path = Path(lib1_dir)
        lib2_path = Path(lib2_dir)

        # Create dataset only in lib1
        df = pd.DataFrame({"a": [1, 2, 3]})
        df.to_csv(lib1_path / "test.csv", index=False)

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        assert len(result["only_lib1"]) == 1
        assert len(result["only_lib2"]) == 0
        assert len(result["common_datasets"]) == 0

        shutil.rmtree(lib1_dir)
        shutil.rmtree(lib2_dir)

    def test_compare_libraries_both_empty(self):
        """Test with both libraries empty."""
        lib1_dir = tempfile.mkdtemp()
        lib2_dir = tempfile.mkdtemp()

        lib1_path = Path(lib1_dir)
        lib2_path = Path(lib2_dir)

        result = compare_libraries(lib1_path, lib2_path, file_pattern="*.csv")

        assert len(result["only_lib1"]) == 0
        assert len(result["only_lib2"]) == 0
        assert len(result["common_datasets"]) == 0

        shutil.rmtree(lib1_dir)
        shutil.rmtree(lib2_dir)

    def test_compare_libraries_with_numeric_tolerance(self, temp_library_dirs):
        """Test library comparison with numeric tolerance."""
        lib1_path, lib2_path = temp_library_dirs

        # Create datasets with small numeric differences
        df1 = pd.DataFrame({"id": [1, 2, 3], "value": [1.0000, 2.0000, 3.0000]})
        df1.to_csv(lib1_path / "numeric_test.csv", index=False)

        df2 = pd.DataFrame({"id": [1, 2, 3], "value": [1.0001, 2.0001, 3.0001]})
        df2.to_csv(lib2_path / "numeric_test.csv", index=False)

        # Without tolerance, should find differences
        result1 = compare_libraries(lib1_path, lib2_path, tolerance=0, file_pattern="*.csv")
        assert result1["dataset_comparisons"]["numeric_test"]["summary"]["status"] == "DIFFERENCES_FOUND"

        # With tolerance, should be identical
        result2 = compare_libraries(lib1_path, lib2_path, tolerance=0.001, file_pattern="*.csv")
        assert result2["dataset_comparisons"]["numeric_test"]["summary"]["status"] == "IDENTICAL"


class TestDatasetComparisonReadDataset:
    """Test suite for _read_dataset method."""

    def test_read_csv_dataset(self):
        """Test reading CSV dataset."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        df.to_csv(temp_path / "test.csv", index=False)

        comparator = DatasetComparison()
        df_read = comparator._read_dataset(temp_path / "test.csv")

        assert len(df_read) == 3
        assert list(df_read.columns) == ["a", "b"]

        shutil.rmtree(temp_dir)

    def test_read_nonexistent_file(self):
        """Test reading nonexistent file."""
        comparator = DatasetComparison()

        with pytest.raises(FileNotFoundError):
            comparator._read_dataset(Path("/nonexistent/file.csv"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
