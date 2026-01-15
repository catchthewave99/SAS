# SAS to Python Migration Report

## Executive Summary

This report documents the migration of SAS scripts from the `catchthewave99/SAS` repository to Python. The migration covers all core data manipulation and statistical analysis scripts, providing equivalent functionality using Python's data science ecosystem.

## Scope of Migration

### Scripts Migrated

1. **CreateCompareTestData.sas** → `create_compare_test_data.py`
2. **xpt2sas_adam_sdtm.sas** → `xpt_to_sas.py`
3. **test_compare_macros.sas** → `test_compare_macros.py`
4. **WPCT-F.07.01.sas** → `boxplot_generator.py`
5. **example_call_wpct-f.07.01.sas** → `example_call_wpct.py`
6. **compvars.sas** (macro) → `utils.py` (compvars function)
7. **complibs.sas** (macro) → `utils.py` (complibs function)

### Scripts Not Migrated

- **blank.sas**: Template/placeholder file with only path definitions
- External utility macros in `tools/downloads/roland_utilmacros/`: These are third-party utilities; only the core comparison macros used by the main scripts were migrated

## Migration Details

### 1. Data Comparison Framework

**Original SAS**: `test_compare_macros.sas`, `compvars.sas`, `complibs.sas`

**Python Equivalent**: `utils.py`, `test_compare_macros.py`

**Functionality**:
- `compvars()`: Compares variable lists between two datasets, returning variables unique to each dataset and common variables
- `complibs()`: Compares all datasets in two directories (libraries), identifying datasets unique to each library and comparing common datasets
- `compare()`: Detailed dataset comparison with support for BY variables, observation-level and value-level differences

**Key Differences**:
- SAS uses global macro variables (`&_left_`, `&_right_`, `&_both_`); Python returns a dictionary
- SAS PROC COMPARE provides detailed output; Python implementation provides similar information in structured format
- Python uses pandas DataFrames instead of SAS datasets

### 2. Test Data Generation

**Original SAS**: `CreateCompareTestData.sas`

**Python Equivalent**: `create_compare_test_data.py`

**Functionality**:
- Copies original ADaM datasets (adsl, adae, advs) to a modified directory
- Modifies adtte dataset with controlled changes:
  - Drops 'saffl' variable
  - Adds 'newvar' variable
  - Deletes every 17th observation
  - Modifies row 11 (race, aval values)
  - Duplicates row 20 with modified usubjid
- Creates a new dataset called 'new'

**Key Differences**:
- Python outputs CSV files instead of SAS7BDAT (pyreadstat can read but not write SAS7BDAT)
- Python uses 0-based indexing; adjustments made to match SAS behavior

### 3. XPT File Conversion

**Original SAS**: `xpt2sas_adam_sdtm.sas`

**Python Equivalent**: `xpt_to_sas.py`

**Functionality**:
- Reads XPT (SAS Transport) files from a directory
- Converts to pandas DataFrames
- Saves in specified format (CSV, Parquet, or Pickle)

**Key Differences**:
- SAS uses PROC COPY with XPORT engine; Python uses the `xport` library
- Python supports multiple output formats; SAS outputs SAS7BDAT

### 4. Box Plot Generation

**Original SAS**: `WPCT-F.07.01.sas`, `example_call_wpct-f.07.01.sas`

**Python Equivalent**: `boxplot_generator.py`, `example_call_wpct.py`

**Functionality**:
- Generates PHUSE-style box plots for clinical trials data
- Supports multiple parameters and timepoints
- Automatic pagination for many visits
- Reference lines for normal range limits
- Highlights out-of-range values with red markers
- Outputs multi-page PDF files

**Key Differences**:
- SAS uses PROC SGRENDER with custom ODS template; Python uses matplotlib
- Visual styling differs but conveys same information
- Python implementation is more flexible for customization

## Challenges Encountered and Resolutions

### Challenge 1: SAS7BDAT File Writing

**Issue**: The `pyreadstat` library can read SAS7BDAT files but cannot write them.

**Resolution**: Python scripts output CSV files, which are universally readable and can be converted to SAS7BDAT using SAS if needed. This maintains data integrity while providing cross-platform compatibility.

### Challenge 2: SAS Macro Variable Scope

**Issue**: SAS uses global macro variables to return results from macros; Python doesn't have an equivalent concept.

**Resolution**: Python functions return dictionaries containing the same information. This is actually more Pythonic and allows for better encapsulation.

### Challenge 3: PROC COMPARE Functionality

**Issue**: SAS PROC COMPARE provides extensive comparison output with specific formatting.

**Resolution**: Implemented custom comparison logic in Python that provides equivalent information in a structured format. The `print_comparison_results()` function formats output similarly to SAS.

### Challenge 4: ODS Graphics Templates

**Issue**: SAS uses custom ODS templates for box plot rendering; these are not directly translatable to Python.

**Resolution**: Used matplotlib with custom styling to create visually similar box plots. The Python implementation provides equivalent statistical visualization with different but professional styling.

### Challenge 5: Missing Value Handling

**Issue**: SAS has special missing values (`.`, `.A` to `.Z`) with specific comparison behavior.

**Resolution**: Python uses `np.nan` for all missing values. Comparison logic explicitly handles NaN values to match SAS behavior where possible.

### Challenge 6: Case Sensitivity

**Issue**: SAS is case-insensitive for variable names; Python is case-sensitive.

**Resolution**: All variable name comparisons are done in uppercase to ensure consistent behavior across platforms.

## How to Run the Python Scripts

### Prerequisites

1. Install Python 3.8 or higher
2. Install required dependencies:

```bash
cd python_programs
pip install -r requirements.txt
```

### Running Individual Scripts

#### 1. Create Test Data

```bash
python create_compare_test_data.py --base-dir /path/to/SAS
```

This creates modified datasets in `data/adam/mod_01/` for testing comparison functions.

#### 2. Convert XPT Files

```bash
python xpt_to_sas.py --base-dir /path/to/SAS --format csv
```

Converts all XPT files in `data/adam/` and `data/sdtm/` directories.

#### 3. Test Comparison Functions

```bash
python test_compare_macros.py --base-dir /path/to/SAS
```

Runs all comparison tests and displays results.

#### 4. Generate Box Plots

```bash
python example_call_wpct.py --base-dir /path/to/SAS --paramcd ALB
```

Generates box plots for the specified parameter.

### Using as a Library

```python
from python_programs.utils import compvars, complibs, compare
from python_programs.boxplot_generator import generate_boxplots

# Compare two DataFrames
result = compvars(df1, df2)
print(f"Variables only in df1: {result['left']}")
print(f"Variables only in df2: {result['right']}")

# Compare two directories of datasets
lib_result = complibs('/path/to/lib1', '/path/to/lib2', sortvars=['usubjid'])

# Generate box plots
generate_boxplots(
    data='/path/to/adlbc.sas7bdat',
    output_folder='/path/to/output',
    paramcd_filter=['ALB', 'GLUC']
)
```

## Verifying Output Against Original SAS

### Comparison Functions

1. Run the original SAS script `test_compare_macros.sas` and capture the log output
2. Run the Python script `test_compare_macros.py`
3. Compare:
   - Variables reported in `&_left_`, `&_right_`, `&_both_` should match Python's `result['left']`, `result['right']`, `result['both']`
   - Observation counts should match
   - Value differences should be identified in the same variables

### Test Data Generation

1. Run `CreateCompareTestData.sas` in SAS
2. Run `create_compare_test_data.py` in Python
3. Compare the modified datasets:
   - Same number of rows (accounting for deleted observations)
   - Same columns (minus dropped, plus added)
   - Same modified values at specified row positions

### Box Plots

1. Generate plots using both SAS and Python
2. Compare:
   - Same parameters and timepoints plotted
   - Same statistical values (n, mean, std, median, Q1, Q3)
   - Same outliers identified
   - Reference lines at same positions

## File Structure

```
python_programs/
├── __init__.py              # Package initialization
├── requirements.txt         # Python dependencies
├── utils.py                 # Utility functions (compvars, complibs, compare)
├── create_compare_test_data.py  # Test data generation
├── xpt_to_sas.py           # XPT file conversion
├── test_compare_macros.py  # Comparison function tests
├── boxplot_generator.py    # PHUSE box plot generation
├── example_call_wpct.py    # Example box plot script
├── SAS_PYTHON_MAPPING.md   # Detailed mapping document
└── MIGRATION_REPORT.md     # This report
```

## Recommendations

1. **Data Format**: Consider using Parquet format for large datasets as it provides better compression and faster read times than CSV.

2. **Testing**: Run both SAS and Python versions on the same data to verify output equivalence before fully transitioning.

3. **Logging**: The Python scripts use print statements; consider implementing Python's logging module for production use.

4. **Error Handling**: Additional error handling may be needed for edge cases specific to your data.

5. **Performance**: For very large datasets, consider using Dask or Polars instead of pandas for better performance.

## Conclusion

The migration successfully converts all core SAS scripts to Python equivalents. The Python implementation provides the same functionality with some improvements in flexibility and cross-platform compatibility. The main trade-off is the inability to write native SAS7BDAT files, which is mitigated by using CSV as an interchange format.
