from pathlib import Path
import shutil
import subprocess


def extract_djvu_pages(file_path: str | Path) -> list[dict]:
    """
    DJVU matnini ajratadi.
    Hozircha butun hujjat bitta mantiqiy bo'lak sifatida qaytadi;
    asl sahifa chegaralari keyingi bosqichda qo'shiladi.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"DJVU topilmadi: {path}")

    executable = shutil.which("djvutxt")
    if not executable:
        raise RuntimeError(
            "djvutxt topilmadi. Docker image ichiga djvulibre-bin "
            "paketini o'rnatish kerak."
        )

    result = subprocess.run(
        [executable, str(path)],
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )

    text = result.stdout.strip()
    if not text:
        return []

    return [{"page_number": 1, "text": text}]