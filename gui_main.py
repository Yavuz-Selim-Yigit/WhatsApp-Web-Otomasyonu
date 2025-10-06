"""
gui_main.py — PyQt5 ana ekran.
- Kaynak Excel/CSV'ye dokunma.
- İş bitince Belgeler/... klasörünü oluştur, results.xlsx'i yaz.
- sent_log.csv ve failed_log.csv'yi aynı klasöre kopyala.
- 'Klasörü Aç' butonu: bitince aktif olur ve klasörü açar.
- Filtre: 'Sadece Status'u boş olanları gönder'
- Planlı başlatma: checkbox + tarih/saat seçici
- İptal butonu (güvenli durdurma)
"""
import os, shutil, sys, subprocess, time
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from typing import List
from data_models import Contact
from utils import load_contacts, now_str
from whatsapp import WhatsAppSender
from results_store import ResultAggregator
from utils_paths import make_run_output_dir
from config import OUTPUT_ROOT_DIRNAME, OUTPUT_XLSX_NAME, SENT_LOG_PATH, FAILED_LOG_PATH

ASSETS_LOGO_PATH = os.path.join("assets", "logo.png")

def open_folder(path: str):
    """İşletim sistemine uygun biçimde klasörü açar."""
    if not path:
        return
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

class SenderWorker(QtCore.QThread):
    """
    Gönderimi ayrı iş parçacığında çalıştırır.
    Bitişte çıktı klasörünü üretir ve yolunu 'finished' sinyali ile gönderir.
    """
    progress = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)   # out_dir path

    def __init__(self, contacts: List[Contact], start_at: datetime = None, parent=None):
        super().__init__(parent)
        self.contacts = contacts
        self._agg = ResultAggregator()
        self._stop = False
        self._start_at = start_at  # planlı başlatma zamanı (opsiyonel)

    def request_stop(self):
        """Dışarıdan iptal isteği set edilir."""
        self._stop = True

    def _should_stop(self) -> bool:
        return self._stop

    def _wait_until_start(self):
        """Planlı başlatma zamanı gelene kadar bekler; iptal edilirse çıkar."""
        if not self._start_at:
            return
        self.progress.emit(f"Planlı başlatma: {self._start_at.strftime('%Y-%m-%d %H:%M:%S')} bekleniyor…")
        while True:
            if self._stop:
                self.progress.emit("Planlı beklemede iken iptal edildi.")
                return
            now = datetime.now()
            if now >= self._start_at:
                self.progress.emit("Planlı zaman geldi, başlıyoruz.")
                return
            time.sleep(0.5)

    def run(self):
        sender = WhatsAppSender()
        out_dir = ""
        try:
            # Planlı başlatma beklemesi
            self._wait_until_start()
            if self._stop:
                self.finished.emit("")  # iptal
                return

            sender.setup_driver()
            self.progress.emit("Tarayıcı açıldı. WhatsApp Web yükleniyor…")
            sender.wait_ready(timeout=60)
            self.progress.emit("WhatsApp hazır. Gönderimler başlıyor…")

            def cb(msg: str):
                self.progress.emit(msg)

            # Asıl gönderim (iptal destekli)
            results = sender.broadcast(self.contacts, on_progress=cb, should_stop=self._should_stop)

            # RAM'e topla
            for r in results:
                self._agg.add(
                    phone=r.phone,
                    name=r.name,
                    status="Sent" if r.ok else "Failed",
                    timestamp=now_str(),
                    final_message=r.final_message or "",
                    error=(r.error or "")
                )

            # Belgeler altında çıktı klasörünü oluştur
            out_dir = make_run_output_dir(OUTPUT_ROOT_DIRNAME)
            out_xlsx = os.path.join(out_dir, OUTPUT_XLSX_NAME)

            # Tek seferde Excel yaz
            self._agg.export_excel(out_xlsx)
            self.progress.emit(f"Excel oluşturuldu: {out_xlsx}")

            # CSV loglarını da arşive kopyala (varsa)
            try:
                if os.path.exists(SENT_LOG_PATH):
                    shutil.copy2(SENT_LOG_PATH, os.path.join(out_dir, os.path.basename(SENT_LOG_PATH)))
                if os.path.exists(FAILED_LOG_PATH):
                    shutil.copy2(FAILED_LOG_PATH, os.path.join(out_dir, os.path.basename(FAILED_LOG_PATH)))
                self.progress.emit("CSV loglar arşiv klasörüne kopyalandı.")
            except Exception as e:
                self.progress.emit(f"CSV kopyalama uyarısı: {e}")

        except Exception as e:
            self.progress.emit(f"FATAL: {e}")
        finally:
            try:
                sender.close()
            except Exception:
                pass
            self.finished.emit(out_dir)

class MainWindow(QtWidgets.QWidget):
    """
    Ana GUI:
    - Logo
    - Dosya seçimi (.csv / .xlsx)
    - Başlat / İptal
    - Log alanı
    - Klasörü Aç (iş bitince aktif)
    - Filtre: 'Sadece Status'u boş olanları gönder'
    - Planlı başlatma: checkbox + tarih/saat seçici
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Broadcast")
        self.setMinimumSize(820, 620)
        self._worker = None
        self._last_out_dir = ""

        # Logo
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self._load_logo()

        # Dosya seçim satırı
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("contacts.csv veya contacts.xlsx")
        self.btn_browse = QtWidgets.QPushButton("Dosya Seç (.csv / .xlsx)")

        # Filtre: sadece Status'u boş olanlar
        self.chk_only_empty_status = QtWidgets.QCheckBox("Sadece Status'u boş olanları gönder")

        # Planlı başlatma
        self.chk_schedule = QtWidgets.QCheckBox("Planlı başlat")
        self.datetime_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setEnabled(False)  # checkbox işaretlenince açılacak
        self.chk_schedule.toggled.connect(lambda checked: self.datetime_edit.setEnabled(checked))

        # Başlat / İptal / Klasörü Aç
        self.btn_start = QtWidgets.QPushButton("Gönderimi Başlat")
        self.btn_cancel = QtWidgets.QPushButton("İptal")
        self.btn_cancel.setEnabled(False)
        self.btn_open_folder = QtWidgets.QPushButton("Klasörü Aç")
        self.btn_open_folder.setEnabled(False)

        # Üst kontrol düzeni
        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.path_edit, 1)
        file_layout.addWidget(self.btn_browse)

        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addWidget(self.chk_only_empty_status)
        options_layout.addWidget(self.chk_schedule)
        options_layout.addWidget(self.datetime_edit)

        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.addWidget(self.btn_start)
        actions_layout.addWidget(self.btn_cancel)
        actions_layout.addWidget(self.btn_open_folder)

        # Log alanı
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("font-family: Consolas, monospace;")

        # Ana yerleşim
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.logo_label)
        layout.addLayout(file_layout)
        layout.addLayout(options_layout)
        layout.addLayout(actions_layout)
        layout.addWidget(self.log_edit, 1)

        # Sinyaller
        self.btn_browse.clicked.connect(self._choose_file)
        self.btn_start.clicked.connect(self._start_send)
        self.btn_cancel.clicked.connect(self._cancel_send)
        self.btn_open_folder.clicked.connect(self._open_last_folder)

    def _load_logo(self):
        if os.path.exists(ASSETS_LOGO_PATH):
            pix = QtGui.QPixmap(ASSETS_LOGO_PATH)
            if not pix.isNull():
                scaled = pix.scaledToHeight(120, QtCore.Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled)
                return
        self.logo_label.setText("WhatsApp Broadcast")
        self.logo_label.setStyleSheet("font-size: 22px; font-weight: 600;")

    def _choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Kişi listesi seç",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.path_edit.setText(path)

    @staticmethod
    def _filter_only_empty_status(contacts: List[Contact]) -> List[Contact]:
        """
        Eğer girişte 'status' kolonu varsa:
            - status boş olanları AL,
            - 'Sent' (büyük/küçük harf fark etmeksizin) olanları AT.
            - diğer tüm durumları (failed/pending) AL (yeniden dene).
        Kolon yoksa: tüm kayıtlar 'boş' kabul edilir ve ALINIR.
        """
        filtered = []
        for c in contacts:
            s = (c.input_status or "").strip().lower()
            if c.input_status is None:
                filtered.append(c)  # status kolonu yok → hepsi gönderilebilir
            else:
                if s == "" or s == " ":
                    filtered.append(c)
                elif s != "sent":
                    filtered.append(c)
                # s == 'sent' → atla
        return filtered

    def _start_send(self):
        path = self.path_edit.text().strip() or "contacts.csv"
        if not os.path.exists(path):
            self._log(f"HATA: Dosya bulunamadı → {path}")
            return
        try:
            contacts = load_contacts(path)
            if not contacts:
                self._log("Uyarı: Liste boş.")
                return
        except Exception as e:
            self._log(f"Dosya okuma hatası: {e}")
            return

        # Filtre aktifse uygula
        if self.chk_only_empty_status.isChecked():
            before = len(contacts)
            contacts = self._filter_only_empty_status(contacts)
            self._log(f"Filtre uygulandı: {before} kayıttan {len(contacts)} kayıt kaldı.")
        if not contacts:
            self._log("Gönderilecek kayıt kalmadı.")
            return

        # Planlı başlatma zamanı
        start_at = None
        if self.chk_schedule.isChecked():
            qdt = self.datetime_edit.dateTime()
            start_at = qdt.toPyDateTime()
            if start_at <= datetime.now():
                self._log("Planlı başlatma zamanı geçmiş. Lütfen ileri bir zaman seçin.")
                return

        # UI durumu
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_open_folder.setEnabled(False)
        self._last_out_dir = ""
        self._log(f"{len(contacts)} kişi yüklendi. Gönderim başlıyor…")

        # Worker
        self._worker = SenderWorker(contacts, start_at=start_at)
        self._worker.progress.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _cancel_send(self):
        if self._worker:
            self._log("İptal talebi gönderildi. Güvenli durdurma bekleniyor…")
            self._worker.request_stop()

    def _log(self, text: str):
        self.log_edit.appendPlainText(text)
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    def _on_finished(self, out_dir_path: str):
        if out_dir_path:
            self._last_out_dir = out_dir_path
            self._log(f"Görev tamamlandı. Çıktı klasörü: {out_dir_path}")
            self.btn_open_folder.setEnabled(True)
        else:
            self._log("Görev tamamlandı.")
            self.btn_open_folder.setEnabled(False)
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)

    def _open_last_folder(self):
        if self._last_out_dir and os.path.isdir(self._last_out_dir):
            open_folder(self._last_out_dir)
        else:
            self._log("Açılacak klasör bulunamadı.")
