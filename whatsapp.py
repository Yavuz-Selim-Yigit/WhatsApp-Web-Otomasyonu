# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
Selenium motoru:
- Retry yok; tek deneme
- should_stop() ile iptal
- override_message varsa Excel mesajlarının yerine geçer
"""
import time, random, urllib.parse
from typing import Iterable, List, Tuple, Callable, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from data_models import Contact, SendResult
from config import (
    USER_DATA_DIR, PROFILE_DIR, WA_WEB_HOME, WA_WEB_SEND,
    MIN_DELAY_SEC, MAX_DELAY_SEC, TEMPLATE_MESSAGE
)
from utils import append_failed_log, append_sent_log, now_str

class WhatsAppSender:
    def __init__(self):
        self.driver = None

    def setup_driver(self) -> None:
        """Chrome'u profil klasörü ile aç; QR tek seferlik olur."""
        opts = Options()
        opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        opts.add_argument(f"--profile-directory={PROFILE_DIR}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )
        self.driver.maximize_window()

    def wait_ready(self, timeout: int = 60) -> None:
        """WhatsApp Web yüklenene kadar bekle."""
        self.driver.get(WA_WEB_HOME)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox'], canvas"))
            )
        except Exception:
            time.sleep(5)

    def _send_to_one(self, phone: str, message: str) -> Tuple[bool, str]:
        """Tek numaraya mesaj gönder, hata varsa yakala."""
        encoded = urllib.parse.quote(message)
        self.driver.get(WA_WEB_SEND.format(phone=phone, text=encoded))
        try:
            btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-icon="send"]'))
            )
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.2)
            return True, ""
        except Exception as e:
            return False, str(e)

    def broadcast(
        self,
        contacts: Iterable[Contact],
        on_progress: Optional[Callable[[str], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        on_result: Optional[Callable[[SendResult], None]] = None,
        override_message: Optional[str] = None,
    ) -> List[SendResult]:
        """Listeyi sırayla gönder ve sonuçları üret."""
        results: List[SendResult] = []
        for idx, c in enumerate(contacts, 1):
            if should_stop and should_stop():
                if on_progress: on_progress("İptal istendi, gönderim sonlandırılıyor…")
                break

            # Mesaj seçim önceliği: UI > Excel > TEMPLATE
            base_msg = (override_message if (override_message and override_message.strip())
                        else (c.message or TEMPLATE_MESSAGE))
            msg = base_msg.replace("{name}", c.name or "")

            if on_progress:
                on_progress(f"[{idx}] Gönderiliyor → {c.phone} ({c.name})")

            ok, err = self._send_to_one(c.phone, msg)
            ts = now_str()
            result = SendResult(
                phone=c.phone, name=c.name, ok=ok, error=err or None,
                final_message=msg, row_index=c.row_index, sheet_name=c.sheet_name, source_path=c.source_path
            )
            results.append(result)
            if on_result: on_result(result)

            if ok:
                append_sent_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg})
                if on_progress: on_progress(f"✔ Başarılı: {c.phone}")
            else:
                append_failed_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg, "error": err})
                if on_progress: on_progress(f"✖ Hata: {c.phone} -> {err}")

            # bekleme sırasında iptal kontrolü
            wait_total = random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC)
            waited, step = 0.0, 0.5
            while waited < wait_total:
                if should_stop and should_stop():
                    if on_progress: on_progress("İptal istendi, bekleme kesiliyor…")
                    break
                time.sleep(step); waited += step
            if on_progress and waited < wait_total:
                on_progress("Bekleme iptal edildi.")
        return results

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None
