"""
Convert XPT transport files to pandas DataFrames.

This is the Python equivalent of xpt2sas_adam_sdtm.sas.

The script reads XPT (SAS Transport) files from a directory and converts them
to pandas DataFrames, which can then be saved in various formats.

Original SAS script: programs/drafts/xpt2sas_adam_sdtm.sas
"""

from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

try:
    import xport
    XPORT_AVAILABLE = True
except ImportError:
    XPORT_AVAILABLE = False
    print("Warning: xport library not available. Install with: pip install xport")


def read_xpt_file(filepath: Union[str, Path]) -> Dict[str, pd.DataFrame]:
    """
    Read an XPT (SAS Transport) file and return its datasets.

    Args:
        filepath: Path to the XPT file

    Returns:
        Dictionary mapping dataset names to DataFrames
    """
    if not XPORT_AVAILABLE:
        raise ImportError("xport library is required. Install with: pip install xport")

    filepath = Path(filepath)
    datasets = {}

    with open(filepath, 'rb') as f:
        library = xport.v56.load(f)
        for name, dataset in library.items():
            datasets[name] = pd.DataFrame(dataset)

    return datasets


def convert_xpt_directory(
    source_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    output_format: str = 'csv'
) -> Dict[str, pd.DataFrame]:
    """
    Convert all XPT files in a directory to the specified format.

    This function replicates the functionality of the %drive macro in xpt2sas_adam_sdtm.sas.

    Args:
        source_dir: Directory containing XPT files
        output_dir: Directory to save converted files (defaults to source_dir)
        output_format: Output format ('csv', 'parquet', 'pickle')

    Returns:
        Dictionary mapping dataset names to DataFrames
    """
    source_dir = Path(source_dir)
    if output_dir is None:
        output_dir = source_dir
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    all_datasets = {}
    xpt_files = list(source_dir.glob("*.xpt")) + list(source_dir.glob("*.XPT"))

    print(f"Found {len(xpt_files)} XPT files in {source_dir}")

    for xpt_file in xpt_files:
        print(f"\nProcessing: {xpt_file.name}")

        try:
            datasets = read_xpt_file(xpt_file)

            for ds_name, df in datasets.items():
                print(f"  - Dataset: {ds_name} ({len(df)} rows, {len(df.columns)} columns)")

                if output_format == 'csv':
                    output_path = output_dir / f"{ds_name.lower()}.csv"
                    df.to_csv(output_path, index=False)
                elif output_format == 'parquet':
                    output_path = output_dir / f"{ds_name.lower()}.parquet"
                    df.to_parquet(output_path, index=False)
                elif output_format == 'pickle':
                    output_path = output_dir / f"{ds_name.lower()}.pkl"
                    df.to_pickle(output_path)
                else:
                    raise ValueError(f"Unsupported output format: {output_format}")

                print(f"    Saved to: {output_path}")
                all_datasets[ds_name] = df

        except Exception as e:
            print(f"  Error processing {xpt_file.name}: {e}")

    return all_datasets


def convert_adam_sdtm(
    base_dir: Optional[Union[str, Path]] = None,
    output_format: str = 'csv'
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Convert ADaM and SDTM XPT files to the specified format.

    This function replicates the main functionality of xpt2sas_adam_sdtm.sas.

    Args:
        base_dir: Base directory of the SAS repository
        output_format: Output format ('csv', 'parquet', 'pickle')

    Returns:
        Dictionary with 'adam' and 'sdtm' keys containing converted datasets
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
    base_dir = Path(base_dir)

    results = {}

    print("=" * 60)
    print("Converting XPT files to", output_format.upper())
    print("=" * 60)

    adam_dir = base_dir / "data" / "adam"
    if adam_dir.exists():
        print(f"\nProcessing ADaM directory: {adam_dir}")
        results['adam'] = convert_xpt_directory(adam_dir, adam_dir, output_format)
    else:
        print(f"\nADaM directory not found: {adam_dir}")

    sdtm_dir = base_dir / "data" / "sdtm"
    if sdtm_dir.exists():
        print(f"\nProcessing SDTM directory: {sdtm_dir}")
        results['sdtm'] = convert_xpt_directory(sdtm_dir, sdtm_dir, output_format)
    else:
        print(f"\nSDTM directory not found: {sdtm_dir}")

    print("\n" + "=" * 60)
    print("XPT conversion complete!")
    print("=" * 60)

    return results


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert XPT transport files to pandas-compatible formats.'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default=None,
        help='Base directory of the SAS repository'
    )
    parser.add_argument(
        '--source-dir',
        type=str,
        default=None,
        help='Source directory containing XPT files (overrides base-dir)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for converted files'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'parquet', 'pickle'],
        default='csv',
        help='Output format (default: csv)'
    )

    args = parser.parse_args()

    if args.source_dir:
        convert_xpt_directory(args.source_dir, args.output_dir, args.format)
    else:
        convert_adam_sdtm(args.base_dir, args.format)


if __name__ == '__main__':
    main()
