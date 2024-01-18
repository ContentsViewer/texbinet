from pathlib import Path

import pyocr
from PIL import Image


def image2text(path: Path) -> str:
    """Convert an image file to text."""

    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        raise RuntimeError("No OCR tool found")

    tool = tools[0]
    image = Image.open(str(path))

    text = tool.image_to_string(
        image, lang="jpn+eng", builder=pyocr.builders.TextBuilder()
    )

    return text
