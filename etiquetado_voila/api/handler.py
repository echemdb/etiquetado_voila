from watchdog.events import FileSystemEventHandler


class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        self.app.file_create(event.src_path)

    def on_deleted(self, event):
        self.app.file_deleted(event.src_path)

class FileDeletionHandler(FileSystemEventHandler):

    def __init__(self, app):
        self.app = app

    def on_deleted(self, event):
        self.app.file_deleted(event.src_path)
