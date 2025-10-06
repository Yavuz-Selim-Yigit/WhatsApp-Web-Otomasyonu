# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
PyQt5 GUI:
- SADECE Excel (.xlsx/.xls)
- Mesajı UI'dan yaz, istersen Excel 'message'larını override et
- Kart tasarım, progress bar, istatistik rozetleri
- Açık/Koyu tema anahtarı
- Planlı başlatma + İptal
- İş bitiminde klasör açma
"""
import os, shutil, sys, subprocess, time
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from typing import List
from data_models import Contact, SendResult
from utils import load_contacts, now_str
from whatsapp import WhatsAppSender
from results_store import ResultAggregator
from utils_paths import make_run_output_dir
from config import OUTPUT_ROOT_DIRNAME, OUTPUT_XLSX_NAME, SENT_LOG_PATH, FAILED_LOG_PATH
from styles import apply_theme, nice_icon

ASSETS_LOGO_PATH = os.path.join("assets", "logo.png")
ASSETS_APP_ICON  = os.path.join("assets", "app_icon.png")  # opsiyonel

def open_folder(path: str):
    if not path: return
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

class SenderWorker(QtCore.QThread):
    """Arka planda gönderimi yürüten iş parçacığı."""
    progress = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)        # out_dir path
    tick = QtCore.pyqtSignal(object)         # SendResult

    def __init__(self, contacts: List[Contact], start_at: datetime = None, override_message: str = "", parent=None):
        super().__init__(parent)
        self.contacts = contacts
        self._agg = ResultAggregator()
        self._stop = False
        self._start_at = start_at
        self._override_message = (override_message or "").strip()

    def request_stop(self): self._stop = True
    def _should_stop(self) -> bool: return self._stop

    def _wait_until_start(self):
        if not self._start_at: return
        self.progress.emit(f"Planlı başlatma: {self._start_at.strftime('%Y-%m-%d %H:%M:%S')} bekleniyor…")
        while True:
            if self._stop:
                self.progress.emit("Planlı beklemede iken iptal edildi.")
                return
            if datetime.now() >= self._start_at:
                self.progress.emit("Planlı zaman geldi, başlıyoruz.")
                return
            time.sleep(0.5)

    def run(self):
        sender = WhatsAppSender()
        out_dir = ""
        try:
            self._wait_until_start()
            if self._stop:
                self.finished.emit("")
                return

            sender.setup_driver()
            self.progress.emit("Tarayıcı açıldı. WhatsApp Web yükleniyor…")
            sender.wait_ready(timeout=60)
            self.progress.emit("WhatsApp hazır. Gönderimler başlıyor…")

            def cb_log(msg: str): self.progress.emit(msg)
            def cb_result(res: SendResult): self.tick.emit(res)

            results = sender.broadcast(
                self.contacts, on_progress=cb_log,
                should_stop=self._should_stop, on_result=cb_result,
                override_message=self._override_message
            )

            for r in results:
                self._agg.add(
                    phone=r.phone, name=r.name,
                    status="Sent" if r.ok else "Failed",
                    timestamp=now_str(),
                    final_message=r.final_message or "",
                    error=(r.error or "")
                )

            out_dir = make_run_output_dir(OUTPUT_ROOT_DIRNAME)
            out_xlsx = os.path.join(out_dir, OUTPUT_XLSX_NAME)
            self._agg.export_excel(out_xlsx)
            self.progress.emit(f"Excel oluşturuldu: {out_xlsx}")

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
            try: sender.close()
            except Exception: pass
            self.finished.emit(out_dir)

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        if os.path.exists(ASSETS_APP_ICON):
            self.setWindowIcon(nice_icon(ASSETS_APP_ICON))
        self.setWindowTitle("WhatsApp Broadcast — ViperaDev")
        self.setMinimumSize(980, 720)
        self._worker = None
        self._last_out_dir = ""
        self._dark = True

        # Üst başlık kartı
        self.header_card = QtWidgets.QFrame(objectName="Card")
        self.header_logo  = QtWidgets.QLabel()
        self.header_title = QtWidgets.QLabel("WhatsApp Broadcast", objectName="Title")
        self.theme_toggle = QtWidgets.QPushButton("Tema: Koyu/Açık", objectName="Secondary")
        self.theme_toggle.clicked.connect(self._toggle_theme)
        self._load_logo()
        hbox = QtWidgets.QHBoxLayout(self.header_card); hbox.setContentsMargins(16,16,16,16)
        left = QtWidgets.QHBoxLayout(); left.setSpacing(12); left.addWidget(self.header_logo); left.addWidget(self.header_title)
        hbox.addLayout(left, 1); hbox.addWidget(self.theme_toggle)

        # Girdi kartı (Excel seçimi + filtre + planlama)
        self.input_card = QtWidgets.QFrame(objectName="Card")
        self.path_edit = QtWidgets.QLineEdit(); self.path_edit.setPlaceholderText("contacts.xlsx veya contacts.xls")
        self.btn_browse = QtWidgets.QPushButton("Excel Seç"); self.btn_browse.setObjectName("Secondary")
        self.chk_only_empty_status = QtWidgets.QCheckBox("Sadece Status'u boş / 'Sent' olmayanları gönder")
        self.chk_schedule = QtWidgets.QCheckBox("Planlı başlat")
        self.datetime_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss"); self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setEnabled(False)
        self.chk_schedule.toggled.connect(lambda c: self.datetime_edit.setEnabled(c))
        grid = QtWidgets.QGridLayout(self.input_card); grid.setContentsMargins(16,16,16,16)
        grid.addWidget(QtWidgets.QLabel("Excel Dosyası:"), 0, 0); grid.addWidget(self.path_edit, 0, 1); grid.addWidget(self.btn_browse, 0, 2)
        grid.addWidget(self.chk_only_empty_status, 1, 0, 1, 3)
        grid.addWidget(self.chk_schedule, 2, 0); grid.addWidget(self.datetime_edit, 2, 1, 1, 2)

        # Mesaj kartı (UI’dan mesaj yazma)
        self.msg_card = QtWidgets.QFrame(objectName="Card")
        self.txt_message = QtWidgets.QPlainTextEdit()
        self.txt_message.setPlaceholderText("Mesaj şablonunu yaz (ör. \"Merhaba {name}! Toplantımız 19:00'da.\")")
        self.chk_use_ui_message = QtWidgets.QCheckBox("Bu mesajı kullan (Excel'deki 'message' değerlerini geçersiz kıl)")
        lay_msg = QtWidgets.QVBoxLayout(self.msg_card); lay_msg.setContentsMargins(16,16,16,16)
        lay_msg.addWidget(QtWidgets.QLabel("Mesaj (UI):"))
        lay_msg.addWidget(self.txt_message)
        lay_msg.addWidget(self.chk_use_ui_message)

        # Kontrol/istatistik kartı
        self.control_card = QtWidgets.QFrame(objectName="Card")
        self.btn_start = QtWidgets.QPushButton("Gönderimi Başlat")
        self.btn_cancel = QtWidgets.QPushButton("İptal"); self.btn_cancel.setObjectName("Secondary"); self.btn_cancel.setEnabled(False)
        self.btn_open_folder = QtWidgets.QPushButton("Klasörü Aç"); self.btn_open_folder.setObjectName("Secondary"); self.btn_open_folder.setEnabled(False)
        self.progress = QtWidgets.QProgressBar(); self.progress.setValue(0)
        self.badge_total = QtWidgets.QLabel("Toplam: 0", objectName="Badge")
        self.badge_ok    = QtWidgets.QLabel("Başarılı: 0", objectName="BadgeOk")
        self.badge_fail  = QtWidgets.QLabel("Hatalı: 0", objectName="BadgeFail")
        ctr = QtWidgets.QGridLayout(self.control_card); ctr.setContentsMargins(16,16,16,16)
        ctr.addWidget(self.btn_start, 0, 0); ctr.addWidget(self.btn_cancel, 0, 1); ctr.addWidget(self.btn_open_folder, 0, 2)
        ctr.addWidget(self.progress, 1, 0, 1, 3)
        badges = QtWidgets.QHBoxLayout(); badges.addWidget(self.badge_total); badges.addWidget(self.badge_ok); badges.addWidget(self.badge_fail); badges.addStretch(1)
        ctr.addLayout(badges, 2, 0, 1, 3)

        # Log kartı
        self.log_card = QtWidgets.QFrame(objectName="Card")
        self.log_edit = QtWidgets.QPlainTextEdit(); self.log_edit.setReadOnly(True)
        lay_log = QtWidgets.QVBoxLayout(self.log_card); lay_log.setContentsMargins(12,12,12,12)
        lay_log.addWidget(QtWidgets.QLabel("Günlük (Log):", objectName="BadgeInfo"))
        lay_log.addWidget(self.log_edit)

        # Ana yerleşim
        root = QtWidgets.QVBoxLayout(self); root.setContentsMargins(16,16,16,16); root.setSpacing(12)
        root.addWidget(self.header_card); root.addWidget(self.input_card); root.addWidget(self.msg_card)
        root.addWidget(self.control_card); root.addWidget(self.log_card, 1)

        # Sinyaller
        self.btn_browse.clicked.connect(self._choose_file)
        self.btn_start.clicked.connect(self._start_send)
        self.btn_cancel.clicked.connect(self._cancel_send)
        self.btn_open_folder.clicked.connect(self._open_last_folder)

        apply_theme(QtWidgets.QApplication.instance(), True)

    # --- Tema/Logo
    def _toggle_theme(self):
        self._dark = not self._dark
        apply_theme(QtWidgets.QApplication.instance(), self._dark)

    def _load_logo(self):
        pix = QtGui.QPixmap(ASSETS_LOGO_PATH)
        self.header_logo.setPixmap(pix.scaledToHeight(36, QtCore.Qt.SmoothTransformation) if not pix.isNull() else QtGui.QPixmap())

    # --- Yardımcılar
    def _log(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_edit.appendPlainText(f"[{ts}] {text}")
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    def _choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Excel dosyası seç", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if path:
            self.path_edit.setText(path)

    @staticmethod
    def _filter_only_empty_status(contacts: List[Contact]) -> List[Contact]:
        filtered = []
        for c in contacts:
            s = (c.input_status or "").strip().lower()
            if c.input_status is None:
                filtered.append(c)  # status yoksa tamamı gönderilebilir
            else:
                if s == "" or s == " ":
                    filtered.append(c)
                elif s != "sent":
                    filtered.append(c)
        return filtered

    def _reset_stats(self, total: int):
        self.progress.setMaximum(max(1, total))
        self.progress.setValue(0)
        self.badge_total.setText(f"Toplam: {total}")
        self.badge_ok.setText("Başarılı: 0")
        self.badge_fail.setText("Hatalı: 0")

    def _on_tick(self, res: SendResult):
        val = self.progress.value() + 1
        self.progress.setValue(val)
        # rozetleri güncelle
        ok = int(self.badge_ok.text().split(":")[-1]) + (1 if res.ok else 0)
        fail = int(self.badge_fail.text().split(":")[-1]) + (0 if res.ok else 1)
        self.badge_ok.setText(f"Başarılı: {ok}")
        self.badge_fail.setText(f"Hatalı: {fail}")

    # --- Başlat / İptal / Bitir
    def _start_send(self):
        path = self.path_edit.text().strip()
        if not path:
            self._log("HATA: Excel dosyası seçilmedi.")
            return
        if not os.path.exists(path):
            self._log(f"HATA: Dosya bulunamadı → {path}")
            return
        try:
            contacts = load_contacts(path)
        except Exception as e:
            self._log(f"Excel okuma hatası: {e}")
            return
        if not contacts:
            self._log("Uyarı: Liste boş.")
            return

        # Filtre
        if self.chk_only_empty_status.isChecked():
            before = len(contacts)
            contacts = self._filter_only_empty_status(contacts)
            self._log(f"Filtre uygulandı: {before} → {len(contacts)}")
        if not contacts:
            self._log("Gönderilecek kayıt kalmadı.")
            return

        # UI mesaj override
        override_message = ""
        if self.chk_use_ui_message.isChecked():
            override_message = (self.txt_message.toPlainText() or "").strip()
            if not override_message:
                self._log("HATA: 'Bu mesajı kullan' seçili ama mesaj boş.")
                return

        # Planlı başlatma
        start_at = None
        if self.chk_schedule.isChecked():
            qdt = self.datetime_edit.dateTime()
            start_at = qdt.toPyDateTime()
            if start_at <= datetime.now():
                self._log("Planlı başlatma zamanı geçmiş. İleri bir zaman seç.")
                return

        # UI state
        self._reset_stats(len(contacts))
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_open_folder.setEnabled(False)
        self._last_out_dir = ""
        self._log(f"{len(contacts)} kişi yüklendi. Gönderim başlıyor…")

        # Worker
        self._worker = SenderWorker(contacts, start_at=start_at, override_message=override_message)
        self._worker.progress.connect(self._log)
        self._worker.tick.connect(self._on_tick)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _cancel_send(self):
        if self._worker:
            self._log("İptal talebi gönderildi. Güvenli durdurma bekleniyor…")
            self._worker.request_stop()

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
