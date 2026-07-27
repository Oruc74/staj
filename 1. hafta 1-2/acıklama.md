📓 Numpy Hap Bilgi Not Defteri
📌 Temel Altın Kurallar
Tek Tip Kuralı (Homojen): Standart Python listelerine hem sayı hem metin koyabilirsin ama Numpy dizilerinin (array) içine koyduğun her şey aynı veri tipinde (örneğin sadece integer) olmak zorundadır. Bu kural onu inanılmaz hızlı yapar.

Döngü Yasak (Vektörizasyon): Numpy kullanırken for döngüsü yazıyorsan, Numpy'ı yanlış kullanıyorsun demektir. Tüm matrisi tek satırda çarpar, böler, filtrelersin.

Arka Plan C Dili: Numpy kodlarını sen Python'da yazarsın ama o çalışırken arka planda 'C' diline döner. Python'ın yavaşlığını bypass eder.

Boyut (Shape) Her Şeydir: Yapay zeka modelleri eğitirken alacağın hataların %90'ı "matris boyutlarının uyuşmamasıdır". (Örn: (3,3)'lük bir matrisi (2,2)'lik modele sokamazsın). Sık sık .shape ve .reshape() kullanacaksın.

🚀 Profesyonel Projelerde Neden Hayati Önem Taşıyor?
1. Veriyi Anlamlandırma (Her Şey Matristir):
Bilgisayar bir köpek fotoğrafını "köpek" olarak görmez; 1024x1024 boyutlarında piksellerden oluşan sayılar topluluğu (matris) olarak görür. Doğal dil işlemede kelimeler ("merhaba"), sayılardan oluşan vektörlere (embedding) dönüşür. İşte bu devasa sayı yığınlarını tutabilen ve işleyebilen tek araç Numpy'dır.

2. Hız ve Donanım Optimizasyonu:
Büyük veri setleriyle çalışırken Python'ın kendi fonksiyonlarını kullanırsan modelin 3 günde eğitilir. Aynı kodu Numpy fonksiyonlarıyla yazarsan işlem 3 saate düşer. Çünkü Numpy işlemciyi (CPU) çok daha verimli kullanacak şekilde dizayn edilmiştir.

3. Ekosistemin Omurgası Olması:
Yapay zeka ve veri bilimi dünyasındaki dev kütüphaneler (Pandas, Scikit-Learn, Matplotlib) bağımsız sistemler değildir. Hepsi arka planda veriyi Numpy dizisi olarak işler. Yani Numpy bilmeden bu kütüphaneleri yönetemezsin.
🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴

📓 JSON Hap Bilgi Not Defteri
📌 Temel Altın Kurallar
Çift Tırnak Kuralı: Anahtar kelimeler (Key) KESİNLİKLE çift tırnak ("") içinde yazılır. Tek tırnak ('') kullanırsan sistem patlar.

Virgül Tuzağı: Son elemandan sonra virgül (,) konmaz. En çok yapılan syntax (sözdizimi) hatası budur.

Sıfır Mantık: İçinde fonksiyon, metot veya hesaplama yapılamaz. Sadece saf veri tutar.

Yorum Yok: İçine // veya # ile yorum satırı eklenemez (Güvenlik ve ayrıştırma hızı sebebiyle)

🚀 Profesyonel Projelerde Neden Hayati Önem Taşıyor?
1. İki Yakayı Bir Araya Getiren Köprü:
Backend (Python/FastAPI) ile Frontend (React/TypeScript) birbirinin dilinden zerre anlamaz. Backend veriyi işler, JSON'a çevirir ve fırlatır. React bu JSON'ı havada yakalar, okur ve ekrandaki o güzel arayüze dönüştürür.

2. NoSQL ve MongoDB'nin Temeli:
SQL veri tabanları Excel gibi katı tablolarla çalışır. Ama MongoDB gibi NoSQL veri tabanları veriyi doğrudan bu gördüğün JSON (arka planda BSON) formatında depolar. O yüzden JSON'ı anlamak, MongoDB'yi yüzde 50 anlamak demektir.

3. Yapay Zekayı Koda Bağlama (JSON Mode):
LLM'ler (Geniş Dil Modelleri) normalde düz hikaye gibi metin üretir. Kodun içinde bir LLM'den gelen cevabı kullanmak istersen, düz metinden veriyi ayıklamak imkansızdır. O yüzden sisteme “Bana cevabı sadece JSON olarak dön” dersin. Model sana yapılandırılmış bir JSON atar, sen de bunu doğrudan değişkenlerine atarsın
🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴 🔴🔴