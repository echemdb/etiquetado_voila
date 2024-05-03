import glob
import os
import yaml

import time
from pathlib import Path

from etiquetado_voila.api.handler import FileObserver
from etiquetado_voila.apps.pieces import ListOptions

from ipywidgets import widgets, HBox, VBox, Layout

import ipyvuetify as v

# Create an ipyvuetify widget (e.g., a button)


class FileObserverApp(FileObserver):

    def __init__(self, observed_dir=".", suffix=".csv"):

        FileObserver.__init__(self, observed_dir=observed_dir, suffix=suffix)

        # buttons
        # self.button_start = widgets.Button(description="Start watching")
        self.button_start = v.Btn(color='primary', children=["Start watching"])
        self.button_stop = widgets.Button(description="Stop watching")

        # button interactions
        # self.button_start.on_click(self.on_start)
        self.button_start.on_event('click', self.on_start)
        self.button_stop.on_click(self.on_stop)

        # Status indicator
        self.indicator = widgets.Button(description="Offline")
        self.indicator.style.button_color = "red"
        self.indicator.style.text_color = "black"

        # output
        self.output = widgets.Output()

    def on_stop(self, *args):
        self.stop()
        self.indicator.style.button_color = "red"
        self.indicator.description = "Offline"

    def on_start(self, *args):
        self.start()
        self.indicator.style.button_color = "lightgreen"
        self.indicator.description = "Watching"

    def restart(self):
        self.on_stop()
        self.on_start()

    def observer_layout(self):
        buttons = HBox(children=[self.button_start, self.button_stop])
        indicator = HBox(children=[self.indicator])
        return VBox(children=[buttons, indicator])

    def gui(self):
        with self.output:
            return self.observer_layout()


class PropertySelectorApp:

    def __init__(self, observed_dir, suffix):

        self._observed_dir = observed_dir
        self._suffix = suffix
        self.output = widgets.Output()

        self.text_box_folder_path = widgets.Text(
            description="folder path", value=self._observed_dir, continuous_update=False
        )
        self.text_box_file_suffix = widgets.Text(
            description="file suffix", value=self._suffix, continuous_update=False
        )

    def properties_layout(self):
        return VBox(children=[self.text_box_folder_path, self.text_box_file_suffix])

    def gui(self):
        with self.output:
            return self.properties_layout()

class TemplateSelector():

    def __init__(self, template_dir, template_suffix='.yaml'):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self.yaml_templates = glob.glob(os.path.join(self._template_dir, '**.yaml'))
        self.dropdown_yaml= widgets.Dropdown(description='Yaml templates', options=self.yaml_templates)

        self.output = widgets.Output()


    @property
    def template_dir(self):
        return self._template_dir

    @property
    def yaml_template(self):
        return self.dropdown_yaml.value

    @property
    def template_suffix(self):
        return self._template_suffix

    def template_selector_layout(self):
        return self.dropdown_yaml

    def gui(self):
        with self.output:
            return self.template_selector_layout()


class FileObserverSelectorApp(PropertySelectorApp, FileObserverApp):

    def __init__(self, observed_dir, suffix):
        self._observed_dir = observed_dir
        self._suffix = suffix
        PropertySelectorApp.__init__(
            self, observed_dir=self._observed_dir, suffix=self._suffix
        )
        FileObserverApp.__init__(
            self, observed_dir=self._observed_dir, suffix=self._suffix
        )

        self.output = widgets.Output()

        self.text_box_folder_path.observe(self.on_text_value_change, names="value")
        self.text_box_file_suffix.observe(self.on_text_value_change, names="value")

    def on_text_value_change(self, change):
        if self.observer:
            if self.observer.is_alive():
                self.restart()

    @property
    def suffix(self):
        return self.text_box_file_suffix.value

    @property
    def observed_dir(self):
        return self.text_box_folder_path.value

    def layout(self):
        return VBox(children=[self.properties_layout(), self.observer_layout()])

    def gui(self):
        with self.output:
            return self.layout()


class AutoQuetado(FileObserverSelectorApp, TemplateSelector):

    def __init__(self, observed_dir, suffix, template_dir, template_suffix='.yaml'):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self._observed_dir = observed_dir
        self._suffix = suffix

        FileObserverSelectorApp.__init__(
            self, observed_dir=self._observed_dir, suffix=self._suffix
        )
        TemplateSelector.__init__(
            self, template_dir=self._template_dir, template_suffix=self._template_suffix
        )

        self.dropdown_yaml.observe(self.on_text_value_change, names="value")

    def extend_metadata(self, metadata):
        metadata.setdefault('time metadata', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        return metadata

    def append_metadata(self, filename):
        # load the metadata from a yaml template
        with open(self.yaml_template, 'rb') as f:
            _metadata = yaml.load(f, Loader=yaml.SafeLoader)

        metadata = self.extend_metadata(_metadata)

        outyaml = Path(filename).with_suffix(f'{self.suffix}.yaml')
        with open(outyaml, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f)

    def processing_callbacks(self, filename):
        # wait to ensure that the file is created
        # otherwise a file permission error might be raised
        # if in any of the following processing steps
        # the measurement file is loaded.
        # time.sleep(1)
        return print(filename), self.append_metadata(filename=filename)


    def layout(self):
        return VBox(children=[self.dropdown_yaml, self.properties_layout(), self.observer_layout()])

    def gui(self):
        with self.output:
            return self.layout()

class AutoQuetadoMetadata(AutoQuetado):

    def __init__(self, observed_dir, suffix='.csv', template_dir='./files/yaml_templates/', template_suffix='.yaml', metadata_defaults=None):

        self._metadata_defaults = metadata_defaults

        self.output = widgets.Output()

        AutoQuetado.__init__(self, observed_dir, suffix, template_dir, template_suffix=template_suffix)

        self.metadata_text_fields = [widgets.Text(description=key, value=value, continuous_update=False) for key, value in metadata_defaults.items()]
        # Restart observer for any kind of Text widget input change
        for text in self.metadata_text_fields:
            text.observe(self.on_text_value_change, names="value")

    @property
    def mds_textfields(self):
        # This definately needs another name or other approach
        return {field.description: field.value for field in self.metadata_text_fields}

    def layout_metadata(self):
        return VBox(children=[field for field in self.metadata_text_fields])

    def extend_metadata(self, metadata):
        _metadata = super().extend_metadata(metadata)
        _metadata['user'] = self.mds_textfields['user']
        return _metadata


    def metagui(self):
        # tabs = {'Observer':self.layout, 'Default Metadata': self.layout_metadata}
        tab = widgets.Tab()
        # tab.children([[],self.layout_metadata])
        # tab_contents = ['P0', 'P1', 'P2', 'P3', 'P4']
        # children = [widgets.Text(description=name) for name in tab_contents]
        tab.children = [self.layout(), self.layout_metadata()]

        tab.titles = ['Observer', 'Default Metadata']
        with self.output:
            return tab

class AutoQuetadoConverter(AutoQuetadoMetadata, ListOptions):

    def __init__(self, observed_dir, suffix='.csv', template_dir='./files/yaml_templates/', template_suffix='.yaml', metadata_defaults=None, outdir_converted='./files/data_converted/'):
        AutoQuetadoMetadata.__init__(self, observed_dir=observed_dir, suffix=suffix, template_dir=template_dir, template_suffix=template_suffix, metadata_defaults=metadata_defaults)
        self.list_options = ListOptions(list_name='Tagged Files')
        self.outdir_converted = outdir_converted

        self.app_output = widgets.Output()
        self.output = widgets.Output()

        self.button_convert_files = widgets.Button(description='Convert selected files')
        self.button_convert_files.on_click(self.on_convert_files)

    def convert_file(self, filename):
        from echemdbconverters.csvloader import CSVloader
        from unitpackage.entry import Entry
        from pathlib import Path
        import yaml
        file = Path(filename)
        with open(file.with_suffix('.csv.yaml')) as f:
            metadata = yaml.load(f, Loader=yaml.SafeLoader)
        loaded = CSVloader(open(filename, 'r'))

        entry = Entry.from_df(loaded.df, basename=file.stem, metadata=metadata)
        entry.save(outdir=self.outdir_converted)

    def on_convert_files(self, *args):
        for filename in self.list_options.option_selector.value:
            self.convert_file(filename=filename)
        # the filenames must be removed from the selector after the conversion
        # otherwise the above loop will break
        for filename in self.list_options.option_selector.value:
            self.list_options.remove_option(filename)

    def processing_callbacks(self, filename):
        return print(filename), self.append_metadata(filename=filename), self.list_options.add_option(filename)

    def conv_gui(self):
        tab = widgets.Tab()
        converter = VBox(children=[self.list_options.option_selector, self.button_convert_files])

        tab.children = [self.layout(), self.layout_metadata(), converter]

        tab.titles = ['Observer', 'Default Metadata', 'Convert Files']
        layout = VBox(children=[tab, self.output])
        with self.app_output:
            return layout

