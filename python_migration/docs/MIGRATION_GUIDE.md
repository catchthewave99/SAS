# SAS to Python Migration Guide

This guide helps users migrate from the original SAS programs to the Python implementation.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Data Format Conversion](#data-format-conversion)
4. [Function Mapping](#function-mapping)
5. [Common Patterns](#common-patterns)
6. [Performance Considerations](#performance-considerations)
7. [Troubleshooting](#troubleshooting)

## Overview

The Python migration provides equivalent functionality to all SAS programs while leveraging modern Python libraries and best practices. The core design principles remain the same:

- Standards compliance (CDISC ADaM/SDTM)
- Regulatory focus (FDA/EMA submissions)
- Comprehensive comparison testing
- PHUSE-compliant visualizations

## Installation

### Step 1: Install Python

Ensure Python 3.8 or higher is installed:

```bash
python --version
```

### Step 2: Install the Package

```bash
cd python_migration
pip install -e .
```

### Step 3: Install SAS Dataset Support (Optional)

To read SAS datasets directly:

```bash
pip install pyreadstat
```

## Data Format Conversion

### Option 1: Convert SAS Datasets to CSV

```python
import pyreadstat

# Read SAS dataset
df, meta = pyreadstat.read_sas7bdat('data/adam/adsl.sas7bdat')

# Write to CSV
df.to_csv('data/adam/adsl.csv', index=False)
```

### Option 2: Use SAS Datasets Directly

The Python package can read SAS datasets directly if `pyreadstat` is installed:

```python
from sas_clinical.utils.data_utils import read_sas_dataset

df = read_sas_dataset('data/adam/adsl.sas7bdat')
```

### Option 3: Batch Conversion Script

```python
from pathlib import Path
import pyreadstat
import pandas as pd

def convert_sas_library(input_dir, output_dir):
    """Convert all SAS datasets in a directory to CSV."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for sas_file in input_path.glob('*.sas7bdat'):
        df, meta = pyreadstat.read_sas7bdat(str(sas_file))
        csv_file = output_path / f"{sas_file.stem}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Converted: {sas_file.name} -> {csv_file.name}")

# Convert ADAM library
convert_sas_library('data/adam', 'data/adam_csv')
```

## Function Mapping

### Comparison Macros

#### SAS: %compvars

```sas
%compvars(adam.adtte, adam_mod.adtte);
%put Variables in left only: &_left_;
%put Variables in right only: &_right_;
%put Variables in both: &_both_;
```

#### Python: compare_vars

```python
from sas_clinical.comparison.dataset_compare import compare_vars
import pandas as pd

df1 = pd.read_csv('data/adam/adtte.csv')
df2 = pd.read_csv('data/adam/mod_01/adtte.csv')

result = compare_vars(df1, df2, 'adam.adtte', 'adam_mod.adtte')

print(f"Variables in left only: {result['left']}")
print(f"Variables in right only: {result['right']}")
print(f"Variables in both: {result['both']}")
```

#### SAS: %complibs

```sas
%complibs(adam, adam_mod, sortvars=usubjid);
```

#### Python: compare_libraries

```python
from sas_clinical.comparison.dataset_compare import compare_libraries

results = compare_libraries(
    'data/adam',
    'data/adam/mod_01',
    by='usubjid'
)

for ds_name, ds_results in results['dataset_comparisons'].items():
    print(f"{ds_name}: {ds_results['summary']['status']}")
```

#### SAS: %compare

```sas
%compare(base=adam.adtte, comp=adam_mod.adtte, by=usubjid);
```

#### Python: compare_datasets

```python
from sas_clinical.comparison.dataset_compare import compare_datasets
import pandas as pd

df1 = pd.read_csv('data/adam/adtte.csv')
df2 = pd.read_csv('data/adam/mod_01/adtte.csv')

results = compare_datasets(df1, df2, by='usubjid')

print(f"Status: {results['summary']['status']}")
if results.get('value_differences'):
    for var, diff in results['value_differences'].items():
        print(f"{var}: {diff['num_differences']} differences")
```

### PHUSE Box Plots

#### SAS: WPCT-F.07.01.sas

```sas
%LET root = /folders/myshortcuts/git;
%LET base = &root/SAS;
%LET outputs_folder = &base/results;

%util_access_test_data(ADLBC);

/* Run WPCT-F.07.01.sas */
```

#### Python: generate_phuse_box_plots

```python
from sas_clinical.visualization.box_plots import generate_phuse_box_plots
import pandas as pd

# Load data
data = pd.read_csv('data/adam/adlbc.csv')

# Generate plots
generate_phuse_box_plots(
    data=data,
    output_dir='results/box_plots',
    treatment_var='trtp',
    treatment_num_var='trtpn',
    measurement_var='aval',
    visit_var='avisit',
    visit_num_var='avisitn',
    param_code_var='paramcd',
    low_ref_var='anrlo',
    high_ref_var='anrhi',
    ref_lines='UNIFORM'
)
```

### Test Data Generation

#### SAS: CreateCompareTestData.sas

```sas
%LET base = /folders/myshortcuts/git/SAS;
LIBNAME adam "&base/data/adam";
LIBNAME adam_mod "&base/data/adam/mod_01";

/* Create modified datasets */
PROC COPY IN=adam OUT=adam_mod;
    SELECT adsl adae advs;
RUN;

DATA adam_mod.adtte;
    SET adam.adtte(DROP=saffl);
    /* ... modifications ... */
RUN;
```

#### Python: create_test_data

```python
from sas_clinical.data_processing.test_data_generator import create_test_data

create_test_data(
    base_path='data/adam',
    mod_path='data/adam/mod_01_python'
)
```

### Utility Functions

#### SAS Utility Macros

```sas
%nvarsc(dataset)          /* Count character variables */
%nvarsn(dataset)          /* Count numeric variables */
%chkuniq(dataset, key)    /* Check unique values */
```

#### Python Utility Functions

```python
from sas_clinical.utils.data_utils import (
    get_variable_list,
    check_unique_values,
    count_unique_values
)

# Get variable lists
char_vars = get_variable_list(df, var_type='character')
num_vars = get_variable_list(df, var_type='numeric')

# Check unique values
result = check_unique_values(df, 'usubjid')
if result['has_duplicates']:
    print(f"Found {result['num_duplicates']} duplicates")

# Count unique values
n_unique = count_unique_values(df, 'paramcd')
```

## Common Patterns

### Pattern 1: Library Setup

#### SAS

```sas
LIBNAME adam "/path/to/data/adam";
LIBNAME adam_mod "/path/to/data/adam/mod_01";
```

#### Python

```python
from pathlib import Path

adam_path = Path('data/adam')
adam_mod_path = Path('data/adam/mod_01')
```

### Pattern 2: Reading Datasets

#### SAS

```sas
DATA work.adsl;
    SET adam.adsl;
RUN;
```

#### Python

```python
import pandas as pd

adsl = pd.read_csv('data/adam/adsl.csv')
# or
from sas_clinical.utils.data_utils import read_sas_dataset
adsl = read_sas_dataset('data/adam/adsl.sas7bdat')
```

### Pattern 3: Filtering Data

#### SAS

```sas
DATA analysis;
    SET adam.adsl;
    WHERE saffl = 'Y' AND anl01fl = 'Y';
RUN;
```

#### Python

```python
from sas_clinical.utils.data_utils import filter_analysis_population

analysis = filter_analysis_population(
    adsl,
    population_flag='saffl',
    analysis_flag='anl01fl'
)

# Or using pandas directly
analysis = adsl[(adsl['saffl'] == 'Y') & (adsl['anl01fl'] == 'Y')]
```

### Pattern 4: Merging Datasets

#### SAS

```sas
PROC SORT DATA=adsl; BY usubjid; RUN;
PROC SORT DATA=adae; BY usubjid; RUN;

DATA merged;
    MERGE adsl(IN=a) adae(IN=b);
    BY usubjid;
    IF a AND b;
RUN;
```

#### Python

```python
from sas_clinical.utils.data_utils import merge_datasets

merged = merge_datasets(adsl, adae, on='usubjid', how='inner')

# Or using pandas directly
merged = adsl.merge(adae, on='usubjid', how='inner')
```

### Pattern 5: Summary Statistics

#### SAS

```sas
PROC MEANS DATA=advs N MEAN STD MEDIAN MIN MAX;
    CLASS trtp avisitn;
    VAR aval;
    OUTPUT OUT=stats;
RUN;
```

#### Python

```python
stats = advs.groupby(['trtp', 'avisitn'])['aval'].agg([
    ('n', 'count'),
    ('mean', 'mean'),
    ('std', 'std'),
    ('median', 'median'),
    ('min', 'min'),
    ('max', 'max')
]).reset_index()
```

## Performance Considerations

### Memory Management

**SAS**: Processes data in chunks, suitable for very large datasets

**Python**: Loads entire dataset into memory

For large datasets in Python:

```python
# Read in chunks
chunks = pd.read_csv('large_file.csv', chunksize=10000)
for chunk in chunks:
    process(chunk)

# Or use Dask for out-of-core processing
import dask.dataframe as dd
df = dd.read_csv('large_file.csv')
```

### Speed Optimization

```python
# Use categorical data types for repeated strings
df['trtp'] = df['trtp'].astype('category')

# Use efficient data types
df['age'] = df['age'].astype('int16')  # Instead of int64

# Vectorize operations instead of loops
df['bmi'] = df['weight'] / (df['height'] / 100) ** 2  # Vectorized
# Instead of: df.apply(lambda row: row['weight'] / (row['height']/100)**2, axis=1)
```

## Troubleshooting

### Issue: Cannot read SAS datasets

**Solution**: Install pyreadstat

```bash
pip install pyreadstat
```

### Issue: Memory error with large datasets

**Solution**: Use chunking or Dask

```python
import dask.dataframe as dd
df = dd.read_csv('large_file.csv')
```

### Issue: Different results from SAS

**Possible causes**:
1. Numeric precision differences
2. Missing value handling
3. Sort order differences

**Solution**: Adjust tolerance in comparisons

```python
results = compare_datasets(df1, df2, by='usubjid', tolerance=1e-6)
```

### Issue: Box plots look different

**Possible causes**:
1. Different default styles
2. Reference line options
3. Outlier detection methods

**Solution**: Adjust plot parameters

```python
generate_phuse_box_plots(
    data=data,
    output_dir='results/',
    ref_lines='UNIFORM',  # Match SAS behavior
    figsize=(14, 8)       # Adjust size
)
```

## Additional Resources

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [PHUSE Scripts Repository](https://github.com/phuse-org/phuse-scripts)
- [CDISC Standards](https://www.cdisc.org/)
- [Original SAS Repository](https://github.com/catchthewave99/SAS)

## Getting Help

For questions or issues:

1. Check this migration guide
2. Review example scripts in `examples/`
3. Run unit tests to verify installation
4. Open an issue on GitHub
