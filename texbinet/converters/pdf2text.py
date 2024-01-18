from pathlib import Path

import pypdf


def pdf2text(path: Path) -> str:
    """Convert a PDF file to text."""

    with path.open("rb") as f:
        pdf = pypdf.PdfReader(f)
        return "\n".join(page.extract_text() for page in pdf.pages)
