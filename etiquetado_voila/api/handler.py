from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, *processing_callbacks, suffix=".csv"):
        r"""``*processing_callbacks`` are python methods which interact and process
        newly created files with the specified ``suffix`` detected by watchdog."""
        self.suffix = suffix
        self.processing_callbacks = processing_callbacks

    def on_created(self, event):
        if Path(event.src_path).suffix == self.suffix:
            filename = event.src_path
            # When a new file is created we catch the filename and parse it to a method
            # to generate, for example, output yaml files and markdown files containing additional notes
            for method in self.processing_callbacks:
                method(filename=filename)


class FileObserver:

    def __init__(self, observed_dir=".", suffix=".csv", callbacks=None):
        self._observed_dir = observed_dir
        self._suffix = suffix
        self.observer = None
        self.callbacks = callbacks

    @property
    def suffix(self):
        return self._suffix

    @property
    def observed_dir(self):
        return self._observed_dir

    def processing_callbacks(self, filename):
        if self.callbacks == None:
            return print(filename)
        return [callback(filename) for callback in self.callbacks]

    def create_observer(self):
        self.observer = Observer()

        from etiquetado_voila.api.handler import FileCreationHandler

        self.observer.schedule(
            FileCreationHandler(self.processing_callbacks, suffix=self.suffix),
            self.observed_dir,
            recursive=False,
        )
        print("observer created")

    def start(self):
        if self.observer is None:
            self.create_observer()
            self.observer.start()
            print(
                f"start watching files with suffix '{self.suffix}' in folder '{self.observed_dir}'."
            )
        elif self.observer.is_alive():
            print("Stop observer before restarting.")
            print(
                f"Currently observing files with suffix '{self.suffix}' in folder '{self.observed_dir}'."
            )

    def stop(self):
        if self.observer is None:
            print("observer not running")
        else:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Stopped watching")
