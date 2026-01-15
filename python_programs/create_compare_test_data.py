"""
Create test data with controlled modifications for comparison testing.

This is the Python equivalent of CreateCompareTestData.sas.

The script creates modified versions of ADaM datasets with known differences
to test the comparison macros/functions:
- Copies original datasets (adsl, adae, advs) to a modified directory
- Modifies adtte dataset:
  - Drops 'saffl' variable
  - Adds 'newvar' variable
  - Deletes every 17th observation
  - Modifies row 11 (race, aval values)
  - Duplicates row 20 with modified usubjid
- Creates a new dataset called 'new'

Original SAS script: programs/drafts/CreateCompareTestData.sas
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
import pyreadstat


def read_sas_dataset(filepath: Union[str, Path]) -> pd.DataFrame:
    """Read a SAS7BDAT dataset file into a pandas DataFrame."""
    df, meta = pyreadstat.read_sas7bdat(str(filepath))
    return df


def write_sas_dataset(df: pd.DataFrame, filepath: Union[str, Path]) -> None:
    """
    Write a pandas DataFrame to a SAS7BDAT file.

    Note: pyreadstat can read but not write SAS7BDAT files.
    We'll save as CSV for the Python version, which can be read by pandas.
    For full SAS compatibility, the data would need to be converted using SAS.
    """
    filepath = Path(filepath)
    csv_path = filepath.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved dataset to: {csv_path}")


def copy_dataset(
    source_dir: Union[str, Path],
    dest_dir: Union[str, Path],
    dataset_name: str
) -> pd.DataFrame:
    """
    Copy a dataset from source to destination directory.

    Args:
        source_dir: Source directory path
        dest_dir: Destination directory path
        dataset_name: Name of the dataset (without extension)

    Returns:
        The copied DataFrame
    """
    source_path = Path(source_dir) / f"{dataset_name}.sas7bdat"
    df = read_sas_dataset(source_path)

    dest_path = Path(dest_dir) / f"{dataset_name}.csv"
    df.to_csv(dest_path, index=False)
    print(f"Copied {dataset_name} from {source_dir} to {dest_dir}")

    return df


def create_compare_test_data(
    base_dir: Optional[Union[str, Path]] = None,
    adam_dir: Optional[Union[str, Path]] = None,
    adam_mod_dir: Optional[Union[str, Path]] = None
) -> dict:
    """
    Create test data with controlled modifications for comparison testing.

    This function replicates the functionality of CreateCompareTestData.sas.

    Args:
        base_dir: Base directory of the SAS repository
        adam_dir: Path to the original ADaM data directory
        adam_mod_dir: Path to the modified ADaM data directory

    Returns:
        Dictionary containing the created/modified datasets
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
    base_dir = Path(base_dir)

    if adam_dir is None:
        adam_dir = base_dir / "data" / "adam"
    adam_dir = Path(adam_dir)

    if adam_mod_dir is None:
        adam_mod_dir = adam_dir / "mod_01"
    adam_mod_dir = Path(adam_mod_dir)

    adam_mod_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    print("=" * 60)
    print("Creating Compare Test Data")
    print("=" * 60)
    print(f"Source directory: {adam_dir}")
    print(f"Output directory: {adam_mod_dir}")
    print()

    print("Step 1: Copying original datasets (adsl, adae, advs)...")
    for ds_name in ['adsl', 'adae', 'advs']:
        try:
            df = copy_dataset(adam_dir, adam_mod_dir, ds_name)
            results[ds_name] = df
        except FileNotFoundError:
            print(f"  Warning: {ds_name}.sas7bdat not found, skipping...")

    print("\nStep 2: Creating modified adtte dataset...")
    try:
        adtte_path = adam_dir / "adtte.sas7bdat"
        adtte = read_sas_dataset(adtte_path)
        original_rows = len(adtte)
        original_cols = list(adtte.columns)

        adtte_mod = adtte.copy()

        saffl_col = None
        for col in adtte_mod.columns:
            if col.upper() == 'SAFFL':
                saffl_col = col
                break

        if saffl_col:
            adtte_mod = adtte_mod.drop(columns=[saffl_col])
            print(f"  - Dropped variable: {saffl_col}")
        else:
            print("  - Variable 'saffl' not found, skipping drop")

        adtte_mod['newvar'] = ''
        print("  - Added variable: newvar (character, length 10)")

        rows_to_delete = [i for i in range(len(adtte_mod)) if (i + 1) % 17 == 0]
        adtte_mod = adtte_mod.drop(adtte_mod.index[rows_to_delete]).reset_index(drop=True)
        print(f"  - Deleted every 17th observation ({len(rows_to_delete)} rows deleted)")

        if len(adtte_mod) > 10:
            race_col = None
            aval_col = None
            for col in adtte_mod.columns:
                if col.upper() == 'RACE':
                    race_col = col
                elif col.upper() == 'AVAL':
                    aval_col = col

            if race_col:
                adtte_mod.loc[10, race_col] = 'white'
                print(f"  - Modified row 11: {race_col} = 'white'")
            if aval_col:
                adtte_mod.loc[10, aval_col] = np.nan
                print(f"  - Modified row 11: {aval_col} = missing")

        if len(adtte_mod) > 19:
            usubjid_col = None
            for col in adtte_mod.columns:
                if col.upper() == 'USUBJID':
                    usubjid_col = col
                    break

            if usubjid_col:
                duplicate_row = adtte_mod.iloc[19].copy()
                duplicate_row[usubjid_col] = '01-705-1185'
                adtte_mod = pd.concat([adtte_mod, pd.DataFrame([duplicate_row])], ignore_index=True)
                print(f"  - Duplicated row 20 with {usubjid_col} = '01-705-1185'")

        output_path = adam_mod_dir / "adtte.csv"
        adtte_mod.to_csv(output_path, index=False)
        print(f"  - Saved modified adtte to: {output_path}")

        results['adtte'] = adtte_mod

        print(f"\n  Summary of adtte modifications:")
        print(f"    Original rows: {original_rows}")
        print(f"    Modified rows: {len(adtte_mod)}")
        print(f"    Original columns: {len(original_cols)}")
        print(f"    Modified columns: {len(adtte_mod.columns)}")

    except FileNotFoundError:
        print("  Warning: adtte.sas7bdat not found, skipping...")

    print("\nStep 3: Creating new dataset 'new'...")
    new_df = pd.DataFrame({'test': [1]})
    new_path = adam_mod_dir / "new.csv"
    new_df.to_csv(new_path, index=False)
    print(f"  - Created new dataset with test=1: {new_path}")
    results['new'] = new_df

    print("\n" + "=" * 60)
    print("Test data creation complete!")
    print("=" * 60)

    return results


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Create test data with controlled modifications for comparison testing.'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default=None,
        help='Base directory of the SAS repository'
    )
    parser.add_argument(
        '--adam-dir',
        type=str,
        default=None,
        help='Path to the original ADaM data directory'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Path to the modified ADaM data output directory'
    )

    args = parser.parse_args()

    create_compare_test_data(
        base_dir=args.base_dir,
        adam_dir=args.adam_dir,
        adam_mod_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
