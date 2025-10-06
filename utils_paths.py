"""
utils_paths.py — Belgeler (Documents) klasörünü platformdan bağımsız bul.
Windows TR'de "Belgeler" görünse de dosya yolu genelde 'Documents' olur.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def get_documents_dir() -> str:
    """
    Kullanıcının belgeler klasörünü tahmin eder.
    Bulamazsa ev dizinine (HOME) döner.
    """
    home = Path.home()
    candidates = [
        home / "Documents",
        home / "Belgeler",      # bazı TR sistemlerde gerçekten böyle
        home / "My Documents",  # eski Windows
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return str(p)
    return str(home)

def make_run_output_dir(root_name: str) -> str:
    """
    Belgeler/<root_name>/<YYYY-MM-DD_HHMMSS> klasörünü oluşturur ve yolunu döner.
    """
    docs = Path(get_documents_dir())
    root = docs / root_name
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = root / ts
    out.mkdir(parents=True, exist_ok=True)
    return str(out)
