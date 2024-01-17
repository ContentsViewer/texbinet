from pathlib import Path
import numpy as np


def pdf2text(path: Path) -> str:
    """Convert a PDF file to text."""

    # import easyocr
    # from pdf2image import convert_from_path

    # images = convert_from_path(path)
    # reader = easyocr.Reader(["en", "ja"])

    # text = ""
    # for image in images:
    #     texts = reader.readtext(np.array(image), detail=0)
    #     print(texts)
    #     text += "\n".join(texts) + "\n"

    # return text

    import pypdf
    with path.open("rb") as f:
        pdf = pypdf.PdfReader(f)
        return "\n".join(page.extract_text() for page in pdf.pages)
