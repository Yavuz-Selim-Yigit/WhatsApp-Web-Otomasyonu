# -*- coding: utf-8 -*-
# ViperaDev — WhatsApp Broadcast Tool
"""
Tüm sabitler ve ayarlar:
- WhatsApp profil dizini
- Zamanlama ve anti-spam aralıkları
- Çıktı dosyaları/klasörleri
"""
import os

# WhatsApp Web kullanıcı profili (QR'ı tekrar okutmayı önler)
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "whatsapp_profile")
PROFILE_DIR = "Profile 1"

# Rastgele bekleme aralığı (anti-spam)
MIN_DELAY_SEC = 15
MAX_DELAY_SEC = 45

# Retry SABİTİ kalsın ama kullanılmıyor (isteğin doğrultusunda)
MAX_RETRIES = 2

# Excel’de message boşsa kullanılacak şablon
TEMPLATE_MESSAGE = "Merhaba {name}! Bu bir test mesajıdır."

# Canlı CSV loglar (görev sırasında güvenlik ağı)
SENT_LOG_PATH = "sent_log.csv"
FAILED_LOG_PATH = "failed_log.csv"

# WhatsApp Web URL'leri
WA_WEB_HOME = "https://web.whatsapp.com"
WA_WEB_SEND = "https://web.whatsapp.com/send?phone={phone}&text={text}"

# Çıktı konumu: Belgeler/WhatsAppBroadcastRuns/<timestamp>/results.xlsx
OUTPUT_ROOT_DIRNAME = "WhatsAppBroadcastRuns"
OUTPUT_XLSX_NAME = "results.xlsx"
