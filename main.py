"""
Main module for dataset browser creation and management.
"""

import pandas as pd


from typing import Optional, Literal, Any
from dataclasses import dataclass
from abc import ABC

from base import BaseDatasetProcessor, BaseDatasetBrowser, BaseRecordBrowser
from singlepoint import (
    SinglePointDatasetProcessor,
    SinglePointDatasetBrowser,
    SinglePointRecordBrowser
)

# Types we currently support
DatasetType = Literal["singlepoint"]  # Add more types as we support them

@dataclass
class DatasetComponents:
    """Container for dataset type-specific components."""
    processor_class: type[BaseDatasetProcessor]
    browser_class: type[BaseDatasetBrowser]
    record_browser_class: type[BaseRecordBrowser]

# Registry of dataset types and their components
_DATASET_TYPES = {
    "singlepoint": DatasetComponents(
        processor_class=SinglePointDatasetProcessor,
        browser_class=SinglePointDatasetBrowser,
        record_browser_class=SinglePointRecordBrowser
    )
    # Add more types as we implement them
}

class DatasetBrowser:
    """
    Main class for browsing datasets. Coordinates processing and visualization.
    
    This class brings together the dataset processor, browser, and record browser
    into a single user-friendly interface.
    """
    
    def __init__(
        self, 
        dataset: Any,
        components: DatasetComponents
    ):
        # Create our components
        self.processor = components.processor_class(dataset)
        self.record_browser_class = components.record_browser_class
        self.browser = components.browser_class(
            self.processor, 
            self.record_browser_class
        )
    
    def _ipython_display_(self):
        """Display the browser in Jupyter."""
        return self.browser._ipython_display_()
    
    @property
    def specifications(self) -> pd.DataFrame:
        """Get dataset specifications."""
        return self.processor.get_specification_df()
    
    def get_entries(
        self, 
        start: Optional[int] = None, 
        stop: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Get dataset entries."""
        return self.processor.get_entry_df(start, stop, **kwargs)
    
    def get_records(
        self,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Get dataset records."""
        return self.processor.get_record_df(start, stop, **kwargs)

def create_dataset_browser(
    dataset: Any,
) -> DatasetBrowser:
    """
    Create a dataset browser for the given dataset.
    
    Parameters
    ----------
    dataset : Any
        The dataset to browse
    dataset_type : str, optional
        Type of dataset, currently supports: "single_point"
        
    Returns
    -------
    DatasetBrowser
        Browser configured for the dataset type
        
    Examples
    --------
    >>> browser = create_dataset_browser(my_dataset)
    >>> display(browser)  # In Jupyter
    >>> 
    >>> # Access data directly if needed
    >>> specs_df = browser.specifications
    >>> entries_df = browser.get_entries()
    """
    
    # Check that it is a valid QCArchive dataset here
    # just do singlepoint for now to be lazy
    dataset_type = "singlepoint"
    
    components = _DATASET_TYPES[dataset_type]
    return DatasetBrowser(dataset, dataset_type, components)