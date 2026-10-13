
from contextlib import contextmanager
from pathlib import Path
import tempfile
import zipfile

import rarfile


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".rtf", ".djvu", ".epub", ".html", ".htm", ".txt"
}

MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


@contextmanager
def extract_archive_files(archive_path: str | Path):
    """
    Arxiv ichidan tanlangan hujjatlarni xavfsiz vaqtinchalik katalogga
    chiqaradi. Natijadagi Path obyektlaridan faqat with bloki ichida
    foydalanish kerak.
    """
    path = Path(archive_path)

    if not path.is_file():
        raise FileNotFoundError(f"Arxiv topilmadi: {path}")

    suffix = path.suffix.lower()

    if suffix not in {".zip", ".rar"}:
        raise ValueError(f"Qo'llab-quvvatlanmaydigan arxiv: {suffix}")

    with tempfile.TemporaryDirectory(prefix="library_ai_") as temp_dir:
        target_dir = Path(temp_dir)
        extracted: list[Path] = []
        total_bytes = 0

        def save_member(member_stream, member_name: str, size: int):
            nonlocal total_bytes

            ext = Path(member_name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                return

            if size > MAX_FILE_BYTES:
                raise ValueError(
                    f"Arxivdagi fayl hajmi limitdan katta: {member_name}"
                )

            if total_bytes + size > MAX_TOTAL_BYTES:
                raise ValueError("Arxivning jami chiqarish hajmi limitdan oshdi.")

            # Asl arxiv yo'lidan foydalanmaymiz: path traversal oldi olinadi.
            output_path = target_dir / f"document_{len(extracted)}{ext}"
            written = 0

            with output_path.open("wb") as output:
                while True:
                    chunk = member_stream.read(1024 * 1024)
                    if not chunk:
                        break

                    written += len(chunk)
                    if written > MAX_FILE_BYTES:
                        raise ValueError(
                            f"Chiqarilayotgan fayl hajmi limitdan oshdi: "
                            f"{member_name}"
                        )

                    output.write(chunk)

            total_bytes += written
            extracted.append(output_path)

        if suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue

                    if Path(member.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                        continue

                    if member.file_size > MAX_FILE_BYTES:
                        raise ValueError(
                            f"ZIP ichidagi fayl juda katta: {member.filename}"
                        )

                    with archive.open(member) as stream:
                        save_member(stream, member.filename, member.file_size)

        else:
            with rarfile.RarFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue

                    if Path(member.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                        continue

                    if member.file_size > MAX_FILE_BYTES:
                        raise ValueError(
                            f"RAR ichidagi fayl juda katta: {member.filename}"
                        )

                    with archive.open(member) as stream:
                        save_member(stream, member.filename, member.file_size)

        yield extracted
