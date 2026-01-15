"""
Test the comparison functions (Python equivalents of SAS comparison macros).

This is the Python equivalent of test_compare_macros.sas.

The script demonstrates and tests the comparison functions:
- compvars: Compare variable lists between two datasets
- complibs: Compare all datasets in two libraries (directories)
- compare: Detailed dataset/library comparison

Original SAS script: programs/example_compare/test_compare_macros.sas
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from utils import (
    compvars,
    complibs,
    compare,
    read_sas_dataset,
    print_comparison_results
)


def test_compvars(
    adam_dir: Union[str, Path],
    adam_mod_dir: Union[str, Path]
) -> None:
    """
    Test the compvars function.

    Equivalent to the COMPVARS section in test_compare_macros.sas.

    Args:
        adam_dir: Path to the original ADaM data directory
        adam_mod_dir: Path to the modified ADaM data directory
    """
    print("\n" + "=" * 60)
    print("COMPVARS TEST")
    print("=" * 60)

    ds1_path = Path(adam_dir) / "adtte.sas7bdat"
    ds2_path = Path(adam_mod_dir) / "adtte.sas7bdat"

    if not ds2_path.exists():
        ds2_path = Path(adam_mod_dir) / "adtte.csv"

    print(f"\nTest 1: Comparing {ds1_path.name} vs {ds2_path.name}")
    print("-" * 40)

    try:
        ds1 = read_sas_dataset(ds1_path)
    except Exception:
        print(f"Could not read {ds1_path}, trying CSV...")
        ds1 = pd.read_csv(ds1_path.with_suffix('.csv'))

    try:
        if ds2_path.suffix == '.csv':
            ds2 = pd.read_csv(ds2_path)
        else:
            ds2 = read_sas_dataset(ds2_path)
    except Exception as e:
        print(f"Could not read {ds2_path}: {e}")
        return

    result = compvars(ds1, ds2)

    print(f"\nVariables found in ds1 (adam.adtte) but not ds2 (adam_mod.adtte):")
    print(f"  {', '.join(result['left']) if result['left'] else '(none)'}")

    print(f"\nVariables found in ds2 (adam_mod.adtte) but not ds1 (adam.adtte):")
    print(f"  {', '.join(result['right']) if result['right'] else '(none)'}")

    print(f"\nVariables found in both ds1 and ds2:")
    print(f"  {', '.join(result['both']) if result['both'] else '(none)'}")

    print("\n" + "-" * 40)
    print("Test 2: Comparing using WORK library equivalent (in-memory DataFrames)")
    print("-" * 40)

    adtte = ds1.copy()
    adtte_mod = ds2.copy()

    result2 = compvars(adtte, adtte_mod)

    print(f"\nVariables found in adtte but not adtte_mod:")
    print(f"  {', '.join(result2['left']) if result2['left'] else '(none)'}")

    print(f"\nVariables found in adtte_mod but not adtte:")
    print(f"  {', '.join(result2['right']) if result2['right'] else '(none)'}")

    print(f"\nVariables found in both adtte and adtte_mod:")
    print(f"  {', '.join(result2['both']) if result2['both'] else '(none)'}")


def test_complibs(
    adam_dir: Union[str, Path],
    adam_mod_dir: Union[str, Path]
) -> None:
    """
    Test the complibs function.

    Equivalent to the COMPLIB section in test_compare_macros.sas.

    Args:
        adam_dir: Path to the original ADaM data directory
        adam_mod_dir: Path to the modified ADaM data directory
    """
    print("\n" + "=" * 60)
    print("COMPLIBS TEST")
    print("=" * 60)

    print("\nTest 3: Comparing libraries without sort variables")
    print("-" * 40)

    result = complibs(adam_dir, adam_mod_dir)
    print_comparison_results(result, verbose=False)

    print("\n" + "-" * 40)
    print("Test 4: Comparing libraries with sortvars=usubjid")
    print("-" * 40)

    result2 = complibs(adam_dir, adam_mod_dir, sortvars=['usubjid'])
    print_comparison_results(result2, verbose=False)


def test_compare(
    adam_dir: Union[str, Path],
    adam_mod_dir: Union[str, Path]
) -> None:
    """
    Test the compare function.

    Equivalent to the COMPARE section in test_compare_macros.sas.

    Args:
        adam_dir: Path to the original ADaM data directory
        adam_mod_dir: Path to the modified ADaM data directory
    """
    print("\n" + "=" * 60)
    print("COMPARE TEST")
    print("=" * 60)

    print("\nTest 5: Comparing single dataset (adam.adtte vs adam_mod.adtte)")
    print("-" * 40)

    base_path = Path(adam_dir) / "adtte.sas7bdat"
    comp_path = Path(adam_mod_dir) / "adtte.sas7bdat"

    if not comp_path.exists():
        comp_path = Path(adam_mod_dir) / "adtte.csv"

    result = compare(base_path, comp_path, by_vars=['usubjid'])
    print_comparison_results(result, verbose=True)

    print("\n" + "-" * 40)
    print("Test 6: Comparing libraries (adam vs adam_mod)")
    print("-" * 40)

    result2 = compare(adam_dir, adam_mod_dir, by_vars=['usubjid'], is_library=True)
    print_comparison_results(result2, verbose=True)


def run_all_tests(
    base_dir: Optional[Union[str, Path]] = None,
    adam_dir: Optional[Union[str, Path]] = None,
    adam_mod_dir: Optional[Union[str, Path]] = None
) -> None:
    """
    Run all comparison tests.

    This function replicates the full functionality of test_compare_macros.sas.

    Args:
        base_dir: Base directory of the SAS repository
        adam_dir: Path to the original ADaM data directory
        adam_mod_dir: Path to the modified ADaM data directory
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

    print("=" * 60)
    print("TESTING COMPARISON MACROS (Python Equivalents)")
    print("=" * 60)
    print(f"\nBase directory: {base_dir}")
    print(f"ADaM directory: {adam_dir}")
    print(f"ADaM modified directory: {adam_mod_dir}")

    if not adam_dir.exists():
        print(f"\nERROR: ADaM directory not found: {adam_dir}")
        return

    if not adam_mod_dir.exists():
        print(f"\nWARNING: Modified ADaM directory not found: {adam_mod_dir}")
        print("Run create_compare_test_data.py first to create test data.")
        return

    test_compvars(adam_dir, adam_mod_dir)

    test_complibs(adam_dir, adam_mod_dir)

    test_compare(adam_dir, adam_mod_dir)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Test the comparison functions (Python equivalents of SAS comparison macros).'
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
        '--adam-mod-dir',
        type=str,
        default=None,
        help='Path to the modified ADaM data directory'
    )

    args = parser.parse_args()

    run_all_tests(
        base_dir=args.base_dir,
        adam_dir=args.adam_dir,
        adam_mod_dir=args.adam_mod_dir
    )


if __name__ == '__main__':
    main()
