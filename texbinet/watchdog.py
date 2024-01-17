import os
from threading import Thread
import queue
from pathlib import Path

import watchdog.events
import watchdog.observers

from .converters import pdf2text, image2text, pptx2text

EVENT_TYPE_WATCHDOG_STOP = "watchdog_stop"
EVENT_TYPE_FILE_SYNC = "file_sync"
EVENT_TYPE_FILE_CREATED = "file_created"
EVENT_TYPE_FILE_MODIFIED = "file_modified"
EVENT_TYPE_FILE_DELETED = "file_deleted"
EVENT_TYPE_FILE_MOVED = "file_moved"


class Event:
    event_type: str = ""


class WatchdogStopEvent(Event):
    event_type = EVENT_TYPE_WATCHDOG_STOP


class FileSyncEvent(Event):
    event_type = EVENT_TYPE_FILE_SYNC

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path


class FileCreatedEvent(Event):
    event_type = EVENT_TYPE_FILE_CREATED

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path


class FileModifiedEvent(Event):
    event_type = EVENT_TYPE_FILE_MODIFIED

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path


class FileDeletedEvent(Event):
    event_type = EVENT_TYPE_FILE_DELETED

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path


class FileMovedEvent(Event):
    event_type = EVENT_TYPE_FILE_MOVED

    def __init__(self, src_path: Path, dest_path: Path):
        self._src_path = src_path
        self._dest_path = dest_path

    @property
    def src_path(self) -> Path:
        return self._src_path

    @property
    def dest_path(self) -> Path:
        return self._dest_path


class Watchdog:
    class FileSystemEventHandler(watchdog.events.FileSystemEventHandler):
        def __init__(self, parent):
            super().__init__()
            self._parent = parent

        def on_modified(self, event):
            self._parent._queue.put(FileModifiedEvent(Path(event.src_path)))

        def on_created(self, event):
            self._parent._queue.put(FileCreatedEvent(Path(event.src_path)))

        def on_deleted(self, event):
            self._parent._queue.put(FileDeletedEvent(Path(event.src_path)))

        def on_moved(self, event):
            self._parent._queue.put(
                FileMovedEvent(Path(event.src_path), Path(event.dest_path))
            )

    def __init__(self, path="./tests"):
        self._running = True
        self._path = path
        self._queue = queue.Queue()

        self._converters = {
            ".pdf": pdf2text,
            ".jpg": image2text,
            ".pptx": pptx2text,
        }

        self._event_handler = self.FileSystemEventHandler(self)
        self._observer = watchdog.observers.Observer()
        self._observer.schedule(self._event_handler, path=path, recursive=True)
        self._observer.start()

        self._thread = Thread(target=self._run)
        self._thread.start()

    def stop(self):
        self._observer.stop()
        self._queue.put(WatchdogStopEvent())

    def join(self):
        self._observer.join()
        self._thread.join()

    def _run(self):
        event_handlers = {
            EVENT_TYPE_WATCHDOG_STOP: self._on_watchdog_stop,
            EVENT_TYPE_FILE_SYNC: self._on_file_sync,
            EVENT_TYPE_FILE_CREATED: self._on_file_created,
            EVENT_TYPE_FILE_MODIFIED: self._on_file_modified,
            EVENT_TYPE_FILE_DELETED: self._on_file_deleted,
            EVENT_TYPE_FILE_MOVED: self._on_file_moved,
        }

        for root, _, files in os.walk(self._path):
            for file in files:
                path = Path(root) / file
                self._queue.put(FileSyncEvent(path))

        while self._running:
            event: Event = self._queue.get()
            event_handlers[event.event_type](event)

    def _on_watchdog_stop(self, event: WatchdogStopEvent):
        self._running = False

    def _on_file_sync(self, event: FileSyncEvent):
        print(f"sync file {event.path}")

        cabitext_path = Path(str(event.path) + ".cabi.txt")
        if cabitext_path.exists() and cabitext_path.stat().st_mtime > event.path.stat().st_mtime:
            return

        try:
            text = self._converters[event.path.suffix.lower()](event.path)
            cabitext_path.write_text(text, encoding="utf-8")
        except KeyError:
            None

    def _on_file_modified(self, event: FileModifiedEvent):
        print(f"file has been modified {event.path}")

    def _on_file_created(self, event: FileCreatedEvent):
        print(f"file has been created {event.path}")

    def _on_file_deleted(self, event: FileDeletedEvent):
        print(f"file has been deleted {event.path}")

    def _on_file_moved(self, event: FileMovedEvent):
        print(f"file has been moved/renamed from {event.src_path} to {event.dest_path}")
