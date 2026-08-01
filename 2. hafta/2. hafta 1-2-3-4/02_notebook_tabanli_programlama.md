# Hücre Tabanlı / Notebook Tabanlı Programlama

## Nedir?

Normal bir `.py` script'inde kod baştan sona tek parça halinde çalışır — dosyayı çalıştırırsın,
sonuç gelene kadar beklersin, bir şeyi değiştirmek istersen (örneğin veri setinin sadece bir
kısmını tekrar yüklemek) genelde her şeyi baştan çalıştırman gerekir.

**Notebook (Jupyter Notebook, Google Colab, VS Code Notebook vb.)** tabanlı programlama ise
kodu **hücrelere (cell)** böler. Her hücre bağımsız olarak çalıştırılabilir, ama aynı "kernel"
(çalışan Python süreci) içinde bellek paylaşırlar — yani bir hücrede tanımladığın `x` değişkeni,
sonraki hücrede hâlâ erişilebilirdir.

```
Hücre 1: import pandas as pd; df = pd.read_csv("veri.csv")   [Çalıştır ✅]
Hücre 2: df.head()                                            [Çalıştır ✅ — sonucu hemen görürsün]
Hücre 3: df["yeni_sutun"] = df["fiyat"] * 1.2                 [Çalıştır ✅]
Hücre 2'yi tekrar çalıştır → df.head() artık yeni_sutun'u da gösterir, veriyi yeniden yüklemene gerek yok
```

## Neden önemli?

### 1. Deneysel iş akışına uygun

Makine öğrenmesi/veri bilimi işi doğası gereği **iteratif ve keşif odaklıdır**: bir grafiği çiz,
bak, veriyi biraz filtrele, tekrar çiz, bir hiperparametreyi değiştir, tekrar eğit... Bu döngüyü her
seferinde tüm scripti baştan çalıştırarak (özellikle veri yükleme veya model eğitimi dakikalar
sürüyorsa) yapmak son derece verimsizdir. Notebook'ta sadece ilgili hücreyi değiştirip
çalıştırırsın; ağır işlemler (veri yükleme, model kurma) bir kere yapılır, kalan her şey hızlıca
denenir.

### 2. Anlık görselleştirme ve belgeleme bir arada

Bir hücrenin çıktısı (bir grafik, bir tablo, bir print) doğrudan o hücrenin altında görünür ve
kaydedilir. Kod, açıklama metni (Markdown hücreleri) ve çıktı (grafik/tablo) aynı dosyada iç
içe durur — bu da notebook'u hem çalışan bir kod hem de bir **rapor/anlatım** haline getirir.
(Tam olarak bu staj görevlerinde bizden istenen format da bu: "her adımdan sonra
`print(tensor.shape)` göster" — bu notebook'un doğal çalışma şeklidir.)

### 3. Öğrenme ve paylaşım için ideal

Yeni bir kütüphaneyi/API'yi öğrenirken küçük parçalar halinde deneme yapmak, hatanın tam
olarak hangi satırda olduğunu görmek çok daha kolaydır. Ayrıca Google Colab gibi bulut
tabanlı notebook'lar ücretsiz GPU sağlar ve link paylaşarak başkasının aynı ortamda,
kurulum yapmadan kodu çalıştırmasını sağlar — bu da staj/ödev teslimlerinde neden
"Colab linki paylaşın" denildiğini açıklar.

## Ne zaman notebook, ne zaman normal script?

| Senaryo | Tercih |
|---|---|
| Veri keşfi (EDA), görselleştirme, prototipleme | **Notebook** |
| Model mimarisini deneme, hiperparametre denemeleri | **Notebook** |
| Eğitim raporunu/adımlarını göstermek gereken ödev/sunum | **Notebook** |
| Production'a alınacak, sürekli/otomatik çalışacak kod (ör. bir API sunucusu, zamanlanmış bir ETL işi) | **Script (.py)** |
| Test edilebilir, versiyon kontrolüyle (git diff) takip edilmesi kritik kod | **Script (.py)** — notebook'ların `.ipynb` formatı JSON olduğu için git diff'i okumak zordur |
| Ekip içinde paylaşılacak, tekrar kullanılabilir kütüphane/modül kodu | **Script (.py)** |

## Pratik not

Gerçek dünyada bu ikisi genelde birlikte kullanılır: bir model önce notebook'ta denenir,
işe yaradığı netleşince asıl mantık `.py` dosyalarına (fonksiyon/sınıf olarak) taşınır ve notebook
sadece bu fonksiyonları çağırıp sonucu göstermek için kalır. Bu proje kapsamında da tam olarak
bu yaklaşımı izledim: bu klasördeki `09_attention_transformer_uygulamasi.ipynb` dosyası
notebook, ama içindeki mantık net fonksiyonlara bölünmüş durumda — böylece hem "adım adım
göster" gereksinimini karşılıyor hem de kod tekrar kullanılabilir kalıyor.
