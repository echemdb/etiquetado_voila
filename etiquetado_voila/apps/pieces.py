import glob
import os
import yaml

import time
from pathlib import Path

from ipywidgets import widgets, HBox, VBox, Layout


class ListOptions:
    r"""Keep the content of a selection widget up to date with content in a file.
    This allows storing the state of the widget in, for example, yaml file
    when you want to pick up the work at a later stage.
    """

    def __init__(
        self, option_selector=None, defaults_file="tagger_defaults.yaml", list_name=None
    ):

        self._defaults_file = defaults_file
        self.list_name = list_name or self.__class__.__name__

        self.option_selector = option_selector or widgets.SelectMultiple(
            options=(""),
            description=f"{self.list_name}",
            layout=Layout(width="600px", height="180px", flex="flex-grow"),
        )

        self.sync_options()

    @property
    def defaults_file(self):
        if not os.path.exists(self._defaults_file):
            with open(self._defaults_file, "w") as f:
                f.write(f"{self.list_name}: []\n")
        return self._defaults_file

    def add_option(self, option):
        new_options = [item for item in self.option_selector.options]
        if new_options:
            if not option in new_options:
                new_options.append(option)
        self.reset_options(new_options)

    def remove_option(self, option):
        new_options = [item for item in self.option_selector.options if item != option]
        self.reset_options(new_options)

    def reset_options(self, options):
        self.option_selector.options = options
        file_metadata = self.file_metadata
        file_metadata[self.list_name] = options
        # tagged = {self.list_name: options}
        with open(self.defaults_file, "w") as f:
            yaml.dump(file_metadata, f)

    def sync_options(self):
        file_options = self.get_file_options()
        widget_options = self.option_selector.options

        new_options = list(set(file_options) | set(widget_options))

        # new_options = [_ for _ in self.tagged_files.options if not _ in self.tagged_files.value]
        self.reset_options(new_options)

    @property
    def file_metadata(self):
        with open(self.defaults_file, "rb") as f:
            file_metadata = yaml.load(f, Loader=yaml.SafeLoader)
        return file_metadata

    def get_file_options(self):
        metadata = self.file_metadata
        metadata.setdefault(self.list_name, [])
        return metadata[self.list_name]
