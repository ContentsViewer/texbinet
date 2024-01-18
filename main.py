import argparse
from pathlib import Path
import time
import sys
import logging

from texbinet.watchdog import Watchdog


class Main:
    def __init__(self, args):
        self._target = Path(args.target)
        self._logger = logging.getLogger("Main")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def run(self):
        self._logger.info(f"Watching {self._target} for changes.")

        running = True

        watchdog = Watchdog(path=self._target)
        while running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                running = False

        self._logger.info("Stopping watchdog.")
        watchdog.stop()
        watchdog.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="texbinet daemon application.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to the directory to watch for changes.",
    )

    Main(parser.parse_args()).run()
