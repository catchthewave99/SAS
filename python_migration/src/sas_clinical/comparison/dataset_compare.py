"""
Dataset comparison module - Python equivalent of SAS %compvars, %complibs, and %compare macros.

This module provides comprehensive dataset comparison functionality for clinical trials data,
replicating the behavior of Roland's utility macros and Scott Bass's comparison macros.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Set
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetComparison:
    """
    Main class for comparing datasets and libraries.
    
    Replicates SAS macros:
    - %compvars: Compare variable lists between datasets
    - %complibs: Compare all datasets in two libraries
    - %compare: Detailed dataset/library comparison
    """
    
    def __init__(self):
        self.left_vars: Set[str] = set()
        self.right_vars: Set[str] = set()
        self.both_vars: Set[str] = set()
        self.comparison_results: Dict = {}
    
    def compare_variables(
        self, 
        df1: pd.DataFrame, 
        df2: pd.DataFrame,
        ds1_name: str = "Dataset 1",
        ds2_name: str = "Dataset 2"
    ) -> Dict[str, Set[str]]:
        """
        Compare variable lists between two datasets.
        
        Python equivalent of SAS %compvars macro.
        
        Args:
            df1: First dataset (left)
            df2: Second dataset (right)
            ds1_name: Name of first dataset for reporting
            ds2_name: Name of second dataset for reporting
            
        Returns:
            Dictionary with keys 'left', 'right', 'both' containing variable sets
        """
        vars1 = set(df1.columns)
        vars2 = set(df2.columns)
        
        self.left_vars = vars1 - vars2
        self.right_vars = vars2 - vars1
        self.both_vars = vars1 & vars2
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Variable Comparison: {ds1_name} vs {ds2_name}")
        logger.info(f"{'='*80}")
        logger.info(f"Variables in {ds1_name} but not {ds2_name}: {sorted(self.left_vars)}")
        logger.info(f"Variables in {ds2_name} but not {ds1_name}: {sorted(self.right_vars)}")
        logger.info(f"Variables in both datasets: {sorted(self.both_vars)}")
        logger.info(f"{'='*80}\n")
        
        return {
            'left': self.left_vars,
            'right': self.right_vars,
            'both': self.both_vars
        }
    
    def compare_datasets(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        by: Optional[Union[str, List[str]]] = None,
        ds1_name: str = "Base Dataset",
        ds2_name: str = "Comparison Dataset",
        tolerance: float = 1e-8
    ) -> Dict:
        """
        Detailed comparison of two datasets.
        
        Python equivalent of SAS %compare macro and PROC COMPARE.
        
        Args:
            df1: Base dataset
            df2: Comparison dataset
            by: Variable(s) to use for matching observations
            ds1_name: Name of base dataset
            ds2_name: Name of comparison dataset
            tolerance: Numeric tolerance for floating point comparisons
            
        Returns:
            Dictionary containing detailed comparison results
        """
        results = {
            'datasets': (ds1_name, ds2_name),
            'variable_comparison': self.compare_variables(df1, df2, ds1_name, ds2_name),
            'row_counts': (len(df1), len(df2)),
            'differences': {},
            'summary': {}
        }
        
        # Compare common variables
        common_vars = list(self.both_vars)
        
        if not common_vars:
            logger.warning("No common variables to compare!")
            results['summary']['status'] = 'NO_COMMON_VARS'
            return results
        
        # If by variable specified, merge on it
        if by:
            by_vars = [by] if isinstance(by, str) else by
            
            # Check if by variables exist in both datasets
            missing_by = set(by_vars) - self.both_vars
            if missing_by:
                logger.error(f"BY variables not in both datasets: {missing_by}")
                results['summary']['status'] = 'INVALID_BY_VARS'
                return results
            
            # Merge datasets
            merged = df1.merge(
                df2, 
                on=by_vars, 
                how='outer', 
                suffixes=('_base', '_comp'),
                indicator=True
            )
            
            # Identify observations only in one dataset
            only_base = merged[merged['_merge'] == 'left_only']
            only_comp = merged[merged['_merge'] == 'right_only']
            both = merged[merged['_merge'] == 'both']
            
            results['obs_only_in_base'] = len(only_base)
            results['obs_only_in_comp'] = len(only_comp)
            results['obs_in_both'] = len(both)
            
            logger.info(f"\nObservation Comparison (by {by_vars}):")
            logger.info(f"  Observations only in {ds1_name}: {len(only_base)}")
            logger.info(f"  Observations only in {ds2_name}: {len(only_comp)}")
            logger.info(f"  Observations in both: {len(both)}")
            
            # Compare values for common observations
            value_diffs = {}
            for var in common_vars:
                if var in by_vars:
                    continue
                
                base_col = f"{var}_base"
                comp_col = f"{var}_comp"
                
                if base_col not in both.columns or comp_col not in both.columns:
                    continue
                
                # Handle numeric vs string comparison
                if pd.api.types.is_numeric_dtype(both[base_col]) and pd.api.types.is_numeric_dtype(both[comp_col]):
                    # Numeric comparison with tolerance
                    diff_mask = ~np.isclose(
                        both[base_col].fillna(0), 
                        both[comp_col].fillna(0), 
                        rtol=tolerance, 
                        atol=tolerance,
                        equal_nan=True
                    )
                else:
                    # String comparison
                    diff_mask = both[base_col].fillna('') != both[comp_col].fillna('')
                
                num_diffs = diff_mask.sum()
                if num_diffs > 0:
                    value_diffs[var] = {
                        'num_differences': int(num_diffs),
                        'pct_different': float(num_diffs / len(both) * 100)
                    }
            
            results['value_differences'] = value_diffs
            
            if value_diffs:
                logger.info(f"\nValue Differences Found:")
                for var, diff_info in value_diffs.items():
                    logger.info(f"  {var}: {diff_info['num_differences']} differences ({diff_info['pct_different']:.2f}%)")
        
        else:
            # Simple row-by-row comparison without BY variable
            logger.info("\nPerforming row-by-row comparison (no BY variable specified)")
            
            # Compare only up to minimum number of rows
            min_rows = min(len(df1), len(df2))
            
            value_diffs = {}
            for var in common_vars:
                if pd.api.types.is_numeric_dtype(df1[var]) and pd.api.types.is_numeric_dtype(df2[var]):
                    diff_mask = ~np.isclose(
                        df1[var].iloc[:min_rows].fillna(0),
                        df2[var].iloc[:min_rows].fillna(0),
                        rtol=tolerance,
                        atol=tolerance,
                        equal_nan=True
                    )
                else:
                    diff_mask = df1[var].iloc[:min_rows].fillna('') != df2[var].iloc[:min_rows].fillna('')
                
                num_diffs = diff_mask.sum()
                if num_diffs > 0:
                    value_diffs[var] = {
                        'num_differences': int(num_diffs),
                        'pct_different': float(num_diffs / min_rows * 100)
                    }
            
            results['value_differences'] = value_diffs
        
        # Summary
        has_diffs = (
            len(self.left_vars) > 0 or 
            len(self.right_vars) > 0 or 
            len(df1) != len(df2) or
            len(results.get('value_differences', {})) > 0
        )
        
        results['summary']['status'] = 'DIFFERENCES_FOUND' if has_diffs else 'IDENTICAL'
        results['summary']['has_variable_diffs'] = len(self.left_vars) > 0 or len(self.right_vars) > 0
        results['summary']['has_row_count_diff'] = len(df1) != len(df2)
        results['summary']['has_value_diffs'] = len(results.get('value_differences', {})) > 0
        
        logger.info(f"\nComparison Summary: {results['summary']['status']}")
        
        return results
    
    def compare_libraries(
        self,
        lib1_path: Union[str, Path],
        lib2_path: Union[str, Path],
        by: Optional[Union[str, List[str]]] = None,
        file_pattern: str = "*.sas7bdat",
        tolerance: float = 1e-8
    ) -> Dict:
        """
        Compare all datasets in two libraries.
        
        Python equivalent of SAS %complibs macro.
        
        Args:
            lib1_path: Path to first library directory
            lib2_path: Path to second library directory
            by: Variable(s) to use for matching observations
            file_pattern: Pattern for dataset files (default: *.sas7bdat)
            tolerance: Numeric tolerance for comparisons
            
        Returns:
            Dictionary containing comparison results for all datasets
        """
        lib1_path = Path(lib1_path)
        lib2_path = Path(lib2_path)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Library Comparison")
        logger.info(f"  Library 1: {lib1_path}")
        logger.info(f"  Library 2: {lib2_path}")
        logger.info(f"{'='*80}\n")
        
        # Get list of datasets in each library
        lib1_files = {f.stem: f for f in lib1_path.glob(file_pattern)}
        lib2_files = {f.stem: f for f in lib2_path.glob(file_pattern)}
        
        only_lib1 = set(lib1_files.keys()) - set(lib2_files.keys())
        only_lib2 = set(lib2_files.keys()) - set(lib1_files.keys())
        common_datasets = set(lib1_files.keys()) & set(lib2_files.keys())
        
        logger.info(f"Datasets only in Library 1: {sorted(only_lib1)}")
        logger.info(f"Datasets only in Library 2: {sorted(only_lib2)}")
        logger.info(f"Common datasets: {sorted(common_datasets)}")
        logger.info(f"\nComparing {len(common_datasets)} common datasets...\n")
        
        results = {
            'library_paths': (str(lib1_path), str(lib2_path)),
            'only_lib1': sorted(only_lib1),
            'only_lib2': sorted(only_lib2),
            'common_datasets': sorted(common_datasets),
            'dataset_comparisons': {}
        }
        
        # Compare each common dataset
        for ds_name in sorted(common_datasets):
            logger.info(f"\n{'='*80}")
            logger.info(f"Comparing dataset: {ds_name}")
            logger.info(f"{'='*80}")
            
            try:
                # Read datasets (assuming SAS format, but will work with CSV too)
                df1 = self._read_dataset(lib1_files[ds_name])
                df2 = self._read_dataset(lib2_files[ds_name])
                
                # Compare datasets
                ds_results = self.compare_datasets(
                    df1, df2,
                    by=by,
                    ds1_name=f"lib1.{ds_name}",
                    ds2_name=f"lib2.{ds_name}",
                    tolerance=tolerance
                )
                
                results['dataset_comparisons'][ds_name] = ds_results
                
            except Exception as e:
                logger.error(f"Error comparing {ds_name}: {str(e)}")
                results['dataset_comparisons'][ds_name] = {'error': str(e)}
        
        return results
    
    def _read_dataset(self, file_path: Path) -> pd.DataFrame:
        """
        Read a dataset file (SAS or CSV format).
        
        Args:
            file_path: Path to dataset file
            
        Returns:
            DataFrame containing the dataset
        """
        if file_path.suffix.lower() in ['.sas7bdat', '.xpt']:
            try:
                import pyreadstat
                df, meta = pyreadstat.read_sas7bdat(str(file_path))
                return df
            except ImportError:
                logger.error("pyreadstat not installed. Install with: pip install pyreadstat")
                raise
        elif file_path.suffix.lower() == '.csv':
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")


def compare_vars(df1: pd.DataFrame, df2: pd.DataFrame, 
                 ds1_name: str = "Dataset 1", ds2_name: str = "Dataset 2") -> Dict[str, Set[str]]:
    """
    Convenience function for variable comparison.
    
    Python equivalent of SAS %compvars macro.
    """
    comp = DatasetComparison()
    return comp.compare_variables(df1, df2, ds1_name, ds2_name)


def compare_datasets(df1: pd.DataFrame, df2: pd.DataFrame,
                    by: Optional[Union[str, List[str]]] = None,
                    **kwargs) -> Dict:
    """
    Convenience function for dataset comparison.
    
    Python equivalent of SAS %compare macro.
    """
    comp = DatasetComparison()
    return comp.compare_datasets(df1, df2, by=by, **kwargs)


def compare_libraries(lib1_path: Union[str, Path], lib2_path: Union[str, Path],
                     by: Optional[Union[str, List[str]]] = None, **kwargs) -> Dict:
    """
    Convenience function for library comparison.
    
    Python equivalent of SAS %complibs macro.
    """
    comp = DatasetComparison()
    return comp.compare_libraries(lib1_path, lib2_path, by=by, **kwargs)
