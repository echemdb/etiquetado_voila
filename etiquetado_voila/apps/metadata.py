import glob
import os
import yaml

from pathlib import Path, PurePath
from ipywidgets import widgets, HBox, VBox, Layout

from etiquetado_voila.apps.fileobserver import FileObserver


class MetadataApp:
    def __init__(
        self,
        template_dir,
        template_suffix=".yaml"
    ):

        self._template_dir = template_dir
        self._template_suffix = template_suffix

        self.yaml_templates = [PurePath(file) for file in glob.glob(os.path.join(self._template_dir, f"**{self.template_suffix}"))]

        self.dropdown_yaml = widgets.Dropdown(
            description="Yaml templates", options=self.yaml_templates,
            layout=Layout(width="400px", flex="flex-grow")
        )

        self.template_observer = FileObserver(observed_dir=self.template_dir, suffix=self.template_suffix)
        self.template_observer.start()
        self.on_file_created(self.add_template)
        self.on_file_deleted(self.update_templates)
        #self.text_box_folder_path.observe(self.template_observer.on_text_value_changed, names="value")

        self.output = widgets.Output()

    def on_file_created(self, *args, **kwargs):
        return self.template_observer.on_file_create(*args, **kwargs)

    def on_file_deleted(self, *args, **kwargs):
        return self.template_observer.on_file_delete(*args, **kwargs)

    @property
    def template_dir(self):
        # might ass well be store in a widget
        return self._template_dir

    @property
    def templates(self):
        return [PurePath(file) for file in glob.glob(os.path.join(self._template_dir, f"**{self.template_suffix}"))]

    @property
    def template_filename(self):
        return self.dropdown_yaml.value

    @property
    def template_suffix(self):
        # might as well be stored in a widget
        return self._template_suffix

    @property
    def template_metadata(self):
        with open(self.template_filename, "rb") as f:
            metadata = yaml.load(f, Loader=yaml.SafeLoader) or {}

        return metadata

    def add_template(self, _, filename):
        # self.dropdown_yaml.options = self.templates
        self.update_templates(_, filename)
        self.dropdown_yaml.value = [option for option in self.dropdown_yaml.options if Path(filename).stem in str(option)][0]

    def update_templates(self, _, filename):
        self.dropdown_yaml.options = self.templates
