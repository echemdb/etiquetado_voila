from etiquetado_voila.api.handler import FileObserver

from ipywidgets import widgets, HBox, VBox, Layout

class FileObserverApp(FileObserver):

    def __init__(self, observed_dir=".", suffix=".csv"):

        FileObserver.__init__(self, observed_dir=observed_dir, suffix=suffix)

        # buttons
        self.button_start = widgets.Button(description="Start watching")
        self.button_stop = widgets.Button(description="Stop watching")

        # button interactions
        self.button_start.on_click(self.on_start)
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
