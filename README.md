# WhatsApp Toplu Gönderim Aracı — Kılavuz (README)

Excel'den alınan kişi listesine **WhatsApp Web** üzerinden **toplu ve kişiselleştirilmiş mesaj** gönderen masaüstü araç. Manuel tek tek sohbet açıp yazma derdini ortadan kaldırır; hız, tutarlılık ve **raporlanabilirlik** sağlar.

> **Özet:** `phone` (zorunlu), `name` (opsiyonel) ve `message` (opsiyonel) kolonlarını okur. Arayüzde yazdığın şablon metin Excel’deki `message` alanını isterse geçersiz kılar. `{name}` yer tutucu ile kişiselleştirir. WhatsApp Web’i Selenium ile otomatik sürer. Gönderim sonunda renkli **Excel raporu** ve **CSV loglar** üretir.

---

## İçindekiler

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım Kılavuzu](#kullanım-kılavuzu)
- [Excel Şablonu](#excel-şablonu)
- [Hız Modları](#hız-modları)
- [Raporlama ve Loglar](#raporlama-ve-loglar)
- [Proje Yapısı](#proje-yapısı)
- [Teknik Notlar](#teknik-notlar)
- [Sık Sorulanlar](#sık-sorulanlar)
- [Riskler ve Sınırlar](#riskler-ve-sınırlar)
- [Katkı ve Geliştirme](#katkı-ve-geliştirme)
- [Sürüm Bilgisi](#sürüm-bilgisi)

---

## Özellikler

- **Kişiselleştirme:** Mesajlarda `{name}` gibi yer tutucularla her alıcıya adıyla hitap edebilirsin.
- **Güvenli Otomasyon:** **SAFE / FAST / TURBO** hız modlarıyla gönderim hızını ve beklemeleri kontrol edersin.
- **Gerçek Zamanlı Takip:** İlerleme çubuğu, başarı/başarısız sayaçları ve log paneli.
- **Kapsamlı Raporlama:** İşlem sonunda renkli `results.xlsx`, ayrıca `sent_log.csv` ve `failed_log.csv`.
- **Planlı Gönderim (opsiyonel):** Belirli bir zamana planlayıp iptal edebilme.
- **Tema ve Konfor:** Açık/koyu tema, net tipografi, sade arayüz.

---

## Kurulum

> Gereksinim: **Python 3.x**, Chrome tarayıcı (WhatsApp Web için).

1) **Proje dosyalarını hazırla**
- Depoyu indir ve bir ana klasöre çıkar.
- `assets/` klasörü oluştur ve `assets/logo.png` dosyanı buraya koy.
- Ana klasörde şu dosyalar bulunduğundan emin ol: `main.py`, `gui.py`, `broadcaster_logic.py`, `requirements.txt`, `README.md`.

2) **Bağımlılıkları kur**
```bash
pip install -r requirements.txt
```

3) **Uygulamayı çalıştır**
```bash
python main.py
```

> İlk çalıştırmada WhatsApp Web oturumu yoksa QR kodu telefondan okutman istenecektir (tek seferlik).

---

## Kullanım Kılavuzu

1. **Excel Hazırlığı:** `phone` (zorunlu), `name` (opsiyonel), `message` (opsiyonel) kolonlarını içeren bir Excel oluştur.
2. **Dosya Seçimi:** Uygulamada **Dosya Seç** ile Excel’i yükle; kişi listesi arayüzde görünür.
3. **Mesaj Şablonu ve Hız:** Ana metin kutusuna şablon mesajı yaz. `{name}` yer tutucusunu kullan. Sol menüden hız modunu seç.
4. **Gönderimi Başlat:** **Gönderimi BAŞLAT** düğmesine bas; Chrome penceresi açılır.
5. **WhatsApp Oturumu:** Gerekirse ekrandaki QR’ı telefondaki WhatsApp ile tara.
6. **İzleme & Raporlama:** İlerlemeyi arayüzden takip et. İşlem bitince rapor klasörü bildirilir.

---

## Excel Şablonu

| phone (zorunlu) | name (ops.)         | message (ops.)              |
|-----------------|---------------------|-----------------------------|
| 905000000000    | Yavuz Selim Yiğit   | Merhaba {name}, duyurumuz…  |
| 905000000000    | —                   | —                           |

- `phone`: **ülke kodu + numara** (başında `+` olmasın). Örn: `905551112233`
- `name`: “Yavuz”, “Selim Y.” vb. Kişiselleştirme için kullanılır.
- `message`: Dilersen kişi bazlı özel metin. **Arayüzdeki şablon**, bu alanı **geçersiz kılabilir**.

**Yer tutucu örneği:**
```
Merhaba {name}, etkinlik duyurumuz var: ...
```

---

## Hız Modları

- **SAFE:** Daha uzun beklemeler; hesap kısıtlama riskini minimize eder.
- **FAST:** Dengeli hız; çoğu senaryo için idealdir.
- **TURBO:** En hızlı; agresif hızlandırma hesap kısıtlaması riskini **artırır**.

> Not: Ağ gecikmesi, donanım ve WhatsApp Web davranışlarına göre bekleme süreleri adaptif tutulur.

---

## Raporlama ve Loglar

Gönderim sonunda **Belgeler/WhatsAppBroadcastRuns/** altında otomatik oluşturulur:

- **`results.xlsx`**: Renkli, özet ve detay sayfalarıyla sonuçlar.
- **`sent_log.csv`**: Başarıyla gönderilen kayıtlar.
- **`failed_log.csv`**: Hatalı/engelli/format dışı telefonlar vb.

Arayüzde ayrıca:
- **İlerleme çubuğu**
- **Başarılı/başarısız sayaçları**
- **Log paneli** bulunur.

---

## Proje Yapısı

```
.
├── main.py                    # Uygulamayı başlatır
├── gui.py                     # Arayüz (dosya seçimi, şablon, hız modu, ilerleme)
├── broadcaster_logic.py       # WhatsApp Web otomasyon akışı, hatalara dayanıklılık
├── requirements.txt           # Bağımlılıklar
├── README.md                  # Bu dosya
└── assets/
    └── logo.png               # Arayüz logosu
```

**Modül Sorumlulukları (yaklaşık):**
- **Arayüz (`gui.py`)** ~ %45  
- **Otomasyon Mantığı (`broadcaster_logic.py`)** ~ %45  
- **Başlatıcı (`main.py`)** ~ %10

---

## Teknik Notlar

- **WhatsApp Web** resmi API değildir; otomasyon Selenium ile Chrome üzerinde çalışır.
- **Oturum Kalıcılığı:** Chrome profil klasörü kullanılarak QR tarama genellikle bir kez yapılır.
- **Çoklu buton seçiciler & adaptif beklemeler:** WhatsApp Web’in arayüz değişimlerine karşı dayanıklılık sağlar.
- **Planlı Gönderim & İptal:** İleri tarih/saatte gönderimi başlatma ve süreç içinde durdurma desteği (varsa).
- **Tema:** Açık/koyu tema, sade ve erişilebilir bileşenler.

---

## Sık Sorulanlar

**WhatsApp numara doğrulaması yapıyor musunuz?**  
Hayır. Hatalı formatlar, engelli alıcılar vb. **Failed** olarak raporlanır.

**Spam’e karşı garanti var mı?**  
Hayır. Hız limitleri ve kullanım kuralları kullanıcı sorumluluğundadır. Aşırı agresif hızlandırma hesap kısıtlamasına yol açabilir.

**`{name}` çalışmıyor gibi, neden?**  
Excel’de `name` boşsa yer tutucu boş kalır. Şablonda `{name}` yazımının doğru olduğundan emin ol.

**Numara formatı nasıl olmalı?**  
`905xxxxxxxxx` gibi; başında `+` ve boşluk/ayraç **olmasın**.

---

## Riskler ve Sınırlar

- WhatsApp’ın **Hizmet Şartları**, **anti-spam politikaları** ve **yerel mevzuat** önceliklidir.
- Tarayıcı eklentileri, yavaş bağlantı ve arayüz değişiklikleri “taslakta kalma” veya “buton görünmüyor” gibi sorunlara yol açabilir. Uygulama korumalar içerir, ancak bu durumlar tamamen engellenemeyebilir.

---

## Katkı ve Geliştirme

**Önerilen geliştirmeler:**
- `{custom1}` gibi **ek yer tutucuları** Excel kolonlarına bağlama.
- **Hata oranına göre otomatik hız modu** (FAST ↔ SAFE) geçişi.
- **A/B metin testleri** ve dönüş analizi.

**Geliştirme adımları:**
1. Fork → feature branch → değişiklikleri yap.
2. Test et ve raporların üretildiğini doğrula.
3. Açıklayıcı bir PR oluştur.

---

## Sürüm Bilgisi

**ViperaDev Versiyon 2.3**

> © ViperaDev — “Çok kişiye nazikçe, tek seferde ve izlenebilir şekilde mesaj atma” problemine pratik bir çözüm.

---
