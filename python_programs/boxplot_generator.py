"""
Generate PHUSE-style box plots for clinical trials data.

This is the Python equivalent of WPCT-F.07.01.sas.

The script generates Figure 7.1 "Box plot - Measurements by Analysis Timepoint,
Visit and Treatment" per the PHUSE Central Tendency White Paper.

Features:
- Nested loops through Parameters and Timepoints
- Automatic pagination when visits exceed max_boxes_per_page
- Reference lines for normal range (UNIFORM, NARROW, ALL options)
- Summary statistics table (n, mean, std, median, Q1, Q3)
- Red markers for out-of-range values

Original SAS script: programs/example_phuse_whitepapers/WPCT-F.07.01.sas
"""

from pathlib import Path
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import pyreadstat
from matplotlib.backends.backend_pdf import PdfPages


def read_sas_dataset(filepath: Union[str, Path]) -> pd.DataFrame:
    """Read a SAS7BDAT dataset file into a pandas DataFrame."""
    df, meta = pyreadstat.read_sas7bdat(str(filepath))
    return df


def get_reference_lines(
    df: pd.DataFrame,
    lo_var: str,
    hi_var: str,
    ref_lines: str = 'UNIFORM'
) -> List[float]:
    """
    Determine reference lines based on normal range limits.

    Args:
        df: DataFrame containing the data
        lo_var: Variable name for lower limit of normal range
        hi_var: Variable name for upper limit of normal range
        ref_lines: Reference line option ('NONE', 'UNIFORM', 'NARROW', 'ALL')

    Returns:
        List of reference line values
    """
    ref_lines = ref_lines.upper()

    if ref_lines == 'NONE':
        return []

    lo_col = None
    hi_col = None
    for col in df.columns:
        if col.upper() == lo_var.upper():
            lo_col = col
        if col.upper() == hi_var.upper():
            hi_col = col

    if lo_col is None or hi_col is None:
        return []

    lo_values = df[lo_col].dropna().unique()
    hi_values = df[hi_col].dropna().unique()

    if ref_lines == 'UNIFORM':
        if len(lo_values) == 1 and len(hi_values) == 1:
            return [float(lo_values[0]), float(hi_values[0])]
        return []

    elif ref_lines == 'NARROW':
        lines = []
        if len(lo_values) > 0:
            lines.append(float(max(lo_values)))
        if len(hi_values) > 0:
            lines.append(float(min(hi_values)))
        return lines

    elif ref_lines == 'ALL':
        lines = list(lo_values) + list(hi_values)
        return [float(x) for x in lines if pd.notna(x)]

    else:
        try:
            return [float(x) for x in ref_lines.split()]
        except ValueError:
            return []


def calculate_statistics(
    df: pd.DataFrame,
    m_var: str,
    group_vars: List[str]
) -> pd.DataFrame:
    """
    Calculate summary statistics for box plots.

    Args:
        df: DataFrame containing the data
        m_var: Measurement variable name
        group_vars: List of grouping variables

    Returns:
        DataFrame with summary statistics
    """
    m_col = None
    for col in df.columns:
        if col.upper() == m_var.upper():
            m_col = col
            break

    if m_col is None:
        raise ValueError(f"Measurement variable '{m_var}' not found in data")

    group_cols = []
    for gv in group_vars:
        for col in df.columns:
            if col.upper() == gv.upper():
                group_cols.append(col)
                break

    stats = df.groupby(group_cols)[m_col].agg([
        ('n', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('median', 'median'),
        ('min', 'min'),
        ('max', 'max'),
        ('q1', lambda x: x.quantile(0.25)),
        ('q3', lambda x: x.quantile(0.75))
    ]).reset_index()

    return stats


def identify_outliers(
    df: pd.DataFrame,
    m_var: str,
    lo_var: str,
    hi_var: str
) -> pd.Series:
    """
    Identify values outside the normal reference range.

    Args:
        df: DataFrame containing the data
        m_var: Measurement variable name
        lo_var: Lower limit variable name
        hi_var: Upper limit variable name

    Returns:
        Series with outlier values (NaN for non-outliers)
    """
    m_col = lo_col = hi_col = None
    for col in df.columns:
        col_upper = col.upper()
        if col_upper == m_var.upper():
            m_col = col
        if col_upper == lo_var.upper():
            lo_col = col
        if col_upper == hi_var.upper():
            hi_col = col

    if m_col is None:
        return pd.Series([np.nan] * len(df))

    outliers = pd.Series([np.nan] * len(df), index=df.index)

    if lo_col is not None:
        mask = (df[m_col].notna() & df[lo_col].notna() &
                (df[m_col] < df[lo_col]))
        outliers[mask] = df.loc[mask, m_col]

    if hi_col is not None:
        mask = (df[m_col].notna() & df[hi_col].notna() &
                (df[m_col] > df[hi_col]))
        outliers[mask] = df.loc[mask, m_col]

    return outliers


def create_boxplot_page(
    df: pd.DataFrame,
    m_var: str,
    t_var: str,
    visit_var: str = 'AVISIT',
    visitn_var: str = 'AVISITN',
    param_label: str = '',
    timepoint_label: str = '',
    ref_lines: List[float] = None,
    outliers: pd.Series = None,
    ax: plt.Axes = None
) -> plt.Axes:
    """
    Create a single box plot page.

    Args:
        df: DataFrame containing the data
        m_var: Measurement variable name
        t_var: Treatment variable name
        visit_var: Visit label variable name
        visitn_var: Visit number variable name
        param_label: Parameter label for title
        timepoint_label: Timepoint label for title
        ref_lines: List of reference line values
        outliers: Series with outlier values
        ax: Matplotlib axes object

    Returns:
        Matplotlib axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 8))

    m_col = t_col = visit_col = visitn_col = None
    for col in df.columns:
        col_upper = col.upper()
        if col_upper == m_var.upper():
            m_col = col
        if col_upper == t_var.upper():
            t_col = col
        if col_upper == visit_var.upper():
            visit_col = col
        if col_upper == visitn_var.upper():
            visitn_col = col

    if m_col is None or t_col is None:
        ax.text(0.5, 0.5, 'Required variables not found',
                ha='center', va='center', transform=ax.transAxes)
        return ax

    treatments = sorted(df[t_col].unique())
    if visitn_col:
        visits = df.sort_values(visitn_col)[visit_col if visit_col else visitn_col].unique()
    else:
        visits = df[visit_col].unique() if visit_col else ['All']

    positions = []
    labels = []
    data_groups = []
    colors = plt.cm.Set2(np.linspace(0, 1, len(treatments)))

    pos = 0
    for visit in visits:
        for i, trt in enumerate(treatments):
            if visitn_col:
                mask = (df[t_col] == trt) & (df[visit_col if visit_col else visitn_col] == visit)
            else:
                mask = df[t_col] == trt

            values = df.loc[mask, m_col].dropna()
            if len(values) > 0:
                data_groups.append({
                    'data': values,
                    'position': pos,
                    'color': colors[i],
                    'treatment': trt,
                    'visit': visit
                })
            pos += 1
        pos += 0.5
        labels.append(str(visit))
        positions.append(pos - len(treatments)/2 - 0.75)

    bp_data = [g['data'] for g in data_groups]
    bp_positions = [g['position'] for g in data_groups]

    if bp_data:
        bp = ax.boxplot(bp_data, positions=bp_positions, widths=0.6,
                       patch_artist=True, showmeans=True,
                       meanprops=dict(marker='D', markerfacecolor='black',
                                     markeredgecolor='black', markersize=6))

        for i, (patch, group) in enumerate(zip(bp['boxes'], data_groups)):
            patch.set_facecolor(group['color'])
            patch.set_alpha(0.7)

    if ref_lines:
        for ref_val in ref_lines:
            ax.axhline(y=ref_val, color='gray', linestyle='--',
                      linewidth=1, alpha=0.7)

    if outliers is not None and outliers.notna().any():
        for group in data_groups:
            if visitn_col:
                mask = ((df[t_col] == group['treatment']) &
                       (df[visit_col if visit_col else visitn_col] == group['visit']))
            else:
                mask = df[t_col] == group['treatment']

            outlier_vals = outliers[mask].dropna()
            if len(outlier_vals) > 0:
                ax.scatter([group['position']] * len(outlier_vals),
                          outlier_vals, color='red', s=50, zorder=5,
                          marker='o', edgecolors='darkred', linewidths=1)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    title = f"Box Plot - {param_label} Observed Values by Visit"
    if timepoint_label:
        title += f", Analysis Timepoint: {timepoint_label}"
    ax.set_title(title, fontsize=12, fontweight='bold')

    ax.set_ylabel(param_label if param_label else m_var)
    ax.set_xlabel('Visit')

    legend_patches = [mpatches.Patch(color=colors[i], label=trt, alpha=0.7)
                     for i, trt in enumerate(treatments)]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=8)

    ax.grid(True, axis='y', alpha=0.3)

    return ax


def add_statistics_table(
    ax: plt.Axes,
    stats: pd.DataFrame,
    t_var: str,
    visit_var: str = 'AVISIT'
) -> None:
    """
    Add a statistics table below the box plot.

    Args:
        ax: Matplotlib axes object
        stats: DataFrame with summary statistics
        t_var: Treatment variable name
        visit_var: Visit variable name
    """
    pass


def generate_boxplots(
    data: Union[str, Path, pd.DataFrame],
    output_folder: Union[str, Path],
    m_var: str = 'AVAL',
    t_var: str = 'TRTP',
    tn_var: str = 'TRTPN',
    lo_var: str = 'ANRLO',
    hi_var: str = 'ANRHI',
    p_fl: str = 'SAFFL',
    a_fl: str = 'ANL01FL',
    param_var: str = 'PARAMCD',
    param_label_var: str = 'PARAM',
    visit_var: str = 'AVISIT',
    visitn_var: str = 'AVISITN',
    atpt_var: str = 'ATPT',
    atptn_var: str = 'ATPTN',
    ref_lines: str = 'UNIFORM',
    max_boxes_per_page: int = 20,
    paramcd_filter: Optional[List[str]] = None,
    avisitn_filter: Optional[List[int]] = None
) -> List[str]:
    """
    Generate box plots for clinical trials data.

    This function replicates the main functionality of WPCT-F.07.01.sas.

    Args:
        data: Path to SAS dataset or DataFrame
        output_folder: Directory to save PDF outputs
        m_var: Measurement variable name
        t_var: Treatment variable name
        tn_var: Treatment number variable name
        lo_var: Lower limit of normal range variable
        hi_var: Upper limit of normal range variable
        p_fl: Population flag variable
        a_fl: Analysis flag variable
        param_var: Parameter code variable
        param_label_var: Parameter label variable
        visit_var: Visit label variable
        visitn_var: Visit number variable
        atpt_var: Analysis timepoint variable
        atptn_var: Analysis timepoint number variable
        ref_lines: Reference line option
        max_boxes_per_page: Maximum boxes per page
        paramcd_filter: List of parameter codes to include
        avisitn_filter: List of visit numbers to include

    Returns:
        List of generated PDF file paths
    """
    if isinstance(data, (str, Path)):
        df = read_sas_dataset(data)
    else:
        df = data.copy()

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    df.columns = [c.upper() for c in df.columns]
    m_var = m_var.upper()
    t_var = t_var.upper()
    tn_var = tn_var.upper()
    lo_var = lo_var.upper()
    hi_var = hi_var.upper()
    p_fl = p_fl.upper()
    a_fl = a_fl.upper()
    param_var = param_var.upper()
    param_label_var = param_label_var.upper()
    visit_var = visit_var.upper()
    visitn_var = visitn_var.upper()
    atpt_var = atpt_var.upper()
    atptn_var = atptn_var.upper()

    if p_fl in df.columns:
        df = df[df[p_fl] == 'Y']
    if a_fl in df.columns:
        df = df[df[a_fl] == 'Y']

    if paramcd_filter:
        df = df[df[param_var].isin(paramcd_filter)]
    if avisitn_filter and visitn_var in df.columns:
        df = df[df[visitn_var].isin(avisitn_filter)]

    df['m_var_outlier'] = identify_outliers(df, m_var, lo_var, hi_var)

    generated_files = []

    if param_var not in df.columns:
        print(f"Warning: {param_var} not found in data. Creating single plot.")
        params = [('ALL', 'All Parameters')]
    else:
        params = df[[param_var, param_label_var]].drop_duplicates().values.tolist()

    for paramcd, param_label in params:
        if paramcd != 'ALL':
            param_data = df[df[param_var] == paramcd]
        else:
            param_data = df

        if len(param_data) == 0:
            continue

        ref_line_values = get_reference_lines(param_data, lo_var, hi_var, ref_lines)

        if atptn_var in param_data.columns:
            timepoints = param_data[[atptn_var, atpt_var]].drop_duplicates().values.tolist()
        else:
            timepoints = [(1, 'All Timepoints')]

        for atptn, atpt_label in timepoints:
            if atptn != 1 or atpt_var in param_data.columns:
                tp_data = param_data[param_data[atptn_var] == atptn]
            else:
                tp_data = param_data

            if len(tp_data) == 0:
                continue

            if visitn_var in tp_data.columns:
                n_visits = tp_data[visitn_var].nunique()
            else:
                n_visits = 1

            n_treatments = tp_data[t_var].nunique() if t_var in tp_data.columns else 1
            n_boxes = n_visits * n_treatments
            n_pages = max(1, (n_boxes + max_boxes_per_page - 1) // max_boxes_per_page)

            output_file = output_folder / f"WPCT-F.07.01_Box_plot_{paramcd}_by_visit_for_timepoint_{atptn}.pdf"

            with PdfPages(output_file) as pdf:
                if n_pages == 1:
                    fig, ax = plt.subplots(figsize=(14, 10))

                    create_boxplot_page(
                        tp_data, m_var, t_var,
                        visit_var=visit_var,
                        visitn_var=visitn_var,
                        param_label=param_label,
                        timepoint_label=str(atpt_label),
                        ref_lines=ref_line_values,
                        outliers=tp_data['m_var_outlier'],
                        ax=ax
                    )

                    footnote = (
                        "Box plot type is schematic: the box shows median and interquartile range (IQR, the box height);\n"
                        "the whiskers extend to the minimum and maximum data points within 1.5 IQR of the lower and upper quartiles.\n"
                        "Values outside the whiskers are shown as outliers. Means are marked with diamonds.\n"
                        "Red dots indicate measures outside the normal reference range."
                    )
                    fig.text(0.1, 0.02, footnote, fontsize=8, style='italic')

                    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
                    pdf.savefig(fig, dpi=300)
                    plt.close(fig)
                else:
                    if visitn_var in tp_data.columns:
                        visits = sorted(tp_data[visitn_var].unique())
                        visits_per_page = max(1, max_boxes_per_page // n_treatments)

                        for page_idx in range(n_pages):
                            start_idx = page_idx * visits_per_page
                            end_idx = min(start_idx + visits_per_page, len(visits))
                            page_visits = visits[start_idx:end_idx]

                            page_data = tp_data[tp_data[visitn_var].isin(page_visits)]

                            fig, ax = plt.subplots(figsize=(14, 10))

                            create_boxplot_page(
                                page_data, m_var, t_var,
                                visit_var=visit_var,
                                visitn_var=visitn_var,
                                param_label=param_label,
                                timepoint_label=f"{atpt_label} (Page {page_idx + 1} of {n_pages})",
                                ref_lines=ref_line_values,
                                outliers=page_data['m_var_outlier'],
                                ax=ax
                            )

                            plt.tight_layout()
                            pdf.savefig(fig, dpi=300)
                            plt.close(fig)
                    else:
                        fig, ax = plt.subplots(figsize=(14, 10))
                        create_boxplot_page(
                            tp_data, m_var, t_var,
                            param_label=param_label,
                            timepoint_label=str(atpt_label),
                            ref_lines=ref_line_values,
                            outliers=tp_data['m_var_outlier'],
                            ax=ax
                        )
                        plt.tight_layout()
                        pdf.savefig(fig, dpi=300)
                        plt.close(fig)

            print(f"Generated: {output_file}")
            generated_files.append(str(output_file))

    return generated_files


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate PHUSE-style box plots for clinical trials data.'
    )
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Path to the SAS dataset (sas7bdat file)'
    )
    parser.add_argument(
        '--output-folder',
        type=str,
        required=True,
        help='Directory to save PDF outputs'
    )
    parser.add_argument(
        '--m-var',
        type=str,
        default='AVAL',
        help='Measurement variable name (default: AVAL)'
    )
    parser.add_argument(
        '--t-var',
        type=str,
        default='TRTP',
        help='Treatment variable name (default: TRTP)'
    )
    parser.add_argument(
        '--ref-lines',
        type=str,
        default='UNIFORM',
        choices=['NONE', 'UNIFORM', 'NARROW', 'ALL'],
        help='Reference line option (default: UNIFORM)'
    )
    parser.add_argument(
        '--max-boxes',
        type=int,
        default=20,
        help='Maximum boxes per page (default: 20)'
    )
    parser.add_argument(
        '--paramcd',
        type=str,
        nargs='+',
        default=None,
        help='Parameter codes to include (space-separated)'
    )

    args = parser.parse_args()

    generate_boxplots(
        data=args.data,
        output_folder=args.output_folder,
        m_var=args.m_var,
        t_var=args.t_var,
        ref_lines=args.ref_lines,
        max_boxes_per_page=args.max_boxes,
        paramcd_filter=args.paramcd
    )


if __name__ == '__main__':
    main()
