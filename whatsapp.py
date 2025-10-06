# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
whatsapp.py
-----------
Selenium tabanlı WhatsApp gönderim motoru.

Özellikler:
- Retry YOK (tek deneme felsefesi)
- GUI'den iptal desteği (should_stop callback)
- UI mesaj önceliği (override_message): Arayüzden yazılan mesaj Excel'dekini geçersiz kılar
- WhatsApp Web UI değişikliklerine daha dayanıklı çoklu-seçici ve ENTER yedeği
- Sohbet hazır kontrolü + contenteditable'a native input event ile yazma

Kullanım:
    sender = WhatsAppSender()
    sender.setup_driver()
    sender.wait_ready()
    results = sender.broadcast(contacts, on_progress=..., should_stop=..., on_result=..., override_message=...)
    sender.close()

Not: Headless önerilmez. WhatsApp Web tarafı headless'ı tespit edebilir.
"""

import time
import random
import urllib.parse
from typing import Iterable, List, Tuple, Callable, Optional

# Selenium importları
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Proje içi importlar
from data_models import Contact, SendResult
from config import (
    USER_DATA_DIR, PROFILE_DIR,
    WA_WEB_HOME, WA_WEB_SEND,
    MIN_DELAY_SEC, MAX_DELAY_SEC,
    TEMPLATE_MESSAGE
)
from utils import append_failed_log, append_sent_log, now_str


class WhatsAppSender:
    """
    WhatsApp Web otomasyon sınıfı.
    - Chrome'u kalıcı profil ile açarak QR'ı her seferinde okutma zorunluluğunu kaldırır.
    - Tek tek numaralara mesaj yollar.
    """
    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None

    # --------------------------------------------------------------------- #
    # Sürücü yaşam döngüsü
    # --------------------------------------------------------------------- #
    def setup_driver(self) -> None:
        """
        Chrome sürücüsünü kalıcı profil klasörü ile ayağa kaldır.
        """
        opts = Options()
        # Kalıcı kullanıcı verisi: QR oturumu tutabilmek için
        opts.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        opts.add_argument(f"--profile-directory={PROFILE_DIR}")
        # CI/VM uyumluluğu
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # Headless önermiyoruz; WhatsApp Web davranışları değişken.
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts
        )
        self.driver.maximize_window()

    def wait_ready(self, timeout: int = 60) -> None:
        """
        WhatsApp Web ana sayfası yüklenene kadar bekle.
        QR akışı yaşanabilir; kullanıcı giriş yapmazsa timeout eder.
        """
        assert self.driver is not None, "Driver setup yapılmamış."
        self.driver.get(WA_WEB_HOME)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    # Ya sohbet ekranındaki textbox ya da QR-Canvas görünsün
                    'div[contenteditable="true"][role="textbox"], canvas'
                ))
            )
        except TimeoutException:
            # Bazı makinelerde ilk yüklenme yavaş olabilir; küçük ek bekleme
            time.sleep(5)

    def close(self) -> None:
        """Tarayıcıyı kapat ve kaynakları serbest bırak."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    # --------------------------------------------------------------------- #
    # Yardımcılar (UI dayanıklılığı için)
    # --------------------------------------------------------------------- #
    def _find_any(self, selectors: List[str], timeout: float = 15.0):
        """
        Birden çok CSS seçici dener; ilk bulunan ve görünür öğeyi döndürür.
        WA Web sık güncellendiği için tek seçiciye güvenmeyiz.
        """
        assert self.driver is not None
        end = time.time() + timeout
        last_err: Optional[Exception] = None
        while time.time() < end:
            for sel in selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el.is_displayed():
                        return el
                except Exception as e:
                    last_err = e
            time.sleep(0.2)
        if last_err:
            raise last_err
        raise NoSuchElementException("Bulunamadı: " + ", ".join(selectors))

    def _wait_chat_ready(self, timeout: int = 20) -> None:
        """
        Sohbet ekranının 'gerçekten' yüklendiğini doğrula.
        En güvenilir sinyal: contenteditable mesaj kutusunun DOM'da olması.
        """
        assert self.driver is not None
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'div[contenteditable="true"][role="textbox"]'
            ))
        )

    def _type_message(self, message: str) -> None:
        """
        Mesajı contenteditable alana sağlam biçimde yerleştir.
        - Kutuyu focusla (click)
        - JS ile textContent yaz ve native input event tetikle
        Neden? Bazı WA sürümlerinde URL ile gelen metin 'Send'i aktifleştirmez.
        """
        assert self.driver is not None
        box = self._find_any([
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]'
        ], timeout=10)

        # Odakla (bazı durumlarda send_keys için şart)
        try:
            box.click()
            time.sleep(0.1)
        except Exception:
            pass

        # JS ile yaz + input event
        self.driver.execute_script(
            """
            const el = arguments[0];
            const txt = arguments[1] ?? "";
            el.focus();
            // mevcut içeriği sil
            let sel = window.getSelection();
            let range = document.createRange();
            range.selectNodeContents(el);
            sel.removeAllRanges();
            sel.addRange(range);
            document.execCommand('delete');
            // yeni içeriği yaz
            el.textContent = txt;
            // input event (WhatsApp'in 'Send' butonunu aktifleştirmesi için)
            el.dispatchEvent(new InputEvent('input', {bubbles:true}));
            """,
            box, message
        )

        # 'Send' aktifleşsin diye minik bekleme
        time.sleep(0.2)

    def _click_send_or_enter(self) -> bool:
        """
        Gönderimi tetiklemek için üç aşamalı strateji:
          1) Yeni WA UI: button[aria-label="Send"]  / TR: "Gönder"
          2) Eski WA UI: span[data-icon="send"]
          3) Yedek:      ENTER tuşu
        """
        assert self.driver is not None

        # 1) Yeni buton (yerelleştirme olasılığına karşı TR'yi de deneriz)
        try:
            btn = self._find_any([
                'button[aria-label="Send"]',
                'button[aria-label="Gönder"]',
            ], timeout=2)
            self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            pass

        # 2) Eski ikon tabanlı buton
        try:
            btn = self._find_any([
                'span[data-icon="send"]',
                'div[role="button"] span[data-icon="send"]',
            ], timeout=2)
            self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            pass

        # 3) ENTER ile gönder
        try:
            box = self._find_any([
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]'
            ], timeout=2)
            box.send_keys(Keys.ENTER)
            return True
        except Exception:
            return False

    # --------------------------------------------------------------------- #
    # Tek numaraya gönderim
    # --------------------------------------------------------------------- #
    def _send_to_one(self, phone: str, message: str) -> Tuple[bool, str]:
        """
        Tek numaraya mesaj yollar (retry yok).
        Adımlar:
            - /send?phone=...&text=... ile sohbeti aç
            - Sohbet hazır olana dek bekle
            - Mesajı 'kutunun içine' tekrar yaz (URL'den gelse bile)
            - 'Gönder'i tıkla (çoklu-seçici / ENTER)
        """
        assert self.driver is not None

        # Sohbeti aç
        encoded = urllib.parse.quote(message)
        self.driver.get(WA_WEB_SEND.format(phone=phone, text=encoded))

        # Sohbet hazır mı?
        try:
            self._wait_chat_ready(timeout=20)
        except TimeoutException:
            return False, "Sohbet yüklenemedi (timeout)."

        # Mesajı güvenle kutuya yaz ve gönder
        try:
            self._type_message(message)
            sent = self._click_send_or_enter()
            if not sent:
                return False, "Gönder butonu/ENTER çalışmadı."
            # Mesaj kuyruğa alınsın
            time.sleep(1.0)
            return True, ""
        except Exception as e:
            return False, f"Gönderim hatası: {e}"

    # --------------------------------------------------------------------- #
    # Toplu gönderim
    # --------------------------------------------------------------------- #
    def broadcast(
        self,
        contacts: Iterable[Contact],
        on_progress: Optional[Callable[[str], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        on_result: Optional[Callable[[SendResult], None]] = None,
        override_message: Optional[str] = None,
    ) -> List[SendResult]:
        """
        Kişi listesini sırayla işler ve her birine mesaj yollamayı dener.
        - on_progress(str): GUI log'u için metin geri bildirimi
        - should_stop():    True dönerse güvenli biçimde döngü kırılır
        - on_result(SendResult): her kişi işlendiğinde tek tek progress güncellemesi
        - override_message: UI'dan gelen mesaj şablonu; varsa Excel 'message' kolonunu yok sayar
        """
        assert self.driver is not None
        results: List[SendResult] = []

        for idx, c in enumerate(contacts, start=1):
            # İptal isteği geldiyse güvenle çık
            if should_stop and should_stop():
                if on_progress:
                    on_progress("İptal istendi, gönderim sonlandırılıyor…")
                break

            # Mesaj seçimi: UI > Excel > TEMPLATE
            base_msg = (override_message if (override_message and override_message.strip())
                        else (c.message or TEMPLATE_MESSAGE))
            msg = base_msg.replace("{name}", c.name or "")

            if on_progress:
                on_progress(f"[{idx}] Gönderiliyor → {c.phone} ({c.name})")

            ok, err = self._send_to_one(c.phone, msg)
            ts = now_str()

            # Sonucu biriktir
            result = SendResult(
                phone=c.phone,
                name=c.name,
                ok=ok,
                error=(err or None),
                final_message=msg,
                row_index=c.row_index,
                sheet_name=c.sheet_name,
                source_path=c.source_path
            )
            results.append(result)

            # GUI’ye tek tek sonuç aktar (progress bar için)
            if on_result:
                try:
                    on_result(result)
                except Exception:
                    # GUI sinyali başarısız olsa bile akışı bozma
                    pass

            # Canlı CSV log
            if ok:
                append_sent_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg})
                if on_progress:
                    on_progress(f"✔ Başarılı: {c.phone}")
            else:
                append_failed_log({"timestamp": ts, "phone": c.phone, "name": c.name, "message": msg, "error": err})
                if on_progress:
                    on_progress(f"✖ Hata: {c.phone} -> {err}")

            # Anti-spam bekleme (ipyal kontrolüyle parça parça)
            wait_total = random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC)
            waited, step = 0.0, 0.5
            while waited < wait_total:
                if should_stop and should_stop():
                    if on_progress:
                        on_progress("İptal istendi, bekleme kesiliyor…")
                    break
                time.sleep(step)
                waited += step

            if on_progress and waited < wait_total:
                on_progress("Bekleme iptal edildi.")

        return results
