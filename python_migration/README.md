# SAS Clinical Trials Toolkit - Python Migration

This is a comprehensive Python migration of the SAS-based clinical trials data management and validation toolkit. It provides all the functionality of the original SAS programs with modern Python libraries and best practices.

## Overview

This Python package replicates all functionality from the original SAS repository:

1. **Data Comparison and Validation**: Comprehensive testing framework for comparing datasets and libraries
2. **Clinical Reporting**: PHUSE-compliant box plots and statistical visualizations
3. **Data Processing**: Test data generation and manipulation utilities
4. **Utility Functions**: Common data operations for clinical trials workflows

## Features

### Data Comparison Framework

Python equivalents of SAS comparison macros:

- `compare_vars()` - Compare variable lists between datasets (equivalent to `%compvars`)
- `compare_datasets()` - Detailed dataset comparison (equivalent to `%compare`)
- `compare_libraries()` - Compare all datasets in two directories (equivalent to `%complibs`)

### PHUSE Box Plots

Generate Figure 7.1 "Box plot - Measurements by Analysis Timepoint, Visit and Treatment" per PHUSE Central Tendency White Paper:

- Full PHUSE compliance
- Automatic pagination for multiple visits
- Reference range lines (UNIFORM, NARROW, ALL options)
- Summary statistics tables
- Outlier detection and highlighting

### Test Data Generation

Create modified test datasets with controlled differences:

- Drop/add variables
- Delete observations
- Modify values
- Duplicate observations
- Create new datasets

### Utility Functions

Common data operations:

- Read/write SAS datasets (via pyreadstat)
- Variable list operations
- Unique value checking
- Label mapping
- Population filtering
- Min/max calculations
- Data merging and transposition

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from source

```bash
cd python_migration
pip install -e .
```

### Install with development dependencies

```bash
pip install -e ".[dev]"
```

### Required packages

The package automatically installs:

- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- plotly >= 5.14.0
- pyreadstat >= 1.2.0 (for reading SAS datasets)
- openpyxl >= 3.1.0
- xlsxwriter >= 3.1.0

## Quick Start

### Example 1: Compare Datasets

```python
from sas_clinical.comparison.dataset_compare import compare_datasets
import pandas as pd

# Load datasets
df1 = pd.read_csv('data/adam/adsl.csv')
df2 = pd.read_csv('data/adam/mod_01/adsl.csv')

# Compare datasets
results = compare_datasets(
    df1, df2,
    by='usubjid',
    ds1_name='Original',
    ds2_name='Modified'
)

print(f"Status: {results['summary']['status']}")
print(f"Value differences: {results['value_differences']}")
```

### Example 2: Generate PHUSE Box Plots

```python
from sas_clinical.visualization.box_plots import generate_phuse_box_plots
import pandas as pd

# Load ADaM data
data = pd.read_csv('data/adam/adlbc.csv')

# Generate box plots
generate_phuse_box_plots(
    data=data,
    output_dir='results/box_plots',
    treatment_var='trtp',
    measurement_var='aval',
    param_code_var='paramcd'
)
```

### Example 3: Create Test Data

```python
from sas_clinical.data_processing.test_data_generator import create_test_data

# Create modified test datasets
create_test_data(
    base_path='data/adam',
    mod_path='data/adam/mod_01_python'
)
```

## Project Structure

```
python_migration/
├── src/
│   └── sas_clinical/
│       ├── comparison/          # Dataset comparison tools
│       │   └── dataset_compare.py
│       ├── visualization/       # Box plots and charts
│       │   └── box_plots.py
│       ├── data_processing/     # Data manipulation
│       │   └── test_data_generator.py
│       └── utils/              # Utility functions
│           └── data_utils.py
├── examples/                   # Example scripts
│   ├── example_compare.py
│   └── example_box_plots.py
├── tests/                      # Unit tests
│   ├── test_dataset_compare.py
│   └── test_data_utils.py
├── docs/                       # Documentation
├── requirements.txt            # Package dependencies
├── setup.py                   # Package setup
└── README.md                  # This file
```

## Running Examples

### Dataset Comparison Example

```bash
cd python_migration
python examples/example_compare.py
```

### Box Plot Example

```bash
python examples/example_box_plots.py
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=sas_clinical --cov-report=html

# Run specific test file
pytest tests/test_dataset_compare.py -v
```

## Code Quality

### Linting

```bash
# Check code style
flake8 src/

# Format code
black src/ tests/ examples/
```

### Type Checking

```bash
mypy src/
```

## Migration from SAS

### SAS to Python Equivalents

| SAS Program | Python Module | Function |
|-------------|---------------|----------|
| `%compvars` | `comparison.dataset_compare` | `compare_vars()` |
| `%complibs` | `comparison.dataset_compare` | `compare_libraries()` |
| `%compare` | `comparison.dataset_compare` | `compare_datasets()` |
| `WPCT-F.07.01.sas` | `visualization.box_plots` | `generate_phuse_box_plots()` |
| `CreateCompareTestData.sas` | `data_processing.test_data_generator` | `create_test_data()` |
| Roland's utility macros | `utils.data_utils` | Various functions |

### Key Differences

1. **Data Format**: Python works with pandas DataFrames instead of SAS datasets
2. **File I/O**: Use `pyreadstat` to read SAS datasets, or convert to CSV/Parquet
3. **Syntax**: Python uses functions and classes instead of SAS macros
4. **Libraries**: Modern Python libraries (pandas, matplotlib) replace SAS procedures

### Migration Guide

See `docs/MIGRATION_GUIDE.md` for detailed migration instructions.

## API Documentation

### DatasetComparison Class

```python
from sas_clinical.comparison.dataset_compare import DatasetComparison

comp = DatasetComparison()

# Compare variables
var_results = comp.compare_variables(df1, df2)

# Compare datasets
ds_results = comp.compare_datasets(df1, df2, by='usubjid')

# Compare libraries
lib_results = comp.compare_libraries('lib1/', 'lib2/', by='usubjid')
```

### PHUSEBoxPlot Class

```python
from sas_clinical.visualization.box_plots import PHUSEBoxPlot

plotter = PHUSEBoxPlot(
    data=adlbc_data,
    treatment_var='trtp',
    measurement_var='aval'
)

plotter.generate_box_plots(
    output_dir='results/',
    param_codes=['ALB', 'GLUC'],
    ref_lines='UNIFORM'
)
```

### TestDataGenerator Class

```python
from sas_clinical.data_processing.test_data_generator import TestDataGenerator

generator = TestDataGenerator('data/adam', 'data/adam/mod_01')
generator.create_compare_test_data()
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - Same as original SAS repository

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/catchthewave99/SAS/issues
- Original SAS Repository: https://github.com/catchthewave99/SAS

## Acknowledgments

This Python migration preserves the functionality and design principles of the original SAS toolkit by Katja Glass Consulting. It leverages:

- Roland's SAS utility macros (datasavantconsulting.com)
- Scott Bass's comparison macros
- PHUSE Central Tendency White Paper specifications
- FDA Jumpstart Scripts (MIT License)

## Version History

- **1.0.0** (2024) - Initial Python migration
  - Complete migration of all SAS programs
  - Full test coverage
  - PHUSE-compliant visualizations
  - Comprehensive documentation
