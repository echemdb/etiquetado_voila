from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path


class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, app):
        r"""``*processing_callbacks`` are python methods which interact and process
        newly created files with the specified ``suffix`` detected by watchdog."""
        self.app = app

    def on_created(self, event):
        self.app.file_create(event.src_path)
