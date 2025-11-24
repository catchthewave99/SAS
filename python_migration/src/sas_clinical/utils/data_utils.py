"""
Data utility functions - Python equivalents of Roland's utility macros.

This module provides common data manipulation and validation functions
used throughout clinical trials data processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_sas_dataset(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Read a SAS dataset file.
    
    Args:
        file_path: Path to SAS dataset (.sas7bdat or .xpt)
        
    Returns:
        DataFrame containing the dataset
    """
    file_path = Path(file_path)
    
    try:
        import pyreadstat
        df, meta = pyreadstat.read_sas7bdat(str(file_path))
        logger.info(f"Read SAS dataset: {file_path.name} ({df.shape[0]} rows, {df.shape[1]} cols)")
        return df
    except ImportError:
        logger.error("pyreadstat not installed. Install with: pip install pyreadstat")
        raise
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        raise


def write_sas_dataset(df: pd.DataFrame, file_path: Union[str, Path]):
    """
    Write a DataFrame to SAS dataset format.
    
    Args:
        df: DataFrame to write
        file_path: Output file path
    """
    file_path = Path(file_path)
    
    try:
        import pyreadstat
        pyreadstat.write_sas7bdat(df, str(file_path))
        logger.info(f"Wrote SAS dataset: {file_path.name}")
    except ImportError:
        logger.warning("pyreadstat not installed. Writing as CSV instead.")
        df.to_csv(file_path.with_suffix('.csv'), index=False)


def get_variable_list(df: pd.DataFrame, var_type: Optional[str] = None) -> List[str]:
    """
    Get list of variables in a dataset, optionally filtered by type.
    
    Args:
        df: DataFrame
        var_type: Variable type filter ('numeric', 'character', or None for all)
        
    Returns:
        List of variable names
    """
    if var_type is None:
        return list(df.columns)
    elif var_type.lower() == 'numeric':
        return list(df.select_dtypes(include=[np.number]).columns)
    elif var_type.lower() in ['character', 'string', 'object']:
        return list(df.select_dtypes(include=['object', 'string']).columns)
    else:
        raise ValueError(f"Invalid var_type: {var_type}")


def check_unique_values(df: pd.DataFrame, key_vars: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Check for duplicate values in key variables.
    
    Python equivalent of SAS %chkuniq macro.
    
    Args:
        df: DataFrame to check
        key_vars: Variable(s) that should be unique
        
    Returns:
        Dictionary with duplicate information
    """
    if isinstance(key_vars, str):
        key_vars = [key_vars]
    
    duplicates = df[df.duplicated(subset=key_vars, keep=False)]
    
    result = {
        'has_duplicates': len(duplicates) > 0,
        'num_duplicates': len(duplicates),
        'duplicate_keys': duplicates[key_vars].drop_duplicates().to_dict('records') if len(duplicates) > 0 else []
    }
    
    if result['has_duplicates']:
        logger.warning(f"Found {result['num_duplicates']} duplicate records for key: {key_vars}")
    else:
        logger.info(f"No duplicates found for key: {key_vars}")
    
    return result


def count_unique_values(df: pd.DataFrame, var: str) -> int:
    """
    Count unique values in a variable.
    
    Python equivalent of SAS %util_count_unique_values.
    
    Args:
        df: DataFrame
        var: Variable name
        
    Returns:
        Count of unique values
    """
    count = df[var].nunique()
    logger.info(f"Variable '{var}' has {count} unique values")
    return count


def get_labels_from_var(df: pd.DataFrame, code_var: str, label_var: str) -> Dict[Any, str]:
    """
    Get mapping of codes to labels from a dataset.
    
    Python equivalent of SAS %util_labels_from_var.
    
    Args:
        df: DataFrame
        code_var: Variable containing codes
        label_var: Variable containing labels
        
    Returns:
        Dictionary mapping codes to labels
    """
    mapping = df[[code_var, label_var]].drop_duplicates().set_index(code_var)[label_var].to_dict()
    logger.info(f"Created label mapping for {code_var}: {len(mapping)} unique values")
    return mapping


def filter_analysis_population(
    df: pd.DataFrame,
    population_flag: str = 'saffl',
    analysis_flag: str = 'anl01fl'
) -> pd.DataFrame:
    """
    Filter dataset to analysis population.
    
    Args:
        df: DataFrame to filter
        population_flag: Population flag variable (e.g., SAFFL, ITTFL)
        analysis_flag: Analysis flag variable
        
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    
    if population_flag in df.columns:
        df_filtered = df_filtered[df_filtered[population_flag] == 'Y']
        logger.info(f"Filtered to {population_flag}='Y': {len(df_filtered)} records")
    
    if analysis_flag in df.columns:
        df_filtered = df_filtered[df_filtered[analysis_flag] == 'Y']
        logger.info(f"Filtered to {analysis_flag}='Y': {len(df_filtered)} records")
    
    return df_filtered


def get_var_min_max(df: pd.DataFrame, var: str, extra_values: Optional[List[float]] = None) -> Tuple[float, float]:
    """
    Get minimum and maximum values for a variable, optionally including extra values.
    
    Python equivalent of SAS %util_get_var_min_max.
    
    Args:
        df: DataFrame
        var: Variable name
        extra_values: Additional values to consider (e.g., reference lines)
        
    Returns:
        Tuple of (min, max)
    """
    values = df[var].dropna()
    
    if len(values) == 0:
        return (0, 0)
    
    var_min = values.min()
    var_max = values.max()
    
    if extra_values:
        var_min = min(var_min, min(extra_values))
        var_max = max(var_max, max(extra_values))
    
    return (var_min, var_max)


def format_value(value: float, decimals: int = 2) -> str:
    """
    Format a numeric value with specified decimal places.
    
    Python equivalent of SAS %util_value_format.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    if pd.isna(value):
        return ''
    return f"{value:.{decimals}f}"


def merge_datasets(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: Union[str, List[str]],
    how: str = 'inner',
    suffixes: Tuple[str, str] = ('_x', '_y')
) -> pd.DataFrame:
    """
    Merge two datasets.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        on: Variable(s) to merge on
        how: Type of merge ('inner', 'outer', 'left', 'right')
        suffixes: Suffixes for overlapping columns
        
    Returns:
        Merged DataFrame
    """
    merged = df1.merge(df2, on=on, how=how, suffixes=suffixes)
    logger.info(f"Merged datasets: {len(df1)} + {len(df2)} -> {len(merged)} records")
    return merged


def transpose_dataset(
    df: pd.DataFrame,
    id_vars: Union[str, List[str]],
    value_vars: Optional[List[str]] = None,
    var_name: str = 'variable',
    value_name: str = 'value'
) -> pd.DataFrame:
    """
    Transpose a dataset from wide to long format.
    
    Args:
        df: DataFrame to transpose
        id_vars: Identifier variable(s)
        value_vars: Variables to transpose (None = all except id_vars)
        var_name: Name for variable column
        value_name: Name for value column
        
    Returns:
        Transposed DataFrame
    """
    if isinstance(id_vars, str):
        id_vars = [id_vars]
    
    if value_vars is None:
        value_vars = [col for col in df.columns if col not in id_vars]
    
    transposed = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=var_name,
        value_name=value_name
    )
    
    logger.info(f"Transposed dataset: {df.shape} -> {transposed.shape}")
    return transposed


def apply_formats(df: pd.DataFrame, format_dict: Dict[str, str]) -> pd.DataFrame:
    """
    Apply display formats to DataFrame columns.
    
    Args:
        df: DataFrame
        format_dict: Dictionary mapping column names to format strings
        
    Returns:
        DataFrame with formatted columns
    """
    df_formatted = df.copy()
    
    for col, fmt in format_dict.items():
        if col in df_formatted.columns:
            if 'date' in fmt.lower():
                df_formatted[col] = pd.to_datetime(df_formatted[col]).dt.strftime('%Y-%m-%d')
            elif '.' in fmt:
                # Numeric format like '8.2'
                decimals = int(fmt.split('.')[-1])
                df_formatted[col] = df_formatted[col].apply(lambda x: format_value(x, decimals))
    
    return df_formatted
