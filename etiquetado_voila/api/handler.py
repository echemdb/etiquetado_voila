from watchdog.events import FileSystemEventHandler


class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        try:
            self.app.file_create(event.src_path)
        except AttributeError:
            pass

    def on_deleted(self, event):
        try:
            self.app.file_deleted(event.src_path)
        except AttributeError:
            pass


class FileDeletionHandler(FileSystemEventHandler):

    def __init__(self, app):
        self.app = app

    def on_deleted(self, event):
        self.app.file_deleted(event.src_path)
