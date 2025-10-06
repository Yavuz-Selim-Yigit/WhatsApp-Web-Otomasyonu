"""
utils.py — Küçük yardımcılar: telefon normalize, log ekleme, CSV okuma vb.
"""
import csv
import os
import time
import pandas as pd
from typing import List
from data_models import Contact
from config import SENT_LOG_PATH, FAILED_LOG_PATH

def normalize_phone(raw: str) -> str:
    """
    Telefon numarasından rakam dışı tüm karakterleri atar.
    '+90 530-123-4567' -> '905301234567'
    """
    return "".join(ch for ch in str(raw) if ch.isdigit())

def load_contacts(csv_path: str) -> List[Contact]:
    """
    CSV'yi okur ve Contact listesi döndürür.
    Beklenen kolonlar: phone, name, message (message opsiyonel)
    """
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df["phone"] = df["phone"].map(normalize_phone)
    contacts = [Contact(phone=row["phone"], name=row.get("name",""), message=row.get("message",""))
                for _, row in df.iterrows()]
    return contacts

def append_sent_log(result_row: dict) -> None:
    """
    Başarılı gönderimi CSV loguna ekler.
    result_row örn: {"timestamp": "...", "phone": "...", "name": "...", "message": "..."}
    """
    header_needed = not os.path.exists(SENT_LOG_PATH)
    with open(SENT_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow(list(result_row.keys()))
        w.writerow(list(result_row.values()))

def append_failed_log(result_row: dict) -> None:
    """
    Başarısız gönderimi CSV loguna ekler (hata incelemesi için).
    """
    header_needed = not os.path.exists(FAILED_LOG_PATH)
    with open(FAILED_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow(list(result_row.keys()))
        w.writerow(list(result_row.values()))

def now_str() -> str:
    """YYYY-mm-dd HH:MM:SS biçiminde zaman damgası üretir."""
    return time.strftime("%Y-%m-%d %H:%M:%S")
