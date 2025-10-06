"""
whatsapp.py — Selenium tabanlı WhatsApp gönderim motoru.
Tek iş: WhatsApp Web'e bağlan, mesaj gönder, kapan.
GUI ya da CLI burayı çağırır; motor kendi içinde modular ve test edilebilir.
"""
import time
import random
import urllib.parse
from typing import Iterable, List, Tuple

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
    MIN_DELAY_SEC, MAX_DELAY_SEC, MAX_RETRIES, TEMPLATE_MESSAGE
)
from utils import append_failed_log, append_sent_log, now_str

class WhatsAppSender:
    """Selenium sürücüsünü yönetir ve numaralara mesaj yollar."""
    def __init__(self):
        self.driver = None

    def setup_driver(self) -> None:
        """Chrome'u profil klasörü ile ayağa kaldırır; QR tek seferlik olur."""
        opts = Options()
        opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")   # profil saklama
        opts.add_argument(f"--profile-directory={PROFILE_DIR}") # profil adı
        opts.add_argument("--no-sandbox")                       # container/CI için
        opts.add_argument("--disable-dev-shm-usage")            # bellek sınırlı ortamlarda
        # Headless *önerilmez* (WA Web tespit edebiliyor)
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )
        self.driver.maximize_window()

    def wait_ready(self, timeout: int = 60) -> None:
        """WhatsApp Web arayüzünün yüklenmesini bekler (QR sonrası)."""
        self.driver.get(WA_WEB_HOME)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox'], canvas"))
            )
        except Exception:
            # Zorunlu değil: bazı makinelerde geç yüklenir; küçük bekleme bırak.
            time.sleep(5)

    def _send_to_one(self, phone: str, message: str, retries: int = 0) -> Tuple[bool, str]:
        """
        Tek numaraya mesaj yollar. Başarılı mı? Hata varsa metni döner.
        """
        encoded = urllib.parse.quote(message)
        self.driver.get(WA_WEB_SEND.format(phone=phone, text=encoded))
        try:
            # 'Gönder' butonu tıklanabilir olana kadar bekle
            send_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-icon="send"]'))
            )
            # Bazı sistemlerde .click() yerine JS ile tıklamak daha stabil
            self.driver.execute_script("arguments[0].click();", send_btn)
            time.sleep(1.2)  # ağ/mobil gecikmeleri için mini bekleme
            return True, ""
        except Exception as e:
            if retries < MAX_RETRIES:
                time.sleep(3)
                return self._send_to_one(phone, message, retries + 1)
            return False, str(e)

    def broadcast(self, contacts: Iterable[Contact], on_progress=None) -> List[SendResult]:
        """
        Bir Contact listesine sırayla mesaj yollar.
        on_progress: GUI'ye canlı bilgi aktarmak için callback (str alır).
        """
        results: List[SendResult] = []
        for idx, c in enumerate(contacts, 1):
            # Mesaj seçimi: kişi özel mesaj yoksa şablon + {name} yer tutucu
            msg = (c.message or TEMPLATE_MESSAGE).replace("{name}", c.name or "")
            if on_progress:
                on_progress(f"[{idx}] Gönderiliyor → {c.phone} ({c.name})")

            ok, err = self._send_to_one(c.phone, msg)
            ts = now_str()
            result = SendResult(phone=c.phone, name=c.name, ok=ok, error=err or None, final_message=msg)
            results.append(result)

            if ok:
                append_sent_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg})
                if on_progress:
                    on_progress(f"✔ Başarılı: {c.phone}")
            else:
                append_failed_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg, "error": err})
                if on_progress:
                    on_progress(f"✖ Hata: {c.phone} -> {err}")

            # Rastgele bekleme: spam benzeri paterni kırar
            wait = random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC)
            if on_progress:
                on_progress(f"{wait:.1f}s bekleniyor…")
            time.sleep(wait)

        return results

    def close(self) -> None:
        """Tarayıcıyı kapatır (kaynakları serbest bırak)."""
        if self.driver:
            self.driver.quit()
            self.driver = None
