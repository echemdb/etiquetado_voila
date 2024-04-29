from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, *file_processing_methods, suffix=".csv"):
        r"""``*file_processing_methods`` are python methods which interact and process
        newly created files with the specified ``suffix`` detected by watchdog."""
        self.suffix = suffix
        self.file_processing_methods = file_processing_methods

    def on_created(self, event):
        if Path(event.src_path).suffix == self.suffix:
            filename = event.src_path
            # When a new file is created we catch the filename and parse it to a method
            # to generate, for example, output yaml files and markdown files containing additional notes
            for method in self.file_processing_methods:
                method(filename)


class FileObserver:

    def __init__(self, observed_dir=".", suffix=".csv"):
        self._observed_dir = observed_dir
        self._suffix = suffix
        self.observer = None

    @property
    def suffix(self):
        return self._suffix

    @property
    def observed_dir(self):
        return self._observed_dir

    def process_tagged_file(self, filename):
        return print(filename)

    def create_observer(self):
        self.observer = Observer()

        from etiquetado_voila.api.handler import FileCreationHandler

        self.observer.schedule(
            FileCreationHandler(self.process_tagged_file, suffix=self.suffix),
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
        self.observer.stop()
        self.observer.join()
        self.observer = None
        print("Stop watching")
