# -*- coding: utf-8 -*-
"""
analyze_books.py
================
selected_books papkasidagi fayllarni tahlil qiladi:
- PDF: matnli yoki rasmli (skanerlangan)
- ZIP/RAR: ichidagi fayllar ro'yxati
- DJVU, DOCX, HTML, RTF, TXT: mavjudligi

Docker orqali ishga tushirish (C:\library-ai-studio\library-ai-studio da):
    docker run --rm -v "${PWD}/selected_books:/data" -v "${PWD}:/scripts" -w /scripts python:3.11-slim sh -c "pip install --quiet pymupdf python-docx beautifulsoup4 striprtf rarfile && python analyze_books.py"

Yoki oddiyroq (packages allaqachon o'rnatilgan bo'lsa):
    docker run --rm -v "${PWD}/selected_books:/data" -v "${PWD}:/scripts" -w /scripts python:3.11-slim python analyze_books.py
"""

import os
import sys
import csv
import json
import zipfile
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ============================================================
# SOZLAMALAR
# ============================================================
SOURCE_DIR = "/data"
OUTPUT_DIR = "/data/reports"

# ============================================================
# LOGGER
# ============================================================
def setup_logger():
    log_dir = Path(OUTPUT_DIR)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        log_dir = Path("/tmp")

    log_file = log_dir / f"analyze_{datetime.now():%Y%m%d_%H%M%S}.log"

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[console, file_handler],
    )
    return log_file


# ============================================================
# PDF TAHLIL
# ============================================================
def analyze_pdf(filepath):
    """PDF faylni tahlil qiladi: matnli yoki rasmli, nechta sahifa."""
    result = {
        "type": "pdf",
        "pages": 0,
        "has_text": False,
        "text_ratio": 0.0,
        "is_scanned": False,
        "size_mb": 0.0,
        "error": None,
    }
    try:
        import fitz  # PyMuPDF
        result["size_mb"] = round(os.path.getsize(filepath) / (1024 * 1024), 2)

        doc = fitz.open(filepath)
        result["pages"] = len(doc)

        if len(doc) == 0:
            doc.close()
            return result

        # Birinchi 5 sahifani tekshiramiz (yoki hammasini, agar 5 dan kam bo'lsa)
        check_pages = min(5, len(doc))
        pages_with_text = 0
        total_text_len = 0

        for i in range(check_pages):
            page = doc[i]
            text = page.get_text().strip()
            if len(text) > 50:  # 50 belgidan ko'p bo'lsa matnli
                pages_with_text += 1
            total_text_len += len(text)

        doc.close()

        result["text_ratio"] = round(pages_with_text / check_pages, 2)
        result["has_text"] = pages_with_text > 0
        result["is_scanned"] = pages_with_text == 0

        return result

    except ImportError:
        result["error"] = "PyMuPDF (fitz) o'rnatilmagan"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# ============================================================
# ZIP TAHLIL
# ============================================================
def analyze_zip(filepath):
    """ZIP faylni tahlil qiladi: ichidagi fayllar ro'yxati."""
    result = {
        "type": "zip",
        "files_inside": [],
        "inner_types": {},
        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
        "error": None,
    }
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            inner_ext = defaultdict(int)
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                result["files_inside"].append(name)
                ext = Path(name).suffix.lower()
                inner_ext[ext] += 1
            result["inner_types"] = dict(inner_ext)
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# ============================================================
# RAR TAHLIL
# ============================================================
def analyze_rar(filepath):
    """RAR faylni tahlil qiladi."""
    result = {
        "type": "rar",
        "files_inside": [],
        "inner_types": {},
        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
        "error": None,
    }
    try:
        import rarfile
        with rarfile.RarFile(filepath, "r") as rf:
            inner_ext = defaultdict(int)
            for name in rf.namelist():
                if name.endswith("/"):
                    continue
                result["files_inside"].append(name)
                ext = Path(name).suffix.lower()
                inner_ext[ext] += 1
            result["inner_types"] = dict(inner_ext)
        return result
    except ImportError:
        result["error"] = "rarfile o'rnatilmagan"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# ============================================================
# BOSHQA FORMATLAR
# ============================================================
def analyze_other(filepath):
    ext = Path(filepath).suffix.lower()
    result = {
        "type": ext.lstrip("."),
        "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
        "error": None,
    }

    try:
        if ext == ".docx":
            import docx
            d = docx.Document(filepath)
            result["pages"] = len(d.paragraphs)
            result["has_text"] = len(d.paragraphs) > 0

        elif ext == ".html" or ext == ".htm":
            from bs4 import BeautifulSoup
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                text = soup.get_text()
            result["has_text"] = len(text.strip()) > 50
            result["text_length"] = len(text)

        elif ext == ".rtf":
            from striprtf.striprtf import rtf_to_text
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = rtf_to_text(f.read())
            result["has_text"] = len(text.strip()) > 50
            result["text_length"] = len(text)

        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            result["has_text"] = len(text.strip()) > 50
            result["text_length"] = len(text)

        elif ext == ".djvu":
            result["has_text"] = None  # keyin tekshiramiz
            result["note"] = "djvutxt kerak"

    except ImportError as e:
        result["error"] = f"Kutubxona yo'q: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result


# ============================================================
# ASOSIY TAHLIL
# ============================================================
def analyze_file(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return analyze_pdf(filepath)
    elif ext == ".zip":
        return analyze_zip(filepath)
    elif ext == ".rar":
        return analyze_rar(filepath)
    else:
        return analyze_other(filepath)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE_DIR)
    parser.add_argument("--output", default=OUTPUT_DIR)
    args = parser.parse_args()

    log_file = setup_logger()

    logging.info("=" * 60)
    logging.info("  TAHLIL BOSHLANDI")
    logging.info("=" * 60)
    logging.info(f"  Manba  : {args.source}")
    logging.info(f"  Hisobot: {args.output}")

    source = Path(args.source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    if not source.is_dir():
        logging.error(f"❌ Manba papka topilmadi: {source}")
        return 2

    # Barcha fayllarni yig'ish (rekursiv)
    all_files = [f for f in source.rglob("*") if f.is_file() and f.name != ".gitkeep"]
    logging.info(f"Jami fayllar: {len(all_files)}")

    # Statistika
    stats = defaultdict(lambda: {"total": 0, "errors": 0, "details": []})
    results = []

    for i, filepath in enumerate(all_files, 1):
        rel = filepath.relative_to(source)
        ext = filepath.suffix.lower() or "(yo'q)"

        info = analyze_file(str(filepath))
        info["filename"] = str(rel)
        info["ext"] = ext
        info["size_mb"] = info.get("size_mb", round(filepath.stat().st_size / (1024 * 1024), 2))
        results.append(info)

        stats[ext]["total"] += 1
        if info.get("error"):
            stats[ext]["errors"] += 1

        # Konsolga qisqa
        status = "✅"
        if info.get("error"):
            status = "❌"
        elif ext == ".pdf":
            if info.get("is_scanned"):
                status = "🖼️ (rasm)"
            elif info.get("has_text"):
                status = "📝 (matn)"
        elif ext in (".zip", ".rar"):
            inner = info.get("inner_types", {})
            inner_str = ", ".join(f"{k}:{v}" for k, v in inner.items())
            status = f"📦 [{inner_str}]"

        logging.info(f"[{i}/{len(all_files)}] {status} {rel} ({info['size_mb']} MB)")
        if info.get("error"):
            logging.warning(f"    ⚠️  {info['error']}")

    # ============================================================
    # HISOBOT
    # ============================================================
    print("\n" + "=" * 60)
    print("  UMUMIY STATISTIKA")
    print("=" * 60)

    by_type = defaultdict(int)
    pdf_text = 0
    pdf_scanned = 0
    pdf_error = 0

    for r in results:
        ext = r["ext"]
        by_type[ext] += 1
        if ext == ".pdf":
            if r.get("error"):
                pdf_error += 1
            elif r.get("is_scanned"):
                pdf_scanned += 1
            elif r.get("has_text"):
                pdf_text += 1

    for ext, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {ext:10s} : {count:4d} ta")

    print("\n  --- PDF TAHLILI ---")
    print(f"  Matnli (o'qish mumkin) : {pdf_text}")
    print(f"  Rasmli (OCR kerak)     : {pdf_scanned}")
    print(f"  Xato                   : {pdf_error}")

    # ZIP/RAR ichidagi fayllar
    print("\n  --- ARXIVLAR ICHIDAGI FAYLLAR ---")
    inner_all = defaultdict(int)
    for r in results:
        if r["type"] in ("zip", "rar"):
            for k, v in r.get("inner_types", {}).items():
                inner_all[k] += v
    for ext, count in sorted(inner_all.items(), key=lambda x: -x[1]):
        print(f"  {ext:10s} : {count:4d} ta")

    # Xatolar
    errors = [r for r in results if r.get("error")]
    if errors:
        print(f"\n  --- XATOLAR ({len(errors)} ta) ---")
        for r in errors[:20]:
            print(f"    • {r['filename']}: {r['error']}")

    # ============================================================
    # FAYLLARGA YOZISH
    # ============================================================
    # JSON
    json_file = output / "analyze_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # CSV
    csv_file = output / "analyze_report.csv"
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "ext", "size_mb", "type", "pages",
                         "has_text", "is_scanned", "text_ratio",
                         "inner_types", "error"])
        for r in results:
            writer.writerow([
                r.get("filename", ""),
                r.get("ext", ""),
                r.get("size_mb", ""),
                r.get("type", ""),
                r.get("pages", ""),
                r.get("has_text", ""),
                r.get("is_scanned", ""),
                r.get("text_ratio", ""),
                json.dumps(r.get("inner_types", {}), ensure_ascii=False),
                r.get("error", "") or "",
            ])

    # Matnli PDF'lar ro'yxati
    text_pdfs = [r["filename"] for r in results
                 if r["ext"] == ".pdf" and r.get("has_text") and not r.get("is_scanned")]
    with open(output / "pdf_text.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(text_pdfs))

    # Rasmli PDF'lar ro'yxati
    scanned_pdfs = [r["filename"] for r in results
                    if r["ext"] == ".pdf" and r.get("is_scanned")]
    with open(output / "pdf_scanned.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(scanned_pdfs))

    print(f"\n  Hisobotlar saqlandi:")
    print(f"    • {json_file}")
    print(f"    • {csv_file}")
    print(f"    • {output / 'pdf_text.txt'} ({len(text_pdfs)} ta)")
    print(f"    • {output / 'pdf_scanned.txt'} ({len(scanned_pdfs)} ta)")
    print(f"    • Log: {log_file}")
    print("=" * 60 + "\n")

    logging.info("✅ TAHLIL TUGADI")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(f"❌ Kutilmagan xato: {e}")
        logging.error(traceback.format_exc())
        sys.exit(4)