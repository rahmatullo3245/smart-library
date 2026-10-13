
from pathlib import Path

import fitz


def extract_pdf_pages(file_path: str | Path) -> list[dict]:
    """
    PDF sahifalarini alohida chiqaradi.
    Sahifa raqami PDF ichidagi 1 dan boshlanadigan tartibda saqlanadi.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF topilmadi: {path}")

    pages = []

    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            if text:
                pages.append({
                    "page_number": page_index + 1,
                    "text": text,
                })

    return pages
