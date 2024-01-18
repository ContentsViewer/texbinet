from pathlib import Path

import easyocr


def image2text(path: Path) -> str:
    """Convert an image file to text."""

    reader = easyocr.Reader(["en", "ja"])
    texts = reader.readtext(str(path))

    text = "\n".join([text for _, text, accuracy in texts if accuracy > 0.5])

    return text
