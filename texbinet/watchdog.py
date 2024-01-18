import os
import sys
import shutil
from threading import Thread
import queue
from pathlib import Path
import logging

import watchdog.events
import watchdog.observers

from .converters.pdf2text import pdf2text
from .converters.image2text import image2text
from .converters.pptx2text import pptx2text
from .converters.docx2text import docx2text


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

    def __init__(self, path: Path):
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        self._running = True
        self._path = path
        self._queue = queue.Queue()

        self._converters = {
            ".pdf": pdf2text,
            ".jpg": image2text,
            ".pptx": pptx2text,
            ".docx": docx2text,
        }
        self._logger = logging.getLogger(f"watchdog({str(path).replace('.', '_')})")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

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
            try:
                event_handlers[event.event_type](event)
            except Exception as e:
                self._logger.error(
                    f"Exception in event handling ({event.event_type}):\n{e}"
                )

    def _get_cabitext_path(self, path: Path) -> Path:
        return Path(str(path) + ".cabi.txt")

    def _is_cabitext_file(self, path: Path) -> bool:
        return (
            path.suffixes[-2:] == [".cabi", ".txt"]
            if len(path.suffixes) >= 2
            else False
        )

    def _get_converter_for_file(self, path: Path):
        suffix = path.suffix.lower()
        return self._converters.get(suffix)

    def _on_watchdog_stop(self, event: WatchdogStopEvent):
        self._running = False

    def _on_file_sync(self, event: FileSyncEvent):
        if self._is_cabitext_file(event.path):
            return

        cabitext_path = self._get_cabitext_path(event.path)
        if (
            cabitext_path.exists()
            and cabitext_path.stat().st_mtime > event.path.stat().st_mtime
        ):
            return

        converter = self._get_converter_for_file(event.path)
        if converter is None:
            return

        self._logger.info(f"Converting {event.path} to {cabitext_path}")

        text = converter(event.path)
        cabitext_path.write_text(text, encoding="utf-8")

    def _on_file_modified(self, event: FileModifiedEvent):
        if self._is_cabitext_file(event.path):
            return

        cabitext_path = self._get_cabitext_path(event.path)

        converter = self._get_converter_for_file(event.path)
        if converter is None:
            return

        self._logger.info(f"Modified {event.path}, Converting to {cabitext_path}")

        text = converter(event.path)
        cabitext_path.write_text(text, encoding="utf-8")

    def _on_file_created(self, event: FileCreatedEvent):
        if self._is_cabitext_file(event.path):
            return

        converter = self._get_converter_for_file(event.path)
        if converter is None:
            return

        cabitext_path = self._get_cabitext_path(event.path)
        self._logger.info(f"Created {event.path}, Convert to {cabitext_path}")

        text = converter(event.path)
        cabitext_path.write_text(text, encoding="utf-8")

    def _on_file_deleted(self, event: FileDeletedEvent):
        if self._is_cabitext_file(event.path):
            return

        cabitext_path = self._get_cabitext_path(event.path)
        if not cabitext_path.exists():
            return

        self._logger.info(f"Deleted {event.path}, Delete {cabitext_path}")
        cabitext_path.unlink()

    def _on_file_moved(self, event: FileMovedEvent):
        if self._is_cabitext_file(event.src_path):
            return

        cabitext_path = self._get_cabitext_path(event.src_path)
        if not cabitext_path.exists():
            return

        self._logger.info(f"Moved {event.src_path}, Move {cabitext_path}")
        shutil.move(str(cabitext_path), str(self._get_cabitext_path(event.dest_path)))
