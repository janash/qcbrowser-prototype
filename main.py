"""

"""

from functools import wraps

from singlepoint import SinglePointDatasetBrowser, SinglePointDatasetProcessor

_processors = {
    "singlepointdataset": SinglePointDatasetProcessor
}

_browsers = {
    "singlepointdataset": SinglePointDatasetBrowser
}
class DatasetBrowser:
    def __init__(self, dataset, dataset_type):
        ProcessorClass = _processors[dataset_type]
        BrowserClass = _browsers[dataset_type]
        
        self.processor = ProcessorClass(dataset)
        self.browser = BrowserClass(self.processor)

        # Create wrapped methods at instantiation time
        self.get_entries = wraps(self.processor.get_entry_df)(
            lambda *args, **kwargs: self.processor.get_entry_df(*args, **kwargs)
        )
        
        self.get_records = wraps(self.processor.get_record_df)(
            lambda *args, **kwargs: self.processor.get_record_df(*args, **kwargs)
        )

        self.get_specifications = wraps(self.processor.get_specification_df)(
            lambda *args, **kwargs: self.processor.get_specification_df(*args, **kwargs)
        )

        self.get_properties = wraps(self.processor.ds.get_properties_df)(
            lambda *args, **kwargs: self.processor.ds.get_properties_df(*args, **kwargs)
        )
    
    def _ipython_display_(self):
        self.browser._ipython_display_()

def create_dataset_browser(dataset):

    dataset_type = type(dataset).__name__.lower()

    return DatasetBrowser(dataset, dataset_type)
