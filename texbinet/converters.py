from pathlib import Path


def pdf2text(path: Path) -> str:
    """Convert a PDF file to text."""
    import pypdf

    with path.open("rb") as f:
        pdf = pypdf.PdfReader(f)
        return "\n".join(page.extract_text() for page in pdf.pages)


def image2text(path: Path) -> str:
    """Convert an image file to text."""

    import easyocr

    reader = easyocr.Reader(["en", "ja"])
    texts = reader.readtext(str(path))

    text = "\n".join([text for _, text, accuracy in texts if accuracy > 0.5])

    return text


def pptx2text(path: Path) -> str:
    """Convert a PPTX file to text."""

    import pptx
    from typing import List

    def extract_table_text(table) -> List[str]:
        """Extract text from table shape in PPTX."""
        texts = []
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = "".join(
                    run.text
                    for paragraph in cell.text_frame.paragraphs
                    for run in paragraph.runs
                )
                row_text.append(cell_text.replace("\n", ""))
            texts.append(", ".join(row_text))
        return texts

    prs = pptx.Presentation(path)

    texts = []

    for i, slide in enumerate(prs.slides, start=1):
        texts.append(f"--- Page {i} ---")

        for shape in slide.shapes:
            if shape.has_text_frame:
                texts.append(shape.text.replace("\n", ""))

            if shape.has_table:
                texts.extend(extract_table_text(shape.table))

    return "\n".join(texts)


def docx2text(path: Path) -> str:
    """Convert a DOCX file to text."""
    import docx
    from typing import List
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    def extract_table_text(table) -> List[str]:
        """Extract text from table in DOCX."""
        texts = []
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = "".join(paragraph.text for paragraph in cell.paragraphs)
                row_text.append(cell_text.replace("\n", ""))
            texts.append(", ".join(row_text))
        return texts

    doc = docx.Document(path)
    texts = []

    for element in doc.element.body:
        if element.tag.endswith("p"):
            paragraph = Paragraph(element, None)
            texts.append(paragraph.text)
        elif element.tag.endswith("tbl"):
            table = Table(element, None)
            texts.extend(extract_table_text(table))

    return "\n".join(texts)
