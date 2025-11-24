"""
Unit tests for PHUSE box plot visualization functionality.
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

from sas_clinical.visualization.box_plots import PHUSEBoxPlot, generate_phuse_box_plots


class TestPHUSEBoxPlot:
    """Test suite for PHUSEBoxPlot class."""

    @pytest.fixture
    def sample_adlbc_data(self):
        """Create sample ADaM ADLBC-like data for testing."""
        np.random.seed(42)

        n_subjects = 12
        n_visits = 3
        n_treatments = 2

        data = []

        for subj_id in range(1, n_subjects + 1):
            trtpn = (subj_id % n_treatments) + 1
            trtp = ["Placebo", "Treatment"][trtpn - 1]

            for visit_num in range(n_visits):
                avisitn = visit_num * 2
                avisit = f"Week {avisitn}"

                # Generate measurement with treatment effect
                baseline = np.random.normal(100, 15)
                treatment_effect = (trtpn - 1) * 5
                aval = baseline + treatment_effect + np.random.normal(0, 10)

                # Reference ranges
                anrlo = 85
                anrhi = 115

                data.append(
                    {
                        "studyid": "STUDY001",
                        "usubjid": f"SUBJ-{subj_id:03d}",
                        "saffl": "Y",
                        "anl01fl": "Y",
                        "trtp": trtp,
                        "trtpn": trtpn,
                        "param": "Albumin (g/L)",
                        "paramcd": "ALB",
                        "aval": aval,
                        "avisitn": avisitn,
                        "avisit": avisit,
                        "atptn": 1,
                        "atpt": "Pre-dose",
                        "anrlo": anrlo,
                        "anrhi": anrhi,
                        "a1lo": anrlo,
                        "a1hi": anrhi,
                    }
                )

        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_phuse_box_plot_initialization(self, sample_adlbc_data):
        """Test PHUSEBoxPlot initialization."""
        plotter = PHUSEBoxPlot(
            data=sample_adlbc_data, treatment_var="trtp", treatment_num_var="trtpn", measurement_var="aval"
        )

        assert plotter.treatment_var == "trtp"
        assert plotter.measurement_var == "aval"
        assert len(plotter.analysis_data) > 0

    def test_filter_analysis_population(self, sample_adlbc_data):
        """Test filtering to analysis population."""
        # Add some records with flags = 'N'
        df_with_flags = sample_adlbc_data.copy()
        df_with_flags.loc[0, "saffl"] = "N"
        df_with_flags.loc[1, "anl01fl"] = "N"

        plotter = PHUSEBoxPlot(data=df_with_flags, treatment_var="trtp", measurement_var="aval")

        # Should filter out records with flags = 'N'
        assert len(plotter.analysis_data) < len(df_with_flags)
        assert all(plotter.analysis_data["saffl"] == "Y")
        assert all(plotter.analysis_data["anl01fl"] == "Y")

    def test_outlier_detection(self, sample_adlbc_data):
        """Test outlier detection based on reference ranges."""
        # Add some outliers
        df_with_outliers = sample_adlbc_data.copy()
        df_with_outliers.loc[0, "aval"] = 50  # Below anrlo
        df_with_outliers.loc[1, "aval"] = 150  # Above anrhi

        plotter = PHUSEBoxPlot(
            data=df_with_outliers,
            treatment_var="trtp",
            measurement_var="aval",
            low_ref_var="anrlo",
            high_ref_var="anrhi",
        )

        # Check outliers are detected
        outliers = plotter.analysis_data[plotter.analysis_data["is_outlier"]]
        assert len(outliers) >= 2

    def test_generate_box_plots_creates_output(self, sample_adlbc_data, temp_output_dir):
        """Test that generate_box_plots creates output files."""
        plotter = PHUSEBoxPlot(
            data=sample_adlbc_data,
            treatment_var="trtp",
            treatment_num_var="trtpn",
            measurement_var="aval",
            param_code_var="paramcd",
        )

        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"], figsize=(10, 6))

        # Check that at least one PDF was created
        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

        # Check file is not empty
        assert pdf_files[0].stat().st_size > 0

    def test_generate_box_plots_with_ref_lines_uniform(self, sample_adlbc_data, temp_output_dir):
        """Test box plot generation with UNIFORM reference lines."""
        plotter = PHUSEBoxPlot(
            data=sample_adlbc_data,
            treatment_var="trtp",
            measurement_var="aval",
            low_ref_var="anrlo",
            high_ref_var="anrhi",
        )

        # Should not crash with UNIFORM ref lines
        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"], ref_lines="UNIFORM")

        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

    def test_generate_box_plots_with_ref_lines_none(self, sample_adlbc_data, temp_output_dir):
        """Test box plot generation with no reference lines."""
        plotter = PHUSEBoxPlot(data=sample_adlbc_data, treatment_var="trtp", measurement_var="aval")

        # Should not crash with NONE ref lines
        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"], ref_lines="NONE")

        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

    def test_generate_box_plots_missing_ref_range_columns(self, sample_adlbc_data, temp_output_dir):
        """Test box plot generation when reference range columns are missing."""
        # Remove reference range columns
        df_no_ref = sample_adlbc_data.drop(columns=["anrlo", "anrhi"])

        plotter = PHUSEBoxPlot(
            data=df_no_ref,
            treatment_var="trtp",
            measurement_var="aval",
            low_ref_var="anrlo",  # Column doesn't exist
            high_ref_var="anrhi",  # Column doesn't exist
        )

        # Should not crash even without ref range columns
        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"])

        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0

    def test_generate_box_plots_no_data_passing_filters(self, sample_adlbc_data, temp_output_dir):
        """Test box plot generation when no data passes filters."""
        # Set all flags to 'N'
        df_no_analysis = sample_adlbc_data.copy()
        df_no_analysis["saffl"] = "N"
        df_no_analysis["anl01fl"] = "N"

        plotter = PHUSEBoxPlot(data=df_no_analysis, treatment_var="trtp", measurement_var="aval")

        # Should handle gracefully (no plots generated)
        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"])

        # No PDFs should be created
        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) == 0

    def test_generate_box_plots_single_parameter_single_timepoint(self, sample_adlbc_data, temp_output_dir):
        """Test simplest case: single parameter, single timepoint."""
        # Filter to single timepoint
        df_single = sample_adlbc_data[sample_adlbc_data["atptn"] == 1].copy()

        plotter = PHUSEBoxPlot(data=df_single, treatment_var="trtp", measurement_var="aval")

        plotter.generate_box_plots(output_dir=temp_output_dir, param_codes=["ALB"])

        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) == 1

    def test_convenience_function(self, sample_adlbc_data, temp_output_dir):
        """Test convenience function for generating box plots."""
        generate_phuse_box_plots(
            data=sample_adlbc_data,
            output_dir=temp_output_dir,
            treatment_var="trtp",
            treatment_num_var="trtpn",
            measurement_var="aval",
            param_code_var="paramcd",
        )

        pdf_files = list(temp_output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0


class TestEdgeCases:
    """Test edge cases for box plot generation."""

    def test_empty_dataset(self):
        """Test with empty dataset."""
        df_empty = pd.DataFrame()

        plotter = PHUSEBoxPlot(data=df_empty, treatment_var="trtp", measurement_var="aval")

        assert len(plotter.analysis_data) == 0

    def test_missing_required_columns(self):
        """Test with missing required columns."""
        df_minimal = pd.DataFrame({"aval": [1, 2, 3], "trtp": ["A", "B", "A"]})

        # Should initialize but may have issues generating plots
        plotter = PHUSEBoxPlot(data=df_minimal, treatment_var="trtp", measurement_var="aval")

        assert plotter.treatment_var == "trtp"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
