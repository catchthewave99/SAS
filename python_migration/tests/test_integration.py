"""
Integration tests for cross-module workflows.

These tests verify that different modules work together correctly
in realistic end-to-end scenarios.
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

from sas_clinical.data_processing.test_data_generator import TestDataGenerator
from sas_clinical.comparison.dataset_compare import compare_libraries, compare_datasets
from sas_clinical.visualization.box_plots import generate_phuse_box_plots
from sas_clinical.utils.data_utils import filter_analysis_population, merge_datasets, get_variable_list


class TestDataGenerationAndComparison:
    """Integration tests for test data generation and comparison workflow."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for integration testing."""
        base_dir = tempfile.mkdtemp()
        mod_dir = tempfile.mkdtemp()
        yield Path(base_dir), Path(mod_dir)
        shutil.rmtree(base_dir)
        shutil.rmtree(mod_dir)

    def test_generate_and_compare_workflow(self, temp_dirs):
        """Test complete workflow: generate test data, then compare it."""
        base_dir, mod_dir = temp_dirs

        # Step 1: Create original datasets
        adsl = pd.DataFrame(
            {
                "usubjid": ["001", "002", "003", "004"],
                "age": [25, 30, 35, 40],
                "sex": ["M", "F", "M", "F"],
                "saffl": ["Y", "Y", "Y", "Y"],
            }
        )
        adsl.to_csv(base_dir / "adsl.csv", index=False)

        adae = pd.DataFrame(
            {
                "usubjid": ["001", "002", "003"],
                "aeterm": ["Headache", "Nausea", "Fatigue"],
                "aesev": ["MILD", "MODERATE", "MILD"],
            }
        )
        adae.to_csv(base_dir / "adae.csv", index=False)

        # Step 2: Generate modified test data
        generator = TestDataGenerator(base_dir, mod_dir)

        # Modify adsl
        adsl_mod = generator.create_modified_dataset(
            adsl, "adsl", drop_vars=["saffl"], add_vars=["newvar"], delete_every_nth=2
        )
        adsl_mod.to_csv(mod_dir / "adsl.csv", index=False)

        # Copy adae unchanged
        adae.to_csv(mod_dir / "adae.csv", index=False)

        # Step 3: Compare libraries
        comparison_result = compare_libraries(base_dir, mod_dir, file_pattern="*.csv")

        # Verify comparison results
        assert "adsl" in comparison_result["common_datasets"]
        assert "adae" in comparison_result["common_datasets"]

        # adsl should have differences
        assert comparison_result["dataset_comparisons"]["adsl"]["summary"]["status"] == "DIFFERENCES_FOUND"
        assert comparison_result["dataset_comparisons"]["adsl"]["summary"]["has_variable_diffs"] == True
        assert comparison_result["dataset_comparisons"]["adsl"]["summary"]["has_row_count_diff"] == True

        # adae should be identical
        assert comparison_result["dataset_comparisons"]["adae"]["summary"]["status"] == "IDENTICAL"

    def test_generate_compare_with_by_variable(self, temp_dirs):
        """Test workflow with BY variable comparison."""
        base_dir, mod_dir = temp_dirs

        # Create dataset with subject-level data
        df = pd.DataFrame(
            {
                "usubjid": ["001", "002", "003"],
                "visit": ["Week 0", "Week 0", "Week 0"],
                "aval": [100.0, 110.0, 120.0],
                "saffl": ["Y", "Y", "Y"],
            }
        )
        df.to_csv(base_dir / "test.csv", index=False)

        # Generate modified version with value changes
        generator = TestDataGenerator(base_dir, mod_dir)
        df_mod = generator.create_modified_dataset(df, "test", modify_row=1, modify_values={"aval": 999.0})
        df_mod.to_csv(mod_dir / "test.csv", index=False)

        # Compare with BY variable
        df_base = pd.read_csv(base_dir / "test.csv")
        df_mod = pd.read_csv(mod_dir / "test.csv")
        result = compare_datasets(df_base, df_mod, by="usubjid")

        # Should detect value difference for usubjid='002'
        assert result["summary"]["status"] == "DIFFERENCES_FOUND"
        assert result["summary"]["has_value_diffs"] == True


class TestDataProcessingAndVisualization:
    """Integration tests for data processing and visualization workflow."""

    @pytest.fixture
    def sample_clinical_data(self):
        """Create sample clinical trial data."""
        np.random.seed(42)

        # Create ADSL (subject-level)
        adsl = pd.DataFrame(
            {
                "studyid": ["STUDY001"] * 20,
                "usubjid": [f"SUBJ-{i:03d}" for i in range(1, 21)],
                "age": np.random.randint(18, 75, 20),
                "sex": np.random.choice(["M", "F"], 20),
                "trtp": np.random.choice(["Placebo", "Treatment"], 20),
                "trtpn": [1 if x == "Placebo" else 2 for x in np.random.choice(["Placebo", "Treatment"], 20)],
                "saffl": ["Y"] * 20,
                "ittfl": ["Y"] * 20,
            }
        )

        # Create ADLBC (lab data)
        adlbc_records = []
        for _, subj in adsl.iterrows():
            for visit_num in [0, 2, 4]:
                adlbc_records.append(
                    {
                        "studyid": subj["studyid"],
                        "usubjid": subj["usubjid"],
                        "trtp": subj["trtp"],
                        "trtpn": subj["trtpn"],
                        "saffl": subj["saffl"],
                        "anl01fl": "Y",
                        "param": "Albumin (g/L)",
                        "paramcd": "ALB",
                        "aval": np.random.normal(100, 15),
                        "avisitn": visit_num,
                        "avisit": f"Week {visit_num}",
                        "atptn": 1,
                        "atpt": "Pre-dose",
                        "anrlo": 85,
                        "anrhi": 115,
                    }
                )

        adlbc = pd.DataFrame(adlbc_records)

        return adsl, adlbc

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_filter_and_visualize_workflow(self, sample_clinical_data, temp_output_dir):
        """Test workflow: filter data, then generate visualizations."""
        adsl, adlbc = sample_clinical_data

        # Step 1: Filter to analysis population
        adlbc_filtered = filter_analysis_population(adlbc, population_flag="saffl", analysis_flag="anl01fl")

        # Verify filtering worked
        assert len(adlbc_filtered) > 0
        assert all(adlbc_filtered["saffl"] == "Y")
        assert all(adlbc_filtered["anl01fl"] == "Y")

        # Step 2: Generate box plots
        generate_phuse_box_plots(
            data=adlbc_filtered,
            output_dir=temp_output_dir,
            treatment_var="trtp",
            treatment_num_var="trtpn",
            measurement_var="aval",
            param_code_var="paramcd",
        )

        # Verify plots were created
        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

    def test_merge_and_analyze_workflow(self, sample_clinical_data):
        """Test workflow: merge datasets, then analyze."""
        adsl, adlbc = sample_clinical_data

        # Step 1: Merge ADSL demographics with ADLBC lab data
        merged = merge_datasets(
            adsl[["usubjid", "age", "sex"]], adlbc[["usubjid", "paramcd", "aval", "avisitn"]], on="usubjid", how="inner"
        )

        # Verify merge worked
        assert len(merged) > 0
        assert "age" in merged.columns
        assert "sex" in merged.columns
        assert "aval" in merged.columns

        # Step 2: Get variable lists
        numeric_vars = get_variable_list(merged, var_type="numeric")
        character_vars = get_variable_list(merged, var_type="character")

        # Verify variable classification
        assert "age" in numeric_vars
        assert "aval" in numeric_vars
        assert "sex" in character_vars
        assert "paramcd" in character_vars


class TestEndToEndScenarios:
    """End-to-end integration tests simulating real-world scenarios."""

    @pytest.fixture
    def temp_workspace(self):
        """Create complete temporary workspace."""
        workspace = tempfile.mkdtemp()
        workspace_path = Path(workspace)

        # Create directory structure
        (workspace_path / "base").mkdir()
        (workspace_path / "modified").mkdir()
        (workspace_path / "outputs").mkdir()

        yield workspace_path

        shutil.rmtree(workspace)

    def test_complete_validation_workflow(self, temp_workspace):
        """
        Test complete validation workflow:
        1. Create original datasets
        2. Generate modified test data
        3. Compare datasets
        4. Verify expected differences detected
        """
        base_dir = temp_workspace / "base"
        mod_dir = temp_workspace / "modified"

        # Step 1: Create original datasets
        adsl = pd.DataFrame(
            {
                "usubjid": [f"{i:03d}" for i in range(1, 11)],
                "age": list(range(25, 35)),
                "sex": ["M", "F"] * 5,
                "race": ["WHITE"] * 10,
                "saffl": ["Y"] * 10,
            }
        )
        adsl.to_csv(base_dir / "adsl.csv", index=False)

        adae = pd.DataFrame(
            {
                "usubjid": [f"{i:03d}" for i in range(1, 6)],
                "aeterm": ["Headache", "Nausea", "Fatigue", "Dizziness", "Rash"],
                "aesev": ["MILD"] * 5,
            }
        )
        adae.to_csv(base_dir / "adae.csv", index=False)

        # Step 2: Generate modified test data with known differences
        generator = TestDataGenerator(base_dir, mod_dir)

        # Modify adsl: drop variable, add variable, delete observations
        adsl_mod = generator.create_modified_dataset(
            adsl, "adsl", drop_vars=["saffl"], add_vars=["newvar"], delete_every_nth=3
        )
        adsl_mod.to_csv(mod_dir / "adsl.csv", index=False)

        # Modify adae: change values
        adae_mod = generator.create_modified_dataset(adae, "adae", modify_row=2, modify_values={"aesev": "SEVERE"})
        adae_mod.to_csv(mod_dir / "adae.csv", index=False)

        # Step 3: Compare libraries
        comparison = compare_libraries(base_dir, mod_dir, file_pattern="*.csv")

        # Step 4: Verify expected differences
        # ADSL should have variable differences and row count differences
        adsl_result = comparison["dataset_comparisons"]["adsl"]
        assert adsl_result["summary"]["status"] == "DIFFERENCES_FOUND"
        assert adsl_result["summary"]["has_variable_diffs"] == True
        assert "saffl" in adsl_result["variable_comparison"]["left"]
        assert "newvar" in adsl_result["variable_comparison"]["right"]
        assert adsl_result["summary"]["has_row_count_diff"] == True

        # ADAE should have value differences
        adae_result = comparison["dataset_comparisons"]["adae"]
        assert adae_result["summary"]["status"] == "DIFFERENCES_FOUND"
        assert adae_result["summary"]["has_value_diffs"] == True

    def test_clinical_reporting_pipeline(self, temp_workspace):
        """
        Test clinical reporting pipeline:
        1. Create clinical trial data
        2. Filter to analysis population
        3. Generate summary statistics
        4. Create visualizations
        """
        np.random.seed(42)
        output_dir = temp_workspace / "outputs"

        # Step 1: Create clinical trial data
        n_subjects = 30
        adlbc = pd.DataFrame(
            {
                "usubjid": [f"SUBJ-{i:03d}" for i in range(1, n_subjects + 1)],
                "trtp": ["Placebo"] * 15 + ["Treatment"] * 15,
                "trtpn": [1] * 15 + [2] * 15,
                "param": ["Albumin (g/L)"] * n_subjects,
                "paramcd": ["ALB"] * n_subjects,
                "aval": np.random.normal(100, 15, n_subjects),
                "avisitn": [0] * n_subjects,
                "avisit": ["Baseline"] * n_subjects,
                "atptn": [1] * n_subjects,
                "atpt": ["Pre-dose"] * n_subjects,
                "saffl": ["Y"] * n_subjects,
                "anl01fl": ["Y"] * n_subjects,
                "anrlo": [85] * n_subjects,
                "anrhi": [115] * n_subjects,
            }
        )

        # Step 2: Filter to analysis population
        adlbc_analysis = filter_analysis_population(adlbc, population_flag="saffl", analysis_flag="anl01fl")

        assert len(adlbc_analysis) == n_subjects

        # Step 3: Generate visualizations
        generate_phuse_box_plots(
            data=adlbc_analysis,
            output_dir=output_dir,
            treatment_var="trtp",
            treatment_num_var="trtpn",
            measurement_var="aval",
            param_code_var="paramcd",
        )

        # Step 4: Verify outputs
        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

        # Verify file is not empty
        assert pdf_files[0].stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
