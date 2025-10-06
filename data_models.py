# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
Veri sınıfları (okunabilirlik ve tip güvenliği için dataclass kullanımı)
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    phone: str
    name: str = ""
    message: str = ""
    # Referans amaçlı metadata (raporlama)
    row_index: Optional[int] = None
    sheet_name: Optional[str] = None
    source_path: Optional[str] = None
    # İsteğe bağlı giriş status (filtre için)
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
