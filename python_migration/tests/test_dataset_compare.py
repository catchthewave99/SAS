"""
Unit tests for dataset comparison functionality.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sas_clinical.comparison.dataset_compare import (
    DatasetComparison,
    compare_vars,
    compare_datasets
)


class TestDatasetComparison:
    """Test suite for DatasetComparison class."""
    
    @pytest.fixture
    def sample_df1(self):
        """Create sample dataset 1."""
        return pd.DataFrame({
            'usubjid': ['001', '002', '003', '004'],
            'age': [25, 30, 35, 40],
            'sex': ['M', 'F', 'M', 'F'],
            'race': ['WHITE', 'BLACK', 'ASIAN', 'WHITE'],
            'saffl': ['Y', 'Y', 'Y', 'Y']
        })
    
    @pytest.fixture
    def sample_df2(self):
        """Create sample dataset 2 with modifications."""
        return pd.DataFrame({
            'usubjid': ['001', '002', '003', '004'],
            'age': [25, 30, 35, 40],
            'sex': ['M', 'F', 'M', 'F'],
            'race': ['WHITE', 'WHITE', 'ASIAN', 'WHITE'],  # Modified value
            'newvar': ['A', 'B', 'C', 'D']  # New variable (saffl dropped)
        })
    
    def test_compare_variables_left_only(self, sample_df1, sample_df2):
        """Test detection of variables only in left dataset."""
        comp = DatasetComparison()
        result = comp.compare_variables(sample_df1, sample_df2)
        
        assert 'saffl' in result['left']
        assert len(result['left']) == 1
    
    def test_compare_variables_right_only(self, sample_df1, sample_df2):
        """Test detection of variables only in right dataset."""
        comp = DatasetComparison()
        result = comp.compare_variables(sample_df1, sample_df2)
        
        assert 'newvar' in result['right']
        assert len(result['right']) == 1
    
    def test_compare_variables_both(self, sample_df1, sample_df2):
        """Test detection of variables in both datasets."""
        comp = DatasetComparison()
        result = comp.compare_variables(sample_df1, sample_df2)
        
        expected_both = {'usubjid', 'age', 'sex', 'race'}
        assert result['both'] == expected_both
    
    def test_compare_datasets_with_by_variable(self, sample_df1, sample_df2):
        """Test detailed dataset comparison with BY variable."""
        comp = DatasetComparison()
        result = comp.compare_datasets(sample_df1, sample_df2, by='usubjid')
        
        assert result['summary']['status'] == 'DIFFERENCES_FOUND'
        assert result['summary']['has_variable_diffs'] is True
        assert result['summary']['has_value_diffs'] is True
        assert 'race' in result['value_differences']
    
    def test_compare_datasets_identical(self):
        """Test comparison of identical datasets."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        df2 = df1.copy()
        
        comp = DatasetComparison()
        result = comp.compare_datasets(df1, df2, by='id')
        
        assert result['summary']['status'] == 'IDENTICAL'
        assert result['summary']['has_variable_diffs'] is False
        assert result['summary']['has_value_diffs'] is False
    
    def test_compare_datasets_numeric_tolerance(self):
        """Test numeric comparison with tolerance."""
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [1.0000001, 2.0000001, 3.0000001]
        })
        df2 = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [1.0, 2.0, 3.0]
        })
        
        comp = DatasetComparison()
        result = comp.compare_datasets(df1, df2, by='id', tolerance=1e-6)
        
        # Should be identical within tolerance
        assert result['summary']['status'] == 'IDENTICAL'
    
    def test_compare_vars_convenience_function(self, sample_df1, sample_df2):
        """Test convenience function for variable comparison."""
        result = compare_vars(sample_df1, sample_df2)
        
        assert 'left' in result
        assert 'right' in result
        assert 'both' in result
        assert 'saffl' in result['left']
        assert 'newvar' in result['right']
    
    def test_compare_datasets_convenience_function(self, sample_df1, sample_df2):
        """Test convenience function for dataset comparison."""
        result = compare_datasets(sample_df1, sample_df2, by='usubjid')
        
        assert 'summary' in result
        assert result['summary']['status'] == 'DIFFERENCES_FOUND'


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_datasets(self):
        """Test comparison of empty datasets."""
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        
        comp = DatasetComparison()
        result = comp.compare_variables(df1, df2)
        
        assert len(result['left']) == 0
        assert len(result['right']) == 0
        assert len(result['both']) == 0
    
    def test_no_common_variables(self):
        """Test datasets with no common variables."""
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'b': [4, 5, 6]})
        
        comp = DatasetComparison()
        result = comp.compare_datasets(df1, df2)
        
        assert result['summary']['status'] == 'NO_COMMON_VARS'
    
    def test_missing_by_variable(self):
        """Test comparison with missing BY variable."""
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'a': [1, 2, 3]})
        
        comp = DatasetComparison()
        result = comp.compare_datasets(df1, df2, by='nonexistent')
        
        assert result['summary']['status'] == 'INVALID_BY_VARS'
    
    def test_different_row_counts(self):
        """Test datasets with different row counts."""
        df1 = pd.DataFrame({'id': [1, 2, 3], 'val': [10, 20, 30]})
        df2 = pd.DataFrame({'id': [1, 2], 'val': [10, 20]})
        
        comp = DatasetComparison()
        result = comp.compare_datasets(df1, df2, by='id')
        
        assert result['summary']['has_row_count_diff'] is True
        assert result['obs_only_in_base'] == 1
        assert result['obs_only_in_comp'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
