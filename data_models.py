"""
data_models.py — Basit veri sınıfları (okunabilirlik ve tip güvenliği).
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    phone: str
    name: str = ""
    message: str = ""
    # Giriş dosyasındaki satır/sayfa bilgileri (raporlama/izleme için)
    row_index: Optional[int] = None
    sheet_name: Optional[str] = None
    source_path: Optional[str] = None
    # Girişten gelen mevcut durum (varsa). Filtrelemede kullanırız.
    input_status: Optional[str] = None

@dataclass
class SendResult:
    phone: str
    name: str
    ok: bool
    error: Optional[str] = None
    final_message: Optional[str] = None
    row_index: Optional[int] = None
    sheet_name: Optional[str] = None
    source_path: Optional[str] = None
