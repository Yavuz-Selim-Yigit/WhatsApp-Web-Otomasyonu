# WhatsApp Broadcast (Selenium + PyQt5)

- WhatsApp Web otomasyonu (resmî API **değil**).
- Liste kaynağı: `.csv` veya `.xlsx`.
- Çalışma sırasında **kaynak Excel'e yazmaz**.
- Sonunda: **Belgeler/WhatsAppBroadcastRuns/<timestamp>/** içine:
  - `results.xlsx` (Broadcast + Summary, koşullu renklendirme),
  - `sent_log.csv` / `failed_log.csv` (varsa),
  - GUI’de **Klasörü Aç** butonu.

## Kurulum

```bash
pip install -r requirements.txt
python app.py
