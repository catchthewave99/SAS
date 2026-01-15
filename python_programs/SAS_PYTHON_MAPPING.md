# SAS to Python Migration Mapping

This document provides a clear mapping between the original SAS scripts and their Python counterparts.

## Script Mapping Table

| Original SAS Script | Python Equivalent | Description |
|---------------------|-------------------|-------------|
| `programs/drafts/CreateCompareTestData.sas` | `python_programs/create_compare_test_data.py` | Creates test data with controlled modifications for comparison testing |
| `programs/drafts/xpt2sas_adam_sdtm.sas` | `python_programs/xpt_to_sas.py` | Converts XPT transport files to pandas DataFrames |
| `programs/example_compare/test_compare_macros.sas` | `python_programs/test_compare_macros.py` | Tests comparison functions |
| `programs/example_phuse_whitepapers/WPCT-F.07.01.sas` | `python_programs/boxplot_generator.py` | Generates PHUSE-style box plots |
| `programs/example_phuse_whitepapers/example_call_wpct-f.07.01.sas` | `python_programs/example_call_wpct.py` | Example script for box plot generation |
| `tools/downloads/roland_utilmacros/compvars.sas` | `python_programs/utils.py` (compvars function) | Compare variable lists between datasets |
| `tools/downloads/roland_utilmacros/complibs.sas` | `python_programs/utils.py` (complibs function) | Compare datasets in two libraries |
| `programs/example_compare/blank.sas` | N/A (template file) | Placeholder/template file - not migrated |

## Function Mapping

### Comparison Functions (utils.py)

| SAS Macro | Python Function | Description |
|-----------|-----------------|-------------|
| `%compvars(ds1, ds2)` | `compvars(ds1, ds2)` | Compare variable lists, returns dict with 'left', 'right', 'both' keys |
| `%complibs(lib1, lib2, sortvars=)` | `complibs(lib_old, lib_new, sortvars=)` | Compare all datasets in two directories |
| `%compare(base=, comp=, by=)` | `compare(base, comp, by_vars=)` | Detailed dataset/library comparison |

### Data I/O Functions

| SAS Operation | Python Function | Description |
|---------------|-----------------|-------------|
| `LIBNAME lib "path"` | `Path("path")` | Directory path handling |
| `SET dataset` | `read_sas_dataset(path)` | Read SAS7BDAT file |
| `PROC COPY IN=lib1 OUT=lib2` | `shutil.copy()` or `df.to_csv()` | Copy datasets |
| XPT file reading | `xport.v56.load()` | Read XPT transport files |

### Statistical Functions

| SAS Procedure | Python Equivalent | Description |
|---------------|-------------------|-------------|
| `PROC SUMMARY` | `df.groupby().agg()` | Calculate summary statistics |
| `PROC COMPARE` | `compare_datasets()` | Compare datasets |
| `PROC SGRENDER` | `matplotlib` + `seaborn` | Generate box plots |

## Variable Mapping

### Global Macro Variables to Python Returns

| SAS Macro Variable | Python Return | Description |
|--------------------|---------------|-------------|
| `&_left_` | `result['left']` | Variables only in first dataset |
| `&_right_` | `result['right']` | Variables only in second dataset |
| `&_both_` | `result['both']` | Variables in both datasets |

### ADaM Variable Handling

| SAS Variable | Python Column | Notes |
|--------------|---------------|-------|
| `USUBJID` | `USUBJID` | Unique subject identifier |
| `SAFFL` | `SAFFL` | Safety population flag |
| `AVAL` | `AVAL` | Analysis value |
| `PARAMCD` | `PARAMCD` | Parameter code |
| `AVISITN` | `AVISITN` | Visit number |
| `AVISIT` | `AVISIT` | Visit label |
| `ATPTN` | `ATPTN` | Analysis timepoint number |
| `ATPT` | `ATPT` | Analysis timepoint label |

## Data Type Considerations

### SAS to Python Type Mapping

| SAS Type | Python Type | Notes |
|----------|-------------|-------|
| Numeric | `float64` | SAS missing (.) becomes `NaN` |
| Character | `object` (string) | SAS missing (' ') becomes empty string or `NaN` |
| Date | `datetime64` | SAS date values converted |
| DateTime | `datetime64` | SAS datetime values converted |

### Special Value Handling

| SAS Value | Python Value | Notes |
|-----------|--------------|-------|
| `.` (missing numeric) | `np.nan` | Use `pd.isna()` to check |
| `' '` (missing character) | `''` or `np.nan` | Depends on pyreadstat settings |
| `.A` to `.Z` (special missing) | `np.nan` | Special missing values not preserved |

## Output Format Differences

### File Formats

| SAS Output | Python Output | Notes |
|------------|---------------|-------|
| `.sas7bdat` | `.csv` | Python writes CSV (readable by pandas) |
| `.xpt` | `.csv` | XPT files converted to CSV |
| PDF (ODS) | PDF (matplotlib) | Box plots saved as PDF |

### Log Output

| SAS | Python | Notes |
|-----|--------|-------|
| `%PUT` | `print()` | Console output |
| SAS Log | stdout/stderr | Standard output streams |
| `OPTIONS NOTES` | Logging level | Use Python logging module |
