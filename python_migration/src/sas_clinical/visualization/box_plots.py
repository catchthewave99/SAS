"""
Box plot visualization module - Python equivalent of WPCT-F.07.01.sas.

This module generates PHUSE-compliant box plots for clinical trials data,
replicating Figure 7.1: Box plot - Measurements by Analysis Timepoint, Visit and Treatment.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Union, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PHUSEBoxPlot:
    """
    Generate PHUSE-compliant box plots for clinical trials data.

    Python equivalent of WPCT-F.07.01.sas functionality.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        treatment_var: str = "trtp",
        treatment_num_var: str = "trtpn",
        measurement_var: str = "aval",
        visit_var: str = "avisit",
        visit_num_var: str = "avisitn",
        timepoint_var: str = "atpt",
        timepoint_num_var: str = "atptn",
        param_var: str = "param",
        param_code_var: str = "paramcd",
        low_ref_var: Optional[str] = "anrlo",
        high_ref_var: Optional[str] = "anrhi",
        population_flag: str = "saffl",
        analysis_flag: str = "anl01fl",
    ):
        """
        Initialize PHUSE box plot generator.

        Args:
            data: ADaM dataset (e.g., ADVS, ADLBC)
            treatment_var: Treatment name variable
            treatment_num_var: Treatment number variable (for ordering)
            measurement_var: Measurement value variable
            visit_var: Visit name variable
            visit_num_var: Visit number variable (for ordering)
            timepoint_var: Analysis timepoint name variable
            timepoint_num_var: Analysis timepoint number variable
            param_var: Parameter name variable
            param_code_var: Parameter code variable
            low_ref_var: Lower reference range variable
            high_ref_var: Upper reference range variable
            population_flag: Population flag variable
            analysis_flag: Analysis flag variable
        """
        self.data = data
        self.treatment_var = treatment_var
        self.treatment_num_var = treatment_num_var
        self.measurement_var = measurement_var
        self.visit_var = visit_var
        self.visit_num_var = visit_num_var
        self.timepoint_var = timepoint_var
        self.timepoint_num_var = timepoint_num_var
        self.param_var = param_var
        self.param_code_var = param_code_var
        self.low_ref_var = low_ref_var
        self.high_ref_var = high_ref_var
        self.population_flag = population_flag
        self.analysis_flag = analysis_flag

        # Filter to analysis population
        self.analysis_data = self._filter_analysis_population()

    def _filter_analysis_population(self) -> pd.DataFrame:
        """Filter data to analysis population."""
        df = self.data.copy()

        if self.population_flag in df.columns:
            df = df[df[self.population_flag] == "Y"]

        if self.analysis_flag in df.columns:
            df = df[df[self.analysis_flag] == "Y"]

        # Create outlier indicator
        if self.low_ref_var and self.high_ref_var:
            if self.low_ref_var in df.columns and self.high_ref_var in df.columns:
                df["is_outlier"] = (df[self.measurement_var] < df[self.low_ref_var]) | (
                    df[self.measurement_var] > df[self.high_ref_var]
                )
            else:
                df["is_outlier"] = False
        else:
            df["is_outlier"] = False

        return df

    def generate_box_plots(
        self,
        output_dir: Union[str, Path],
        param_codes: Optional[List[str]] = None,
        ref_lines: str = "UNIFORM",
        max_boxes_per_page: int = 20,
        figsize: Tuple[int, int] = (14, 8),
    ):
        """
        Generate box plots for all parameters and timepoints.

        Args:
            output_dir: Directory to save output plots
            param_codes: List of parameter codes to plot (None = all)
            ref_lines: Reference line option ('NONE', 'UNIFORM', 'NARROW', 'ALL')
            max_boxes_per_page: Maximum number of visit boxes per page
            figsize: Figure size (width, height)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get list of parameters
        if param_codes is None:
            param_codes = self.analysis_data[self.param_code_var].unique()

        logger.info("\n" + "=" * 80)
        logger.info("Generating PHUSE Box Plots")
        logger.info(f"  Parameters: {param_codes}")
        logger.info(f"  Output directory: {output_dir}")
        logger.info("=" * 80 + "\n")

        # Loop through each parameter
        for param_code in param_codes:
            param_data = self.analysis_data[self.analysis_data[self.param_code_var] == param_code]

            if len(param_data) == 0:
                logger.warning(f"No data for parameter: {param_code}")
                continue

            param_name = param_data[self.param_var].iloc[0]

            # Get timepoints for this parameter
            timepoints = sorted(param_data[self.timepoint_num_var].unique())

            # Loop through each timepoint
            for tp_num in timepoints:
                tp_data = param_data[param_data[self.timepoint_num_var] == tp_num]
                tp_name = tp_data[self.timepoint_var].iloc[0]

                # Generate plot
                self._generate_single_plot(tp_data, param_code, param_name, tp_name, output_dir, ref_lines, figsize)

    def _generate_single_plot(
        self,
        data: pd.DataFrame,
        param_code: str,
        param_name: str,
        timepoint_name: str,
        output_dir: Path,
        ref_lines: str,
        figsize: Tuple[int, int],
    ):
        """Generate a single box plot for a parameter and timepoint."""

        # Sort by visit number and treatment number
        data = data.sort_values([self.visit_num_var, self.treatment_num_var])

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create box plot
        visits = sorted(data[self.visit_num_var].unique())
        treatments = sorted(data[self.treatment_num_var].unique())

        # Prepare data for plotting
        plot_data = []
        positions = []
        labels = []
        pos = 0

        for visit_num in visits:
            visit_data = data[data[self.visit_num_var] == visit_num]
            visit_name = visit_data[self.visit_var].iloc[0]

            for trt_num in treatments:
                trt_data = visit_data[visit_data[self.treatment_num_var] == trt_num]

                if len(trt_data) > 0:
                    values = trt_data[self.measurement_var].dropna()
                    if len(values) > 0:
                        plot_data.append(values)
                        positions.append(pos)

                        trt_name = trt_data[self.treatment_var].iloc[0]
                        labels.append(f"{visit_name}\n{trt_name}")

                pos += 1

            pos += 0.5  # Add space between visits

        # Create box plot
        if plot_data:
            bp = ax.boxplot(
                plot_data,
                positions=positions,
                widths=0.6,
                patch_artist=True,
                showfliers=False,  # We'll add outliers separately
            )

            # Style boxes
            for patch in bp["boxes"]:
                patch.set_facecolor("lightblue")
                patch.set_alpha(0.7)

            # Add outliers as red dots
            for i, (pos, values) in enumerate(zip(positions, plot_data)):
                # Get reference ranges for this group
                visit_num = visits[i // len(treatments)]
                trt_num = treatments[i % len(treatments)]

                group_data = data[(data[self.visit_num_var] == visit_num) & (data[self.treatment_num_var] == trt_num)]

                outliers = group_data[group_data["is_outlier"]][self.measurement_var]
                if len(outliers) > 0:
                    ax.scatter([pos] * len(outliers), outliers, color="red", s=50, zorder=3, alpha=0.6)

            # Add reference lines
            if ref_lines != "NONE" and self.low_ref_var and self.high_ref_var:
                self._add_reference_lines(ax, data, ref_lines)

            # Set labels and title
            ax.set_xticks(positions)
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel(f"{param_name} ({self.measurement_var.upper()})", fontsize=10)
            ax.set_title(
                f"Box Plot: {param_name} by Visit and Treatment\n" f"Analysis Timepoint: {timepoint_name}",
                fontsize=12,
                fontweight="bold",
            )

            # Add grid
            ax.grid(axis="y", alpha=0.3, linestyle="--")

            # Add statistics table
            self._add_statistics_table(fig, ax, data, visits, treatments)

            plt.tight_layout()

            # Save plot
            output_file = output_dir / f"WPCT-F.07.01_{param_code}_{timepoint_name.replace(' ', '_')}.pdf"
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"  Generated: {output_file.name}")

    def _add_reference_lines(self, ax, data: pd.DataFrame, ref_lines: str):
        """Add reference range lines to plot."""
        if self.low_ref_var not in data.columns or self.high_ref_var not in data.columns:
            return

        low_vals = data[self.low_ref_var].dropna()
        high_vals = data[self.high_ref_var].dropna()

        if len(low_vals) == 0 or len(high_vals) == 0:
            return

        if ref_lines == "UNIFORM":
            # Only plot if uniform across all observations
            if low_vals.nunique() == 1 and high_vals.nunique() == 1:
                ax.axhline(low_vals.iloc[0], color="green", linestyle="--", linewidth=1, alpha=0.7, label="Lower Ref")
                ax.axhline(high_vals.iloc[0], color="green", linestyle="--", linewidth=1, alpha=0.7, label="Upper Ref")

        elif ref_lines == "NARROW":
            # Plot narrowest range (max low, min high)
            ax.axhline(low_vals.max(), color="green", linestyle="--", linewidth=1, alpha=0.7, label="Lower Ref")
            ax.axhline(high_vals.min(), color="green", linestyle="--", linewidth=1, alpha=0.7, label="Upper Ref")

        elif ref_lines == "ALL":
            # Plot all unique reference lines
            for val in low_vals.unique():
                ax.axhline(val, color="green", linestyle="--", linewidth=0.5, alpha=0.5)
            for val in high_vals.unique():
                ax.axhline(val, color="green", linestyle="--", linewidth=0.5, alpha=0.5)

    def _add_statistics_table(self, fig, ax, data: pd.DataFrame, visits: List, treatments: List):
        """Add summary statistics table below the plot."""
        # Calculate statistics for each visit/treatment combination
        stats_data = []

        for visit_num in visits:
            for trt_num in treatments:
                group_data = data[(data[self.visit_num_var] == visit_num) & (data[self.treatment_num_var] == trt_num)]

                if len(group_data) > 0:
                    values = group_data[self.measurement_var].dropna()

                    if len(values) > 0:
                        stats_data.append(
                            {
                                "Visit": group_data[self.visit_var].iloc[0],
                                "Treatment": group_data[self.treatment_var].iloc[0],
                                "N": len(values),
                                "Mean": f"{values.mean():.2f}",
                                "SD": f"{values.std():.2f}",
                                "Median": f"{values.median():.2f}",
                                "Q1": f"{values.quantile(0.25):.2f}",
                                "Q3": f"{values.quantile(0.75):.2f}",
                            }
                        )

        if stats_data:
            stats_df = pd.DataFrame(stats_data)

            # Add table as text annotation (simplified version)
            table_text = "Summary Statistics:\n"
            table_text += f"{'Visit':<15} {'Trt':<10} {'N':<5} {'Mean':<8} {'SD':<8} {'Median':<8}\n"
            table_text += "-" * 70 + "\n"

            for _, row in stats_df.head(10).iterrows():  # Limit to first 10 rows
                table_text += f"{row['Visit']:<15} {row['Treatment']:<10} {row['N']:<5} "
                table_text += f"{row['Mean']:<8} {row['SD']:<8} {row['Median']:<8}\n"

            # Add as figure text
            fig.text(0.1, 0.02, table_text, fontsize=7, family="monospace", verticalalignment="bottom")


def generate_phuse_box_plots(data: pd.DataFrame, output_dir: Union[str, Path], **kwargs):
    """
    Convenience function to generate PHUSE box plots.

    Python equivalent of WPCT-F.07.01.sas.
    """
    plotter = PHUSEBoxPlot(data, **kwargs)
    plotter.generate_box_plots(output_dir)
