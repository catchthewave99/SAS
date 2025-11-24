"""
SAS Clinical Trials Toolkit - Python Migration

A comprehensive Python package for clinical trials data management and validation,
migrated from the original SAS toolkit.

Modules:
    comparison: Dataset and library comparison tools
    visualization: PHUSE-compliant box plots and visualizations
    data_processing: Test data generation and manipulation
    utils: Common utility functions for clinical trials data
"""

__version__ = "1.0.0"
__author__ = "Katja Glass Consulting"
__license__ = "MIT"

from sas_clinical.comparison.dataset_compare import (
    DatasetComparison,
    compare_vars,
    compare_datasets,
    compare_libraries
)

from sas_clinical.visualization.box_plots import (
    PHUSEBoxPlot,
    generate_phuse_box_plots
)

from sas_clinical.data_processing.test_data_generator import (
    TestDataGenerator,
    create_test_data
)

__all__ = [
    'DatasetComparison',
    'compare_vars',
    'compare_datasets',
    'compare_libraries',
    'PHUSEBoxPlot',
    'generate_phuse_box_plots',
    'TestDataGenerator',
    'create_test_data',
]
