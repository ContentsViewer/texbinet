from pathlib import Path

import openpyxl


def xlsx2text(path: Path) -> str:
    """Convert a XLSX file to text."""

    wb = openpyxl.load_workbook(path)

    texts = []

    for sheet in wb.worksheets:
        texts.append(f"--- Sheet {sheet.title} ---")

        for row in sheet.rows:
            row_text = []
            for cell in row:
                row_text.append(str("" if cell.value is None else cell.value))
            texts.append(", ".join(row_text))

    return "\n".join(texts)
