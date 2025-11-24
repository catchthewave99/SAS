"""
Example script demonstrating dataset comparison functionality.

Python equivalent of test_compare_macros.sas.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sas_clinical.comparison.dataset_compare import (
    DatasetComparison,
    compare_vars,
    compare_datasets,
    compare_libraries
)
from sas_clinical.data_processing.test_data_generator import create_test_data
import pandas as pd


def main():
    """Run comparison examples."""
    
    # Set up paths
    base_dir = Path(__file__).parent.parent.parent
    adam_path = base_dir / 'data' / 'adam'
    adam_mod_path = base_dir / 'data' / 'adam' / 'mod_01_python'
    
    print("\n" + "="*80)
    print("Python Clinical Trials Data Comparison Examples")
    print("="*80 + "\n")
    
    # Example 1: Create test data
    print("\n" + "="*80)
    print("Example 1: Creating Test Data")
    print("="*80 + "\n")
    
    # Note: This would require SAS datasets to be present
    # For demonstration, we'll show the API
    # create_test_data(adam_path, adam_mod_path)
    
    # Example 2: Compare variables between two datasets
    print("\n" + "="*80)
    print("Example 2: Compare Variables (compvars)")
    print("="*80 + "\n")
    
    # Create sample datasets for demonstration
    df1 = pd.DataFrame({
        'usubjid': ['001', '002', '003'],
        'age': [25, 30, 35],
        'sex': ['M', 'F', 'M'],
        'race': ['WHITE', 'BLACK', 'ASIAN'],
        'saffl': ['Y', 'Y', 'Y']
    })
    
    df2 = pd.DataFrame({
        'usubjid': ['001', '002', '003'],
        'age': [25, 30, 35],
        'sex': ['M', 'F', 'M'],
        'race': ['WHITE', 'WHITE', 'ASIAN'],  # Modified value
        'newvar': ['A', 'B', 'C']  # New variable (saffl dropped)
    })
    
    # Compare variables
    var_comparison = compare_vars(df1, df2, "Original Dataset", "Modified Dataset")
    
    print(f"\nVariables only in Original: {var_comparison['left']}")
    print(f"Variables only in Modified: {var_comparison['right']}")
    print(f"Variables in both: {var_comparison['both']}")
    
    # Example 3: Detailed dataset comparison
    print("\n" + "="*80)
    print("Example 3: Detailed Dataset Comparison (compare)")
    print("="*80 + "\n")
    
    results = compare_datasets(
        df1, df2,
        by='usubjid',
        ds1_name="Original Dataset",
        ds2_name="Modified Dataset"
    )
    
    print(f"\nComparison Status: {results['summary']['status']}")
    print(f"Has variable differences: {results['summary']['has_variable_diffs']}")
    print(f"Has value differences: {results['summary']['has_value_diffs']}")
    
    if results.get('value_differences'):
        print("\nValue Differences:")
        for var, diff_info in results['value_differences'].items():
            print(f"  {var}: {diff_info['num_differences']} differences")
    
    # Example 4: Library comparison
    print("\n" + "="*80)
    print("Example 4: Library Comparison (complibs)")
    print("="*80 + "\n")
    
    print("Note: Library comparison requires actual SAS datasets.")
    print("API usage:")
    print("""
    results = compare_libraries(
        lib1_path='data/adam',
        lib2_path='data/adam/mod_01',
        by='usubjid'
    )
    """)
    
    # Example 5: Using DatasetComparison class directly
    print("\n" + "="*80)
    print("Example 5: Using DatasetComparison Class")
    print("="*80 + "\n")
    
    comp = DatasetComparison()
    
    # Compare variables
    var_results = comp.compare_variables(df1, df2, "Dataset A", "Dataset B")
    
    # Compare datasets
    ds_results = comp.compare_datasets(df1, df2, by='usubjid')
    
    print("\nComparison complete!")
    print(f"Status: {ds_results['summary']['status']}")
    
    print("\n" + "="*80)
    print("All Examples Complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
