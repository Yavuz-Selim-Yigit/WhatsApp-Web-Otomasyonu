"""
data_models.py — Tip güvenliği ve okunabilirlik için basit veri sınıfları.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    phone: str           # Ülke koduyla (örn. 905551112233)
    name: str = ""       # Kişi adı (kişiselleştirme için)
    message: str = ""    # Kişiye özel mesaj (boşsa template kullanılır)

@dataclass
class SendResult:
    phone: str
    name: str
    ok: bool
    error: Optional[str] = None
    final_message: Optional[str] = None  # Gerçekte gönderilen (placeholder dolmuş) mesaj
