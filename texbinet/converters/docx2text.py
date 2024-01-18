from pathlib import Path
from typing import List

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph


def docx2text(path: Path) -> str:
    """Convert a DOCX file to text."""

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
