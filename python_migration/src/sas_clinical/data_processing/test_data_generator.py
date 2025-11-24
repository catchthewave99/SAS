"""
Test data generation module - Python equivalent of CreateCompareTestData.sas.

This module creates modified test datasets with controlled differences for comparison testing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataGenerator:
    """
    Generate test datasets with controlled modifications.

    Python equivalent of CreateCompareTestData.sas functionality.
    """

    def __init__(self, base_path: Union[str, Path], mod_path: Union[str, Path]):
        """
        Initialize test data generator.

        Args:
            base_path: Path to base/original data directory
            mod_path: Path to modified data directory
        """
        self.base_path = Path(base_path)
        self.mod_path = Path(mod_path)
        self.mod_path.mkdir(parents=True, exist_ok=True)

    def create_modified_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        drop_vars: Optional[List[str]] = None,
        add_vars: Optional[List[str]] = None,
        delete_every_nth: Optional[int] = None,
        modify_row: Optional[int] = None,
        modify_values: Optional[dict] = None,
        duplicate_row: Optional[int] = None,
        duplicate_key_value: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Create a modified version of a dataset with controlled changes.

        Replicates the modifications in CreateCompareTestData.sas:
        - Drop variables
        - Add variables
        - Delete observations
        - Modify values
        - Duplicate observations

        Args:
            df: Original dataset
            dataset_name: Name of the dataset
            drop_vars: List of variables to drop
            add_vars: List of variables to add
            delete_every_nth: Delete every Nth observation
            modify_row: Row index to modify
            modify_values: Dictionary of {column: value} to modify
            duplicate_row: Row index to duplicate
            duplicate_key_value: Value for key variable in duplicated row

        Returns:
            Modified DataFrame
        """
        df_mod = df.copy()

        logger.info(f"\nCreating modified dataset: {dataset_name}")
        logger.info(f"  Original shape: {df.shape}")

        # Drop variables
        if drop_vars:
            existing_vars = [v for v in drop_vars if v in df_mod.columns]
            if existing_vars:
                df_mod = df_mod.drop(columns=existing_vars)
                logger.info(f"  Dropped variables: {existing_vars}")

        # Add variables
        if add_vars:
            for var in add_vars:
                df_mod[var] = np.nan
            logger.info(f"  Added variables: {add_vars}")

        # Delete every Nth observation
        if delete_every_nth:
            indices_to_keep = [i for i in range(len(df_mod)) if (i + 1) % delete_every_nth != 0]
            num_deleted = len(df_mod) - len(indices_to_keep)
            df_mod = df_mod.iloc[indices_to_keep].reset_index(drop=True)
            logger.info(f"  Deleted every {delete_every_nth}th observation ({num_deleted} rows)")

        # Modify specific row
        if modify_row is not None and modify_values:
            if modify_row < len(df_mod):
                for col, val in modify_values.items():
                    if col in df_mod.columns:
                        df_mod.loc[modify_row, col] = val
                logger.info(f"  Modified row {modify_row}: {modify_values}")

        # Duplicate specific row
        if duplicate_row is not None and duplicate_row < len(df_mod):
            dup_row = df_mod.iloc[duplicate_row : duplicate_row + 1].copy()
            if duplicate_key_value and "usubjid" in dup_row.columns:
                dup_row["usubjid"] = duplicate_key_value
            df_mod = pd.concat([df_mod, dup_row], ignore_index=True)
            logger.info(f"  Duplicated row {duplicate_row}")

        logger.info(f"  Modified shape: {df_mod.shape}")

        return df_mod

    def create_compare_test_data(
        self, datasets_to_copy: List[str] = ["adsl", "adae", "advs"], dataset_to_modify: str = "adtte"
    ):
        """
        Create complete test data structure for comparison testing.

        Replicates CreateCompareTestData.sas functionality:
        1. Copy some datasets unchanged
        2. Modify one dataset with multiple types of changes
        3. Create a new dataset

        Args:
            datasets_to_copy: List of dataset names to copy unchanged
            dataset_to_modify: Name of dataset to modify
        """
        logger.info(f"\n{'='*80}")
        logger.info("Creating Compare Test Data")
        logger.info(f"  Base path: {self.base_path}")
        logger.info(f"  Modified path: {self.mod_path}")
        logger.info(f"{'='*80}")

        # Copy datasets unchanged
        for ds_name in datasets_to_copy:
            src_file = self.base_path / f"{ds_name}.sas7bdat"
            if not src_file.exists():
                src_file = self.base_path / f"{ds_name}.csv"

            if src_file.exists():
                df = self._read_dataset(src_file)
                self._write_dataset(df, self.mod_path / f"{ds_name}.csv")
                logger.info(f"Copied {ds_name}: {df.shape}")
            else:
                logger.warning(f"Dataset not found: {ds_name}")

        # Modify one dataset with multiple changes
        src_file = self.base_path / f"{dataset_to_modify}.sas7bdat"
        if not src_file.exists():
            src_file = self.base_path / f"{dataset_to_modify}.csv"

        if src_file.exists():
            df = self._read_dataset(src_file)

            # Apply modifications matching CreateCompareTestData.sas
            df_mod = self.create_modified_dataset(
                df,
                dataset_to_modify,
                drop_vars=["saffl"],  # Drop SAFFL variable
                add_vars=["newvar"],  # Add NEWVAR variable
                delete_every_nth=17,  # Delete every 17th observation
                modify_row=10,  # Modify row 11 (0-indexed = 10)
                modify_values={"race": "WHITE", "aval": np.nan},
                duplicate_row=19,  # Duplicate row 20 (0-indexed = 19)
                duplicate_key_value="01-705-1185",
            )

            self._write_dataset(df_mod, self.mod_path / f"{dataset_to_modify}.csv")
        else:
            logger.warning(f"Dataset not found: {dataset_to_modify}")

        # Create a new dataset
        new_df = pd.DataFrame({"test": [1]})
        self._write_dataset(new_df, self.mod_path / "new.csv")
        logger.info("Created new dataset: new")

        logger.info(f"\n{'='*80}")
        logger.info("Test data creation complete!")
        logger.info(f"{'='*80}\n")

    def _read_dataset(self, file_path: Path) -> pd.DataFrame:
        """Read a dataset file (SAS or CSV format)."""
        if file_path.suffix.lower() in [".sas7bdat", ".xpt"]:
            try:
                import pyreadstat

                df, meta = pyreadstat.read_sas7bdat(str(file_path))
                return df
            except ImportError:
                logger.error("pyreadstat not installed. Install with: pip install pyreadstat")
                raise
        elif file_path.suffix.lower() == ".csv":
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _write_dataset(self, df: pd.DataFrame, file_path: Path):
        """Write a dataset to CSV format."""
        df.to_csv(file_path, index=False)
        logger.info(f"  Wrote: {file_path.name}")


def create_test_data(base_path: Union[str, Path], mod_path: Union[str, Path]):
    """
    Convenience function to create test data.

    Python equivalent of CreateCompareTestData.sas.
    """
    generator = TestDataGenerator(base_path, mod_path)
    generator.create_compare_test_data()
