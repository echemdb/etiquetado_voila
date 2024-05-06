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


class FileObserverApp:

    def __init__(self, observed_dir=".", suffix=".csv", callbacks=None, output=None):

        self.observed_dir = observed_dir
        self._suffix = suffix
        self.callbacks = callbacks
        self._output = output

        # input widgets
        self.text_box_folder_path = widgets.Text(
            description="folder path", value=self.observed_dir, continuous_update=False
        )
        self.text_box_file_suffix = widgets.Text(
            description="file suffix", value=self._suffix, continuous_update=False
        )
        self.text_box_folder_path.observe(self.on_text_value_change, names="value")
        self.text_box_file_suffix.observe(self.on_text_value_change, names="value")

        # Homebrew widgets
        self.fileobserver = FileObserver(observed_dir=self.observed_dir, suffix=self._suffix, callbacks=self.callbacks)

        # buttons
        self.button_stop = widgets.Button(description="Stop watching")
        self.button_stop.on_click(self.on_stop)

        # demo ipyvuetifiy button
        # self.button_start = v.Btn(color='primary', children=["Start watching"])
        # self.button_start.on_event('click', self.on_start)
        # ipywidgets button
        self.button_start = widgets.Button(description="Start watching")
        self.button_start.on_click(self.on_start)

        # Status indicator
        self.indicator = widgets.Button(description="Offline")
        self.indicator.style.button_color = "red"
        self.indicator.style.text_color = "black"



        # output
        self._output = output or widgets.Output()

    @property
    def output(self):
        return self._output

    @property
    def suffix(self):
        return self.text_box_file_suffix.value

    def on_text_value_change(self, change):
        if self.fileobserver.observer:
            if self.fileobserver.observer.is_alive():
                self.fileobserver._suffix = self.text_box_file_suffix.value
                self.restart()

    def on_stop(self, *args):
        self.fileobserver.stop()
        self.indicator.style.button_color = "red"
        self.indicator.description = "Offline"

    def on_start(self, *args):
        self.fileobserver.start()
        self.indicator.style.button_color = "lightgreen"
        self.indicator.description = "Watching"

    def restart(self):
        self.on_stop()
        self.on_start()

    def observer_layout(self):
        selectors = VBox(children=[self.text_box_folder_path, self.text_box_file_suffix])
        buttons = HBox(children=[self.button_start, self.button_stop])
        indicator = HBox(children=[self.indicator])
        return VBox(children=[selectors, buttons, indicator])

    def gui(self):
        with self.output:
            return self.observer_layout()


class TemplateSelector():

    def __init__(self, template_dir, template_suffix='.yaml'):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self.yaml_templates = glob.glob(os.path.join(self._template_dir, '**.yaml'))
        self.dropdown_yaml= widgets.Dropdown(description='Yaml templates', options=self.yaml_templates)

        self.output = widgets.Output()


    @property
    def template_dir(self):
        # might ass well be store in a widget
        return self._template_dir

    @property
    def yaml_template(self):
        return self.dropdown_yaml.value

    @property
    def template_suffix(self):
        # might as well be stored in a widget
        return self._template_suffix

    def update_template_list(self):
        # Update the dropdown list when new templates
        # are created in the templates folder
        pass

    def template_selector_layout(self):
        return self.dropdown_yaml

    def gui(self):
        with self.output:
            return self.template_selector_layout()


class AutoQuetado:

    def __init__(self, observed_dir, suffix, template_dir, template_suffix='.yaml'):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self._observed_dir = observed_dir
        self._suffix = suffix
        self.output = widgets.Output()

        self.foa = FileObserverApp(
            observed_dir=self._observed_dir, suffix=self._suffix, callbacks=self.callbacks()
        )
        self.template_selector = TemplateSelector(
            template_dir=self._template_dir, template_suffix=self._template_suffix
        )

        self.template_selector.dropdown_yaml.observe(self.foa.on_text_value_change, names="value")

    def extend_metadata(self, metadata, filename):
        metadata.setdefault('time metadata', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        metadata.setdefault('filename', filename)
        return metadata

    def append_metadata(self, filename):
        # load the metadata from a yaml template
        with open(self.template_selector.yaml_template, 'rb') as f:
            _metadata = yaml.load(f, Loader=yaml.SafeLoader)

        metadata = self.extend_metadata(metadata=_metadata, filename=filename)

        outyaml = Path(filename).with_suffix(f'{self.foa.suffix}.yaml')
        with open(outyaml, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f)

    def callbacks(self):
        # For manual tagging of files.
        def print_filename(filename):
            return print(filename)

        return [print_filename, self.append_metadata]

    def tag(self, filename):
        for callback in self.callbacks():
            callback(filename)

    def layout(self):
        return VBox(children=[self.template_selector.dropdown_yaml, self.foa.observer_layout()])

    def gui(self):
        with self.output:
            return self.layout()

class AutoQuetadoMetadata(AutoQuetado):
    # The app should provide some convenience functionalities
    # such that the most commonly changed variables in the metadata template
    # can be updated in the GUI.

    def __init__(self, observed_dir, suffix='.csv', template_dir='./files/yaml_templates/', template_suffix='.yaml', metadata_defaults=None):

        self._metadata_defaults = metadata_defaults

        # self.output = widgets.Output()

        AutoQuetado.__init__(self, observed_dir, suffix, template_dir, template_suffix=template_suffix)

        self.metadata_text_fields = [widgets.Text(description=key, value=value, continuous_update=False) for key, value in metadata_defaults.items()]
        # Restart observer for any kind of Text widget input change
        for text in self.metadata_text_fields:
            text.observe(self.foa.on_text_value_change, names="value")

    @property
    def mds_textfields(self):
        # This definitely needs another name or other approach
        return {field.description: field.value for field in self.metadata_text_fields}

    def extend_metadata(self, metadata):
        _metadata = super().extend_metadata(metadata)
        _metadata['user'] = self.mds_textfields['user']
        return _metadata

    def layout_metadata(self):
        return VBox(children=[field for field in self.metadata_text_fields])

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

class AutoQuetadoConverter(AutoQuetado):

    def __init__(self, observed_dir, suffix='.csv', template_dir='./files/yaml_templates/', template_suffix='.yaml', metadata_defaults=None, outdir_converted='./files/data_converted/'):

        AutoQuetado.__init__()
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

