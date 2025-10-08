import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd
import time
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from threading import Thread
# Logo yüklemek için PIL kütüphanesi import edildi
from PIL import Image, ImageTk 

# --- Global Yapılandırma ve Sabitler ---
# Uygulamanın versiyon bilgisi.
VERSION = "ViperaDev Versiyon 2.3 (Tema Algılama Düzeltmesi)"
# Chrome kullanıcı verilerinin saklanacağı yol. Bu, QR kodunu tekrar okutmamak için gereklidir.
# WhatsApp oturumunu bu klasörde saklar.
CHROME_PROFILE_PATH = os.path.join(os.path.expanduser("~"), "whatsapp_profile") 

# Raporların kaydedileceği ana klasör yolu.
REPORT_BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "WhatsAppBroadcastRuns")
# Rapor klasörünün varlığını kontrol eder ve yoksa oluşturur.
os.makedirs(REPORT_BASE_DIR, exist_ok=True)

# Logo dosya yolu
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")


class WhatsAppBroadcaster(ctk.CTk):
    """
    Ana Uygulama Sınıfı.
    WhatsApp Web üzerinden toplu ve kişiselleştirilmiş mesaj gönderimini yöneten 
    masaüstü arayüzünü (GUI) ve tüm arka plan mantığını içerir.
    """
    def __init__(self):
        super().__init__()
        
        # --- Arayüz Temel Ayarları ---
        self.title("WhatsApp Toplu Gönderim Aracı - ViperaDev") # Uygulama başlığı güncellendi
        self.geometry("1100x900") # Arayüz başlangıç boyutu
        
        # Ana ızgara (grid) yapısını yapılandırma: Ekranın genişlemesini sağlar
        self.grid_columnconfigure(1, weight=1) # Ana içerik sütunu genişleyebilir
        self.grid_columnconfigure(2, weight=1) # Kişi listesi sütunu genişleyebilir
        self.grid_rowconfigure(0, weight=1)    # Ana içerik ve liste satırı genişleyebilir
        self.grid_rowconfigure(4, weight=1)    # Terminal alanı satırı genişleyebilir

        # Varsayılan tema ayarları
        # Temayı "System" olarak ayarlar, ancak başlangıç değeri "System" olarak görünür.
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue") # Varsayılan renk temasını ayarlar

        # --- Durum ve Veri Değişkenleri ---
        self.is_running = False        # Gönderim sürecinin aktif olup olmadığını tutar
        self.driver = None             # Selenium WebDriver nesnesi (tarayıcı kontrolü)
        self.df_data = None            # Excel'den okunan Pandas DataFrame
        self.failed_log = []           # Başarısız gönderim kayıtları
        self.sent_log = []             # Başarılı gönderim kayıtları
        self.total_recipients = 0      # Toplam alıcı sayısı
        self.current_run_dir = None    # Mevcut çalıştırma için oluşturulan rapor klasörü
        self.current_thread = None     # Arka planda çalışan gönderim iş parçacığı
        
        # --- Arayüz Bileşenlerini Oluşturma Sırası ---
        self._create_sidebar()
        self._create_main_frames()
        self._create_list_frame() 
        self._create_controls_frame()
        self._create_progress_frame()
        self._create_log_frame() # Terminal alanı
        
        # Kişi listesi arayüz öğeleri (anlık durum güncellemesi için saklanır)
        self.recipient_widgets = {}

    def _create_sidebar(self):
        """
        Sol taraftaki navigasyon ve yapılandırma çubuğunu oluşturur.
        Tasarım güncellendi: Logo alanı görselle değiştirildi ve düzen sadeleştirildi.
        """
        # Sidebar çerçevesini daha belirgin yapmak için farklı bir arka plan renk tonu kullandık
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0, fg_color=("gray85", "gray15"))
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsew") 
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Versiyon etiketinin altında boşluk bırakmak için

        # --- LOGO VE BAŞLIK ALANI ---
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=("gray80", "gray18"), corner_radius=0, height=80)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logo_frame.grid_columnconfigure(0, weight=1)

        try:
            # Logo görselini yükle
            pil_image = Image.open(LOGO_PATH)
            # Görsel boyutunu küçült (Örneğin: 40x40 piksel)
            pil_image = pil_image.resize((40, 40)) 
            self.logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(40, 40))

            # Görsel ve metin içeren etiket
            logo_label = ctk.CTkLabel(logo_frame, text="Broadcast Tool", image=self.logo_image, compound="left", 
                                     font=ctk.CTkFont(family="Inter", size=18, weight="bold"))
        except FileNotFoundError:
            # Logo dosyası bulunamazsa varsayılan metni kullan
            logo_label = ctk.CTkLabel(logo_frame, text="🔴 Logo Missing", 
                                     font=ctk.CTkFont(family="Inter", size=18, weight="bold"))
            self._log_to_terminal(f"UYARI: Logo dosyası bulunamadı: {LOGO_PATH}", "error")
        
        logo_label.grid(row=0, column=0, padx=10, pady=20)
        # ---------------------------------------------

        # Kodu Destek Başlığı (Logo'nun altına kaydırıldı)
        ctk.CTkLabel(self.sidebar_frame, text="Kodlama Desteği", 
                     font=ctk.CTkFont(family="Inter", size=16, weight="bold")).grid(row=1, column=0, padx=20, pady=(15, 5))
        
        # Hız Modu Seçimi Kontrolleri
        ctk.CTkLabel(self.sidebar_frame, text="Hız Modu:", anchor="w", 
                     font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.speed_mode = ctk.StringVar(value="FAST")
        self.mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["SAFE", "FAST", "TURBO"], command=self._show_delay_info)
        self.mode_optionemenu.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="ew")
        
        # Hız moduna ilişkin açıklayıcı bilgi etiketi
        self.delay_info_label = ctk.CTkLabel(self.sidebar_frame, text="Gecikme: 5-8 sn", font=ctk.CTkFont(size=10), text_color="gray")
        self.delay_info_label.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="n") 
        
        # Tema Seçimi Kontrolleri
        ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w", 
                     font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # Başlangıç temasını sistem ayarına göre ayarla (CustomTkinter'ın iç fonksiyonu)
        initial_appearance = ctk.get_appearance_mode().capitalize()
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, 
                                                            values=["Light", "Dark", "System"], 
                                                            command=self.change_appearance_mode_event,
                                                            variable=ctk.StringVar(value=initial_appearance)) # Başlangıç değerini sisteme göre set et
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(5, 5), sticky="ew")
        
        # Versiyon ve imza bilgisi (Çubuğun en altına sabitlendi)
        ctk.CTkLabel(self.sidebar_frame, text="ViperaDev ©", 
                     font=ctk.CTkFont(size=11, slant="italic", weight="bold")).grid(row=7, column=0, padx=20, pady=(20, 0), sticky="s")
        ctk.CTkLabel(self.sidebar_frame, text=VERSION, 
                     font=ctk.CTkFont(size=10)).grid(row=8, column=0, padx=20, pady=(0, 20), sticky="s")
        
        self._show_delay_info(self.speed_mode.get())

    def _show_delay_info(self, mode):
        """Seçilen hız moduna göre gecikme bilgisini günceller."""
        if mode == "SAFE":
            info = "Gecikme: 8-15 sn (Güvenli, Önerilir)"
        elif mode == "FAST":
            info = "Gecikme: 5-8 sn (Dengeli)"
        elif mode == "TURBO":
            info = "Gecikme: 3-5 sn (Çok Hızlı, Riskli)"
        self.delay_info_label.configure(text=info)
        self.speed_mode.set(mode)

    def _create_main_frames(self):
        """Ana içerik çerçevelerini (Dosya Yolu ve Mesaj Şablonu) oluşturur. (Tasarım iyileştirmesi)"""
        
        # --- Dosya Yolu Çerçevesi ---
        # Köşeleri yuvarlatılmış ve kenarlıklı çerçeve
        self.file_frame = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        self.file_frame.grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.file_frame, text="1. Excel Dosyası Seç (phone, name, message sütunları zorunludur):", anchor="w", 
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.file_path_entry = ctk.CTkEntry(self.file_frame, placeholder_text="Excel dosyasının tam yolu...", height=30)
        self.file_path_entry.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        self.file_button = ctk.CTkButton(self.file_frame, text="Dosya Seç", command=self.select_file, 
                                          fg_color="#3498db", hover_color="#2980b9")
        self.file_button.grid(row=1, column=1, padx=15, pady=(0, 15))

        # --- Mesaj Şablonu Çerçevesi ---
        self.message_frame = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        self.message_frame.grid(row=1, column=1, padx=(20, 10), pady=(10, 10), sticky="nsew")
        self.message_frame.grid_columnconfigure(0, weight=1)
        self.message_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.message_frame, text="2. Mesaj Şablonu (Kişiselleştirme için {name} kullanın):", anchor="w", 
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.message_textbox = ctk.CTkTextbox(self.message_frame, height=150, corner_radius=8)
        self.message_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Mesaj tekrarını önlemek için, bu satırın yalnızca bir kez çağrıldığından emin olduk.
        self.message_textbox.insert("0.0", "Merhaba {name},\n\nBu, toplu mesaj gönderim aracımızın bir testidir. İyi günler!")

    def _create_list_frame(self):
        """Excel'den çekilen kişileri ve anlık durumlarını gösteren çerçeveyi oluşturur. (Tasarım iyileştirmesi)"""
        self.list_container_frame = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        self.list_container_frame.grid(row=0, column=2, rowspan=2, padx=(10, 20), pady=(20, 10), sticky="nsew")
        self.list_container_frame.grid_columnconfigure(0, weight=1)
        self.list_container_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.list_container_frame, text="3. Kişi Listesi ve Anlık Durum:", anchor="w", 
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        # Scrollable Frame'e hafif bir iç boşluk ekledik
        self.list_scroll_frame = ctk.CTkScrollableFrame(self.list_container_frame, label_text="Yüklenen Kişiler (0 Kişi)", label_font=ctk.CTkFont(weight="bold"))
        self.list_scroll_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.list_scroll_frame.grid_columnconfigure(0, weight=1)

    def _create_controls_frame(self):
        """Başlatma/İptal etme düğmelerini içeren kontrol çerçevesini oluşturur."""
        self.controls_frame = ctk.CTkFrame(self, corner_radius=10)
        self.controls_frame.grid(row=2, column=1, columnspan=2, padx=(20, 20), pady=(10, 10), sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1), weight=1)

        # Başlat düğmesi, daha canlı bir görünüm için rengi vurgulandı
        self.start_button = ctk.CTkButton(self.controls_frame, text="Gönderimi BAŞLAT", command=self.start_broadcast_thread, height=45, 
                                          font=ctk.CTkFont(size=15, weight="bold"),
                                          fg_color="#2ecc71", hover_color="#27ae60")
        self.start_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # İptal düğmesi
        self.cancel_button = ctk.CTkButton(self.controls_frame, text="Gönderimi İPTAL ET", command=self.cancel_broadcast, height=45, 
                                           font=ctk.CTkFont(size=15, weight="bold"),
                                           fg_color="#e74c3c", hover_color="#c0392b", state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    
    def _create_progress_frame(self):
        """İlerleme çubuğunu ve sayaçları içeren durumu gösteren çerçeveyi oluşturur."""
        self.progress_frame = ctk.CTkFrame(self, corner_radius=10)
        self.progress_frame.grid(row=3, column=1, columnspan=2, padx=(20, 20), pady=(10, 10), sticky="ew")
        self.progress_frame.grid_columnconfigure((0, 1), weight=1)
        
        # İlerleme Çubuğu
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, orientation="horizontal", height=10)
        self.progress_bar.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 10), sticky="ew")
        self.progress_bar.set(0)

        # Sayaçlar
        self.counter_label = ctk.CTkLabel(self.progress_frame, text="Hazır | Toplam Kişi: 0", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.counter_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Durum: Bekleniyor...", anchor="e", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="e")

    def _create_log_frame(self):
        """Uygulama mesajlarını ve durumunu gösteren terminal alanını oluşturur."""
        self.log_frame = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        # Terminal alanı, tüm alt kısmı kaplar
        self.log_frame.grid(row=4, column=1, columnspan=2, padx=(20, 20), pady=(10, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.log_frame, text="Terminal Çıktısı (Anlık İşlem Günlükleri):", anchor="w", 
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        # Terminal için özel bir görünüm sağlamak amacıyla yazı tipi ayarı
        self.terminal_textbox = ctk.CTkTextbox(self.log_frame, height=150, activate_scrollbars=True, 
                                               corner_radius=8, font=ctk.CTkFont(family="Consolas", size=12))
        self.terminal_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.terminal_textbox.configure(state="disabled") # Terminal sadece okuma modunda olmalı
        self._log_to_terminal(f"[{self.title()}] Uygulama başlatıldı. Lütfen Excel dosyasını seçin.", "info")

    def _log_to_terminal(self, message, tag="info"):
        """
        Mesajı terminal alanına ekler.
        Bu metod, arka plan işlemlerinden arayüze bilgi akışını sağlar.
        """
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        # Mesaj etiketlerine göre ön ek ayarlanır
        if tag == "error":
            prefix = "[HATA]"
        elif tag == "success":
            prefix = "[BAŞARILI]"
        else:
            prefix = "[BİLGİ]"
            
        full_message = f"{timestamp} {prefix} {message}\n"
        
        # Terminale yazmak için durumu etkinleştir ve mesajı ekle
        self.terminal_textbox.configure(state="normal")
        self.terminal_textbox.insert(ctk.END, full_message)
        
        # Otomatik kaydırma
        self.terminal_textbox.see(ctk.END)
        self.terminal_textbox.configure(state="disabled")

    # --- Arayüz İşleyicileri ---

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Uygulamanın tema (Light/Dark/System) değişimini yönetir."""
        ctk.set_appearance_mode(new_appearance_mode)

    def select_file(self):
        """Kullanıcının Excel dosyasını seçmesini ve veriyi okumasını sağlar."""
        file_path = filedialog.askopenfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Dosyaları", "*.xlsx"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self._preview_data(file_path)

    def _preview_data(self, file_path):
        """Seçilen dosyayı Pandas ile okur, sütunları kontrol eder ve kişi listesini doldurur."""
        try:
            self.df_data = pd.read_excel(file_path)
            
            # Zorunlu sütun kontrolü: 'phone' olmalı
            required_cols = ['phone']
            missing_cols = [col for col in required_cols if col not in self.df_data.columns]
            
            if missing_cols:
                messagebox.showerror("Hata", f"Excel dosyasında zorunlu sütun(lar) eksik: {', '.join(missing_cols)}. Lütfen 'phone' sütununun bulunduğundan emin olun.")
                self.df_data = None
                self.total_recipients = 0
                self._log_to_terminal(f"Zorunlu sütun(lar) eksik: {', '.join(missing_cols)}", "error")
            else:
                self.total_recipients = len(self.df_data)
                self.counter_label.configure(text=f"Hazır | Toplam Kişi: {self.total_recipients}")
                self.status_label.configure(text="Durum: Veri Yüklendi.")
                self._populate_list()
                self._log_to_terminal(f"Excel verisi başarıyla yüklendi. Toplam {self.total_recipients} kişi.", "info")
                
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunamadı veya biçim hatası: {e}")
            self.df_data = None
            self.total_recipients = 0
            self.counter_label.configure(text="Hazır | Toplam Kişi: 0")
            self._clear_list()
            self._log_to_terminal(f"Dosya okuma hatası: {e}", "error")

    def _clear_list(self):
        """Kişi listesi görünümündeki tüm öğeleri temizler."""
        for widget in self.list_scroll_frame.winfo_children():
            widget.destroy()
        self.recipient_widgets = {}
        self.list_scroll_frame.configure(label_text="Yüklenen Kişiler (0 Kişi)")

    def _populate_list(self):
        """DataFrame'den kişileri okur ve arayüzdeki kaydırılabilir listeye doldurur."""
        self._clear_list()
        
        self.list_scroll_frame.configure(label_text=f"Yüklenen Kişiler ({self.total_recipients} Kişi)")
        
        # DataFrame'deki her bir satırı döngüye al
        for list_row_index, (_, row) in enumerate(self.df_data.iterrows()):
            
            phone_raw = row['phone']
            # İsim sütunu yoksa veya boşsa varsayılan değer atar
            name = row['name'] if 'name' in row and pd.notna(row['name']) else '(İsimsiz Kişi)'
            status = row['status'] if 'status' in row and pd.notna(row['status']) else 'Bekliyor'
            
            # Her kişi için özel bir çerçeve (satır) oluşturur (Yuvarlatılmış ve kenarlıklı)
            person_frame = ctk.CTkFrame(self.list_scroll_frame, border_width=1, corner_radius=5)
            person_frame.grid(row=list_row_index, column=0, padx=5, pady=3, sticky="ew")
            person_frame.grid_columnconfigure(0, weight=1)
            
            # İsim ve Telefon etiketleri
            name_label = ctk.CTkLabel(person_frame, text=f"{name} ({phone_raw})", anchor="w", 
                                       font=ctk.CTkFont(weight="bold", size=13))
            name_label.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="w")
            
            # Durum göstergesi (gönderim sırasında güncellenecek)
            status_label = ctk.CTkLabel(person_frame, text=f"Durum: {status}", anchor="e", text_color="gray", 
                                         font=ctk.CTkFont(weight="bold"))
            status_label.grid(row=0, column=1, padx=10, pady=(5, 5), sticky="e")
            
            # Anlık durum güncellemesi için widget'ları saklar (index 0'dan başlar)
            self.recipient_widgets[list_row_index] = {
                'frame': person_frame,
                'status_label': status_label
            }


    def _update_list_status(self, index, status_text, color_key="pending"):
        """Kişi listesindeki bir öğenin durumunu ve rengini anlık olarak günceller."""
        if index in self.recipient_widgets:
            status_widget = self.recipient_widgets[index]['status_label']
            frame_widget = self.recipient_widgets[index]['frame']
            
            # Durum rengini ayarla
            if color_key == "sent":
                color = "#2ecc71" # Canlı yeşil
            elif color_key == "failed":
                color = "#e74c3c" # Canlı kırmızı
            elif color_key == "sending":
                color = "orange" # Turuncu
            else: # pending
                color = "gray"
            
            status_widget.configure(text=f"Durum: {status_text}", text_color=color)
            
            # Çerçeve arka plan rengi (gönderim tamamlanınca)
            if color_key == "sent":
                # Koyu yeşil tonu (okunurluk için)
                frame_widget.configure(fg_color=("#C6EFCE", "#3A533E")) 
            elif color_key == "failed":
                # Koyu kırmızı tonu
                frame_widget.configure(fg_color=("#FFC7CE", "#533A3A")) 
            else:
                # Varsayılan arka plan rengine dön
                frame_widget.configure(fg_color=self.list_scroll_frame.cget("fg_color"))


    # --- Mesaj Gönderim Mantığı ---

    def _get_delays(self):
        """Seçilen hıza göre bekleme sürelerini (saniye) döndürür."""
        mode = self.speed_mode.get()
        # Dönüş sırası: WA_OPEN_DELAY, SEND_DELAY, SEARCH_SUCCESS_DELAY, SEARCH_FAIL_DELAY
        if mode == "SAFE":
            return 8, 15, 4, 7
        elif mode == "FAST":
            return 5, 8, 2, 4
        elif mode == "TURBO":
            return 3, 5, 1, 2
        return 5, 8, 2, 4

    def _clean_phone_number(self, phone):
        """Telefon numarasını sadece rakamları içerecek ve '90' ile başlayacak şekilde temizler."""
        phone = re.sub(r'[^0-9]', '', str(phone))
        if not phone.startswith('90'):
            return '90' + phone
        return phone

    def _init_browser(self):
        """
        Chrome tarayıcısını (Selenium) başlatır ve WhatsApp Web'e oturum açmaya çalışır.
        Daha önce kaydedilmiş bir profil varsa, QR kodunu atlar.
        """
        
        options = webdriver.ChromeOptions()
        # Oturum verilerini kaydetmek için kullanıcı profili yolu eklenir.
        options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}") 
        options.add_argument("--start-maximized")
        # Bot olduğunun anlaşılmasını zorlaştırmak için bazı otomasyon özelliklerini devre dışı bırakır.
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        try:
            self._log_to_terminal("Chrome sürücüsü indiriliyor ve başlatılıyor...", "info")
            # Chrome sürücüsünü otomatik olarak indirir ve kurar.
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get("https://web.whatsapp.com")

            # BAŞARILI GİRİŞ KONTROLÜ: Yan çubuktaki arama kutusunun yüklenmesini bekler.
            SEARCH_INPUT_XPATH = '//*[@id="side"]//div[@role="textbox"]'
            
            self.status_label.configure(text="Durum: QR Kodu Taranıyor... (Lütfen Tarayıcıya Bakın)")
            self._log_to_terminal("Tarayıcı başlatıldı. Oturum kontrol ediliyor (60sn bekleniyor)...")
            
            # Maksimum 60 saniye bekler. Oturum açıksa hemen geçer.
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, SEARCH_INPUT_XPATH)) 
            )
            
            self.status_label.configure(text="Durum: WhatsApp Web Hazır.")
            self._log_to_terminal("WhatsApp Web oturumu başarıyla açıldı. Gönderim başlıyor...")
            return True

        except Exception as e:
            # Sürüm uyumsuzluğu veya bağlantı hatası oluşursa tarayıcıyı kapat ve hatayı logla
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self._log_error(f"Tarayıcı başlatılırken veya WhatsApp Web yüklenirken kritik hata: {e}")
            self._log_to_terminal("WhatsApp Web oturumu açılamadı. Hata: Tarayıcı sürücüsü bağlantısı kurulamadı (Lütfen Chrome sürümünüzü kontrol edin).", "error")
            return False

    def _send_message(self, index, row, message_template, delays):
        """Belirli bir kişiye kişiselleştirilmiş mesajı WhatsApp Web üzerinden gönderir."""
        
        WA_OPEN_DELAY, SEND_DELAY, SEARCH_SUCCESS_DELAY, SEARCH_FAIL_DELAY = delays
        
        phone_raw = row['phone']
        name = row['name'] if 'name' in row and pd.notna(row['name']) else 'kişi'
        
        excel_message = row['message'] if 'message' in row and pd.notna(row['message']) else None
        
        # Mesaj içeriğini belirler: Excel'deki mesaj yoksa arayüzdeki şablon kullanılır.
        if excel_message:
            message_content = str(excel_message).replace('{name}', name).strip()
        else:
            message_content = message_template.replace('{name}', name).strip()

        phone_clean = self._clean_phone_number(phone_raw)
        
        self._update_list_status(index, "Gönderiliyor...", "sending")
        
        # WhatsApp API linkine mesaj içeriği eklenmiyor, sadece sohbeti açmak için kullanılıyor.
        link = f"https://web.whatsapp.com/send?phone={phone_clean}"
        
        try:
            self.driver.get(link)
            # Sohbetin ve mesaj kutusunun yüklenmesi için bekleme süresi
            time.sleep(WA_OPEN_DELAY) 
            
            try:
                # Mesaj kutusunu bulma
                message_box_xpath = '//*[@id="main"]//footer//*[@contenteditable="true"]'
                
                message_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, message_box_xpath))
                )
                
                # --- Çift Yazma Sorunu Çözümü (Geri Dönüş): Temizleme ve Tek Yazma ---
                
                # 1. Kutuya odaklan ve içeriği temizle (Çift yazma sorununu kesin çözer)
                # NOT: Bu, URL'den kaynaklanan otomatik doldurmayı temizler.
                message_box.click() # Odaklan
                message_box.send_keys(Keys.CONTROL, 'a') # Tüm metni seç
                message_box.send_keys(Keys.BACKSPACE) # Sil
                
                # 2. Mesajı tek seferde ve güvenli bir şekilde yazdır ve gönder
                # Gerekirse mesajı satır satır yazmak yerine, WhatsApp'ın klavye olayını görmesi için 
                # mesajı satır sonu olmadan tek bir akışta göndermek daha iyi olabilir.
                
                # Mesajdaki yeni satır karakterlerini (\n) ENTER tuşu olayına dönüştürerek gönder.
                # Bu, mesajın WhatsApp tarafından doğru algılanmasını sağlar.
                lines = message_content.split('\n')
                for i, line in enumerate(lines):
                    message_box.send_keys(line)
                    if i < len(lines) - 1:
                        # Yeni satır için SHIFT+ENTER kullanma (mesajı göndermesini engeller)
                        message_box.send_keys(Keys.SHIFT, Keys.ENTER)
                
                # Sonunda mesajı göndermek için ENTER tuşuna bas
                message_box.send_keys(Keys.ENTER)
                
                self._log_success(index, phone_raw, name, message_content)
                time.sleep(SEND_DELAY) # Gönderimden sonra bekleme süresi (Bot algılamasını azaltır)
            
            # Mesaj kutusu bulunamazsa veya gönderim başarısız olursa
            except Exception as e:
                if self._check_number_invalid():
                    self._log_fail(index, phone_raw, name, "Numara WhatsApp kullanıcısı değil veya geçersiz.", None)
                    time.sleep(SEARCH_FAIL_DELAY)
                else:
                    self._log_fail(index, phone_raw, name, f"Mesaj kutusu bulunamadı/Gönderim hatası: {e}", None)
                    time.sleep(SEARCH_FAIL_DELAY)
                    
        except Exception as e:
            self._log_fail(index, phone_raw, name, f"Genel Gönderim Hatası: {e}", e)
            time.sleep(SEARCH_FAIL_DELAY)

    def _check_number_invalid(self):
        """Geçersiz numara pop-up'ını (WhatsApp kullanıcısı değil) kontrol eder."""
        try:
            # Geçersiz numara uyarısının görünmesini bekler
            invalid_popup_xpath = '//*[contains(text(), "telefon numarası geçersiz")] | //*[contains(text(), "WhatsApp kullanıcısı değil")]'
            
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, invalid_popup_xpath))
            )
            return True
        except:
            return False # Pop-up bulunamadıysa numara geçerli kabul edilir

    def _log_success(self, index, phone, name, message):
        """Başarılı gönderimi kaydeder, ilerlemeyi ve arayüzü günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sent_log.append({
            'timestamp': now, 
            'phone': phone, 
            'name': name, 
            'message': message, 
            'status': 'SENT'
        })
        self.update_progress()
        self._update_list_status(index, "BAŞARILI", "sent")
        self._log_to_terminal(f"BAŞARILI: {name} ({phone}) kişisine mesaj gönderildi.", "success")

    def _log_fail(self, index, phone, name, reason, exception):
        """Başarısız gönderimi kaydeder, ilerlemeyi ve arayüzü günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_detail = str(exception) if exception else reason
        self.failed_log.append({
            'timestamp': now, 
            'phone': phone, 
            'name': name, 
            'reason': reason, 
            'error_detail': error_detail
        })
        self.update_progress()
        self._update_list_status(index, f"BAŞARISIZ ({reason})", "failed")
        self.status_label.configure(text=f"Durum: {name} kişisine gönderim BAŞARISIZ.")
        self._log_to_terminal(f"BAŞARISIZ: {name} ({phone}). Sebep: {reason}", "error")

    def _log_error(self, message):
        """Uygulama düzeyinde kritik hataları hem terminale hem de pop-up ile kullanıcıya bildirir."""
        self._log_to_terminal(f"Uygulama Hatası: {message}", "error")
        # Pop-up penceresini kaldırıyoruz, sadece terminalde gösterilmesi yeterli.
        # messagebox.showerror("Uygulama Hatası", message) # Bu satır kaldırıldı
        self.status_label.configure(text=f"Durum: HATA! İşlem durduruldu. ({message})")

    def update_progress(self):
        """Arayüzdeki ilerleme çubuğunu ve sayaçları anlık olarak günceller."""
        sent_count = len(self.sent_log)
        failed_count = len(self.failed_log)
        processed_count = sent_count + failed_count
        
        # İlerleme değerini hesapla
        progress_value = processed_count / self.total_recipients if self.total_recipients > 0 else 0
        
        self.progress_bar.set(progress_value)
        self.counter_label.configure(text=f"İşlendi: {processed_count}/{self.total_recipients} | Başarılı: {sent_count} | Başarısız: {failed_count}")
        
        if processed_count < self.total_recipients:
            self.status_label.configure(text=f"Durum: Gönderiliyor... (Kişi {processed_count + 1}/{self.total_recipients})")

    # --- Başlatma/Kontrol Fonksiyonları ---

    def start_broadcast_thread(self):
        """
        Gönderim işlemini arayüzü dondurmaması için ayrı bir iş parçacığında başlatır.
        Temel kontrol ve hazırlıkları yapar.
        """
        if self.is_running:
            messagebox.showwarning("Uyarı", "Gönderim zaten devam ediyor.")
            return

        file_path = self.file_path_entry.get()
        message_template = self.message_textbox.get("0.0", "end-1c")

        # Gerekli veri kontrolleri: Dosya seçildi mi ve kişi var mı?
        if not file_path or self.df_data is None or self.total_recipients == 0: 
            messagebox.showerror("Hata", "Lütfen geçerli bir Excel dosyası seçin ve veriyi yükleyin.")
            self._log_to_terminal("HATA: Gönderim başlatılamadı. Dosya seçimi veya veri yüklemesi eksik.", "error")
            return
        
        # Mesaj içeriği kontrolü: Genel şablon boşsa ve Excel'de özel mesaj yoksa durdur.
        has_message_col = 'message' in self.df_data.columns and not self.df_data['message'].isna().all()
        if not message_template.strip() and not has_message_col:
             messagebox.showerror("Hata", "Lütfen bir mesaj şablonu girin veya Excel dosyanızdaki 'message' sütununu doldurun.")
             self._log_to_terminal("HATA: Gönderim başlatılamadı. Mesaj içeriği eksik.", "error")
             return
            
        # Gönderim durumunu sıfırla ve arayüzü hazırla
        self.is_running = True
        self.failed_log = []
        self.sent_log = []
        self.start_button.configure(state="disabled", text="Gönderim Başladı")
        self.cancel_button.configure(state="normal")
        self.progress_bar.set(0)
        self.update_progress()
        self._reset_list_colors() 
        self._log_to_terminal(f"Gönderim işlemi başlatılıyor. Hız Modu: {self.speed_mode.get()}", "info")

        # Gönderim işini ayrı bir Thread'e devreder
        self.current_thread = Thread(target=self.start_broadcast, args=(message_template,))
        self.current_thread.start()

    def _reset_list_colors(self):
        """Gönderim başlamadan listeyi 'Bekliyor' durumuna ve rengine sıfırlar."""
        for index, widgets in self.recipient_widgets.items():
            widgets['status_label'].configure(text="Durum: Bekliyor", text_color="gray")
            widgets['frame'].configure(fg_color=self.list_scroll_frame.cget("fg_color"))


    def start_broadcast(self, message_template):
        """Ana gönderim döngüsünü çalıştırır ve tarayıcıyı kontrol eder."""
        
        # Eğer başlatma başarısız olursa, durdur.
        if not self._init_browser():
            self.cancel_broadcast(hard_stop=True)
            return 

        delays = self._get_delays()
        
        try:
            # Tüm alıcıları döngüye al
            for index, (_, row) in enumerate(self.df_data.iterrows()):
                if not self.is_running:
                    break # Kullanıcı iptal ettiyse döngüyü kır
                
                self._send_message(index, row, message_template, delays)
                
        except Exception as e:
            self._log_error(f"Beklenmedik bir hata oluştu: {e}")
            
        finally:
            # İşlem bittiğinde veya kesildiğinde tarayıcıyı kapat
            if self.driver:
                self.driver.quit()
            self._finish_broadcast()

    def cancel_broadcast(self, hard_stop=False):
        """Gönderimi durdurur ve arayüzü temizler."""
        if self.is_running:
            self.is_running = False
            self.status_label.configure(text="Durum: İptal Ediliyor...")
            self._log_to_terminal("Kullanıcı isteği üzerine iptal ediliyor. Tarayıcı kapatılıyor...", "info")
            
            # Tarayıcıyı güvenli bir şekilde kapatmaya çalışır
            if self.driver:
                 try:
                    self.driver.quit()
                 except:
                    pass
                 self.driver = None

            # Thread'in tamamlanmasını bekler
            if not hard_stop and self.current_thread and self.current_thread.is_alive():
                self.current_thread.join(timeout=5)
            
            self._finish_broadcast(cancelled=True)
        else:
             if hard_stop:
                self._finish_broadcast(cancelled=True)
             else:
                messagebox.showinfo("Bilgi", "Gönderim zaten durdurulmuş.")


    def _finish_broadcast(self, cancelled=False):
        """Gönderim tamamlandığında veya iptal edildiğinde son işlemleri (raporlama, arayüz sıfırlama) yapar."""
        self.is_running = False
        self.start_button.configure(state="normal", text="Gönderimi BAŞLAT")
        self.cancel_button.configure(state="disabled")

        if cancelled:
            self.status_label.configure(text="Durum: GÖNDERİM İPTAL EDİLDİ.")
            self._log_to_terminal("Gönderim kullanıcı tarafından İPTAL EDİLDİ.", "info")
        else:
            self.status_label.configure(text="Durum: GÖNDERİM TAMAMLANDI.")
            self._log_to_terminal("Gönderim başarıyla TAMAMLANDI.", "success")

        # Raporlama sadece gönderim denemesi yapıldıysa gerçekleşir
        if self.sent_log or self.failed_log:
            self._generate_reports()
            self._log_to_terminal(f"Raporlar oluşturuldu ve '{self.current_run_dir}' klasörüne kaydedildi.", "info")
            messagebox.showinfo("Tamamlandı", f"Gönderim tamamlandı.\nRaporlar şu klasöre kaydedildi: \n{self.current_run_dir}")
        elif not cancelled:
             messagebox.showinfo("Bilgi", "İşlenecek veri yok veya işlem başlatılamadı.")
             self._log_to_terminal("İşlenecek veri kalmadı, işlem sonlandı.", "info")

    # --- Raporlama Mantığı ---

    def _generate_reports(self):
        """Gönderim sonuçlarını rapor dosyalarına (Excel, CSV) kaydeder."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = os.path.join(REPORT_BASE_DIR, f"run_{timestamp}")
        os.makedirs(self.current_run_dir, exist_ok=True)
        
        # 1. Genel Rapor (results.xlsx - Renkli Rapor)
        final_df = self.df_data.copy()
        
        # Logları Pandas DataFrame'lere dönüştür
        sent_df = pd.DataFrame(self.sent_log)
        failed_df = pd.DataFrame(self.failed_log)
        
        # Ana tabloyu sonuçlarla güncellemek için varsayılan sütunları ekler
        final_df['status'] = 'PENDING'
        final_df['log_time'] = ''
        final_df['reason'] = ''

        # Gönderim sonuçlarını (SENT/FAILED) ana veri çerçevesine işler
        for index, row in final_df.iterrows():
            phone_raw = row['phone']
            
            # Başarılı ve başarısız logları telefon numarasına göre ana tabloya eşler
            
            match_sent = sent_df[sent_df['phone'] == phone_raw]
            if not match_sent.empty:
                final_df.loc[index, 'status'] = 'SENT'
                final_df.loc[index, 'log_time'] = match_sent.iloc[0]['timestamp']
                continue

            match_failed = failed_df[failed_df['phone'] == phone_raw]
            if not match_failed.empty:
                final_df.loc[index, 'status'] = 'FAILED'
                final_df.loc[index, 'log_time'] = match_failed.iloc[0]['timestamp']
                final_df.loc[index, 'reason'] = match_failed.iloc[0]['reason']

        report_file_path = os.path.join(self.current_run_dir, "results.xlsx")
        
        try:
            # Excel'e kaydetme ve Renklendirme (xlsxwriter motoru kullanılır)
            writer = pd.ExcelWriter(report_file_path, engine='xlsxwriter')
            final_df.to_excel(writer, sheet_name='Rapor', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Rapor']

            # Renk formatlarını tanımlar
            sent_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            failed_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

            # 'SENT' ve 'FAILED' durumlarına göre tüm satırı koşullu olarak renklendirir
            worksheet.conditional_format('A1:Z' + str(len(final_df) + 1), 
                                        {'type': 'text', 'criteria': 'containing', 'value': 'SENT', 'format': sent_format})

            worksheet.conditional_format('A1:Z' + str(len(final_df) + 1), 
                                        {'type': 'text', 'criteria': 'containing', 'value': 'FAILED', 'format': failed_format})
            
            writer.close()

            # 2. Sent Log (sent_log.csv) - Başarılı kayıtları kaydeder
            sent_csv_path = os.path.join(self.current_run_dir, "sent_log.csv")
            if not sent_df.empty:
                sent_df.to_csv(sent_csv_path, index=False, encoding='utf-8')

            # 3. Failed Log (failed_log.csv) - Başarısız kayıtları kaydeder
            failed_csv_path = os.path.join(self.current_run_dir, "failed_log.csv")
            if not failed_df.empty:
                failed_df.to_csv(failed_csv_path, index=False, encoding='utf-8')

        except Exception as e:
            self._log_error(f"Rapor oluşturulurken hata oluştu: {e}")

if __name__ == "__main__":
    app = WhatsAppBroadcaster()
    app.mainloop()
