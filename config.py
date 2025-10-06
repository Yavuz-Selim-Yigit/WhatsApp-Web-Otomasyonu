"""
config.py — Uygulama genel ayarları ve sabitleri.
Tüm modüller buradan okur; tek yerden yönetilir.
"""
import os

# WhatsApp Web profil klasörü (QR'ı her seferinde okutmayı önler)
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "whatsapp_profile")
PROFILE_DIR = "Profile 1"

# Dosya seçiminde varsayılan isim (GUI üzerinden değişebilir)
DEFAULT_CSV_PATH = "contacts.csv"

# Anti-spam için rastgele bekleme aralığı (saniye)
MIN_DELAY_SEC = 15
MAX_DELAY_SEC = 45

# Başarısız tek numara için tekrar deneme hakkı (BU SÜRÜMDE KULLANILMIYOR)
MAX_RETRIES = 2

# CSV'de 'message' boşsa kullanılacak şablon
TEMPLATE_MESSAGE = "Merhaba {name}! Bu bir test mesajıdır."

# Canlı loglar (iş sırasında güvenlik ağı)
SENT_LOG_PATH = "sent_log.csv"
FAILED_LOG_PATH = "failed_log.csv"

# WhatsApp Web URL'leri
WA_WEB_HOME = "https://web.whatsapp.com"
WA_WEB_SEND = "https://web.whatsapp.com/send?phone={phone}&text={text}"

# Çıktı konumu: Belgeler/WhatsAppBroadcastRuns/<timestamp>/results.xlsx
OUTPUT_ROOT_DIRNAME = "WhatsAppBroadcastRuns"
OUTPUT_XLSX_NAME = "results.xlsx"
