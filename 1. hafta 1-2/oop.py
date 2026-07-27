"""
=======================================================================
OOP (NESNE YÖNELİMLİ PROGRAMLAMA) NE İŞE YARAR?
=======================================================================

1. Düzen ve Modülerlik: 
   Kodları dağınık fonksiyonlar olarak yazmak yerine, verileri ve bu 
   verilerle çalışan fonksiyonları "Sınıf" (Class) adı verilen tek bir 
   kapsülde toplar. Proje büyüdüğünde kodun çorbaya dönmesini engeller.

2. Tekrar Kullanılabilirlik (Şablon Mantığı): 
   Bir kere Sınıf (şablon) yazarsın, o şablondan istediğin kadar 
   Nesne (Object) üretirsin. Aynı kodları tekrar tekrar yazmaktan kurtarır.

3. Yapay Zeka ve Projelerdeki Yeri: 
   Yapay zeka modelleri (örn: bir LLM veya veri işleme aracı) karmaşık 
   sistemlerdir. Her model bir nesne olarak tasarlanır ki, farklı 
   parametreler ve verilerle birbirinden bağımsız, temiz çalışabilsin.
=======================================================================
"""
class MailAssistant:
    # 1. __init__ metodu: Nesne ilk oluşturulduğunda çalışır (Kurucu)
    def __init__(self, asistan_adi):
        # Değişkenler ve Veri Tipleri (String, Integer)
        self.asistan_adi = asistan_adi
        self.toplam_mail = 0
        
        # Veri Yapıları: Liste (List) ve Sözlük (Dictionary)
        self.gelen_kutusu = []       # Mailleri burada tutacağız
        self.iliski_skorlari = {}    # Kişilerin skorlarını eşleştireceğiz (Örn: {"Can": 60})

    # 2. Fonksiyonlar (Metotlar)
    def mail_ekle(self, gonderen, konu, aciliyet):
        # Sözlük oluşturup listeye ekleme (Veri yapılarını iç içe kullanma)
        yeni_mail = {
            "gonderen": gonderen, 
            "konu": konu, 
            "aciliyet": aciliyet
        }
        self.gelen_kutusu.append(yeni_mail)
        self.toplam_mail += 1
        print(f"[{self.asistan_adi}] Yeni mail eklendi: '{konu}'")

    def skorlari_hesapla(self):
        # 3. For Döngüsü: Listedeki her bir maili tek tek geziyoruz
        for mail in self.gelen_kutusu:
            kisi = mail["gonderen"]
            durum = mail["aciliyet"]
            
            # 4. If-Else Kontrol Yapıları
            # Eğer kişi sözlükte yoksa, ona varsayılan 50 puan verelim
            if kisi not in self.iliski_skorlari:
                self.iliski_skorlari[kisi] = 50
                
            # Aciliyet durumuna göre matematiksel işlemler
            if durum == "yüksek":
                self.iliski_skorlari[kisi] += 10
            elif durum == "normal":
                self.iliski_skorlari[kisi] += 2
            else:
                self.iliski_skorlari[kisi] -= 5

        print(f"[{self.asistan_adi}] Tüm ilişki skorları güncellendi!")

    def asistan_raporu(self):
        # F-string ile ekrana formatlı yazdırma
        print("\n--- GÜNCEL ASİSTAN RAPORU ---")
        print(f"İncelenen Toplam Mail: {self.toplam_mail}")
        print("Gönderenlerin Güncel Skorları:")
        
        # Sözlük içinde döngü kurma
        for kisi, skor in self.iliski_skorlari.items():
            print(f" - {kisi}: {skor} puan")


# ==========================================
# KODUN KULLANIMI (Nesne Üretme ve Test)
# ==========================================

# Sınıftan (Class) yeni bir nesne (Object) yaratıyoruz
asistanim = MailAssistant("Mail_AI")

# Asistana mailler ekliyoruz
asistanim.mail_ekle("hoca@universite.edu", "Staj Raporu Teslimi", "yüksek")
asistanim.mail_ekle("can@takim.com", "Naber kanka?", "düşük")
asistanim.mail_ekle("hoca@universite.edu", "Yeni Veritabanı Görevi", "yüksek")
asistanim.mail_ekle("gorkem@takim.com", "Toplantı Linki", "normal")

# Skor hesaplama metodunu çalıştırıyoruz (Döngüler ve if-else burada tetikleniyor)
asistanim.skorlari_hesapla()

# Sonuçları ekrana basıyoruz
asistanim.asistan_raporu()