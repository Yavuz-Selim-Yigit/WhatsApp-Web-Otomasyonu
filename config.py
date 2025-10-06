"""
config.py — Uygulama genel ayarları ve sabitler.
Tek yerde toplayıp diğer modüllerde import ederek tutarlılığı koruruz.
"""
import os

# Kullanıcı profilinin saklanacağı klasör; QR'ı her seferinde okutmayı önler
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "whatsapp_profile")  # ör: C:\Users\Sen\whatsapp_profile
PROFILE_DIR = "Profile 1"  # Chrome kullanıcı profili adı

# CSV yolu için varsayılan (GUI'de değiştirilebilir)
DEFAULT_CSV_PATH = "contacts.csv"

# Gecikme aralığı (anti-spam riskini azaltmak için rastgele bekleme)
MIN_DELAY_SEC = 15
MAX_DELAY_SEC = 45

# Başarısız bir gönderim için tekrar deneme sayısı
MAX_RETRIES = 2

# Şablon mesaj (CSV'de message boşsa kullanılır)
TEMPLATE_MESSAGE = "Merhaba {name}! Bu bir test mesajıdır."

# Log dosyaları
SENT_LOG_PATH = "sent_log.csv"
FAILED_LOG_PATH = "failed_log.csv"

# WhatsApp Web URL sabitleri
WA_WEB_HOME = "https://web.whatsapp.com"
WA_WEB_SEND = "https://web.whatsapp.com/send?phone={phone}&text={text}"
