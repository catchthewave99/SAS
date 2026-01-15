"""
Example script showing how to call the box plot generator.

This is the Python equivalent of example_call_wpct-f.07.01.sas.

The script demonstrates how to:
- Set up paths and configuration
- Load and prepare test data
- Call the box plot generator with appropriate parameters

Original SAS script: programs/example_phuse_whitepapers/example_call_wpct-f.07.01.sas
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd
import pyreadstat

from boxplot_generator import generate_boxplots


def read_sas_dataset(filepath: Union[str, Path]) -> pd.DataFrame:
    """Read a SAS7BDAT dataset file into a pandas DataFrame."""
    df, meta = pyreadstat.read_sas7bdat(str(filepath))
    return df


def prepare_adlbc_data(
    data_path: Union[str, Path],
    add_timepoint: bool = True
) -> pd.DataFrame:
    """
    Load and prepare ADLBC data for box plot generation.

    Args:
        data_path: Path to the ADLBC SAS dataset
        add_timepoint: If True, add dummy timepoint variables if not present

    Returns:
        Prepared DataFrame
    """
    df = read_sas_dataset(data_path)

    df.columns = [c.upper() for c in df.columns]

    if add_timepoint:
        if 'ATPTN' not in df.columns:
            df['ATPTN'] = 1
            print("Added dummy ATPTN = 1")
        if 'ATPT' not in df.columns:
            df['ATPT'] = "TimePoint unknown"
            print("Added dummy ATPT = 'TimePoint unknown'")

    return df


def create_treatment_format(df: pd.DataFrame, tn_var: str = 'TRTPN') -> pd.DataFrame:
    """
    Create shortened treatment labels.

    Equivalent to the PROC FORMAT in the SAS script.

    Args:
        df: DataFrame with treatment data
        tn_var: Treatment number variable name

    Returns:
        DataFrame with added short treatment labels
    """
    tn_var = tn_var.upper()

    if tn_var not in df.columns:
        return df

    trt_format = {
        0: 'P',
        54: 'X-high',
        81: 'X-low'
    }

    df['TRTP_SHORT'] = df[tn_var].map(trt_format).fillna('UNEXPECTED')

    return df


def run_example(
    base_dir: Optional[Union[str, Path]] = None,
    output_folder: Optional[Union[str, Path]] = None,
    paramcd: str = 'ALB',
    avisitn_filter: Optional[list] = None
) -> None:
    """
    Run the example box plot generation.

    This function replicates the functionality of example_call_wpct-f.07.01.sas.

    Args:
        base_dir: Base directory of the SAS repository
        output_folder: Directory to save PDF outputs
        paramcd: Parameter code to filter (default: 'ALB' for Albumin)
        avisitn_filter: List of visit numbers to include
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
    base_dir = Path(base_dir)

    if output_folder is None:
        output_folder = base_dir / "results"
    output_folder = Path(output_folder)

    if avisitn_filter is None:
        avisitn_filter = [0, 2, 4, 6]

    print("=" * 60)
    print("EXAMPLE: Box Plot Generation")
    print("=" * 60)
    print(f"\nBase directory: {base_dir}")
    print(f"Output folder: {output_folder}")
    print(f"Parameter: {paramcd}")
    print(f"Visit filter: {avisitn_filter}")

    adlbc_path = base_dir / "data" / "adam" / "adlbc.sas7bdat"

    if not adlbc_path.exists():
        print(f"\nERROR: ADLBC dataset not found at: {adlbc_path}")
        print("Please ensure the data files are available.")
        return

    print(f"\nLoading data from: {adlbc_path}")
    df = prepare_adlbc_data(adlbc_path, add_timepoint=True)
    print(f"Loaded {len(df)} records")

    df = create_treatment_format(df, tn_var='TRTPN')

    print("\nGenerating box plots...")
    generated_files = generate_boxplots(
        data=df,
        output_folder=output_folder,
        m_var='AVAL',
        t_var='TRTP_SHORT',
        tn_var='TRTPN',
        lo_var='A1LO',
        hi_var='A1HI',
        p_fl='SAFFL',
        a_fl='ANL01FL',
        param_var='PARAMCD',
        param_label_var='PARAM',
        visit_var='AVISIT',
        visitn_var='AVISITN',
        atpt_var='ATPT',
        atptn_var='ATPTN',
        ref_lines='UNIFORM',
        max_boxes_per_page=20,
        paramcd_filter=[paramcd],
        avisitn_filter=avisitn_filter
    )

    print("\n" + "=" * 60)
    print("EXAMPLE COMPLETE")
    print("=" * 60)
    print(f"\nGenerated {len(generated_files)} PDF file(s):")
    for f in generated_files:
        print(f"  - {f}")


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Example script showing how to call the box plot generator.'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default=None,
        help='Base directory of the SAS repository'
    )
    parser.add_argument(
        '--output-folder',
        type=str,
        default=None,
        help='Directory to save PDF outputs'
    )
    parser.add_argument(
        '--paramcd',
        type=str,
        default='ALB',
        help='Parameter code to filter (default: ALB)'
    )
    parser.add_argument(
        '--avisitn',
        type=int,
        nargs='+',
        default=[0, 2, 4, 6],
        help='Visit numbers to include (default: 0 2 4 6)'
    )

    args = parser.parse_args()

    run_example(
        base_dir=args.base_dir,
        output_folder=args.output_folder,
        paramcd=args.paramcd,
        avisitn_filter=args.avisitn
    )


if __name__ == '__main__':
    main()
