"""
Classes for Singlepoint records and datasets
"""

import pandas as pd
import mols2grid

from base import BaseDatasetProcessor, BaseDatasetBrowser, BaseRecordBrowser
from rdkit import Chem

from copy import deepcopy
from util import gather_molecular_data

import ipywidgets as widgets
from IPython.display import display, HTML

from IPython.display import display, HTML
import ipywidgets as widgets

class SinglePointDatasetBrowser(BaseDatasetBrowser):
    """Browser for viewing single point datasets."""
    
    def __init__(self, dataset_processor):
        super().__init__(dataset_processor)
        self._current_view = None
        self._output = widgets.Output()
        self._num_headers = 0
    
    def create_header(self):
        """Create the dataset header display."""
        return widgets.HTML(f"""
        <div style="
            background: #f5f5f5;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            width: 100%;
            margin-bottom: 10px;
            box-sizing: border-box;
        ">
            <strong>{self.dataset_processor.name}</strong><br>
            {self.dataset_processor.description}
        </div>
        """)
    
    def create_navigation(self):
        """Create navigation controls."""
        spec_button = widgets.Button(
            description='View Specifications',
            layout=widgets.Layout(width='150px')
        )
        entry_button = widgets.Button(
            description='View Entries',
            layout=widgets.Layout(width='150px')
        )
        record_button = widgets.Button(
            description='View Records',
            layout=widgets.Layout(width='150px')
        )
        
        def show_specs(b):
            self._current_view = 'specifications'
            self._output.clear_output()
            with self._output:
                self._create_specification_table()
        
        def show_entries(b):
            self._current_view = 'entries'
            self._output.clear_output()
            with self._output:
                self._create_entry_table()
        
        def show_records(b):
            self._current_view = 'records'
            self._output.clear_output()
            with self._output:
                self._create_record_table()
        
        spec_button.on_click(show_specs)
        entry_button.on_click(show_entries)
        record_button.on_click(show_records)
        
        return widgets.HBox(
            [spec_button, entry_button, record_button],
            layout=widgets.Layout(
                justify_content='flex-start',
                margin='10px 0'
            )
        )
    
    def create_content(self):
        """Create the main content area."""
        # Initial view
        with self._output:
            self._create_specification_table()
        return self._output
    
    def create_style(self):
        """Create CSS styling."""
        return HTML("""
        <style>
        .widget-html {
            padding: 8px;
        }
        .widget-gridbox {
            border-collapse: collapse;
        }
        .widget-gridbox > .widget-html:nth-child(-n+{self._num_headers}) {
            border-bottom: 2px solid #000;
        }
        .widget-gridbox > .widget-html, .widget-gridbox > .widget-vbox {
            border-bottom: 1px solid #ddd;
            padding: 8px;
        }
        </style>
        """)
    
    def _create_specification_table(self):
        """Create the specifications display table."""
        df = self.dataset_processor.get_specification_df()
        
        # Create headers
        headers = [widgets.HTML(f'<strong>{col}</strong>') for col in df.columns]
        grid_items = headers

        self._num_headers = len(headers)
        
        for _, row in df.iterrows():
            for col, value in row.items():
                if col == 'Properties' or col == 'Protocols':
                    # Create expandable properties button
                    try:
                        properties = value.keys()
                    except AttributeError:
                        properties = value  
                    properties_container = widgets.VBox([
                        widgets.Button(
                            description=f"{col} ({len(properties)})",
                            layout=widgets.Layout(width='auto')
                        )
                    ])


                    output = widgets.Output()
                    with output:
                        print('\n'.join(properties))
                    output.layout.display = 'none'
                    properties_container.children = (*properties_container.children, output)

                    def make_handler(out):
                        def handler(b):
                            out.layout.display = 'none' if out.layout.display == 'block' else 'block'
                        return handler

                    properties_container.children[0].on_click(make_handler(output))
                    grid_items.append(properties_container)
                else:
                    grid_items.append(widgets.HTML(str(value)))
        
        grid = widgets.GridBox(
            grid_items,
            layout=widgets.Layout(
                grid_template_columns=f'repeat({len(df.columns)}, auto)',
                grid_gap='0',
                width='100%'
            )
        )
        display(grid)

    def _create_entry_table(self):
        """Create a paginated table of entry names with clickable entries."""
        PAGE_SIZE = 12
        total_entries = self.dataset_processor.n_entries
        total_pages = (total_entries + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = [0]
        self._num_headers = 1

        # Check if we have any RDKit molecules
        sample_df = self.dataset_processor.get_entry_df(stop=5, get_rdkit=True)
        has_rdkit = sample_df["RDKit Molecule"].notna().any()

        # Create view toggle
        view_toggle = widgets.ToggleButtons(
            options=['List', 'Grid'] if has_rdkit else ['List'],
            description='View:',
            value='List',
            layout=widgets.Layout(margin='0 0 10px 0')
        )

        if not has_rdkit:
            view_message = widgets.HTML(
                '<div style="color: #666; font-style: italic; margin-left: 10px;">'
                'Grid view unavailable: No RDKit molecules could be created</div>'
            )
            view_controls = widgets.HBox([view_toggle, view_message])
        else:
            view_controls = view_toggle

        # Create pagination controls
        prev_button = widgets.Button(
            description='Previous', 
            disabled=True,
            layout=widgets.Layout(width='100px')
        )
        next_button = widgets.Button(
            description='Next',
            disabled=total_pages <= 1,
            layout=widgets.Layout(width='100px')
        )
        page_input = widgets.Text(
            value='1',
            layout=widgets.Layout(width='50px')
        )
        page_label = widgets.HTML(
            value=f'of {total_pages}',
            layout=widgets.Layout(padding='5px 10px')
        )

        # Create content areas
        content_output = widgets.Output()
        table_output = widgets.Output()
        details_output = widgets.Output()

        def show_entry_details(entry_name):
            details_output.clear_output()
            with details_output:
                print(f"Showing entry {entry_name}")
                entry = self.dataset_processor.ds.get_entry(entry_name)
                display(entry.molecule)

        def update_list_view(page_num):
            start_idx = page_num * PAGE_SIZE
            df = self.dataset_processor.get_entry_df(
                start=start_idx,
                stop=start_idx + PAGE_SIZE
            )
            
            buttons = widgets.VBox([
                widgets.Button(
                    description=str(row['Entry Name']),
                    layout=widgets.Layout(width='auto')
                )
                for _, row in df.iterrows()
            ])
            
            for button in buttons.children:
                button.on_click(
                    lambda b, name=button.description: show_entry_details(name)
                )
            
            table_output.clear_output()
            with table_output:
                display(HTML("<table><tr><th>Entry Name</th></tr></table>"))
                display(buttons)

        def update_grid_view(page_num):
            start_idx = page_num * PAGE_SIZE
            df = self.dataset_processor.get_entry_df(
                start=start_idx,
                stop=start_idx + PAGE_SIZE,
                get_rdkit=True
            )
            df_filtered = df.dropna(subset=["RDKit Molecule"])
            
            content_output.clear_output()
            with content_output:
                if len(df_filtered) > 0:
                    df_filtered["SMILES"] = df_filtered["RDKit Molecule"].apply(Chem.MolToSmiles)
                    display(mols2grid.display(df_filtered, size=(200, 200)))
                else:
                    display(HTML(
                        "<p style='color: #666; font-style: italic;'>"
                        "No RDKit molecules available for current page</p>"
                    ))

        def update_view(view_type, page_num):
            if view_type == 'List':
                content_output.clear_output()
                with content_output:
                    display(widgets.HBox([table_output, details_output]))
                update_list_view(page_num)
            else:
                update_grid_view(page_num)

        def on_view_change(change):
            if change.new != change.old:
                update_view(change.new, current_page[0])

        def on_page_submit(event):
            try:
                new_page = int(page_input.value) - 1
                if 0 <= new_page < total_pages:
                    current_page[0] = new_page
                    prev_button.disabled = new_page == 0
                    next_button.disabled = new_page == total_pages - 1
                    update_view(view_toggle.value, new_page)
                else:
                    page_input.value = str(current_page[0] + 1)
            except ValueError:
                page_input.value = str(current_page[0] + 1)

        def on_prev_clicked(b):
            current_page[0] = max(0, current_page[0] - 1)
            update_view(view_toggle.value, current_page[0])
        
        def on_next_clicked(b):
            current_page[0] = min(total_pages - 1, current_page[0] + 1)
            update_view(view_toggle.value, current_page[0])

        # Wire up controls
        view_toggle.observe(on_view_change, names='value')
        prev_button.on_click(on_prev_clicked)
        next_button.on_click(on_next_clicked)
        page_input.on_submit(on_page_submit)
        
        # Create pagination
        pagination = widgets.HBox(
            [prev_button, page_input, page_label, next_button],
            layout=widgets.Layout(justify_content='center', margin='10px 0')
        )
        
        # Build final container
        container = widgets.VBox([
            view_controls,
            pagination,
            content_output
        ])
        
        display(container)
        update_view('List', 0)
    
    def _create_record_table(self):
        """Create a paginated table of records with clickable entries."""
        PAGE_SIZE = 5
        total_entries = self.dataset_processor.n_entries
        total_pages = (total_entries + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = [0]

        # Create content areas
        table_output = widgets.Output()
        details_output = widgets.Output()
        
        contents = widgets.VBox([
            widgets.VBox([table_output], layout=widgets.Layout(width='100%')),
            widgets.HTML('<hr style="margin: 20px 0;">'),
            widgets.VBox([details_output], layout=widgets.Layout(width='100%', margin='20px 0'))
        ])

        def show_record_details(entry_name, spec_name):
            details_output.clear_output()
            with details_output:
                record = self.dataset_processor.ds.get_record(entry_name, spec_name)
                if record is not None:
                    display(SinglePointRecordBrowser(record, entry_name=entry_name))
                else:
                    display(HTML("<p>No record found.</p>"))

        def make_handler(entry_name, spec_name, callback):
            def handler(b):
                callback(entry_name, spec_name)
            return handler

        def update_table(page_num):
            start_idx = page_num * PAGE_SIZE
            df = self.dataset_processor.get_record_df(
                start=start_idx,
                stop=start_idx + PAGE_SIZE
            )
            specs = [col for col in df.columns if col != 'Entry Name']
            self._num_headers = len(specs) + 1
            
            headers = [widgets.HTML('<div style="font-weight: bold; padding: 8px;">Entry</div>')]
            for spec in specs:
                headers.append(widgets.HTML(
                    f'<div style="font-weight: bold; text-align: center; padding: 8px;">{spec}</div>'
                ))
            
            grid_items = headers
            for _, row in df.iterrows():
                grid_items.append(widgets.HTML(
                    f'<div style="padding: 8px; border-top: 1px solid #ddd;">{row["Entry Name"]}</div>'
                ))
                
                for spec in specs:
                    if pd.notna(row[spec]):
                        button = widgets.Button(
                            description='View',
                            layout=widgets.Layout(width='60px')
                        )
                        button.on_click(make_handler(row['Entry Name'], spec, show_record_details))
                        cell = widgets.HBox(
                            [button],
                            layout=widgets.Layout(
                                justify_content='center',
                                padding='8px',
                                border_top='1px solid #ddd'
                            )
                        )
                        grid_items.append(cell)
                    else:
                        grid_items.append(widgets.HTML(
                            '<div style="text-align: center; padding: 8px; border-top: 1px solid #ddd; color: #666;">No record</div>'
                        ))
            
            grid = widgets.GridBox(
                grid_items,
                layout=widgets.Layout(
                    grid_template_columns=f'repeat({len(specs) + 1}, auto)',
                    grid_gap='0',
                    width='100%',
                    border='1px solid #ddd'
                )
            )
            
            table_output.clear_output()
            with table_output:
                display(grid)

        # Create pagination controls and wire them up
        pagination = self._create_pagination(total_pages, current_page, update_table)
        
        container = widgets.VBox([pagination, contents])
        display(container)
        update_table(0)

    def _create_pagination(self, total_pages, current_page, update_callback):
        """Create pagination controls for tables."""
        prev_button = widgets.Button(
            description='Previous',
            disabled=True,
            layout=widgets.Layout(width='100px')
        )
        next_button = widgets.Button(
            description='Next',
            disabled=total_pages <= 1,
            layout=widgets.Layout(width='100px')
        )
        page_input = widgets.Text(
            value='1',
            layout=widgets.Layout(width='50px')
        )
        page_label = widgets.HTML(
            value=f'of {total_pages}',
            layout=widgets.Layout(padding='5px 10px')
        )

        def on_page_submit(event):
            try:
                new_page = int(page_input.value) - 1
                if 0 <= new_page < total_pages:
                    current_page[0] = new_page
                    prev_button.disabled = new_page == 0
                    next_button.disabled = new_page == total_pages - 1
                    update_callback(new_page)
                else:
                    page_input.value = str(current_page[0] + 1)
            except ValueError:
                page_input.value = str(current_page[0] + 1)

        def on_prev_clicked(b):
            current_page[0] = max(0, current_page[0] - 1)
            page_input.value = str(current_page[0] + 1)
            prev_button.disabled = current_page[0] == 0
            next_button.disabled = False
            update_callback(current_page[0])
        
        def on_next_clicked(b):
            current_page[0] = min(total_pages - 1, current_page[0] + 1)
            page_input.value = str(current_page[0] + 1)
            prev_button.disabled = False
            next_button.disabled = current_page[0] == total_pages - 1
            update_callback(current_page[0])

        prev_button.on_click(on_prev_clicked)
        next_button.on_click(on_next_clicked)
        page_input.on_submit(on_page_submit)

        return widgets.HBox(
            [prev_button, page_input, page_label, next_button],
            layout=widgets.Layout(justify_content='center', margin='10px 0')
        )

class SinglePointRecordBrowser(BaseRecordBrowser):
    """Browser for single point calculation records."""
    
    def create_style(self):
        """Create CSS styling for single point record display."""
        return HTML("""
        <style>
        .widget-html {
            padding: 8px;
        }
        .property-table tr:nth-child(even) {
            background-color: #f5f5f5;
        }
        .property-table td, .property-table th {
            padding: 8px;
            text-align: left;
        }
        .property-table th {
            border-bottom: 2px solid #000;
        }
        </style>
        """)

    def create_header(self):
        """Create the header display for this record type."""
        return widgets.HTML(f"""
        <div style="
            background: #f5f5f5;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            width: 100%;
            margin-bottom: 10px;
            box-sizing: border-box;
        ">
            <strong>Program:</strong> {self.record.provenance.creator}<br>
            <strong>Version:</strong> {self.record.provenance.version}<br>
            <strong>Method:</strong> {self.record.specification.method}<br>
            <strong>Basis:</strong> {self.record.specification.basis}<br>
            <strong>Entry:</strong> {self.entry_name} <br>
        </div>
        """)

    def create_content(self):
        """Create the main content display for this record type."""
        molecule_display = self._create_molecule_display()
        property_table = self._create_property_table()
        
        return widgets.HBox([
            # Left panel with molecule
            widgets.VBox(
                [molecule_display],
                layout=widgets.Layout(width='40%')
            ),
            # Right panel with properties
            widgets.VBox(
                [property_table],
                layout=widgets.Layout(width='60%', padding='0 0 0 20px')
            )
        ])

    def _create_molecule_display(self):
        """Create the molecule display area."""
        output = widgets.Output()
        with output:
            display(self.record.molecule)
        return output

    def _create_property_table(self):
        """Create the paginated property table."""
        PAGE_SIZE = 10
        self.props = list(self.record.properties.items())
        total_pages = max(1, (len(self.props) + PAGE_SIZE - 1) // PAGE_SIZE)
        current_page = [0]  # List to allow modification in closure

        # Create pagination controls
        prev_button = widgets.Button(
            description='Previous',
            disabled=True,
            layout=widgets.Layout(width='100px')
        )
        
        next_button = widgets.Button(
            description='Next',
            disabled=total_pages <= 1,
            layout=widgets.Layout(width='100px')
        )
        
        page_input = widgets.Text(
            value='1',
            layout=widgets.Layout(width='50px')
        )
        
        page_label = widgets.HTML(
            value=f'of {total_pages}',
            layout=widgets.Layout(padding='5px 10px')
        )

        # Create content areas
        table_output = widgets.Output()
        details_output = widgets.Output()

        def show_detail(prop_name):
            """Display details for a property with its label"""
            details_output.clear_output()
            with details_output:
                display(widgets.HTML(f"<div style='font-weight: bold; margin-bottom: 10px;'>{prop_name}</div>"))
                display(self.record.properties[prop_name])

        def update_table(page_num):
            # Update pagination controls
            prev_button.disabled = page_num == 0
            next_button.disabled = page_num == total_pages - 1
            page_input.value = str(page_num + 1)
            
            # Clear details
            details_output.clear_output()
            
            # Get properties for this page
            start_idx = page_num * PAGE_SIZE
            end_idx = start_idx + PAGE_SIZE
            page_props = self.props[start_idx:end_idx]
            
            # Create table rows with buttons
            rows = []
            buttons = []  # Store button references
            
            for name, value in page_props:
                if self._is_scalar(value):
                    rows.append(widgets.HBox([
                        widgets.HTML(f'<strong>{name}</strong>'),
                        widgets.HTML(str(value))
                    ]))
                else:
                    expand_button = widgets.Button(description='Expand')
                    expand_button.on_click(lambda b, n=name: show_detail(n))
                    buttons.append(expand_button)  # Keep reference
                    rows.append(widgets.HBox([
                        widgets.HTML(f'<strong>{name}</strong>'),
                        expand_button
                    ]))
            
            # Display table
            table_output.clear_output()
            with table_output:
                display(widgets.VBox(rows))

        def on_page_submit(event):
            try:
                new_page = int(page_input.value) - 1
                if 0 <= new_page < total_pages:
                    current_page[0] = new_page
                    update_table(new_page)
                else:
                    page_input.value = str(current_page[0] + 1)
            except ValueError:
                page_input.value = str(current_page[0] + 1)

        def on_prev_clicked(b):
            current_page[0] = max(0, current_page[0] - 1)
            update_table(current_page[0])
        
        def on_next_clicked(b):
            current_page[0] = min(total_pages - 1, current_page[0] + 1)
            update_table(current_page[0])

        # Wire up controls
        prev_button.on_click(on_prev_clicked)
        next_button.on_click(on_next_clicked)
        page_input.on_submit(on_page_submit)

        # Create layouts
        pagination = widgets.HBox([
            prev_button, 
            page_input,
            page_label,
            next_button
        ], layout=widgets.Layout(
            justify_content='center',
            margin='10px 0'
        ))

        content = widgets.HBox([
            widgets.VBox([table_output], layout=widgets.Layout(width='70%')),
            widgets.VBox([details_output], layout=widgets.Layout(width='30%'))
        ])
        
        container = widgets.VBox([pagination, content])
        # Trigger initial update
        update_table(0)
        return container

    def _is_scalar(self, value):
        """Determine if a value should be displayed directly."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str) and len(value) < 40:
            return True
        return False

class SinglePointDatasetProcessor(BaseDatasetProcessor):
    """Dataset processor for singlepoint datasets."""

    def get_specification_df(self) -> pd.DataFrame:
        """Return a DataFrame of specifications with protocols and properties."""
        specs_table = []
        specifications = deepcopy(self.ds.specifications)
        status = self.ds.status()

        for v in specifications.values():
            protocols = {
                k: str(v)
                for k, v in v.specification.protocols.dict().items()
            }

            records = status.get(v.name,0)
            complete = 0
            error = 0
            invalid = 0

            if records:
                complete = status[v.name].get("complete", 0)
                error = status[v.name].get("error", 0)
                invalid = status[v.name].get("invalid", 0)
            
            row_data = [
                v.name,
                v.specification.program,
                v.specification.method,
                v.specification.basis,
                complete,
                error,
                invalid,
                protocols,
                self.ds.computed_properties.get(v.name, [])
            ]
            specs_table.append(row_data)
            
        return pd.DataFrame(
            specs_table,
            columns=["Specification Name", "Program", "Method", "Basis", "Num Complete", "Num Error", "Num Invalid", "Protocols", "Properties"]
        )
    
    def get_entry_df(self, start=None, 
                    stop=None, 
                    store_entry=False, 
                    get_openff=False, 
                    get_rdkit=False,
                    include_error=False) -> pd.DataFrame:
        """
        Return a DataFrame of entries with optional molecule processing.
        """
        entry_names = self.ds.entry_names[start:stop]
        
        self.ds.fetch_entries(entry_names)
        
        def process_entry(name):
            entry = self.ds.get_entry(name)
            return gather_molecular_data(
                entry,
                store_entry=store_entry,
                get_openff=get_openff,
                get_rdkit=get_rdkit,
                include_error=include_error
            )
        
        # Process entries sequentially but with pre-fetched data
        entries_data = [process_entry(name) for name in entry_names]
        
        df = pd.DataFrame({'Entry Name': entry_names})
        molecular_data = pd.DataFrame(entries_data)
        
        return pd.concat([df, molecular_data], axis=1)
    
    def get_record_df(self, start=None, stop=None, **kwargs) -> pd.DataFrame:
        """
        Return a DataFrame of records with specifications.
        """
        specifications = self.ds.specification_names
        entries = list(self.ds.entry_names)[slice(start, stop)]
        
        # Initialize empty DataFrame with entries as index
        df = pd.DataFrame(index=pd.Index(entries, name='Entry Name'), columns=specifications)
        
        # Pre-fetch and fill records by specification
        for spec in specifications:
            self.ds.fetch_records(specification_names=spec, entry_names=entries)
            
            # Create dictionary mapping entries to their records to ensure alignment
            record_dict = {
                entry: self.ds.get_record(entry, spec) 
                for entry in entries
            }
            
            # Fill column using the mapping
            df[spec] = df.index.map(record_dict)
        
        return df.reset_index()
            
        