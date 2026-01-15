"""
Utility functions for data comparison and manipulation.

This module provides Python equivalents of the SAS comparison macros:
- compvars: Compare variable lists between two datasets
- complibs: Compare all datasets in two libraries (directories)
- compare: Detailed dataset/library comparison

Original SAS macros from Roland's utilmacros (datasavantconsulting.com)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import pandas as pd
import pyreadstat


def read_sas_dataset(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Read a SAS7BDAT dataset file into a pandas DataFrame.

    Args:
        filepath: Path to the SAS7BDAT file

    Returns:
        pandas DataFrame containing the dataset
    """
    df, meta = pyreadstat.read_sas7bdat(str(filepath))
    return df


def get_dataset_variables(df: pd.DataFrame) -> Set[str]:
    """
    Get the set of variable (column) names from a DataFrame.

    Args:
        df: pandas DataFrame

    Returns:
        Set of column names (uppercase for case-insensitive comparison)
    """
    return set(col.upper() for col in df.columns)


def compvars(ds1: pd.DataFrame, ds2: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Compare the differences in variables present in two datasets.

    This is the Python equivalent of the SAS %compvars macro.

    Args:
        ds1: First ("left") DataFrame for comparison
        ds2: Second ("right") DataFrame for comparison

    Returns:
        Dictionary with keys:
        - 'left': Variables in ds1 but not ds2
        - 'right': Variables in ds2 but not ds1
        - 'both': Variables in both ds1 and ds2
    """
    vars1 = get_dataset_variables(ds1)
    vars2 = get_dataset_variables(ds2)

    left_only = sorted(vars1 - vars2)
    right_only = sorted(vars2 - vars1)
    both = sorted(vars1 & vars2)

    return {
        'left': left_only,
        'right': right_only,
        'both': both
    }


def list_sas_datasets(directory: Union[str, Path]) -> List[str]:
    """
    List all SAS7BDAT datasets in a directory.

    Args:
        directory: Path to the directory

    Returns:
        List of dataset names (without extension)
    """
    dir_path = Path(directory)
    datasets = []
    for f in dir_path.glob("*.sas7bdat"):
        datasets.append(f.stem.upper())
    return sorted(datasets)


def complibs(
    lib_old: Union[str, Path],
    lib_new: Union[str, Path],
    sortvars: Optional[List[str]] = None,
    direct: bool = False,
    dslist: Optional[List[str]] = None
) -> Dict[str, dict]:
    """
    Compare identically-named datasets in two libraries (directories).

    This is the Python equivalent of the SAS %complibs macro.

    Args:
        lib_old: Path to the "old" library directory
        lib_new: Path to the "new" library directory
        sortvars: List of variables to sort by for comparison
        direct: If True, do observation-by-observation comparison
        dslist: Optional list of specific datasets to compare

    Returns:
        Dictionary with comparison results for each dataset
    """
    lib_old_path = Path(lib_old)
    lib_new_path = Path(lib_new)

    if dslist is None:
        old_datasets = set(list_sas_datasets(lib_old_path))
        new_datasets = set(list_sas_datasets(lib_new_path))
        common_datasets = sorted(old_datasets & new_datasets)

        only_in_old = sorted(old_datasets - new_datasets)
        only_in_new = sorted(new_datasets - old_datasets)
    else:
        common_datasets = [ds.upper() for ds in dslist]
        only_in_old = []
        only_in_new = []

    results = {
        'datasets_only_in_old': only_in_old,
        'datasets_only_in_new': only_in_new,
        'comparisons': {}
    }

    for ds_name in common_datasets:
        old_file = lib_old_path / f"{ds_name.lower()}.sas7bdat"
        new_file = lib_new_path / f"{ds_name.lower()}.sas7bdat"

        if not old_file.exists() or not new_file.exists():
            continue

        try:
            df_old = read_sas_dataset(old_file)
            df_new = read_sas_dataset(new_file)

            comparison = compare_datasets(
                df_old, df_new,
                by_vars=sortvars,
                direct=direct,
                dataset_name=ds_name
            )
            results['comparisons'][ds_name] = comparison
        except Exception as e:
            results['comparisons'][ds_name] = {'error': str(e)}

    return results


def compare_datasets(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    by_vars: Optional[List[str]] = None,
    direct: bool = False,
    dataset_name: str = "dataset"
) -> Dict:
    """
    Compare two datasets and return detailed comparison results.

    This is the Python equivalent of the SAS %compare macro.

    Args:
        base: Base DataFrame for comparison
        comp: Comparison DataFrame
        by_vars: List of variables to use as ID/sort variables
        direct: If True, do observation-by-observation comparison
        dataset_name: Name of the dataset for reporting

    Returns:
        Dictionary with comparison results
    """
    results = {
        'dataset_name': dataset_name,
        'base_obs': len(base),
        'comp_obs': len(comp),
        'variable_comparison': compvars(base, comp),
        'value_differences': [],
        'obs_differences': {
            'only_in_base': 0,
            'only_in_comp': 0,
            'in_both': 0
        }
    }

    base_cols = [c.upper() for c in base.columns]
    comp_cols = [c.upper() for c in comp.columns]
    base.columns = base_cols
    comp.columns = comp_cols

    common_vars = results['variable_comparison']['both']

    if not common_vars:
        results['error'] = "No common variables to compare"
        return results

    if by_vars:
        by_vars_upper = [v.upper() for v in by_vars]
        valid_by_vars = [v for v in by_vars_upper if v in common_vars]
    else:
        valid_by_vars = None

    if direct or not valid_by_vars:
        min_rows = min(len(base), len(comp))
        base_subset = base[common_vars].head(min_rows).reset_index(drop=True)
        comp_subset = comp[common_vars].head(min_rows).reset_index(drop=True)

        diff_mask = base_subset != comp_subset
        diff_count = diff_mask.sum().sum()

        results['direct_comparison'] = {
            'rows_compared': min_rows,
            'total_differences': int(diff_count),
            'differences_by_variable': {
                col: int(diff_mask[col].sum())
                for col in common_vars
                if diff_mask[col].sum() > 0
            }
        }
    else:
        base_sorted = base.sort_values(by=valid_by_vars).reset_index(drop=True)
        comp_sorted = comp.sort_values(by=valid_by_vars).reset_index(drop=True)

        base_keys = base_sorted[valid_by_vars].apply(tuple, axis=1)
        comp_keys = comp_sorted[valid_by_vars].apply(tuple, axis=1)

        base_key_set = set(base_keys)
        comp_key_set = set(comp_keys)

        only_in_base = base_key_set - comp_key_set
        only_in_comp = comp_key_set - base_key_set
        in_both = base_key_set & comp_key_set

        results['obs_differences'] = {
            'only_in_base': len(only_in_base),
            'only_in_comp': len(only_in_comp),
            'in_both': len(in_both)
        }

        if in_both:
            merged = pd.merge(
                base_sorted, comp_sorted,
                on=valid_by_vars,
                suffixes=('_base', '_comp'),
                how='inner'
            )

            value_vars = [v for v in common_vars if v not in valid_by_vars]
            diff_summary = {}

            for var in value_vars:
                base_col = f"{var}_base"
                comp_col = f"{var}_comp"

                if base_col in merged.columns and comp_col in merged.columns:
                    base_vals = merged[base_col]
                    comp_vals = merged[comp_col]

                    base_null = base_vals.isna()
                    comp_null = comp_vals.isna()

                    both_null = base_null & comp_null
                    neither_null = ~base_null & ~comp_null

                    diff_mask = pd.Series([False] * len(merged))
                    diff_mask[neither_null] = base_vals[neither_null].astype(str) != comp_vals[neither_null].astype(str)
                    diff_mask[base_null != comp_null] = True
                    diff_mask[both_null] = False

                    diff_count = diff_mask.sum()
                    if diff_count > 0:
                        diff_summary[var] = int(diff_count)

            results['value_differences'] = diff_summary

    return results


def compare(
    base: Union[str, Path, pd.DataFrame],
    comp: Union[str, Path, pd.DataFrame],
    by_vars: Optional[List[str]] = None,
    is_library: bool = False
) -> Dict:
    """
    Compare datasets or libraries.

    This is the Python equivalent of the SAS %compare macro from Scott Bass.

    Args:
        base: Base dataset (path, DataFrame) or library path
        comp: Comparison dataset (path, DataFrame) or library path
        by_vars: List of BY variables for comparison
        is_library: If True, treat base and comp as library paths

    Returns:
        Dictionary with comparison results
    """
    if is_library:
        return complibs(base, comp, sortvars=by_vars)

    if isinstance(base, (str, Path)):
        base_df = read_sas_dataset(base)
        base_name = Path(base).stem
    else:
        base_df = base
        base_name = "base"

    if isinstance(comp, (str, Path)):
        comp_df = read_sas_dataset(comp)
        comp_name = Path(comp).stem
    else:
        comp_df = comp
        comp_name = "comp"

    return compare_datasets(
        base_df, comp_df,
        by_vars=by_vars,
        dataset_name=f"{base_name} vs {comp_name}"
    )


def print_comparison_results(results: Dict, verbose: bool = True) -> None:
    """
    Print comparison results in a formatted manner.

    Args:
        results: Dictionary of comparison results from compare functions
        verbose: If True, print detailed output
    """
    if 'comparisons' in results:
        print("=" * 60)
        print("LIBRARY COMPARISON RESULTS")
        print("=" * 60)

        if results.get('datasets_only_in_old'):
            print(f"\nDatasets only in OLD library: {', '.join(results['datasets_only_in_old'])}")
        if results.get('datasets_only_in_new'):
            print(f"Datasets only in NEW library: {', '.join(results['datasets_only_in_new'])}")

        for ds_name, comp_result in results['comparisons'].items():
            print(f"\n{'-' * 40}")
            print(f"Dataset: {ds_name}")
            print(f"{'-' * 40}")
            _print_single_comparison(comp_result, verbose)
    else:
        _print_single_comparison(results, verbose)


def _print_single_comparison(results: Dict, verbose: bool = True) -> None:
    """Print results for a single dataset comparison."""
    if 'error' in results:
        print(f"ERROR: {results['error']}")
        return

    print(f"Base observations: {results.get('base_obs', 'N/A')}")
    print(f"Comparison observations: {results.get('comp_obs', 'N/A')}")

    var_comp = results.get('variable_comparison', {})
    if var_comp.get('left'):
        print(f"\nVariables only in BASE: {', '.join(var_comp['left'])}")
    if var_comp.get('right'):
        print(f"Variables only in COMP: {', '.join(var_comp['right'])}")
    if verbose and var_comp.get('both'):
        print(f"Variables in BOTH: {', '.join(var_comp['both'])}")

    obs_diff = results.get('obs_differences', {})
    if obs_diff:
        print(f"\nObservation differences:")
        print(f"  Only in BASE: {obs_diff.get('only_in_base', 0)}")
        print(f"  Only in COMP: {obs_diff.get('only_in_comp', 0)}")
        print(f"  In BOTH: {obs_diff.get('in_both', 0)}")

    val_diff = results.get('value_differences', {})
    if val_diff:
        print(f"\nValue differences by variable:")
        for var, count in val_diff.items():
            print(f"  {var}: {count} differences")

    direct_comp = results.get('direct_comparison', {})
    if direct_comp:
        print(f"\nDirect comparison:")
        print(f"  Rows compared: {direct_comp.get('rows_compared', 0)}")
        print(f"  Total differences: {direct_comp.get('total_differences', 0)}")
        if direct_comp.get('differences_by_variable'):
            print("  Differences by variable:")
            for var, count in direct_comp['differences_by_variable'].items():
                print(f"    {var}: {count}")
