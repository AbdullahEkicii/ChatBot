import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import random
from difflib import get_close_matches as yakin_sonuclari_getir
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import threading
import time
from datetime import datetime
import sys

try:
    # Windows'ta yüksek DPI için
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class ModernChatScreen:
    def __init__(self, master, get_response_func, add_new_answer_func):
        self.master = master
        self.get_response_func = get_response_func
        self.add_new_answer_func = add_new_answer_func
        self.typing_animation = False
        self.setup_colors()
        self.build_modern_ui()
        self.welcome_message()
        # Pencereyi güncelle ve min boyut ayarla
        self.master.update_idletasks()
        self.master.minsize(800, 600)
        
    def setup_colors(self):
        """Modern renk şeması"""
        self.colors = {
            'bg_primary': '#1a1a1a',      # Koyu arka plan
            'bg_secondary': '#2d2d2d',    # Mesaj alanı arka planı
            'bg_tertiary': '#3a3a3a',     # Giriş alanı arka planı
            'accent_blue': '#4a9eff',     # Mavi vurgu
            'accent_green': '#00d084',    # Yeşil vurgu
            'text_primary': '#ffffff',    # Ana metin
            'text_secondary': '#b0b0b0',  # İkincil metin
            'user_bubble': '#4a9eff',     # Kullanıcı mesaj balonu
            'bot_bubble': '#3a3a3a',      # Bot mesaj balonu
            'button_hover': '#5ab0ff',    # Buton hover efekti
            'error_red': '#ff4757',       # Hata rengi
            'success_green': '#2ed573'    # Başarı rengi
        }
    
    def build_modern_ui(self):
        """Modern arayüz tasarımı"""
        self.master.title("🤖 AI Chat Assistant")
        self.master.geometry("800x600")
        self.master.configure(bg=self.colors['bg_primary'])
        self.master.resizable(True, True)
        self.master.update_idletasks()
        self.master.minsize(800, 600)
        
        # Başlık çubuğu
        self.create_header()
        
        # Ana chat alanı
        self.create_chat_area()
        
        # Giriş alanı
        self.create_input_area()
        
        # Durum çubuğu
        self.create_status_bar()
        
        # Animasyon için timer
        self.setup_animations()
    
    def create_header(self):
        """Başlık çubuğu oluşturma"""
        header_frame = tk.Frame(self.master, bg=self.colors['bg_secondary'], height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Bot ikonu ve başlık
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        title_label = tk.Label(title_frame, text="🤖 AI Chat Assistant", 
                              font=("Segoe UI", 16, "bold"), 
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_secondary'])
        title_label.pack(side=tk.LEFT)
        
        # Durum göstergesi
        self.status_indicator = tk.Label(header_frame, text="● Çevrimiçi", 
                                       font=("Segoe UI", 10), 
                                       fg=self.colors['success_green'], 
                                       bg=self.colors['bg_secondary'])
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Ayarlar butonu
        settings_btn = tk.Button(header_frame, text="⚙️", 
                               font=("Segoe UI", 14), 
                               bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'],
                               border=0,
                               cursor="hand2",
                               command=self.show_settings)
        settings_btn.pack(side=tk.RIGHT, padx=10, pady=15)
    
    def create_chat_area(self):
        """Sohbet alanı oluşturma"""
        chat_frame = tk.Frame(self.master, bg=self.colors['bg_primary'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        chat_frame.pack_propagate(False)
        
        # Sohbet penceresi
        self.sohbet_alani = scrolledtext.ScrolledText(
            chat_frame, 
            state='disabled', 
            wrap=tk.WORD, 
            font=("Segoe UI", 12),  # Font büyütüldü
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent_blue'],
            selectbackground=self.colors['accent_blue'],
            selectforeground=self.colors['text_primary'],
            border=0,
            padx=15,
            pady=10
        )
        self.sohbet_alani.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar özelleştirme
        scrollbar = self.sohbet_alani.vbar
        scrollbar.config(bg=self.colors['bg_tertiary'], 
                        troughcolor=self.colors['bg_secondary'],
                        borderwidth=0,
                        highlightthickness=0)
    
    def create_input_area(self):
        """Giriş alanı oluşturma"""
        input_frame = tk.Frame(self.master, bg=self.colors['bg_primary'], height=80)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        input_frame.pack_propagate(False)
        
        # İç çerçeve
        inner_frame = tk.Frame(input_frame, bg=self.colors['bg_tertiary'])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Giriş alanı
        self.giris_alani = tk.Entry(
            inner_frame,
            font=("Segoe UI", 13),  # Font büyütüldü
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent_blue'],
            border=0,
            relief=tk.FLAT
        )
        self.giris_alani.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.giris_alani.bind('<Return>', lambda event: self.mesaj_gonder())
        self.giris_alani.bind('<KeyPress>', self.on_key_press)
        
        # Placeholder metin
        self.add_placeholder()
        
        # Gönder butonu
        self.gonder_buton = tk.Button(
            inner_frame,
            text="➤",
            font=("Segoe UI", 15, "bold"),  # Font büyütüldü
            bg=self.colors['accent_blue'],
            fg=self.colors['text_primary'],
            border=0,
            cursor="hand2",
            command=self.mesaj_gonder,
            width=4
        )
        self.gonder_buton.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Buton hover efekti
        self.gonder_buton.bind("<Enter>", lambda e: self.gonder_buton.config(bg=self.colors['button_hover']))
        self.gonder_buton.bind("<Leave>", lambda e: self.gonder_buton.config(bg=self.colors['accent_blue']))
    
    def create_status_bar(self):
        """Durum çubuğu oluşturma"""
        status_frame = tk.Frame(self.master, bg=self.colors['bg_secondary'], height=25)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Hazır", 
                                   font=("Segoe UI", 9), 
                                   fg=self.colors['text_secondary'], 
                                   bg=self.colors['bg_secondary'])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Mesaj sayacı
        self.mesaj_sayaci = tk.Label(status_frame, text="Mesaj: 0", 
                                   font=("Segoe UI", 9), 
                                   fg=self.colors['text_secondary'], 
                                   bg=self.colors['bg_secondary'])
        self.mesaj_sayaci.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def add_placeholder(self):
        """Placeholder metin ekleme"""
        self.placeholder_text = "Mesajınızı buraya yazın..."
        self.giris_alani.insert(0, self.placeholder_text)
        self.giris_alani.config(fg=self.colors['text_secondary'])
        
        self.giris_alani.bind('<FocusIn>', self.on_focus_in)
        self.giris_alani.bind('<FocusOut>', self.on_focus_out)
    
    def on_focus_in(self, event):
        """Giriş alanı focus aldığında"""
        if self.giris_alani.get() == self.placeholder_text:
            self.giris_alani.delete(0, tk.END)
            self.giris_alani.config(fg=self.colors['text_primary'])
    
    def on_focus_out(self, event):
        """Giriş alanı focus kaybettiğinde"""
        if not self.giris_alani.get():
            self.giris_alani.insert(0, self.placeholder_text)
            self.giris_alani.config(fg=self.colors['text_secondary'])
    
    def on_key_press(self, event):
        """Tuş basıldığında"""
        self.update_status("Yazıyor...")
        self.master.after(1000, lambda: self.update_status("Hazır"))
    
    def setup_animations(self):
        """Animasyon ayarları"""
        self.typing_dots = 0
        self.typing_timer = None
    
    def welcome_message(self):
        """Hoş geldin mesajı"""
        welcome_text = """
🤖 Merhaba! AI Chat Assistant'a hoş geldiniz!

✨ Bana istediğiniz soruyu sorabilirsiniz
📚 Öğrenmek istediğim konularda bana yardımcı olabilirsiniz
💬 Doğal dilde konuşabilirsiniz

Başlamak için bir mesaj yazın...
"""
        self.add_message("Bot", welcome_text, is_welcome=True)
    
    def add_message(self, sender, message, is_welcome=False):
        """Mesaj ekleme fonksiyonu"""
        self.sohbet_alani.config(state='normal')
        
        # Zaman damgası
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "Siz":
            # Kullanıcı mesajı
            self.sohbet_alani.insert(tk.END, f"\n")
            self.sohbet_alani.insert(tk.END, f"{'':>50}Siz {timestamp}\n", "user_header")
            self.sohbet_alani.insert(tk.END, f"{'':>30}{message}\n", "user_message")
        else:
            # Bot mesajı
            if not is_welcome:
                self.sohbet_alani.insert(tk.END, f"\n")
            self.sohbet_alani.insert(tk.END, f"🤖 Bot {timestamp}\n", "bot_header")
            self.sohbet_alani.insert(tk.END, f"{message}\n", "bot_message")
        
        # Metin stilleri
        self.sohbet_alani.tag_config("user_header", foreground=self.colors['accent_blue'], font=("Segoe UI", 10, "bold"))
        self.sohbet_alani.tag_config("user_message", foreground=self.colors['text_primary'], font=("Segoe UI", 11))
        self.sohbet_alani.tag_config("bot_header", foreground=self.colors['accent_green'], font=("Segoe UI", 10, "bold"))
        self.sohbet_alani.tag_config("bot_message", foreground=self.colors['text_primary'], font=("Segoe UI", 11))
        
        self.sohbet_alani.config(state='disabled')
        self.sohbet_alani.see(tk.END)
    
    def show_typing_indicator(self):
        """Yazıyor animasyonu"""
        self.typing_animation = True
        self.typing_dots = 0
        self._animate_typing()
    
    def _animate_typing(self):
        """Yazıyor animasyonu döngüsü"""
        if not self.typing_animation:
            return
        
        self.typing_dots = (self.typing_dots + 1) % 4
        dots = "." * self.typing_dots
        self.update_status(f"Bot yazıyor{dots}")
        
        self.typing_timer = self.master.after(500, self._animate_typing)
    
    def stop_typing_indicator(self):
        """Yazıyor animasyonunu durdur"""
        self.typing_animation = False
        if self.typing_timer:
            self.master.after_cancel(self.typing_timer)
        self.update_status("Hazır")
    
    def update_status(self, message):
        """Durum güncelleme"""
        self.status_label.config(text=message)
    
    def update_message_count(self):
        """Mesaj sayacı güncelleme"""
        current = self.mesaj_sayaci.cget("text")
        count = int(current.split(": ")[1]) + 1
        self.mesaj_sayaci.config(text=f"Mesaj: {count}")
    
    def mesaj_gonder(self):
        """Mesaj gönderme fonksiyonu"""
        soru = self.giris_alani.get().strip()
        
        # Placeholder kontrolü
        if not soru or soru == self.placeholder_text:
            self.shake_input()
            return
        
        soru_lower = soru.lower()
        
        # Mesaj ekleme
        self.add_message("Siz", soru)
        self.giris_alani.delete(0, tk.END)
        self.update_message_count()
        
        # Çıkış kontrolü
        if soru_lower in ['çık', 'exit', 'quit', 'bye']:
            self.add_message("Bot", "👋 Hoşçakalın! Tekrar görüşmek üzere...")
            self.master.after(2000, self.master.destroy)
            return
        
        # Bot yanıtını işleme
        self.process_bot_response(soru_lower)

    def process_bot_response(self, soru):
        """Bot yanıtını işleme"""
        # Typing indicator başlat
        self.show_typing_indicator()
        
        # Asenkron işlem
        def bot_response():
            time.sleep(1)  # Gerçekçi gecikme
            
            verilecek_cevap = self.get_response_func(soru)
            self.master.after(0, self.stop_typing_indicator)
            if verilecek_cevap and not verilecek_cevap.startswith("Üzgünüm, bu soruyla ilgili bir cevabım yok"):
                self.master.after(0, lambda: self.add_message("Bot", verilecek_cevap))
            else:
                self.master.after(0, lambda: self.handle_unknown_question(soru))
        
        # Thread'de çalıştır
        threading.Thread(target=bot_response, daemon=True).start()
    
        
    def handle_unknown_question(self, soru):
        """Bilinmeyen soru işleme"""
        message = "🤔 Bu konuda henüz bilgim yok. Bana öğretir misiniz?"
        self.add_message("Bot", message)
        self.master.after(500, lambda: self.cevap_ogret(soru))
    
    def shake_input(self):
        """Giriş alanını sallama animasyonu"""
        original_bg = self.giris_alani.cget('bg')
        self.giris_alani.config(bg=self.colors['error_red'])
        
        def restore_color():
            self.giris_alani.config(bg=original_bg)
        
        self.master.after(200, restore_color)
    
    def cevap_ogret(self, soru):
        """Cevap öğretme penceresi (modern ve kullanıcı dostu)"""
        ogret_pencere = tk.Toplevel(self.master)
        ogret_pencere.title("🎓 Botu Eğit")
        ogret_pencere.geometry("680x680")  # Boyut büyütüldü
        ogret_pencere.configure(bg=self.colors['bg_primary'])
        ogret_pencere.resizable(False, False)

        # Başlık
        title_label = tk.Label(ogret_pencere, text="🎓 Yeni Bilgi Öğret", 
                              font=("Segoe UI", 14, "bold"), 
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_primary'])
        title_label.pack(pady=(18, 5))

        # Açıklama
        aciklama = tk.Label(
            ogret_pencere,
            text="Bu sorunun cevabını biliyorsan aşağıya yazıp kaydedebilirsin.\nCevap vermek istemiyorsan 'Atla'ya tıkla.",
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        )
        aciklama.pack(pady=(0, 10))

        # Soru gösterimi
        soru_frame = tk.Frame(ogret_pencere, bg=self.colors['bg_secondary'])
        soru_frame.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(soru_frame, text="Soru:", font=("Segoe UI", 10, "bold"), 
                fg=self.colors['text_secondary'], bg=self.colors['bg_secondary']).pack(anchor=tk.W, padx=10, pady=3)
        tk.Label(soru_frame, text=soru, font=("Segoe UI", 11), 
                fg=self.colors['text_primary'], bg=self.colors['bg_secondary']).pack(anchor=tk.W, padx=10, pady=3)

        # Cevap girişi
        tk.Label(ogret_pencere, text="Cevap:", font=("Segoe UI", 10, "bold"), 
                fg=self.colors['text_secondary'], bg=self.colors['bg_primary']).pack(anchor=tk.W, padx=30, pady=(10, 3))
        cevap_alani = tk.Text(ogret_pencere, height=5, font=("Segoe UI", 12),
                             bg=self.colors['bg_tertiary'], fg=self.colors['text_primary'],
                             insertbackground=self.colors['accent_blue'], border=0)
        cevap_alani.pack(fill=tk.X, padx=30, pady=5)
        cevap_alani.focus()

        # Hata etiketi
        hata_label = tk.Label(ogret_pencere, text="", font=("Segoe UI", 9), fg=self.colors['error_red'], bg=self.colors['bg_primary'])
        hata_label.pack(pady=(0, 2))

        # Butonlar (ortalanmış)
        button_frame = tk.Frame(ogret_pencere, bg=self.colors['bg_primary'])
        button_frame.pack(pady=8)  # pady azaltıldı

        def kaydet():
            yeni_cevap = cevap_alani.get("1.0", tk.END).strip()
            if not yeni_cevap:
                hata_label.config(text="Lütfen bir cevap girin veya 'Atla'ya tıklayın.")
                cevap_alani.focus()
                return
            self.save_new_answer(soru, yeni_cevap)
            ogret_pencere.destroy()

        def atla():
            self.add_message("Bot", "📝 Tamam, bu soruyu atlıyorum.")
            ogret_pencere.destroy()

        kaydet_btn = tk.Button(button_frame, text="💾 Kaydet", 
                              command=kaydet,
                              font=("Segoe UI", 11, "bold"),
                              bg=self.colors['accent_green'],
                              fg=self.colors['text_primary'],
                              border=0, cursor="hand2", width=14, height=2)
        kaydet_btn.pack(side=tk.LEFT, padx=12)

        atla_btn = tk.Button(button_frame, text="⏭️ Atla", 
                            command=atla,
                            font=("Segoe UI", 11),
                            bg=self.colors['bg_tertiary'],
                            fg=self.colors['text_primary'],
                            border=0, cursor="hand2", width=14, height=2)
        atla_btn.pack(side=tk.LEFT, padx=12)

        # Enter ile kaydet, Shift+Enter ile satır atla
        def on_key(event):
            if event.keysym == "Return" and not (event.state & 0x0001):  # Shift yoksa
                kaydet()
                return "break"
            # Shift+Enter ile satır atla
        cevap_alani.bind("<Return>", on_key)

        # Pencereyi kapatınca atla gibi davran
        ogret_pencere.protocol("WM_DELETE_WINDOW", atla)
        ogret_pencere.transient(self.master)
        ogret_pencere.grab_set()
    
    def save_new_answer(self, soru, yeni_cevap):
        """Yeni cevabı kaydetme"""
        # Yeni cevabı ana ChatBot fonksiyonuna ilet
        self.add_new_answer_func(soru, yeni_cevap)
        self.add_message("Bot", "🎉 Teşekkürler! Yeni bir şey öğrendim.")
    
    def show_settings(self):
        """Ayarlar penceresi"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("⚙️ Ayarlar")
        settings_window.geometry("300x200")
        settings_window.configure(bg=self.colors['bg_primary'])
        
        tk.Label(settings_window, text="⚙️ Ayarlar", 
                font=("Segoe UI", 14, "bold"), 
                fg=self.colors['text_primary'], 
                bg=self.colors['bg_primary']).pack(pady=20)
        
        # Temizle butonu
        clear_btn = tk.Button(settings_window, text="🗑️ Sohbeti Temizle", 
                             command=self.clear_chat,
                             font=("Segoe UI", 10),
                             bg=self.colors['error_red'],
                             fg=self.colors['text_primary'],
                             border=0, cursor="hand2")
        clear_btn.pack(pady=10)
        
        # Hakkında butonu
        about_btn = tk.Button(settings_window, text="ℹ️ Hakkında", 
                             command=self.show_about,
                             font=("Segoe UI", 10),
                             bg=self.colors['accent_blue'],
                             fg=self.colors['text_primary'],
                             border=0, cursor="hand2")
        about_btn.pack(pady=10)
    
    def clear_chat(self):
        """Sohbeti temizleme"""
        if messagebox.askyesno("Onay", "Tüm sohbet geçmişini silmek istediğinize emin misiniz?"):
            self.sohbet_alani.config(state='normal')
            self.sohbet_alani.delete(1.0, tk.END)
            self.sohbet_alani.config(state='disabled')
            self.welcome_message()
    
    def show_about(self):
        """Hakkında penceresi"""
        about_text = """
🤖 AI Chat Assistant

Sürüm: 2.0
Geliştirici: Modern UI Team

Bu uygulama yapay zeka destekli 
bir sohbet asistanıdır.

© 2024 Tüm hakları saklıdır.
"""
        messagebox.showinfo("Hakkında", about_text)