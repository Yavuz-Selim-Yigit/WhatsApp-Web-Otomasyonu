"""
utils.py — Telefon normalize, dosya okuma (CSV/XLSX), CSV log, zaman damgası.
Çalışma sırasında kaynak Excel'e DOKUNMAZ.
"""
import csv, os, time
from typing import List
import pandas as pd
from data_models import Contact
from config import SENT_LOG_PATH, FAILED_LOG_PATH

def normalize_phone(raw: str) -> str:
    """
    Rakam dışındaki her şeyi atar.
    '+90 530-123-4567' -> '905301234567'
    """
    return "".join(ch for ch in str(raw) if ch.isdigit())

def _contacts_from_dataframe(df: pd.DataFrame, source_path: str,
                             sheet_name: str = None, excel_row_offset: int = 2) -> List[Contact]:
    """
    DataFrame'den Contact listesi türetir.
    Beklenen başlıklar: phone, name, message (case-insensitive tolerans).
    Opsiyonel başlık: status
    """
    cols = {c.lower(): c for c in df.columns}
    def pick(col): return cols.get(col, None)
    phone_col   = pick("phone")
    name_col    = pick("name")
    message_col = pick("message")
    status_col  = pick("status")  # opsiyonel
    if not phone_col:
        raise ValueError("'phone' kolonu bulunamadı.")

    contacts: List[Contact] = []
    for i, row in df.iterrows():
        phone = normalize_phone(row.get(phone_col, ""))
        if not phone:
            continue
        name = str(row.get(name_col, "") or "")
        message = str(row.get(message_col, "") or "")
        input_status = str(row.get(status_col, "") or "") if status_col else None
        row_index = i + excel_row_offset  # 1-based excel satırı (header 1)
        contacts.append(Contact(
            phone=phone, name=name, message=message,
            row_index=row_index, sheet_name=sheet_name, source_path=source_path,
            input_status=input_status
        ))
    return contacts

def load_contacts(path: str) -> List[Contact]:
    """
    Yol uzantısına göre CSV veya Excel okur.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        xls = pd.ExcelFile(path, engine="openpyxl")
        sheet = xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet, dtype=str).fillna("")
        return _contacts_from_dataframe(df, source_path=path, sheet_name=sheet, excel_row_offset=2)
    elif ext == ".csv":
        df = pd.read_csv(path, dtype=str).fillna("")
        return _contacts_from_dataframe(df, source_path=path, sheet_name=None, excel_row_offset=2)
    else:
        raise ValueError("Desteklenmeyen dosya türü. .csv veya .xlsx kullanın.")

def append_sent_log(row: dict) -> None:
    """
    Anlık başarılı gönderimleri CSV loguna ekler (görev bitse de bitmese de iz kalır).
    """
    header = not os.path.exists(SENT_LOG_PATH)
    with open(SENT_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header: w.writerow(list(row.keys()))
        w.writerow(list(row.values()))

def append_failed_log(row: dict) -> None:
    """
    Anlık hatalı gönderimleri CSV loguna ekler.
    """
    header = not os.path.exists(FAILED_LOG_PATH)
    with open(FAILED_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header: w.writerow(list(row.keys()))
        w.writerow(list(row.values()))

def now_str() -> str:
    """YYYY-mm-dd HH:MM:SS biçiminde zaman damgası üretir."""
    return time.strftime("%Y-%m-%d %H:%M:%S")
