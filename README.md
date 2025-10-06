<!-- ViperaDev — WhatsApp Broadcast Tool -->

# WhatsApp Broadcast (Selenium + PyQt5)

- Yalnızca **Excel** kaynağı (.xlsx/.xls)
- Mesaj metnini **arayüzden** yaz, istersen Excel’deki `message` kolonunu **geçersiz kıl**
- Çalışma sırasında **kaynak Excel’e yazmaz**; sonuçlar RAM + CSV log
- İş bitiminde: **Belgeler/WhatsAppBroadcastRuns/<YYYY-MM-DD_HHMMSS>/**
  - `results.xlsx` (Broadcast + Summary, koşullu renklendirme)
  - `sent_log.csv` ve `failed_log.csv` (varsa)

## Kurulum
```bash
pip install -r requirements.txt
python app.py
