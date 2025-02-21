"""
Base classes for dataset processing and visualization system.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import pandas as pd
from IPython.display import display, HTML
import ipywidgets as widgets

class BaseRecordBrowser(ABC):
    """Base class for record viewing widgets."""
    
    def __init__(self, record: Any, entry_name: Optional[str] = None):
        self.record = record
        self.entry_name = entry_name
        self._style = None
        self._header = None
        self._content = None
    
    @abstractmethod
    def create_header(self) -> widgets.Widget:
        """Create the header display for this record type."""
        pass
    
    @abstractmethod
    def create_content(self) -> widgets.Widget:
        """Create the main content display for this record type."""
        pass
    
    def create_style(self) -> HTML:
        """Create CSS styling. Can be overridden by subclasses."""
        return HTML("""
        <style>
        .record-browser {
            padding: 8px;
        }
        .record-browser-header {
            background: #f5f5f5;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        </style>
        """)
    
    def _ipython_display_(self):
        """Display the record browser."""
        self._style = self.create_style()
        self._header = self.create_header()
        self._content = self.create_content()
        
        layout = widgets.VBox([
            self._header,
            self._content
        ])
        
        display(self._style, layout)


class BaseDatasetBrowser(ABC):
    """Base class for dataset viewing widgets."""
    
    def __init__(self, dataset_processor):
        self.dataset_processor = dataset_processor
        self._style = None
        self._header = None
        self._navigation = None
        self._content = None
    
    @abstractmethod
    def create_header(self) -> widgets.Widget:
        """Create the dataset header display."""
        pass
    
    @abstractmethod
    def create_navigation(self) -> widgets.Widget:
        """Create navigation controls."""
        pass
    
    @abstractmethod
    def create_content(self) -> widgets.Widget:
        """Create the main content area."""
        pass
    
    def create_style(self) -> HTML:
        """Create CSS styling. Can be overridden by subclasses."""
        return HTML("""
        <style>
        .dataset-browser {
            padding: 8px;
        }
        .dataset-navigation {
            margin: 10px 0;
        }
        </style>
        """)
    
    def _ipython_display_(self):
        """Display the dataset browser."""
        self._style = self.create_style()
        self._header = self.create_header()
        self._navigation = self.create_navigation()
        self._content = self.create_content()
        
        layout = widgets.VBox([
            self._header,
            self._navigation,
            self._content
        ])
        
        display(self._style, layout)


class BaseDatasetProcessor(ABC):
    """Base class for dataset processing."""
    
    def __init__(self, ds):
        self.ds = ds
    
    @abstractmethod
    def get_specification_df(self) -> pd.DataFrame:
        """Get specifications as a DataFrame."""
        pass
    
    @abstractmethod
    def get_entry_df(
        self,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Get entries as a DataFrame."""
        pass
    
    @abstractmethod
    def get_record_df(
        self,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Get records as a DataFrame."""
        pass
    
    @property
    def name(self) -> str:
        """Get dataset name."""
        return self.ds.name
    
    @property
    def description(self) -> str:
        """Get dataset description."""
        return self.ds.description
    
    @property
    def n_entries(self) -> int:
        """Get number of entries."""
        return len(self.ds.entry_names)
    
    @property
    def n_specifications(self) -> int:
        """Get number of specifications."""
        return len(self.ds.specification_names)