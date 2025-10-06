"""
gui_main.py — PyQt5 ana ekran.
Özellikler:
- Üstte logo (assets/logo.png)
- CSV seç butonu
- Gönderimi başlat/durdur
- Canlı durum log penceresi
- Arka planda iş (QThread) -> UI donmaz
"""
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from typing import List
from data_models import Contact
from utils import load_contacts
from whatsapp import WhatsAppSender

ASSETS_LOGO_PATH = os.path.join("assets", "logo.png")

class SenderWorker(QtCore.QThread):
    """
    Gönderimi ayrı iş parçacığında çalıştırır.
    Sinyallerle GUI'ye log basar ve tamamlandığında haber verir.
    """
    progress = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, contacts: List[Contact], parent=None):
        super().__init__(parent)
        self.contacts = contacts
        self._stop = False

    def run(self):
        sender = WhatsAppSender()
        try:
            sender.setup_driver()                 # Chrome'u başlat
            self.progress.emit("Tarayıcı açıldı. WhatsApp Web yükleniyor…")
            sender.wait_ready(timeout=60)         # QR gerekiyorsa okut; profil kaydı ile 1 kez
            self.progress.emit("WhatsApp hazır. Gönderimler başlıyor…")

            def cb(msg: str):
                self.progress.emit(msg)           # Her adımda GUI'ye yaz

            sender.broadcast(self.contacts, on_progress=cb)
        except Exception as e:
            self.progress.emit(f"FATAL: {e}")
        finally:
            try:
                sender.close()
            except Exception:
                pass
            self.finished.emit()

class MainWindow(QtWidgets.QWidget):
    """
    Ana GUI: Logo + kontroller + log alanı.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Broadcast")
        self.setMinimumSize(720, 520)
        self._worker = None

        # --- ÜST: Logo ---
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self._load_logo()

        # --- Orta: Kontroller ---
        self.csv_path_edit = QtWidgets.QLineEdit()
        self.csv_path_edit.setPlaceholderText("contacts.csv")
        self.btn_browse = QtWidgets.QPushButton("CSV Seç")
        self.btn_start = QtWidgets.QPushButton("Gönderimi Başlat")
        self.btn_start.setEnabled(True)

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.addWidget(self.csv_path_edit, 1)
        controls_layout.addWidget(self.btn_browse)
        controls_layout.addWidget(self.btn_start)

        # --- Alt: Log alanı ---
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("font-family: Consolas, monospace;")

        # --- Ana yerleşim ---
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.logo_label)
        layout.addLayout(controls_layout)
        layout.addWidget(self.log_edit, 1)

        # --- Sinyaller ---
        self.btn_browse.clicked.connect(self._choose_csv)
        self.btn_start.clicked.connect(self._start_send)

    def _load_logo(self):
        """
        assets/logo.png dosyasını yükler, yoksa uyarı metni gösterir.
        Pixmap'i pencere genişliğine göre orantılı ölçekler.
        """
        if os.path.exists(ASSETS_LOGO_PATH):
            pix = QtGui.QPixmap(ASSETS_LOGO_PATH)
            if not pix.isNull():
                scaled = pix.scaledToHeight(120, QtCore.Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled)
                return
        # Logo yoksa basit yazı
        self.logo_label.setText("WhatsApp Broadcast")
        self.logo_label.setStyleSheet("font-size: 22px; font-weight: 600;")

    def _choose_csv(self):
        """Dosya seçici ile CSV yolu seçtirir."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "contacts.csv seç", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.csv_path_edit.setText(path)

    def _start_send(self):
        """CSV'yi yükler ve gönderim iş parçacığını başlatır."""
        path = self.csv_path_edit.text().strip() or "contacts.csv"
        if not os.path.exists(path):
            self._log(f"HATA: CSV bulunamadı → {path}")
            return
        try:
            contacts = load_contacts(path)
            if not contacts:
                self._log("Uyarı: CSV boş.")
                return
        except Exception as e:
            self._log(f"CSV okuma hatası: {e}")
            return

        self.btn_start.setEnabled(False)
        self._log(f"{len(contacts)} kişi yüklendi. Gönderim başlıyor…")
        self._worker = SenderWorker(contacts)
        self._worker.progress.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _log(self, text: str):
        """Log alanına satır ekler ve en alta kaydırır."""
        self.log_edit.appendPlainText(text)
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    def _on_finished(self):
        """İş bittiğinde butonları aç ve kullanıcıya bildir."""
        self._log("Gönderim tamamlandı. Tarayıcı kapatıldı.")
        self.btn_start.setEnabled(True)
