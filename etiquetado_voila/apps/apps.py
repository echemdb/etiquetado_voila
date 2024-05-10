import glob
import os
import yaml

import time
from pathlib import Path

from etiquetado_voila.apps.pieces import ListOptions

from ipywidgets import widgets, HBox, VBox, Layout
from ipywidgets.widgets.widget import CallbackDispatcher


class FileObserverApp:

    def __init__(self, observed_dir=".", suffix=".csv", output=None):

        self._output = output or widgets.Output()
        self._file_create_handlers = CallbackDispatcher()

        # input widgets
        self.text_box_folder_path = widgets.Text(
            description="folder path", value=observed_dir, continuous_update=False,
        )
        self.text_box_file_suffix = widgets.Text(
            description="file suffix", value=suffix, continuous_update=False
        )
        self.text_box_folder_path.observe(self.on_text_value_changed, names="value")
        self.text_box_file_suffix.observe(self.on_text_value_changed, names="value")

        # Homebrew widgets
        self.observer = None

        self.button_start_stop = widgets.Button(description="Stop watching")
        self.button_start_stop.style.button_color = "red"
        self.button_start_stop.style.text_color = "black"
        self.button_start_stop.on_click(self.toggle_start_stop)

    def on_file_create(self, callback, remove=False):
        """
        """
        self._file_create_handlers.register_callback(callback, remove=remove)

    def file_create(self, filename):
        """
        """
        if Path(filename).suffix == self.suffix: # suffix of the textbox
            self._file_create_handlers(self, filename)

    @property
    def output(self):
        return self._output

    @property
    def suffix(self):
        return self.text_box_file_suffix.value

    @property
    def observed_dir(self):
        return self.text_box_folder_path.value

    def on_text_value_changed(self, change):
        self.stop() and self.start()

    def start(self):
        if self.observer is not None:
            return False

        from watchdog.observers import Observer
        self.observer = Observer()

        from etiquetado_voila.api.handler import FileCreationHandler

        self.observer.schedule(
            FileCreationHandler(app=self),
            path=self.observed_dir,
            recursive=False,)

        self.button_start_stop.style.button_color = "lightgreen"
        self.button_start_stop.description = "Watching"
        self.button_start_stop.description = "Stop watching"
        self.observer.start()
        print(
            f"start watching files with suffix '{self.suffix}' in folder '{self.observed_dir}'."
        )
        return True

    def stop(self):
        if self.observer is None:
            print("observer not running")
            return False
        self.observer.stop()
        self.observer.join()
        self.observer = None
        self.button_start_stop.style.button_color = "red"
        self.button_start_stop.style.text_color = "black"
        self.button_start_stop.description = "Start watching"
        print("Stopped watching")
        return True

    def toggle_start_stop(self, *args):
        return self.stop() or self.start()

    def restart(self):
        self.stop()
        self.start()

    def observer_layout(self):
        selectors = VBox(
            children=[self.text_box_folder_path, self.text_box_file_suffix]
        )

        return VBox(children=[selectors, self.button_start_stop])

    def gui(self):
        with self.output:
            return self.observer_layout()


class MetadataApp:
    # This has to be cleaned and seems useless...
    def __init__(
        self,
        template_dir,
        template_suffix=".yaml",
    ):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self.yaml_templates = glob.glob(os.path.join(self._template_dir, f"**{self.template_suffix}"))
        self.dropdown_yaml = widgets.Dropdown(
            description="Yaml templates", options=self.yaml_templates,
            layout=Layout(width="400px", flex="flex-grow")
        )

        self.output = widgets.Output()

    @property
    def template_dir(self):
        # might ass well be store in a widget
        return self._template_dir

    @property
    def template_filename(self):
        return self.dropdown_yaml.value

    @property
    def template_suffix(self):
        # might as well be stored in a widget
        return self._template_suffix

    @property
    def _metadata(self):
        with open(self.template_filename, "rb") as f:
            metadata = yaml.load(f, Loader=yaml.SafeLoader)

        return metadata

    def metadata(self):
        _metadata = self._metadata
        # update _metadata with fields from other schema
        return _metadata

    def store_metadata(self, outyaml):
        # outyaml = Path(self.filename).with_suffix(f'{self.foa.suffix}.yaml')
        # outyaml = Path(self.filename).with_suffix(self.output_suffix)
        with open(outyaml, "w", encoding="utf-8") as f:
            yaml.dump(self.metadata, f)

    def update_template_list(self):
        # Update the dropdown list when new templates
        # are created in the templates folder
        pass


class AutoQuetado:

    def __init__(
        self,
        observed_dir,
        suffix,
        template_dir,
        update_metadata=None, # method that changes metadata received from YAML or adds new metadata
        variable_metadata=None,
        template_suffix=".yaml",
    ):

        self._template_dir = template_dir
        self._template_suffix = template_suffix


        self._update_metadata = update_metadata
        self._variable_metadata = variable_metadata
        self.output = widgets.Output()

        self.foa = FileObserverApp(
            observed_dir=observed_dir,
            suffix=suffix,
            output=self.output
        )

        self.on_file_created(self.tag_data)
        # self.on_file_created(lambda _, filename: print(filename))

        self.metadata_app = MetadataApp(
            template_dir=self._template_dir, template_suffix=self._template_suffix
        )

        self.metadata_app.dropdown_yaml.observe(
            self.foa.on_text_value_changed, names="value"
        )

        self.metadata_text_fields = None

        if self._variable_metadata:
            self.metadata_text_fields = [
                widgets.Text(description=key, value=value, continuous_update=False)
                for key, value in self._variable_metadata.items()
            ]
            for text in self.metadata_text_fields:
                text.observe(self.foa.on_text_value_changed, names="value")

    def on_file_created(self, *args, **kwargs):
        return self.foa.on_file_create(*args, **kwargs)


    def tag_data(self, _, filename):
        # load the metadata from a yaml template
        with open(self.metadata_app.template_filename, "rb") as f:
            _metadata = yaml.load(f, Loader=yaml.SafeLoader)

        metadata = self.update_metadata(metadata=_metadata, filename=filename)

        outyaml = Path(filename).with_suffix(f"{self.foa.suffix}.yaml")

        with open(outyaml, "w", encoding="utf-8") as f:
            yaml.dump(metadata, f)

    @property
    def variable_metadata(self):
        # returns the name/description of the text fields and the current values
        return {text_field.description: text_field.value for text_field in self.metadata_text_fields}

    def update_metadata(self, metadata, filename):
        if self._update_metadata:
            return self._update_metadata(metadata=metadata, filename=filename)

        metadata.setdefault(
            "time metadata", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        metadata.setdefault("filename", filename)
        if self._variable_metadata:
            for key, item in self.variable_metadata.items():
                metadata[key] = item
        return metadata


    def layout_metadata(self):
        return VBox(children=[field for field in self.metadata_text_fields])

    def layout_observer(self):
        return VBox(
            children=[self.metadata_app.dropdown_yaml, self.foa.observer_layout()]
        )

    def basic_gui(self):
        tab = widgets.Tab()
        tab.children = [self.layout_observer()]
        tab.titles = ["Observer"]
        with self.output:
            return tab

    def metadata_gui(self):
        tab = widgets.Tab()
        tab.children = [self.layout_observer(), self.layout_metadata()]
        tab.titles = ["Observer", "Variable Metadata"]

        with self.output:
            return tab

    def gui(self):
        if self.metadata_text_fields:
            return self.metadata_gui()
        with self.output:
            return self.basic_gui()


class AutoQuetadoConverter(AutoQuetado):

    def __init__(
        self,
        observed_dir,
        suffix=".csv",
        template_dir="./files/yaml_templates/",
        template_suffix=".yaml",
        update_metadata=None,
        variable_metadata=None,
        converter = None,
        outdir_converted="./files/data_converted/",
    ):
        self._converter = converter
        self.list_options = ListOptions(list_name="Tagged Files")

        AutoQuetado.__init__(
            self,
            observed_dir=observed_dir,
            suffix=suffix,
            template_dir=template_dir,
            template_suffix=template_suffix,
            update_metadata=update_metadata,
            variable_metadata=variable_metadata,
        )
        self.outdir_converted = outdir_converted

        self.app_output = widgets.Output()
        self.output = widgets.Output()

        self.on_file_created(self.add_tagged_file_option)

        self.button_convert_files = widgets.Button(description="Export & convert selected files")
        self.button_convert_files.on_click(self.on_convert_files)

    def add_tagged_file_option(self, _, filename):
        return self.list_options.add_option(filename)

    def base_converter(self, filename, metadata_suffix, outdir):
        from echemdbconverters.csvloader import CSVloader
        from unitpackage.entry import Entry
        from pathlib import Path
        import yaml

        file = Path(filename)
        with open(file.with_suffix(metadata_suffix)) as f:
            metadata = yaml.load(f, Loader=yaml.SafeLoader)
        loaded = CSVloader(open(filename, "r"))

        entry = Entry.from_df(loaded.df, basename=file.stem, metadata=metadata)
        entry.save(outdir=outdir)

    def convert_file(self, filename):
        if self._converter:
            return self._converter(filename)
        self.base_converter(filename, metadata_suffix=".csv.yaml", outdir=self.outdir_converted)


    def on_convert_files(self, *args):
        for filename in self.list_options.option_selector.value:
            self.convert_file(filename=filename)
        # the filenames must be removed from the selector after the conversion
        # otherwise the above loop will break
        for filename in self.list_options.option_selector.value:
            self.list_options.remove_option(filename)

    def layout_converter(self):
        return VBox(
            children=[self.list_options.option_selector, self.button_convert_files]
        )

    def gui(self):
        if self._variable_metadata:
            tab = widgets.Tab()

            tab.children = [
                self.layout_observer(),
                self.layout_metadata(),
                self.layout_converter(),
            ]

            tab.titles = ["Observer", "Variable Metadata", "Convert Files"]
            layout = VBox(children=[tab, self.output])
            with self.app_output:
                return layout

        tab = widgets.Tab()

        tab.children = [
            self.layout_observer(),
            self.layout_converter(),
        ]

        tab.titles = ["Observer", "Convert Files"]
        layout = VBox(children=[tab, self.output])
        with self.app_output:
            return layout
