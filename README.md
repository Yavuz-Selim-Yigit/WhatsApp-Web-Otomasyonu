<!-- ViperaDev — WhatsApp Broadcast Tool -->

# WhatsApp Broadcast (Selenium + PyQt5)

- Yalnızca **Excel** kaynağı (.xlsx/.xls)
- Mesajı **arayüzden** yaz ve istersen Excel `message` kolonunu **geçersiz kıl**
- Çalışırken kaynağa yazmaz; sonuçlar RAM + CSV log
- İş bitiminde: **Belgeler/WhatsAppBroadcastRuns/<YYYY-MM-DD_HHMMSS>/**
  - `results.xlsx` (Broadcast + Summary, koşullu renklendirme)
  - `sent_log.csv`, `failed_log.csv` (varsa)

## Hız modları
`config.py` → `THROTTLE_MODE = "FAST"` (varsayılan), seçenekler: `SAFE | FAST | TURBO`  
Ortam değişkeniyle de ayarlanabilir:
- Windows PowerShell: `setx WB_MODE TURBO` (terminali yeniden aç)
- macOS/Linux: `export WB_MODE=TURBO`

## Kurulum
```bash
pip install -r requirements.txt
python app.py
