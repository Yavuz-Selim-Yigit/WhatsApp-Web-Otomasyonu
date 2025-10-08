# Sendify

Excel'den WhatsApp Web'e kişiselleştirilmiş **toplu mesaj** göndermeyi otomatikleştiren masaüstü araç. Elle tek tek sohbet açma derdini bitirir; hız, tutarlılık ve **raporlanabilirlik** sağlar.

> **Not:** Bu proje resmi WhatsApp API'si **değildir**; WhatsApp Web arayüzünü otomasyonla sürer. Kullanımda WhatsApp'ın Hizmet Şartları ve yerel mevzuat önceliklidir.

---

## İçindekiler
- [Genel Bakış](#genel-bakış)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım Kılavuzu](#kullanım-kılavuzu)
- [Excel Şablonu](#excel-şablonu)
- [Hız Modları](#hız-modları)
- [Raporlama ve Loglar](#raporlama-ve-loglar)
- [Proje Yapısı](#proje-yapısı)
- [Sık Sorulanlar](#sık-sorulanlar)
- [Sorun Giderme](#sorun-giderme)
- [Yol Haritası](#yol-haritası)
- [Lisans](#lisans)
- [Sürüm Bilgisi](#sürüm-bilgisi)

---

## Genel Bakış

Sendify, Excel'deki kişi listelerini okuyarak **kişiselleştirilmiş** mesajları WhatsApp Web üzerinden, gerçek klavye girdisi taklidi ile gönderir. İleri/geri izlenebilirlik, hız modları ve zengin raporlama ile güvenli ve şeffaf bir gönderim deneyimi sunar.

## Özellikler
- **Kişiselleştirme:** Mesajlarda `{name}` gibi yer tutucular; Excel'deki `name` kolonuyla otomatik doldurma.
- **Şablonlu Gönderim:** Arayüzdeki metin, Excel'deki `message` alanını isterseniz **geçersiz kılar**.
- **Hız Modları:** `SAFE`, `FAST`, `TURBO` seçenekleri; risk–hız dengesini sizin belirlemeniz için.
- **Planlama / Durdurma:** Gönderimi ileri zamana planlayıp başlatabilir, süreçte durdurabilirsiniz.
- **Gerçek Zamanlı Takip:** İlerleme çubuğu, canlı sayaçlar, log paneli.
- **Raporlama:** İş bitince `Belgeler/WhatsAppBroadcastRuns/` altında `results.xlsx` (renkli), `sent_log.csv`, `failed_log.csv`.
- **Tema ve Konfor:** Koyu/açık tema, çoklu buton seçiciler, adaptif beklemeler.
- **Dayanıklılık:** Çoklu seçici stratejisi, buton görünmüyor/taslakta kalma gibi durumlara karşı koruma.

---

## Kurulum

### Gereksinimler
- **Python 3.9+**
- Google Chrome
- Aşağıdaki Python paketleri (requirements.txt içinde):

```
selenium
webdriver-manager
pandas
openpyxl
customtkinter
pyinstaller
```

### Adımlar
1. Projeyi indirin ve çıkarın.
2. Ana klasörde `assets/` oluşturun ve `assets/logo.png` yerleştirin (opsiyonel).
3. Bağımlılıkları kurun:
   ```bash
   pip install -r requirements.txt
   ```
4. Uygulamayı çalıştırın:
   ```bash
   python main.py
   ```

> **İpucu:** Chrome oturumunu tekrar QR okutmaya gerek kalmadan korumak için uygulama, kullanıcı profilini kalıcı bir klasörde saklayabilir (örn. `~/whatsapp_profile`).

---

## Kullanım Kılavuzu

1. **Excel'i Hazırla:** `phone` (zorunlu), `name` (opsiyonel), `message` (opsiyonel) sütunlarıyla bir dosya oluşturun.
2. **Dosyayı Seç:** Uygulamada **Dosya Seç** ile Excel'i içe aktarın; listeyi görürsünüz.
3. **Mesaj Şablonu:** Ana metin kutusuna yazın. `{name}` yer tutucusuyla kişiselleştirin. İsterseniz Excel'deki `message` her satır için geçerli olur.
4. **Hız Modu:** `SAFE / FAST / TURBO` arasından seçim yapın.
5. **Başlat:** **Gönderimi BAŞLAT** butonuna tıklayın. Chrome açılır.
6. **WhatsApp Oturumu:** Gerekirse ilk kullanımda QR'ı telefonunuzdaki WhatsApp ile okutun.
7. **İzleme ve Raporlar:** İlerlemeyi UI üzerinden takip edin. İşlem bitince rapor klasörü gösterilecektir.

---

## Excel Şablonu

| phone        | name      | message                                  |
|--------------|-----------|-------------------------------------------|
| +90555XXXXXXX| Ayşe      | Merhaba {name}, etkinliğimize bekleriz!   |
| +90444YYYYYYY| (boş)     | (boş bırakılabilir; şablon metni kullanır)|

- **Zorunlu:** `phone` (uluslararası format önerilir, artı işaretli).
- **İsteğe bağlı:** `name`, `message`.
- **Yer tutucu:** `{name}` — satırda `name` yoksa otomatik kaldırılır/boş gelir.

---

## Hız Modları

- **SAFE:** Maksimum bekleme, düşük risk. Yeni hesaplar ve hassas kampanyalar için.
- **FAST:** Dengeli hız. Çoğu senaryo için önerilir.
- **TURBO:** En hızlı; hata oranı artabilir, hesap kısıtlaması riski daha yüksektir.

> Uygulama; buton bulunamadı, taslakta kaldı gibi durumlarda **adaptif beklemeler** ve **çoklu seçici** stratejileri kullanır.

---

## Raporlama ve Loglar

Gönderim bittiğinde otomatik olarak oluşturulur:

- `results.xlsx` — Renkli özet: **Başarılı/İptal/Başarısız** durumları.
- `sent_log.csv` — Gönderilen numaralar ve zaman damgası.
- `failed_log.csv` — Hata alan satırlar ve temel hata nedeni.

Varsayılan konum: `Belgeler/WhatsAppBroadcastRuns/<TARİH-SAAT>/`

---

## Proje Yapısı

```
.
├── main.py                  # Uygulama başlatıcı
├── gui.py                   # Arayüz (CustomTkinter/Tk + status/progress)
├── broadcaster_logic.py     # WhatsApp Web otomasyon mantığı (Selenium)
├── requirements.txt
├── README.md
└── assets/
    └── logo.png
```

> Sorumluluk dağılımı (yaklaşık): **gui.py %45**, **broadcaster_logic.py %45**, **main.py %10**.

---

## Sık Sorulanlar

**Excel'deki metni mi, şablon metnini mi kullanır?**  
Varsayılan: Excel satırındaki `message` varsa **o**, yoksa arayüzdeki şablon metni kullanılır.

**`{name}` nasıl çalışır?**  
Satırdaki `name` değeriyle yer değiştirir; yoksa boş kalır veya otomatik kaldırılır.

**QR'ı her seferinde okutmak zorunda mıyım?**  
Hayır. Chrome profil klasörü kalıcıysa bir kere yeterli olur.

**Numara engelli/format hatalıysa?**  
Satır **Failed** olarak raporlanır; detay **failed_log.csv**'dedir.

---

## Sorun Giderme

- **Mesaj taslakta kalıyor / Gönderilmiyor:** Hız modunu düşürün (`SAFE`), beklemeleri artırın. Tarayıcı eklentilerini kapatın. Pencerenin görünür olduğundan emin olun.
- **Buton görünmüyor:** WhatsApp Web güncellemeleri seçicileri bozmuş olabilir; alternatif seçiciler devreye girer. Yine de olmuyorsa güncelleme alın.
- **QR Sürekli İstiyor:** Profil klasörünün yazılabilir olduğundan ve tek Chrome örneği kullanıldığından emin olun.
- **Excel okunmuyor:** Dosya açık olabilir; kapatıp tekrar deneyin. `openpyxl` kurulu mu kontrol edin.

---

## Yol Haritası

- `{custom1}` gibi ek değişkenler → Excel kolonlarına bağlama  
- Hata oranına göre otomatik mod geçişi (FAST ↔ SAFE)  
- A/B metin testleri ve dönüşüm analizi

---

## Lisans
Bu proje MIT lisansı ile lisanslanmıştır. Ayrıntılar için `LICENSE` dosyasına bakın.

---

## Sürüm Bilgisi
**ViperaDev Versiyon:** 2.3 (Tema Algılama Düzeltmesi)

