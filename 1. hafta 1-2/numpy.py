"""
=======================================================================
NUMPY (Numerical Python) NE İŞE YARAR? TEMEL MANTIĞI VE KULLANIM AMACI
=======================================================================
1. Yüksek Hız ve Performans: 
   Normal Python listeleri hafızada dağınık tutulduğu için büyük veri 
   setlerinde çok yavaş çalışır. Numpy ise arka planda 'C' programlama 
   diliyle yazıldığı ve verileri bitişik bloklar halinde tuttuğu için 
   devasa verilerde bile saniyenin binde biri sürede işlem yapar.

2. Döngüsüz İşlem (Vektörizasyon): 
   Klasik programlamada bir listedeki 10.000 elemanın her birine bir 
   matematiksel işlem uygulamak (örneğin 5 ile çarpmak) için 'for' 
   döngüsü yazmak zorundayız. Numpy'da ise diziyi (array) direkt 5 ile 
   çarparız. Bu sayede kod hem kısalır hem de inanılmaz hızlanır.

3. Yapay Zeka ve Optimizasyonun Temeli Olması: 
   Doğal Dil İşleme (NLP), makine öğrenmesi veya havacılık/sistem 
   optimizasyonu gibi alanlarda sistemler metinleri veya sensör 
   değerlerini anlamaz. Her şeyi matrislere (sayısal tablolara/tensörlere) 
   dönüştürmemiz gerekir. Numpy, bu devasa matrisleri oluşturup onları 
   hızlıca analiz etmemizi sağlayan omurgadır.

4. Gelişmiş Matematiksel Fonksiyonlar:
   İçerisinde ileri seviye istatistik, lineer cebir, matris çarpımları 
   ve şekil değiştirme (reshape) gibi yapay zeka modellerini eğitirken 
   kullandığımız tüm ağır matematiksel araçları hazır olarak sunar.
=======================================================================
"""

import numpy as np

# ==========================================
# 1. KÜÇÜK ÖRNEKLER (Isınma Turları)
# ==========================================

# 1 Boyutlu (1D) Array (Dizi) Oluşturma
sicakliklar = np.array([22.5, 23.1, 24.0, 21.8])

# 2 Boyutlu (2D) Matris Oluşturma 
# Örnek: Bir aracın 4 farklı andaki [İrtifa, Hız, Motor Sıcaklığı] değerleri
sensor_verisi = np.array([
    [120, 125, 130, 128],  # 0. Satır: İrtifa (Metre)
    [45,  48,  50,  47],   # 1. Satır: Hız (m/s)
    [22,  23,  26,  24]    # 2. Satır: Motor Sıcaklığı (°C)
])

# Vektörel İşlem: For döngüsü YAZMADAN tüm irtifayı 10 metre artırmak
yeni_irtifa = sensor_verisi[0] + 10 

# ==========================================
# 2. BÜYÜK ÖRNEK: VERİ MATRİSİNİ BİRLEŞTİRME VE ANALİZ
# ==========================================

def ucus_verilerini_analiz_et(veri_matrisi):
    print("--- SİSTEM OPTİMİZASYON ANALİZİ ---\n")
    
    # .shape: Matrisin boyutunu verir (Satır, Sütun)
    print(f"Veri Matrisi Boyutu: {veri_matrisi.shape}")
    
    # Slicing (Dilimleme): Sadece Hız ve Sıcaklık verilerini al (1. satırdan sona kadar)
    hiz_ve_sicaklik = veri_matrisi[1:, :]
    
    # Numpy İstatistiksel Fonksiyonları
    maks_irtifa = np.max(veri_matrisi[0])     # İlk satırın (İrtifa) maksimum değeri
    ortalama_hiz = np.mean(veri_matrisi[1])   # İkinci satırın (Hız) ortalaması
    
    print(f"Ulaşılan Maksimum İrtifa: {maks_irtifa} metre")
    print(f"Ortalama Uçuş Hızı: {ortalama_hiz:.2f} m/s")
    
    # Koşullu Seçim (Maskeleme): Numpy'ın en güçlü olduğu yer!
    # Sıcaklığın 25'ten büyük olduğu değerleri şak diye filtreler.
    kritik_sicaklik_anlari = veri_matrisi[2][veri_matrisi[2] > 25]
    
    if len(kritik_sicaklik_anlari) > 0:
        print(f"DİKKAT! Kritik motor sıcaklığı tespit edildi: {kritik_sicaklik_anlari} °C")
    else:
        print("Motor sıcaklıkları stabil seviyede.")

# Hazırladığımız 2 boyutlu veri matrisini fonksiyona yolluyoruz
ucus_verilerini_analiz_et(sensor_verisi)