
from pathlib import Path
import zipfile
import importlib.util

from collections import Counter
import fitz

ROOT = Path("selected_books")

stats = Counter()
report = []

def inspect_pdf(path):
    try:
        doc = fitz.open(path)
        pages = len(doc)
        text_pages = 0
        image_pages = 0
        total_chars = 0

        for page in doc:
            text = page.get_text("text").strip()
            images = page.get_images(full=True)

            if len(text) >= 30:
                text_pages += 1
                total_chars += len(text)

            if images:
                image_pages += 1

        if text_pages == 0:
            status = "OCR kerak bo'lishi mumkin"
        elif text_pages < pages:
            status = "Aralash: matnli va ehtimol skan sahifalar"
        else:
            status = "Asosan matnli"

        return {
            "pages": pages,
            "text_pages": text_pages,
            "image_pages": image_pages,
            "chars": total_chars,
            "status": status,
        }
    except Exception as e:
        return {"status": f"PDF xatosi: {e}"}

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    ext = path.suffix.lower()
    stats[ext or "[extensionsiz]"] += 1

    if ext == ".pdf":
        result = inspect_pdf(path)
        report.append({
            "file": str(path),
            "type": ext,
            **result,
        })

    elif ext in {".zip", ".rar"}:
        report.append({
            "file": str(path),
            "type": ext,
            "status": "Arxiv; ichidagi fayllar hali tekshirilmagan",
        })

    else:
        report.append({
            "file": str(path),
            "type": ext,
            "status": "Format bo'yicha keyingi bosqichda tekshiriladi",
        })

print("\n=== FORMATLAR BO'YICHA ===")
for ext, count in sorted(stats.items()):
    print(f"{ext}: {count}")

print("\n=== PDF HOLATI ===")
pdfs = [r for r in report if r["type"] == ".pdf"]

for item in pdfs:
    print(
        f'{item["status"]} | {item["file"]} | '
        f'sahifa={item.get("pages", "?")} | '
        f'matnli_sahifa={item.get("text_pages", "?")} | '
        f'belgi={item.get("chars", "?")}'
    )

print(f"\nJami fayl: {len(report)}")
print(f"PDF: {len(pdfs)}")

import json
Path("books_inventory.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("Hisobot saqlandi: books_inventory.json")
