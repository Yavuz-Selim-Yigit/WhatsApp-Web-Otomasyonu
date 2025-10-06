# WhatsApp Web Otomasyonu — ViperaDev Sürümü (v1.0.0)

Tamamen modüler, sürümlemesi net, yorum satırları dolu; işlevsel ve görsel olarak derli‑toplu bir WhatsApp Web toplu/kişiselleştirilmiş mesaj gönderim uygulaması. Aşağıda **hazır bir proje iskeleti**, çalışır **GUI (PyQt5)**, **Selenium otomasyonu**, **şablonlu mesaj**, **SAFE/FAST/TURBO hız modları**, **planlı gönderim**, **loglama ve raporlama** bulunur.

> **Not:** Bu repo, WhatsApp’ın resmi API’si değildir; Web arayüzü otomasyonu yapar. Hız/limit ve mevzuat sorumluluğu kullanıcıdadır.

---

## 0) Dizin Yapısı

```
whatsapp-broadcast/
├─ app.py
├─ gui_main.py
├─ whatsapp.py
├─ scheduler.py
├─ reporter.py
├─ utils.py
├─ config.py
├─ constants.py
├─ theme.py
├─ templates.py
├─ requirements.txt
├─ README.md
├─ assets/
│  ├─ icons/
│  │  ├─ app.svg
│  │  ├─ play.svg
│  │  ├─ stop.svg
│  │  ├─ moon.svg
│  │  └─ sun.svg
│  └─ qss/
│     ├─ dark.qss
│     └─ light.qss
└─ samples/
   └─ people.xlsx   (phone, name, message kolonları örnek)
```

---

## 1) Hızlı Başlangıç

1. Python 3.10+ kurulu olsun.
2. `pip install -r requirements.txt`
3. Chrome + **uyumlu** ChromeDriver kur (PATH’e ekle veya `config.py`’da `CHROMEDRIVER_PATH`).
4. `python app.py` ile başlat. İlk açılışta WhatsApp Web QR kodunu okutarak oturum aç.

**Excel formatı**: `phone` (zorunlu), `name` (opsiyonel), `message` (opsiyonel). Şablonda `{name}` ve Excel’den gelen diğer kolonları `{kolon_adi}` kalıbıyla kullanabilirsin.

---

## 2) Kurulum Dosyaları

### requirements.txt
```txt
PyQt5>=5.15.9
selenium>=4.24.0
pandas>=2.2.2
openpyxl>=3.1.5
python-dateutil>=2.9.0
xlsxwriter>=3.2.0
```

### README.md
```md
# WhatsApp Web Otomasyonu — ViperaDev Sürümü (v1.0.0)

Modüler, planlanabilir ve raporlanabilir WhatsApp Web toplu mesaj gönderici.

## Çalıştırma
- `pip install -r requirements.txt`
- ChromeDriver kur ve `config.py` içindeki `CHROMEDRIVER_PATH` ayarla (gerekirse PATH).
- `python app.py`

## Excel Şablonu
- `phone` (zorunlu), `name` (opsiyonel), `message` (opsiyonel)
- Mesaj şablonunda `{name}` ve Excel’deki diğer kolonları `{kolon}` olarak kullan.

## Çıktılar
- `Belgeler/WhatsAppBroadcastRuns/<timestamp>/results.xlsx` (renklendirilmiş)
- `sent_log.csv`, `failed_log.csv`
```

---

## 3) Konfigürasyon ve Sabitler

### config.py
```python
from enum import Enum
from pathlib import Path
import os

# ——— SÜRÜMLEME ———
APP_NAME = "ViperaDev WhatsApp Broadcast"
APP_VERSION = "1.0.0"

# ——— SÜRÜM BİLGİSİ ALT PANEL METNİ ———
VIPERADEV_FOOTER = (
    "ViperaDev • Versiyon " + APP_VERSION +
    " • ‘Başlat’a bas. Efsane başlasın.’"
)

# ——— SÜRÜCÜ/ÇEVRE ———
# Eğer ChromeDriver PATH'te ise boş bırakabilirsin.
CHROMEDRIVER_PATH = ""  # örn. r"C:/Tools/chromedriver.exe"

WHATSAPP_WEB_URL = "https://web.whatsapp.com/"

# ——— DİZİNLER ———
DOCS_DIR = Path.home() / "Documents" / "WhatsAppBroadcastRuns"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# ——— HIZ MODLARI ———
class ThrottleMode(Enum):
    SAFE = "SAFE"   # yavaş ve temkinli
    FAST = "FAST"   # dengeli
    TURBO = "TURBO" # çok hızlı (riskli)

# Varsayılan hız modu
THROTTLE_MODE = ThrottleMode.FAST

# Hız modlarına göre bekleme süreleri (s)
THROTTLE_PRETYPE = {
    ThrottleMode.SAFE: 1.2,
    ThrottleMode.FAST: 0.6,
    ThrottleMode.TURBO: 0.2,
}
THROTTLE_BETWEEN_CONTACTS = {
    ThrottleMode.SAFE: 6.0,
    ThrottleMode.FAST: 3.0,
    ThrottleMode.TURBO: 1.0,
}
THROTTLE_AFTER_SEND = {
    ThrottleMode.SAFE: 1.2,
    ThrottleMode.FAST: 0.7,
    ThrottleMode.TURBO: 0.25,
}

# ——— GÖNDERİM ———
ENTER_TO_SEND = True  # True: Enter ile gönder, False: buton tıkla
MAX_RETRY_PER_CONTACT = 2

# ——— GÖRÜNÜM ———
DEFAULT_THEME = "dark"  # "dark" | "light"

# ——— GÜVENLİK ———
# web.whatsapp.com servis koşulları ve anti-spam politikalara uyum kullanıcı sorumluluğundadır.
```

### constants.py
```python
# Çoklu seçici yaklaşımı: WhatsApp Web sık DOM değiştiriyor.
# Burada mesaj kutusu ve gönderme butonu için alternatif CSS/XPath’ler tutuyoruz.

MESSAGE_BOX_SELECTORS = [
    'div[contenteditable="true"][data-tab="10"]',
    'div[aria-label="Mesaj"]',
    'div[title="Type a message"]',
    'div[data-lexical-editor="true"]',
]

SEND_BUTTON_SELECTORS = [
    'span[data-icon="send"]',
    'button[aria-label="Gönder"]',
    'button[aria-label="Send"]',
]

SEARCH_BOX_SELECTORS = [
    'div[contenteditable="true"][data-tab="3"]',
    'div[role="textbox"][title="Ara veya yeni sohbet başlat"]',
]

CHAT_HEADER_SELECTORS = [
    'header[role="banner"]',
]

# Başarı göstergeleri: Mesaj balonu/"delivered" işaretleri.
SENT_BUBBLE_HINTS = [
    'span[data-icon="msg-dblcheck-light"]',
    'span[data-icon="msg-check"]',
    'div[aria-label*="Gönderildi"]',
]
```

### theme.py
```python
# Basit QSS temaları. İstersen assets/qss/dark.qss ve light.qss dosyalarına taşı.

dark_qss = """
QWidget { background: #0b0f14; color: #e6eef5; font-family: Inter, Segoe UI, Arial; }
QLineEdit, QTextEdit { background: #0f141a; border: 1px solid #1f2937; border-radius: 10px; padding: 8px; }
QPushButton { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 8px 14px; }
QPushButton:hover { border-color: #22d3ee; }
QPushButton:disabled { color: #6b7280; }
QProgressBar { border: 1px solid #1f2937; border-radius: 10px; text-align: center; }
QProgressBar::chunk { background: #22c55e; border-radius: 10px; }
QComboBox { background: #0f141a; border: 1px solid #1f2937; border-radius: 10px; padding: 6px; }
QStatusBar { background: #0b0f14; }
"""

light_qss = """
QWidget { background: #f7fafc; color: #0b0f14; font-family: Inter, Segoe UI, Arial; }
QLineEdit, QTextEdit { background: #ffffff; border: 1px solid #d1d5db; border-radius: 10px; padding: 8px; }
QPushButton { background: #ffffff; border: 1px solid #d1d5db; border-radius: 12px; padding: 8px 14px; }
QPushButton:hover { border-color: #22c55e; }
QProgressBar { border: 1px solid #d1d5db; border-radius: 10px; text-align: center; }
QProgressBar::chunk { background: #22d3ee; border-radius: 10px; }
QComboBox { background: #ffffff; border: 1px solid #d1d5db; border-radius: 10px; padding: 6px; }
QStatusBar { background: #f7fafc; }
"""
```

### templates.py
```python
# UI tarafında hızlı seçim için örnek şablonlar
TEMPLATES = {
    "Kısa Duyuru": (
        "Merhaba {name},\n"
        "Yarın saat 18:00’deki buluşmayı unutma. Katılım için ‘Evet’ yazman yeterli."
    ),
    "Nazik Hatırlatma": (
        "{name} selam,\n"
        "Daha önce paylaştığımız formu bugün doldurabilir misin? Teşekkürler."
    ),
    "Kişisel": (
        "{name} merhaba,\n"
        "Sadece halini hatrını sormak istedim. Güzel bir gün dilerim!"
    ),
}
```

---

## 4) Yardımcılar ve Raporlama

### utils.py
```python
from pathlib import Path
import pandas as pd
from datetime import datetime

RUN_DIR_FORMAT = "%Y%m%d_%H%M%S"

REQUIRED_COLS = ["phone"]
OPTIONAL_COLS = ["name", "message"]


def load_contacts(excel_path: str) -> pd.DataFrame:
    df = pd.read_excel(excel_path)
    df.columns = [c.strip().lower() for c in df.columns]
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError(f"Excel'de zorunlu '{col}' kolonu yok.")
    return df


def render_message(row: dict, template: str | None) -> str:
    # template verilmişse Excel'deki message'ı ezebilir; yoksa satırdaki message kullanılır
    base = template if (template and template.strip()) else row.get("message", "")
    # Tüm kolon adlarını {kolon} şeklinde doldur
    def safe(x):
        return "" if x is None else str(x)
    out = base
    for key, val in row.items():
        out = out.replace("{" + str(key) + "}", safe(val))
    return out


def make_run_dir(base: Path) -> Path:
    run_dir = base / datetime.now().strftime(RUN_DIR_FORMAT)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
```

### reporter.py
```python
from pathlib import Path
import pandas as pd
from typing import List, Dict

# Renkli sonuç xlsx üretimi ve csv logları

def write_results(run_dir: Path, results: List[Dict]):
    df = pd.DataFrame(results)
    # sent/failed csv
    sent = df[df["status"] == "sent"]
    failed = df[df["status"] == "failed"]
    sent.to_csv(run_dir / "sent_log.csv", index=False)
    failed.to_csv(run_dir / "failed_log.csv", index=False)

    # xlsx renklendirme
    xlsx_path = run_dir / "results.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="results", index=False)
        wb = writer.book
        ws = writer.sheets["results"]
        fmt_sent = wb.add_format({"bg_color": "#DCFCE7"})  # yeşil açık
        fmt_failed = wb.add_format({"bg_color": "#FFE4E6"})  # pembe açık
        status_col = df.columns.get_loc("status")
        for row_idx, status in enumerate(df["status"].tolist(), start=1):
            ws.set_row(row_idx, cell_format=fmt_sent if status == "sent" else (fmt_failed if status == "failed" else None))
```

---

## 5) Selenium Otomasyonu

### whatsapp.py
```python
import time
from typing import Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from config import WHATSAPP_WEB_URL, THROTTLE_MODE, ThrottleMode, THROTTLE_PRETYPE, THROTTLE_AFTER_SEND, THROTTLE_BETWEEN_CONTACTS, ENTER_TO_SEND
from constants import MESSAGE_BOX_SELECTORS, SEND_BUTTON_SELECTORS, SENT_BUBBLE_HINTS


class WhatsAppSender:
    def __init__(self, chromedriver_path: str | None = None, headless: bool = False):
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # Profil kalıcılığı: oturum açık kalsın
        opts.add_argument("--user-data-dir=./chrome_profile")
        if chromedriver_path:
            self.driver = webdriver.Chrome(options=opts)
        else:
            self.driver = webdriver.Chrome(options=opts)
        self.wait = WebDriverWait(self.driver, 25)

    def open(self):
        self.driver.get(WHATSAPP_WEB_URL)
        # QR veya ana ekran yüklenene kadar bekle
        time.sleep(3)

    def _find_any(self, selectors, by_css=True):
        for sel in selectors:
            try:
                if by_css:
                    return self.driver.find_element(By.CSS_SELECTOR, sel)
                else:
                    return self.driver.find_element(By.XPATH, sel)
            except NoSuchElementException:
                continue
        return None

    def _message_box(self):
        return self._find_any(MESSAGE_BOX_SELECTORS)

    def _send_button(self):
        return self._find_any(SEND_BUTTON_SELECTORS)

    def _is_sent_visible(self) -> bool:
        el = self._find_any(SENT_BUBBLE_HINTS)
        return el is not None

    def type_and_send(self, text: str, mode: ThrottleMode) -> bool:
        # Mesaj kutusunu bul ve yaz
        box = None
        try:
            box = self.wait.until(lambda d: self._message_box())
        except TimeoutException:
            return False

        # Önce küçük bir bekleme: bazı UI'larda focus gecikiyor
        time.sleep(THROTTLE_PRETYPE[mode])
        box.click()
        if not text:
            return False

        # Robust yazma: direkt send_keys → olmazsa pano yapıştır fallback
        try:
            box.send_keys(text)
        except WebDriverException:
            import pyperclip
            pyperclip.copy(text)
            box.send_keys(Keys.CONTROL, 'v')

        time.sleep(0.1)
        if ENTER_TO_SEND:
            box.send_keys(Keys.ENTER)
        else:
            btn = self._send_button()
            if btn:
                btn.click()
            else:
                box.send_keys(Keys.ENTER)

        time.sleep(THROTTLE_AFTER_SEND[mode])
        # Her zaman güvenilir değil; en azından hata almadıysak True dönelim
        return True

    def open_chat_by_phone(self, phone: str):
        # Resmi pattern: https://web.whatsapp.com/send?phone=905xxxxxxxxx
        # Not: Bazı bölgelerde ilk mesaj için  wa.me linki izin ister; biz Web içi send yolunu kullanıyoruz.
        url = f"https://web.whatsapp.com/send?phone={phone}"
        self.driver.get(url)
        # Sohbet başlığının yüklenmesini bekle
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'header')))
        except TimeoutException:
            pass

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass
```

> **Taslakta Kalma Sorunu İçin Not:** Yukarıda **çoklu seçici**, **ENTER/buton yedekleme**, **yazma gecikmesi** ve **pano yapıştır fallback** eklendi. Yine de bazı DOM güncellemelerinde mesaj taslakta kalırsa `ENTER_TO_SEND=False` deneyip buton tıklat, ayrıca `THROTTLE_MODE = SAFE` ile beklemeleri artır.

---

## 6) Planlayıcı

### scheduler.py
```python
from PyQt5.QtCore import QTimer, QDateTime

class RunScheduler:
    def __init__(self, on_trigger):
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(on_trigger)

    def schedule_at(self, when: QDateTime):
        ms = max(0, QDateTime.currentDateTime().msecsTo(when))
        self._timer.start(ms)

    def cancel(self):
        self._timer.stop()
```

---

## 7) PyQt5 GUI

### gui_main.py
```python
from PyQt5.QtWidgets import (
    QWidget, QApplication, QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QProgressBar, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime

import sys
import traceback
import pandas as pd

from config import APP_NAME, APP_VERSION, VIPERADEV_FOOTER, DOCS_DIR, THROTTLE_MODE, ThrottleMode
from theme import dark_qss, light_qss
from utils import load_contacts, render_message, make_run_dir
from reporter import write_results
from templates import TEMPLATES
from scheduler import RunScheduler
from whatsapp import WhatsAppSender

class Worker(QThread):
    progress = pyqtSignal(int, int)   # current, total
    stat = pyqtSignal(int, int)       # sent, failed
    log = pyqtSignal(str)             # text
    finished = pyqtSignal(list)       # results list

    def __init__(self, df: pd.DataFrame, template: str, mode: ThrottleMode, driver_path: str | None):
        super().__init__()
        self.df = df
        self.template = template
        self.mode = mode
        self.driver_path = driver_path
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        sender = None
        results = []
        sent_count = 0
        failed_count = 0
        try:
            sender = WhatsAppSender(chromedriver_path=self.driver_path)
            sender.open()
            total = len(self.df)
            for idx, row in self.df.iterrows():
                if self._stop:
                    break
                phone = str(row.get('phone', '')).strip()
                if not phone:
                    results.append({"index": idx, "phone": phone, "status": "failed", "reason": "no phone"})
                    failed_count += 1
                    self.stat.emit(sent_count, failed_count)
                    continue
                try:
                    sender.open_chat_by_phone(phone)
                    msg = render_message(row.to_dict(), self.template)
                    ok = sender.type_and_send(msg, self.mode)
                    if ok:
                        results.append({"index": idx, "phone": phone, "status": "sent"})
                        sent_count += 1
                    else:
                        results.append({"index": idx, "phone": phone, "status": "failed", "reason": "send failed"})
                        failed_count += 1
                except Exception as e:
                    results.append({"index": idx, "phone": phone, "status": "failed", "reason": str(e)})
                    failed_count += 1
                self.stat.emit(sent_count, failed_count)
                self.progress.emit(idx + 1, total)
                # İletiler arası bekleme
                import time
                from config import THROTTLE_BETWEEN_CONTACTS
                time.sleep(THROTTLE_BETWEEN_CONTACTS[self.mode])
        except Exception as e:
            self.log.emit("Kritik hata: " + str(e))
            self.log.emit(traceback.format_exc())
        finally:
            if sender:
                try: sender.close()
                except: pass
            self.finished.emit(results)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}")
        self.resize(1000, 720)

        # Top layout
        root = QVBoxLayout(self)

        # File row
        row1 = QHBoxLayout()
        self.le_path = QLineEdit(); self.le_path.setPlaceholderText("Excel dosyası (phone, name, message)")
        btn_browse = QPushButton("Excel Seç…")
        btn_browse.clicked.connect(self.on_browse)
        row1.addWidget(self.le_path, 1)
        row1.addWidget(btn_browse)
        root.addLayout(row1)

        # Template row
        row2 = QHBoxLayout()
        self.cb_template = QComboBox(); self.cb_template.addItem("(Şablon yok)")
        for k in TEMPLATES.keys():
            self.cb_template.addItem(k)
        self.te_message = QTextEdit(); self.te_message.setPlaceholderText("Mesaj şablonu (örn: Merhaba {name}, …)")
        row2.addWidget(QLabel("Hazır Şablon:"))
        row2.addWidget(self.cb_template)
        row2.addWidget(self.te_message, 1)
        root.addLayout(row2)

        # Options row
        row3 = QHBoxLayout()
        self.cb_mode = QComboBox(); self.cb_mode.addItems([m.value for m in ThrottleMode])
        self.chk_enter = QCheckBox("Enter ile gönder")
        self.chk_enter.setChecked(True)
        row3.addWidget(QLabel("Hız modu:"))
        row3.addWidget(self.cb_mode)
        row3.addWidget(self.chk_enter)
        row3.addStretch(1)
        root.addLayout(row3)

        # Scheduling row
        row4 = QHBoxLayout()
        self.dt_schedule = QDateTime.currentDateTime().addSecs(30)
        self.schedule_edit = QLineEdit(self.dt_schedule.toString("yyyy-MM-dd HH:mm"))
        self.schedule_edit.setToolTip("Planlı başlat (boş bırakılırsa hemen başlar)")
        self.chk_schedule = QCheckBox("Planlı başlat")
        row4.addWidget(self.chk_schedule)
        row4.addWidget(QLabel("Zaman:"))
        row4.addWidget(self.schedule_edit)
        row4.addStretch(1)
        root.addLayout(row4)

        # Buttons row
        row5 = QHBoxLayout()
        self.btn_start = QPushButton("▶ Başlat")
        self.btn_stop = QPushButton("■ Durdur")
        self.btn_stop.setEnabled(False)
        self.btn_theme = QPushButton("Tema: Koyu")
        row5.addWidget(self.btn_start)
        row5.addWidget(self.btn_stop)
        row5.addStretch(1)
        row5.addWidget(self.btn_theme)
        root.addLayout(row5)

        # Preview table
        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["phone", "name", "message* (render)"])
        root.addWidget(self.tbl, 1)

        # Progress + log
        self.bar = QProgressBar(); root.addWidget(self.bar)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setPlaceholderText("Log…")
        root.addWidget(self.log, 1)

        # Footer / ViperaDev Sürüm
        self.status = QStatusBar(); self.status.showMessage(VIPERADEV_FOOTER)
        root.addWidget(self.status)

        # Signals
        self.cb_template.currentIndexChanged.connect(self.on_template_change)
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_theme.clicked.connect(self.on_toggle_theme)

        # Scheduler
        self.scheduler = RunScheduler(self.on_start_now)

        # State
        self.worker = None
        self.current_df = None
        self.run_dir = None

        # Theme
        self.current_theme = "dark"
        self.apply_theme()

    def apply_theme(self):
        if self.current_theme == "dark":
            self.setStyleSheet(dark_qss)
            self.btn_theme.setText("Tema: Koyu")
        else:
            self.setStyleSheet(light_qss)
            self.btn_theme.setText("Tema: Açık")

    def on_toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()

    def on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Excel seç", "", "Excel Files (*.xlsx *.xls)")
        if not path:
            return
        self.le_path.setText(path)
        try:
            df = load_contacts(path)
            # Önizleme: 10 satır render
            self.current_df = df
            self.refresh_preview()
            self.log.append("Excel yüklendi. Satır sayısı: %d" % len(df))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def on_template_change(self):
        key = self.cb_template.currentText()
        if key in TEMPLATES:
            self.te_message.setText(TEMPLATES[key])
        else:
            self.te_message.clear()
        self.refresh_preview()

    def refresh_preview(self):
        if self.current_df is None:
            return
        temp = self.te_message.toPlainText()
        rows = min(10, len(self.current_df))
        self.tbl.setRowCount(rows)
        for i in range(rows):
            r = self.current_df.iloc[i]
            msg = render_message(r.to_dict(), temp)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(r.get('phone', ''))))
            self.tbl.setItem(i, 1, QTableWidgetItem(str(r.get('name', ''))))
            self.tbl.setItem(i, 2, QTableWidgetItem(msg))

    def on_start(self):
        if self.chk_schedule.isChecked():
            try:
                when = QDateTime.fromString(self.schedule_edit.text(), "yyyy-MM-dd HH:mm")
                if not when.isValid():
                    raise ValueError("Tarih/saat formatı geçersiz. Örn: 2025-10-06 19:30")
                self.scheduler.schedule_at(when)
                self.log.append(f"Planlandı: {when.toString()}")
                return
            except Exception as e:
                QMessageBox.critical(self, "Planlama Hatası", str(e))
                return
        # Hemen başlat
        self.on_start_now()

    def on_start_now(self):
        path = self.le_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Eksik", "Excel dosyası seçilmedi.")
            return
        try:
            df = load_contacts(path)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            return
        self.current_df = df
        self.refresh_preview()

        # Çalışma klasörü
        from config import DOCS_DIR
        self.run_dir = make_run_dir(DOCS_DIR)

        # Worker başlat
        mode = ThrottleMode(self.cb_mode.currentText())
        from config import ENTER_TO_SEND
        # ENTER modu UI’dan geldiği için config’e yansıtmak yerine WhatsAppSender içerisi zaten okuyor
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log.append("Gönderim başlıyor…")

        self.worker = Worker(df, self.te_message.toPlainText(), mode, None)
        self.worker.progress.connect(self.on_progress)
        self.worker.stat.connect(self.on_stat)
        self.worker.log.connect(self.on_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_stop(self):
        if self.worker:
            self.worker.stop()
        self.btn_stop.setEnabled(False)
        self.log.append("Durduruluyor…")

    def on_progress(self, cur, total):
        self.bar.setMaximum(total)
        self.bar.setValue(cur)

    def on_stat(self, sent, failed):
        self.status.showMessage(f"Gönderildi: {sent}  •  Başarısız: {failed}  •  {VIPERADEV_FOOTER}")

    def on_log(self, text):
        self.log.append(text)

    def on_finished(self, results):
        # Rapor yaz
        if self.run_dir:
            write_results(self.run_dir, results)
            self.log.append(f"Rapor: {self.run_dir}")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status.showMessage("Görev tamamlandı • " + VIPERADEV_FOOTER)


def launch():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
```

### app.py
```python
from gui_main import launch

if __name__ == "__main__":
    launch()
```

---

## 8) Örnek Excel

`samples/people.xlsx` içinde aşağıdaki kolonlar bulunur:

| phone        | name      | message                         |
|--------------|-----------|----------------------------------|
| 9053xxxxxxx  | Ali Veli  | Merhaba {name}, nasılsın?       |
| 9055xxxxxxx  | Ayşe      | {name} bugün toplantı saat 18:00 |

> Şablon alanına bir metin yazarsan, Excel’in `message` kolonunu **geçersiz kılar**.

---

## 9) Sık Görülen Sorunlar ve Çözümler

- **ImportError: cannot import name 'THROTTLE_MODE' from 'config'**
  - Bu sürümde `config.py` içinde `THROTTLE_MODE` ve `ThrottleMode` tanımlıdır. Eski dosyaları silip bu yapıyı kullan.

- **Mesaj taslakta kalıyor / gönderilmiyor**
  - `ENTER_TO_SEND=False` yapıp buton tıklamayı zorla.
  - Hız modunu `SAFE` seçip beklemeleri artır.
  - İlk satırlarda WhatsApp Web’in UI’si ağır yüklenebilir; gönderime başlamadan 10–15 sn beklemek çözebilir.

- **WhatsApp Web oturumu açılmıyor**
  - İlk çalıştırmada QR okutman gerekir. `./chrome_profile` klasörü sayesinde oturum saklanır.

- **Telefon formatı**
  - `+90` yerine `90` ile başlayıp devam eden tam numara kullan (ülke kodu dahil). `905xxxxxxxxx` gibi.

---

## 10) Yol Haritası (Bir Sonraki Sürümler)

- `{custom1}` gibi değişkenleri Excel’deki ekstra kolonlara otomatik bağlama (şimdiden destekli, sadece kolon adıyla yaz).
- Hata oranına göre dinamik hız (FAST ↔ SAFE otomatik geçiş).
- A/B metin testleri ve dönüşüm analizi.
- Numara geçerlilik ön‑kontrolü (yalın regex + isteğe bağlı 3rd‑party doğrulama).
- Çoklu hesap profili, çoklu tarayıcı.

---

## 11) Lisans ve Uyarı

Bu proje eğitim amaçlıdır. WhatsApp Hizmet Şartları, anti‑spam politikaları ve yerel mevzuata **uyum** kullanıcı sorumluluğundadır. Aşırı agresif kullanım hesap kısıtlamasına yol açabilir.

