from pathlib import Path

from ipywidgets import widgets, VBox
from ipywidgets.widgets.widget import CallbackDispatcher

class FileObserver:

    def __init__(self, observed_dir=".", suffix=".csv", output=None):

        self._output = output or widgets.Output()
        self._file_create_handlers = CallbackDispatcher()
        self._file_delete_handlers = CallbackDispatcher()

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

    def on_file_delete(self, callback, remove=False):
        """
        """
        self._file_delete_handlers.register_callback(callback, remove=remove)

    def file_deleted(self, filename):
        """
        """
        if Path(filename).suffix == self.suffix: # suffix of the textbox
            self._file_delete_handlers(self, filename)

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
            f"Watching files with suffix '{self.suffix}' in folder '{self.observed_dir}'."
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
