# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
Belgeler klasörünün platform bağımsız bulunması ve
tarihli çıktı klasörünün oluşturulması.
"""
from pathlib import Path
from datetime import datetime

def get_documents_dir() -> str:
    home = Path.home()
    for p in [home / "Documents", home / "Belgeler", home / "My Documents"]:
        if p.exists() and p.is_dir():
            return str(p)
    return str(home)

def make_run_output_dir(root_name: str) -> str:
    """
    Belgeler/<root_name>/<YYYY-MM-DD_HHMMSS> oluştur ve geri döndür.
    """
    docs = Path(get_documents_dir())
    out = docs / root_name / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    return str(out)
